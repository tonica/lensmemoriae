from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    lensmemoriae_public_blur_enabled = fields.Boolean(
        string="Blur on Public Thumbnails",
        config_parameter="lensmemoriae.public_blur_enabled",
    )
    lensmemoriae_public_watermark_enabled = fields.Boolean(
        string="Watermark on Public Thumbnails",
        config_parameter="lensmemoriae.public_watermark_enabled",
    )
    lensmemoriae_watermark_text = fields.Char(
        string="Watermark Text",
        config_parameter="lensmemoriae.watermark_text",
    )
    lensmemoriae_public_blur_intensity = fields.Integer(
        string="Blur Intensity",
        config_parameter="lensmemoriae.public_blur_intensity",
        default=10,
    )
    lensmemoriae_public_watermark_opacity = fields.Integer(
        string="Watermark Opacity (0–100%)",
        config_parameter="lensmemoriae.public_watermark_opacity",
        default=60,
        help="Opacity percentage (0 = invisible, 100 = fully opaque).",
    )
    lensmemoriae_public_watermark_font_scale = fields.Integer(
        string="Watermark Font Scale",
        config_parameter="lensmemoriae.public_watermark_font_scale",
        default=20,
    )
    lensmemoriae_public_watermark_spacing_x = fields.Float(
        string="Watermark Horizontal Spacing",
        config_parameter="lensmemoriae.public_watermark_spacing_x",
        default=2.5,
    )
    lensmemoriae_public_watermark_spacing_y = fields.Float(
        string="Watermark Vertical Spacing",
        config_parameter="lensmemoriae.public_watermark_spacing_y",
        default=3.0,
    )
    lensmemoriae_public_watermark_angle = fields.Integer(
        string="Watermark Angle",
        config_parameter="lensmemoriae.public_watermark_angle",
        default=30,
    )
    lensmemoriae_public_jpeg_quality = fields.Integer(
        string="JPEG Quality",
        config_parameter="lensmemoriae.public_jpeg_quality",
        default=85,
    )

    @api.model
    def set_values(self):
        for name in (
            "lensmemoriae_public_blur_enabled",
            "lensmemoriae_public_watermark_enabled",
            "lensmemoriae_watermark_text",
        ):
            icp = self._fields[name].config_parameter
            if not self[name]:
                self.env["ir.config_parameter"].sudo().set_param(icp, "False")
        for name in (
            "lensmemoriae_public_blur_intensity",
            "lensmemoriae_public_watermark_opacity",
            "lensmemoriae_public_watermark_font_scale",
            "lensmemoriae_public_watermark_spacing_x",
            "lensmemoriae_public_watermark_spacing_y",
            "lensmemoriae_public_watermark_angle",
            "lensmemoriae_public_jpeg_quality",
        ):
            if not self[name]:
                icp = self._fields[name].config_parameter
                self.env["ir.config_parameter"].sudo().set_param(
                    icp, str(self._fields[name].default)
                )
        return super().set_values()
