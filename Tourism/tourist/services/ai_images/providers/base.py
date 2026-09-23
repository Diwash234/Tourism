"""
AI image-generation provider abstraction.

Every provider implements the same small interface so the pipeline never
cares which backend actually generated an image. To add a provider,
subclass ``ImageProvider`` and register it in ``get_provider``.

Providers read their credentials from environment variables / Django
settings -- nothing is hard-coded.
"""
from __future__ import annotations
import abc
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GeneratedImage:
    """A single image returned by a provider."""
    url: str                       # remote URL or local media path
    provider: str
    model: str
    prompt: str
    negative_prompt: str = ""
    seed: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    b64: Optional[str] = None      # raw bytes (base64) when provider returns inline
    meta: dict = field(default_factory=dict)


class ImageProvider(abc.ABC):
    name: str = "base"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.kwargs = kwargs

    @abc.abstractmethod
    def generate(self, prompt: str, negative_prompt: str = "", n: int = 1,
                 size: str = "1024x1024", **kwargs) -> List[GeneratedImage]:
        """Return a list of GeneratedImage objects. Raise on failure."""
        raise NotImplementedError

    def is_configured(self) -> bool:
        return bool(self.api_key)


# ---------------------------------------------------------------------------
# Provider adapters. Each uses the official SDK if installed, otherwise a
# raw HTTP call. They import heavy deps lazily so the module loads even
# without the SDKs present.
# ---------------------------------------------------------------------------

class OpenAIProvider(ImageProvider):
    name = "openai"

    def generate(self, prompt, negative_prompt="", n=1, size="1024x1024", **kwargs):
        import requests
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        resp = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.kwargs.get("model", "gpt-image-1"),
                  "prompt": prompt, "n": n, "size": size,
                  **({"negative_prompt": negative_prompt} if negative_prompt else {})},
            timeout=120,
        )
        resp.raise_for_status()
        out = []
        for item in resp.json().get("data", []):
            out.append(GeneratedImage(
                url=item.get("url", ""), b64=item.get("b64_json"),
                provider=self.name, model=self.kwargs.get("model", "gpt-image-1"),
                prompt=prompt, negative_prompt=negative_prompt,
            ))
        return out


class StabilityProvider(ImageProvider):
    name = "stability"

    def generate(self, prompt, negative_prompt="", n=1, size="1024x1024", **kwargs):
        import requests
        if not self.api_key:
            raise RuntimeError("STABILITY_API_KEY is not set")
        w, h = size.split("x")
        resp = requests.post(
            f"https://api.stability.ai/v2beta/stable-image/generate/{self.kwargs.get('model','core')}",
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            files={"none": ""},
            data={"prompt": prompt, "negative_prompt": negative_prompt,
                  "output_format": "webp", "width": int(w), "height": int(h), "n": n},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return [GeneratedImage(
            url="", b64=img.get("base64"), provider=self.name,
            model=self.kwargs.get("model", "core"), prompt=prompt,
            negative_prompt=negative_prompt, seed=img.get("seed"),
        ) for img in data.get("images", [])]


class GoogleImagenProvider(ImageProvider):
    name = "google"

    def generate(self, prompt, negative_prompt="", n=1, size="1024x1024", **kwargs):
        import requests
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY / GEMINI_API_KEY is not set")
        model = self.kwargs.get("model", "imagen-3.0-generate-002")
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={self.api_key}",
            json={"instances": [{"prompt": prompt}],
                  "parameters": {"sampleCount": n, "negativePrompt": negative_prompt}},
            timeout=120,
        )
        resp.raise_for_status()
        out = []
        for pred in resp.json().get("predictions", []):
            bytes_b64 = pred.get("bytesBase64Encoded")
            out.append(GeneratedImage(
                url="", b64=bytes_b64, provider=self.name, model=model,
                prompt=prompt, negative_prompt=negative_prompt,
            ))
        return out


class FluxProvider(ImageProvider):
    """Black Forest Labs FLUX via Replicate or fal.ai adapter."""
    name = "flux"

    def generate(self, prompt, negative_prompt="", n=1, size="1024x1024", **kwargs):
        import requests
        token = self.api_key
        if not token:
            raise RuntimeError("REPLICATE_API_TOKEN / FAL_KEY is not set")
        w, h = size.split("x")
        model = self.kwargs.get("model", "black-forest-labs/flux-1.1-pro")
        resp = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={"Authorization": f"Bearer {token}", "Prefer": "wait"},
            json={"version": self.kwargs.get("version"), "input": {
                "prompt": prompt, "negative_prompt": negative_prompt,
                "width": int(w), "height": int(h), "num_outputs": n}},
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        return [GeneratedImage(
            url=u, provider=self.name, model=model, prompt=prompt,
            negative_prompt=negative_prompt,
        ) for u in (data.get("output") or [])]


class PollinationsProvider(ImageProvider):
    """
    Free, no-key reference provider (pollinations.ai). Used as a fallback
    when no commercial key is configured. Rate-limited; not for production
    scale but lets the pipeline run end-to-end out of the box.
    """
    name = "pollinations"

    def is_configured(self) -> bool:
        return True  # no key needed

    def generate(self, prompt, negative_prompt="", n=1, size="1024x1024", **kwargs):
        from urllib.parse import quote
        w, h = size.split("x")
        base = "https://image.pollinations.ai/prompt/"
        return [GeneratedImage(
            url=f"{base}{quote(prompt)}?width={w}&height={h}&nologo=true&seed={kwargs.get('seed', i*7+1)}",
            provider=self.name, model="flux", prompt=prompt,
            negative_prompt=negative_prompt, seed=kwargs.get("seed"),
        ) for i in range(n)]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
_PROVIDERS = {
    "openai": (OpenAIProvider, "OPENAI_API_KEY"),
    "stability": (StabilityProvider, "STABILITY_API_KEY"),
    "google": (GoogleImagenProvider, "GOOGLE_API_KEY"),
    "flux": (FluxProvider, "REPLICATE_API_TOKEN"),
    "pollinations": (PollinationsProvider, None),
}


def get_provider(name: Optional[str] = None) -> ImageProvider:
    """
    Return a configured provider. If ``name`` is None, pick the first
    commercially-configured provider, else fall back to the free Pollinations
    adapter so the system always works.
    """
    from django.conf import settings
    import os
    if name:
        cls, env = _PROVIDERS[name]
        key = os.environ.get(env or "", "") if env else ""
        return cls(api_key=key)
    for nm, (cls, env) in _PROVIDERS.items():
        if nm == "pollinations":
            continue
        if env and os.environ.get(env):
            return cls(api_key=os.environ[env])
    logger.warning("No commercial image API key configured; using free Pollinations provider")
    return PollinationsProvider()


def available_providers() -> List[str]:
    import os
    return [nm for nm, (_, env) in _PROVIDERS.items()
            if not env or os.environ.get(env)]
