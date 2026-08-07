import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LensMemoriaeVisualSearchController(http.Controller):
    @http.route(
        "/lens-memoriae/visual-search",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def visual_search(self, image, limit=None, threshold=None, **kw):
        """JSON endpoint used by the Visual Search client action.

        ``image`` may be raw base64 or a ``data:`` URL produced by the browser.
        """
        if not image:
            return {"error": "No image provided."}
        if len(image) > 20 * 1024 * 1024:
            return {"error": "Image is too large (max 20 MB)."}
        try:
            results = request.env["lensmemoriae.image"].visual_search(
                image, limit=limit, threshold=threshold
            )
        except Exception:
            _logger.exception("Visual search failed")
            return {"error": "Visual search failed."}
        return {"results": results}
