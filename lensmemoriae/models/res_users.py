from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    lensmemoriae_show_scrap = fields.Boolean(
        string="Show Scrap button",
        default=True,
    )
    lensmemoriae_show_clear_all = fields.Boolean(
        string="Show Clear All button",
        default=False,
    )
    lensmemoriae_show_download = fields.Boolean(
        string="Show Download Pending button",
        default=True,
    )
