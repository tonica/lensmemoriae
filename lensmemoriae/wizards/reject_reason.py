from odoo import fields, models


class LensMemoriaeRejectReason(models.TransientModel):
    _name = "lensmemoriae.reject.reason"
    _description = "Note Rejection Reason"

    message_id = fields.Many2one("mail.message", required=True)
    reason = fields.Text(required=True)

    def action_confirm_reject(self):
        self.message_id.write(
            {
                "moderation_state": "rejected",
                "moderation_reason": self.reason,
                "moderated_by": self.env.user.id,
                "moderation_date": fields.Datetime.now(),
            }
        )
        return {"type": "ir.actions.act_window_close"}
