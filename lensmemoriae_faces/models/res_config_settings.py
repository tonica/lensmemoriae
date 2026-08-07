from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    lensmemoriae_faces_enabled = fields.Boolean(
        string="Automatic Face Detection",
        config_parameter="lensmemoriae_faces.enabled",
        default=True,
        help="Enable/disable the scheduled face scan and suggestion crons. "
        "The manual 'Scan for Faces' button keeps working regardless.",
    )
    lensmemoriae_faces_scan_batch_size = fields.Integer(
        string="Images per Scan Run",
        config_parameter="lensmemoriae_faces.scan_batch_size",
        default=200,
        help="How many images the scheduled scan processes per run.",
    )
    lensmemoriae_faces_suggest_batch_size = fields.Integer(
        string="Faces per Suggestion Run",
        config_parameter="lensmemoriae_faces.suggest_batch_size",
        default=50,
        help="How many faces the scheduled suggestion cron evaluates per run.",
    )
