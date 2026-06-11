from odoo import fields, models


class LensMemoriaeBulkTag(models.TransientModel):
    _name = "lensmemoriae.bulk.tag"
    _description = "Bulk Tag Images"

    image_ids = fields.Many2many("lensmemoriae.image", string="Images")
    tag_ids = fields.Many2many("lensmemoriae.tag", string="Tags")
    operation = fields.Selection(
        [("add", "Add Tags"), ("remove", "Remove Tags")],
        default="add",
        required=True,
    )

    def action_apply(self):
        images = self.image_ids
        for img in images:
            if self.operation == "add":
                img.write({"tag_ids": [(4, t.id) for t in self.tag_ids]})
            else:
                img.write({"tag_ids": [(3, t.id) for t in self.tag_ids]})
        return {"type": "ir.actions.act_window_close"}
