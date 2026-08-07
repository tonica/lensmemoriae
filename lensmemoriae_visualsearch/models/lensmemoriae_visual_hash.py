import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class LensMemoriaeVisualHash(models.Model):
    _name = "lensmemoriae.visual.hash"
    _description = "LensMemoriae Visual Search Hash"
    _order = "image_id, kind, region"
    _rec_name = "hash"

    image_id = fields.Many2one(
        "lensmemoriae.image",
        required=True,
        index=True,
        ondelete="cascade",
    )
    kind = fields.Char(string="Region Kind", required=True)
    region = fields.Char(string="Region", required=True)
    x = fields.Float(string="X", digits=(16, 4))
    y = fields.Float(string="Y", digits=(16, 4))
    width = fields.Float(string="Width", digits=(16, 4))
    height = fields.Float(string="Height", digits=(16, 4))
    hash = fields.Char(string="pHash", index=True, required=True)
