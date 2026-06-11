from odoo import api, fields, models
from odoo.fields import Domain


class MailMessage(models.Model):
    _inherit = "mail.message"

    moderation_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="approved",
    )
    moderated_by = fields.Many2one("res.users")
    moderation_date = fields.Datetime()
    moderation_reason = fields.Text()

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        if not self.env.su and not self.env.user.has_group(
            "lensmemoriae.group_moderator"
        ):
            moderation_filter = [
                "|",
                ("model", "!=", "lensmemoriae.image"),
                "|",
                ("moderation_state", "=", "approved"),
                ("author_id", "=", self.env.user.partner_id.id),
            ]
            domain = list(Domain(domain or []) & Domain(moderation_filter))
        return super().search(domain, offset=offset, limit=limit, order=order)

    lensmemoriae_image_preview = fields.Binary(
        string="Image", compute="_compute_lensmemoriae_image_preview"
    )

    def _compute_lensmemoriae_image_preview(self):
        for record in self:
            if record.model == "lensmemoriae.image" and record.res_id:
                record.lensmemoriae_image_preview = (
                    record.env["lensmemoriae.image"].browse(record.res_id).image
                )
            else:
                record.lensmemoriae_image_preview = False

    def action_open_image(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "lensmemoriae.image",
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }

    def action_moderate_approve(self):
        self.write(
            {
                "moderation_state": "approved",
                "moderated_by": self.env.user.id,
                "moderation_date": fields.Datetime.now(),
            }
        )
        return True

    def action_moderate_reject(self):
        ctx = dict(self.env.context, default_message_id=self.id)
        return {
            "type": "ir.actions.act_window",
            "name": "Motiu del Rebuig",
            "res_model": "lensmemoriae.reject.reason",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }
