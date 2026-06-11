from odoo import fields, models


class LensMemoriaeFaceBatchIdentify(models.TransientModel):
    _name = "lensmemoriae.face.batch.identify"
    _description = "Batch Identify Faces"

    face_ids = fields.Many2many(
        "lensmemoriae.face",
        string="Faces",
        required=True,
    )
    person_id = fields.Many2one(
        "lensmemoriae.person",
        required=True,
        string="Person",
    )

    def action_confirm(self):
        faces = self.face_ids
        faces |= self.env["lensmemoriae.face"].search(
            [
                ("suggested_person_id", "=", self.person_id.id),
                ("state", "=", "suggested"),
            ]
        )
        faces.write(
            {
                "person_id": self.person_id.id,
                "state": "identified",
                "identified_by": self.env.user.id,
                "identified_date": fields.Datetime.now(),
                "suggested_person_id": False,
            }
        )
        for face in faces:
            face._add_to_person_images()
        return {"type": "ir.actions.act_window_close"}
