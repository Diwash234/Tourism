#!/usr/bin/env python3
"""Automated Production Smoke Test Suite for Nepal Yatra.

Performs live end-to-end HTTP verification of the deployed application:
  - Frontend SPA entrypoint & static SEO endpoints (/robots.txt, /sitemap.xml)
  - Deployment health probe (/health/, /api/v1/health/)
  - Public catalogue queries (/api/v1/destinations/, /api/v1/districts/)
  - Spatial nearby discovery & route navigation endpoints
  - Authentication and trip sharing endpoints

Usage:
    python scripts/production_smoke.py [--base-url http://127.0.0.1:8000]
    SITE_URL=https://tourism-recommendation.onrender.com python scripts/production_smoke.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


class SmokeTestRunner:
    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.results: List[Tuple[str, str, int, float, bool, str]] = []

    def request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, bytes, Dict[str, str], float]:
        url = f"{self.base_url}{path}"
        req_headers = {"User-Agent": "NepalYatra-ProductionSmokeSuite/1.0"}
        if headers:
            req_headers.update(headers)

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed = (time.perf_counter() - start) * 1000
                content = resp.read()
                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                return resp.status, content, resp_headers, elapsed
        except urllib.error.HTTPError as exc:
            elapsed = (time.perf_counter() - start) * 1000
            content = exc.read()
            resp_headers = {k.lower(): v for k, v in exc.headers.items()}
            return exc.code, content, resp_headers, elapsed
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            raise ConnectionError(f"Failed to connect to {url}: {exc}") from exc

    def test(
        self,
        name: str,
        method: str,
        path: str,
        expected_status: List[int],
        body: Optional[Dict[str, Any]] = None,
        validator=None,
    ) -> bool:
        try:
            status, content, headers, elapsed = self.request(method, path, body)
            passed = status in expected_status
            note = f"HTTP {status}"

            if passed and validator:
                valid, val_note = validator(content, headers)
                if not valid:
                    passed = False
                    note = f"Validation failed: {val_note}"
                else:
                    note = f"HTTP {status} ({val_note})"

            self.results.append((name, path, status, elapsed, passed, note))
            return passed
        except Exception as exc:
            self.results.append((name, path, 0, 0.0, False, str(exc)))
            return False

    def run(self) -> int:
        print("=" * 76)
        print(f"NEPAL YATRA PRODUCTION SMOKE TEST SUITE")
        print(f"Target Origin: {self.base_url}")
        print("=" * 76)

        # 1. Root SPA entrypoint
        def val_html(content, headers):
            text = content.decode("utf-8", errors="ignore")
            if "<html" in text.lower() or "nepal yatra" in text.lower():
                return True, "Valid SPA HTML"
            return False, "Missing HTML document tags"

        self.test("Root SPA Entrypoint", "GET", "/", [200], validator=val_html)

        # 2. Robots.txt
        def val_robots(content, headers):
            text = content.decode("utf-8", errors="ignore")
            if "User-agent" in text:
                return True, "Robots.txt present"
            return False, "Missing User-agent declaration"

        self.test("Robots.txt Declaration", "GET", "/robots.txt", [200], validator=val_robots)

        # 3. Sitemap.xml
        def val_sitemap(content, headers):
            text = content.decode("utf-8", errors="ignore")
            if "urlset" in text or "sitemap" in text.lower():
                return True, "Valid XML Sitemap"
            return False, "Missing urlset declaration"

        self.test("Sitemap XML Index", "GET", "/sitemap.xml", [200], validator=val_sitemap)

        # 4. Root Health Check Probe
        def val_health(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                status = data.get("status")
                if status in ("ok", "degraded"):
                    return True, f"status={status}"
                return False, f"unexpected status {status}"
            except Exception as e:
                return False, f"JSON parse error: {e}"

        self.test("System Health Probe", "GET", "/health/", [200], validator=val_health)
        self.test("API Health Endpoint", "GET", "/api/v1/health/", [200], validator=val_health)

        # 5. Destination Catalogue API
        sample_slug = "kathmandu"

        def val_destinations(content, headers):
            nonlocal sample_slug
            try:
                data = json.loads(content.decode("utf-8"))
                items = data if isinstance(data, list) else data.get("results", [])
                if len(items) > 0:
                    first = items[0]
                    if first.get("slug"):
                        sample_slug = first["slug"]
                    return True, f"{len(items)} items returned"
                return False, "Empty destination array"
            except Exception as e:
                return False, f"Invalid JSON: {e}"

        self.test("Destinations Catalogue", "GET", "/api/v1/destinations/", [200], validator=val_destinations)

        # 6. Destination Detail by Slug
        def val_dest_detail(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                if data.get("name") or data.get("title") or data.get("slug"):
                    return True, f"found: {data.get('name') or data.get('slug')}"
                return False, "Missing destination name/slug"
            except Exception as e:
                return False, str(e)

        self.test(f"Destination Detail ({sample_slug})", "GET", f"/api/v1/destinations/{sample_slug}/", [200, 404], validator=val_dest_detail)

        # 7. Search Query API
        def val_search(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                results = data if isinstance(data, list) else data.get("results", [])
                return True, f"{len(results)} matches"
            except Exception as e:
                return False, str(e)

        self.test("Catalogue Search Query", "GET", "/api/v1/destinations/?search=temple", [200], validator=val_search)

        # 8. Canonical Districts Endpoint
        def val_districts(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
        # 8. Canonical Districts Endpoint
        def val_districts(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                count = data.get("count") or len(data.get("districts") or data.get("results") or data)
                return True, f"{count} districts recorded"
            except Exception as e:
                return False, str(e)

        self.test("77 Districts Catalogue", "GET", "/api/v1/districts/", [200], validator=val_districts)

        # 9. Spatial Discovery Nearby Places API
        def val_nearby(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                items = data if isinstance(data, list) else data.get("results", [])
                return True, f"{len(items)} nearby places found"
            except Exception as e:
                return False, str(e)

        self.test("Nearby Places Probe", "GET", "/api/v1/destinations/nearby/?latitude=27.7172&longitude=85.3240&radius_km=25", [200], validator=val_nearby)

        # 10. Navigation Road Routing Probe
        def val_route(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                if data.get("route") or data.get("directions") or data.get("steps") or data.get("distance_km"):
                    engine = data.get("routing_engine") or "graph/road"
                    return True, f"engine: {engine}"
                return False, "Missing route or step data"
            except Exception as e:
                return False, str(e)

        self.test(
            "Navigation Routing Endpoint",
            "POST",
            "/api/v1/navigation/route",
            [200],
            body={"start_latitude": 27.7172, "start_longitude": 85.3240, "end_latitude": 28.2096, "end_longitude": 83.9856},
            validator=val_route,
        )

        # 11. Travel Planner Curated Plans
        def val_plans(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                plans = data if isinstance(data, list) else data.get("results", [])
                return True, f"{len(plans)} plans available"
            except Exception as e:
                return False, str(e)

        self.test("Curated Travel Plans", "GET", "/api/v1/curated-itineraries/", [200], validator=val_plans)

        # 12. Authentication Endpoint Readiness Probe
        def val_auth(content, headers):
            try:
                data = json.loads(content.decode("utf-8"))
                if "detail" in data or "code" in data or "non_field_errors" in data:
                    return True, f"auth handled: {data.get('code') or 'rejected'}"
                return False, "Unexpected auth response body"
            except Exception as e:
                return False, str(e)

        self.test(
            "Auth Login Probe",
            "POST",
            "/api/v1/auth/login/",
            [400, 401, 404, 429],
            body={"email": "probe@example.com", "password": "bad"},
            validator=val_auth,
        )

        # Summary Presentation
        print("\n" + "-" * 76)
        print(f"{'ENDPOINT / FEATURE':<36} {'STATUS':<10} {'LATENCY':<10} {'OUTCOME'}")
        print("-" * 76)

        failures = 0
        for name, path, code, elapsed, passed, note in self.results:
            icon = "✓ PASS" if passed else "✗ FAIL"
            code_str = str(code) if code else "ERR"
            time_str = f"{elapsed:.1f}ms" if elapsed else "-"
            print(f"{name:<36} {code_str:<10} {time_str:<10} {icon} ({note})")
            if not passed:
                failures += 1

        print("=" * 76)
        if failures == 0:
            print(f"ALL {len(self.results)} PRODUCTION SMOKE GATES PASSED! System is operational.")
            print("=" * 76)
            return 0
        else:
            print(f"WARNING: {failures} of {len(self.results)} gates did not pass. Inspect logs above.")
            print("=" * 76)
            return 1


def main():
    parser = argparse.ArgumentParser(description="Live smoke testing suite for Nepal Yatra")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SITE_URL") or os.environ.get("PUBLIC_SITE_URL") or "http://127.0.0.1:8000",
        help="Target site origin (default: SITE_URL or http://127.0.0.1:8000)",
    )
    parser.add_argument("--timeout", type=int, default=15, help="HTTP request timeout in seconds (default: 15)")
    args = parser.parse_args()

    runner = SmokeTestRunner(base_url=args.base_url, timeout=args.timeout)
    sys.exit(runner.run())


if __name__ == "__main__":
    main()
