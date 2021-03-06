from django.middleware.cache import UpdateCacheMiddleware
from django.utils.cache import patch_vary_headers
from phased.utils import second_pass_render, drop_vary_headers


class PhasedRenderMiddleware(object):
    """
    Performs a second-phase template rendering on the response and should be
    placed before the UpdateCacheMiddleware
    (or :class:`~phased.middleware.PatchedVaryUpdateCacheMiddleware`) in the
    ``MIDDLEWARE_CLASES`` setting.
    """
    def process_response(self, request, response):
        """
        If the content-type starts with ``text/html`` performs a second-phase
        render on response.content and updates the ``Content-Length`` header
        of the response to reflect the change in size after rendering.
        """
        if not response['content-type'].startswith("text/html"):
            return response
        response.content = second_pass_render(request, response.content)
        response['Content-Length'] = str(len(response.content))
        return response


class PatchedVaryUpdateCacheMiddleware(UpdateCacheMiddleware):
    """
    If ``Vary: Cookie`` is set in the response object, Django's cache
    middleware will vary the cache key based on the value of the cookie.

    This subclass of Django's UpdateCacheMiddleware is designed to cache
    without varying the cache key on cookie contents.
    """
    def process_response(self, request, response):
        """
        This removes the ``Vary: Cookie`` header prior to running the standard
        Django ``UpdateCacheMiddleware.process_response()`` and adds the
        header back after caching so that in-browser caches are aware to vary
        the cache on cookies.
        """
        drop_vary_headers(response, ['Cookie'])
        response = super(PatchedVaryUpdateCacheMiddleware, self).process_response(request, response)
        patch_vary_headers(response, ['Cookie'])
        return response
