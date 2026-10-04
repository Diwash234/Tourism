r"""OpenAPI generation fixes for the dual-prefix (v1 + v2) API surface.

drf-spectacular derives a default ``operationId`` by tokenising the request
path, and its tokenizer discards the two things that actually distinguish
one route from another::

    path = re.sub(r'\{[\w\-]+\}', '', path)   # /widgets/{id}/ -> /widgets/
    tokenized_path = path.rstrip('/').split('/')

So every child of a collection collapses onto its collection's id::

    GET /api/v1/curated-itineraries/          -> api_v1_curated_itineraries_retrieve
    GET /api/v1/curated-itineraries/{slug}/  -> api_v1_curated_itineraries_retrieve

This project makes that much worse: ``tourist.urls`` is mounted under both
``/api/v1/`` and ``/api/v2/``, and it registers deliberate slash-tolerance
aliases (``/feedback`` next to ``/feedback/``, ``/budget/summary`` next to
``/budget/summary/``) on top of that. The result was 80 colliding
operationIds. drf-spectacular "resolves" collisions by appending numeric
suffixes, so the published document advertised ids such as
``api_v1_admin_users_retrieve_2`` that map to no route at all -- exactly
what a generated client needs in order to break.

Two changes remove every collision without hiding a single endpoint:

``UniqueOperationIdSchema``
    Keeps the path variable in the tokenised path (``{slug}`` -> ``by_slug``)
    so a collection and its children get genuinely distinct ids.

``drop_slash_alias_operations``
    Drops the no-trailing-slash twin whenever the slashed route is also
    registered. Each such pair is one handler registered twice for
    compatibility, so documenting both would only duplicate one operation.
"""

import re

from drf_spectacular.openapi import AutoSchema


class UniqueOperationIdSchema(AutoSchema):
    """``AutoSchema`` that keeps path variables when building operationIds.

    Only ``_tokenize_path`` changes; the action name, the method position and
    the component-splitting behaviour are all inherited unchanged.
    """

    def _tokenize_path(self):
        path = re.sub(
            pattern=self.path_prefix,
            repl='',
            string=self.path,
            flags=re.IGNORECASE,
        )
        # Keep the path variable. The library default removes it entirely,
        # which is what makes /widgets/ and /widgets/{id}/ collide. Render it
        # as ``by_<name>`` so the token stays a valid identifier, and drop any
        # converter (``<int:pk>`` -> ``pk``) for the same reason.
        path = re.sub(pattern=r'\{(\w+)(?::[^}]+)?\}', repl=r'by_\1', string=path)
        return [token for token in path.strip('/').split('/') if token]


def drop_slash_alias_operations(endpoints, **kwargs):
    """Hide the no-trailing-slash twin of routes that are also registered with one.

    ``endpoints`` is drf-spectacular's list of ``(path, path_regex, method,
    view)`` tuples. Only a route whose slashed twin exists *for the same
    HTTP method* is removed, so a route that merely happens to end without a
    slash (``/ai-images/destinations``, ``/emergency/contacts``) is kept.
    """
    slashed = set()
    for path, _path_regex, method, _view in endpoints:
        if path.endswith('/'):
            slashed.add((method, path.rstrip('/') or '/'))

    return [
        endpoint
        for endpoint in endpoints
        # Keep anything that already ends in a slash, and keep a bare path
        # unless its slashed twin is registered for the same method.
        if endpoint[0].endswith('/') or (endpoint[2], endpoint[0]) not in slashed
    ]