from odoo import fields, models


class LensMemoriaeLocationPicker(models.TransientModel):
    _name = "lensmemoriae.location.picker"
    _description = "Location Picker"

    image_id = fields.Many2one("lensmemoriae.image", required=True)
    latitude = fields.Float(digits=(9, 6))
    longitude = fields.Float(digits=(9, 6))

    def action_save_location(self):
        self.image_id.write({"latitude": self.latitude, "longitude": self.longitude})
        return {"type": "ir.actions.act_window_close"}
