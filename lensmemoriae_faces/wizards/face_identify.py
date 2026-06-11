from odoo import fields, models


class LensMemoriaeFaceIdentify(models.TransientModel):
    _name = "lensmemoriae.face.identify"
    _description = "Identify Face"

    face_id = fields.Many2one("lensmemoriae.face", required=True)
    person_id = fields.Many2one(
        "lensmemoriae.person",
        required=True,
        string="Person",
    )

    def action_confirm(self):
        self.face_id.write(
            {
                "person_id": self.person_id.id,
                "state": "identified",
                "identified_by": self.env.user.id,
                "identified_date": fields.Datetime.now(),
            }
        )
        self.face_id._add_to_person_images()
        return {"type": "ir.actions.act_window_close"}
