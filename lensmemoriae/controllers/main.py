import base64
import json
import logging
import os
import time

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW = 60


def _safe_int(val, default):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val, default):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


class LensMemoriaeController(http.Controller):
    @http.route(
        "/lens-memoriae/thumbnail/<int:image_id>/<int:width>x<int:height>",
        auth="user",
        type="http",
    )
    def serve_thumbnail(self, image_id, width=0, height=0, **kw):
        image = request.env["lensmemoriae.image"].sudo().browse(image_id)
        if not image.exists():
            return request.not_found()

        att = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "lensmemoriae.image"),
                    ("res_id", "=", image.id),
                    ("res_field", "=", "image"),
                ],
                limit=1,
            )
        )
        if not att or not att.store_fname:
            return request.not_found()

        from odoo.tools.config import config

        filepath = os.path.join(config.filestore(request.db), att.store_fname)
        if not os.path.isfile(filepath):
            return request.not_found()

        with open(filepath, "rb") as f:
            raw = f.read()

        if width and height:
            from odoo.tools.image import image_process

            raw = image_process(raw, size=(width, height))

        return request.make_response(
            raw,
            [
                ("Content-Type", att.mimetype or "image/jpeg"),
                ("Cache-Control", "max-age=3600, public"),
            ],
        )

    @http.route(
        "/lens-memoriae/public-thumbnail/<public_uid>/<int:width>x<int:height>",
        auth="public",
        type="http",
    )
    def serve_public_thumbnail(self, public_uid, width=0, height=0, **kw):
        image = (
            request.env["lensmemoriae.image"]
            .sudo()
            .search([("public_uid", "=", public_uid)], limit=1)
        )
        if not image or not image.image:
            return request.not_found()

        from odoo.tools.image import image_process

        raw = image.image
        if isinstance(raw, str):
            raw = base64.b64decode(raw)
        elif raw[:4] != b"\xff\xd8\xff\xe0" and raw[:2] != b"\x89P":
            raw = base64.b64decode(raw)

        if width and height:
            raw = image_process(raw, size=(width, height))

        if self._is_rate_limited():
            return request.make_response(
                b"",
                [("Content-Type", "image/jpeg"), ("Retry-After", "60")],
                status=429,
            )

        ICP = request.env["ir.config_parameter"].sudo()
        blur_enabled = (
            ICP.get_param("lensmemoriae.public_blur_enabled", "False") == "True"
        )
        watermark_enabled = (
            ICP.get_param("lensmemoriae.public_watermark_enabled", "False") == "True"
        )
        watermark_text = ICP.get_param("lensmemoriae.watermark_text", "Alfons Güell")
        blur_intensity = _safe_int(
            ICP.get_param("lensmemoriae.public_blur_intensity", "10"), 10
        )
        watermark_opacity = _safe_int(
            ICP.get_param("lensmemoriae.public_watermark_opacity", "60"), 60
        )
        watermark_font_scale = _safe_int(
            ICP.get_param("lensmemoriae.public_watermark_font_scale", "20"), 20
        )
        watermark_spacing_x = _safe_float(
            ICP.get_param("lensmemoriae.public_watermark_spacing_x", "2.5"), 2.5
        )
        watermark_spacing_y = _safe_float(
            ICP.get_param("lensmemoriae.public_watermark_spacing_y", "3.0"), 3.0
        )
        watermark_angle = _safe_int(
            ICP.get_param("lensmemoriae.public_watermark_angle", "30"), 30
        )
        jpeg_quality = _safe_int(
            ICP.get_param("lensmemoriae.public_jpeg_quality", "85"), 85
        )

        cache_field = (
            f"public_thumb_{width}x{height}"
            f"_blur{int(blur_enabled)}_bi{blur_intensity}"
            f"_wm{int(watermark_enabled)}_wo{watermark_opacity}"
            f"_fs{watermark_font_scale}_sx{watermark_spacing_x}"
            f"_sy{watermark_spacing_y}_a{watermark_angle}"
            f"_j{jpeg_quality}"
        )
        att = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "lensmemoriae.image"),
                    ("res_id", "=", image.id),
                    ("res_field", "=", cache_field),
                ],
                limit=1,
            )
        )
        if att and att.store_fname:
            from odoo.tools.config import config

            filepath = os.path.join(config.filestore(request.db), att.store_fname)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    raw = f.read()
                return request.make_response(
                    raw,
                    [
                        ("Content-Type", "image/jpeg"),
                        ("Cache-Control", "max-age=86400, public"),
                    ],
                )

        from .image_protection import protect_image

        raw = protect_image(
            raw,
            blur_enabled=blur_enabled,
            watermark_enabled=watermark_enabled,
            watermark_text=watermark_text,
            blur_intensity=blur_intensity,
            watermark_opacity=watermark_opacity,
            watermark_font_scale=watermark_font_scale,
            watermark_spacing_x=watermark_spacing_x,
            watermark_spacing_y=watermark_spacing_y,
            watermark_angle=watermark_angle,
            jpeg_quality=jpeg_quality,
        )

        att_data = base64.b64encode(raw)
        if att:
            att.write({"datas": att_data})
        else:
            request.env["ir.attachment"].sudo().create(
                {
                    "name": (
                        f"public_thumb_{image.id}_{width}x{height}"
                        f"_blur{int(blur_enabled)}_wm{int(watermark_enabled)}.jpg"
                    ),
                    "res_model": "lensmemoriae.image",
                    "res_id": image.id,
                    "res_field": cache_field,
                    "datas": att_data,
                    "mimetype": "image/jpeg",
                }
            )

        return request.make_response(
            raw,
            [
                ("Content-Type", "image/jpeg"),
                ("Cache-Control", "max-age=86400, public"),
            ],
        )

    def _is_rate_limited(self):
        ICP = request.env["ir.config_parameter"].sudo()
        key = "lensmemoriae.public_thumbnail_rate_limit"
        raw = ICP.get_param(key, "{}")
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            data = {}

        ip = request.httprequest.remote_addr
        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW

        # Clean old entries and count requests for this IP
        for addr in list(data.keys()):
            data[addr] = [ts for ts in data[addr] if ts > window_start]
            if not data[addr]:
                del data[addr]

        ip_requests = data.get(ip, [])
        ip_requests = [ts for ts in ip_requests if ts > window_start]
        limited = len(ip_requests) >= RATE_LIMIT_MAX

        if not limited:
            ip_requests.append(now)
            data[ip] = ip_requests

        ICP.set_param(key, json.dumps(data))
        return limited
