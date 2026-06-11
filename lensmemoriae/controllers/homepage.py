import logging
import random

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LensMemoriaePublicHome(http.Controller):
    @http.route("/lensmemoriae-home", auth="public", sitemap=False)
    def index(self, **kw):
        # Odoo ORM doesn't accept RANDOM() in order, so fetch all and shuffle
        images = (
            request.env["lensmemoriae.image"].sudo().search([("image", "!=", False)])
        )
        images_list = list(images)
        random.shuffle(images_list)
        selected = images_list[:8]
        _logger.warning(
            "Homepage: found %d images, selected %d", len(images_list), len(selected)
        )
        for img in selected:
            _logger.warning("  Image id=%s name=%s", img.id, img.name)
        return request.render(
            "lensmemoriae.homepage",
            {
                "images": selected,
            },
        )
