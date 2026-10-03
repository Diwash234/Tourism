"""Shared page-number pagination for the public API.

Two bugs lived here, and both were user-visible on the destinations listing.

1. ``get_next_link``/``get_previous_link`` were declared as
   ``(self, obj)`` -- the signature DRF uses -- but ``get_paginated_response``
   called them with no argument. That raised
   ``TypeError: StandardResultsPagination.get_next_link() missing 1 required
   positional argument: 'obj'`` inside ``get_paginated_response``, so **every
   paginated endpoint in the project answered HTTP 500**: the destination
   list, destination search, hotels, hospitals, police, reviews. The public
   site had no listing at all.

2. Even when it did not 500, the links were the bare string ``?page=2``.
   That discards every other query parameter, so paging from a filtered
   search silently dropped the filter and showed unfiltered results on page 2.

The link is now built from the incoming query string with only the page
parameter replaced, so ``?search=pokhara&district=Kaski&page=2`` stays a
filtered page 2.
"""

from urllib.parse import urlencode

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def _page_link(self, page_number):
        """Absolute URL for ``page_number``, preserving all other filters.

        Every parameter the caller sent is carried through unchanged except
        the page number itself, so paging never silently discards a search
        term or an active filter.
        """
        if not page_number:
            return None
        params = self.request.query_params.copy()
        params[self.page_query_param] = page_number
        base = self.request.build_absolute_uri().split("?", 1)[0]
        return f"{base}?{urlencode(params, doseq=True)}"

    # `obj=None` keeps DRF's own call sites working (it passes the page's
    # object list) while allowing the argument-free call this class makes.
    def get_next_link(self, obj=None):
        if self.page.has_next():
            return self._page_link(self.page.next_page_number())
        return None

    def get_previous_link(self, obj=None):
        if self.page.has_previous():
            return self._page_link(self.page.previous_page_number())
        return None

    def get_first_link(self):
        return self._page_link(1)

    def get_last_link(self):
        return self._page_link(self.page.paginator.num_pages)

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "page_size": self.get_page_size(self.request),
                "current_page": self.page.number,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "first": self.get_first_link(),
                "last": self.get_last_link(),
                "results": data,
            }
        )