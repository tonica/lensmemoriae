from odoo import api, fields, models


class LensMemoriaePerson(models.Model):
    _name = "lensmemoriae.person"
    _description = "Identified Person"
    _order = "name"

    name = fields.Char(required=True)
    notes = fields.Text()
    partner_id = fields.Many2one("res.partner", string="Contact")
    face_ids = fields.One2many(
        "lensmemoriae.face", "person_id", string="Reference Faces"
    )
    image_ids = fields.Many2many(
        "lensmemoriae.image",
        relation="lensmemoriae_image_person_rel",
        column1="person_id",
        column2="image_id",
        string="Photos",
    )
    face_count = fields.Integer(compute="_compute_face_count", string="Faces")
    image_count = fields.Integer(compute="_compute_image_count", string="Photos")

    @api.depends("face_ids")
    def _compute_face_count(self):
        for rec in self:
            rec.face_count = len(rec.face_ids)

    @api.depends("image_ids")
    def _compute_image_count(self):
        for rec in self:
            rec.image_count = len(rec.image_ids)

    def action_open_images(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "lensmemoriae.image",
            "domain": [("face_ids.person_id", "=", self.id)],
            "context": dict(self.env.context, search_default_person_id=self.id),
            "view_mode": "kanban,list,form",
            "target": "current",
        }

    def action_find_matches(self):
        self.ensure_one()
        Image = self.env["lensmemoriae.image"]
        matched = Image._match_person_in_all_images(self.id)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Search Complete",
                "message": f"Found {matched} new potential matches for {self.name}.",
                "type": "success" if matched else "info",
                "sticky": False,
            },
        }
