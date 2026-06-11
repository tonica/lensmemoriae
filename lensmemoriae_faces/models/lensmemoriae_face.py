import base64
import io
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class LensMemoriaeFace(models.Model):
    _name = "lensmemoriae.face"
    _description = "Detected Face"
    _order = "id desc"
    name = fields.Char(compute="_compute_name", store=False)

    @api.depends("person_id", "state", "image_id")
    def _compute_name(self):
        for rec in self:
            if rec.person_id:
                rec.name = rec.person_id.name
            elif rec.state == "suggested" and rec.suggested_person_id:
                rec.name = f"{rec.suggested_person_id.name}?"
            else:
                rec.name = f"Face #{rec.id}"

    image_id = fields.Many2one(
        "lensmemoriae.image",
        required=True,
        ondelete="cascade",
    )
    person_id = fields.Many2one(
        "lensmemoriae.person",
        ondelete="set null",
        index=True,
    )
    state = fields.Selection(
        [
            ("detected", "Detected"),
            ("suggested", "Suggestion"),
            ("identified", "Identified"),
            ("ignored", "Ignored"),
        ],
        default="detected",
        required=True,
        index=True,
    )
    suggested_person_id = fields.Many2one(
        "lensmemoriae.person",
        ondelete="set null",
    )
    confidence = fields.Float()
    top = fields.Float()
    right = fields.Float()
    bottom = fields.Float()
    left = fields.Float()
    encoding = fields.Text()
    thumbnail = fields.Binary(
        compute="_compute_thumbnail",
        store=False,
    )
    identified_by = fields.Many2one("res.users")
    identified_date = fields.Datetime()
    image_name = fields.Char(related="image_id.name", string="Image Name", store=False)

    @api.depends("image_id.image", "top", "right", "bottom", "left")
    def _compute_thumbnail(self):
        for rec in self:
            if not rec.image_id.image or not all(
                [rec.top, rec.right, rec.bottom, rec.left]
            ):
                rec.thumbnail = False
                continue
            try:
                from PIL import Image

                raw = base64.b64decode(rec.image_id.image)
                pil_img = Image.open(io.BytesIO(raw))
                w, h = pil_img.size
                box = (
                    int(rec.left * w),
                    int(rec.top * h),
                    int(rec.right * w),
                    int(rec.bottom * h),
                )
                crop = pil_img.crop(box)
                buf = io.BytesIO()
                crop.save(buf, format="PNG")
                rec.thumbnail = base64.b64encode(buf.getvalue())
            except Exception:
                _logger.exception("Failed to generate face thumbnail")
                rec.thumbnail = False

    def action_identify(self):
        self.ensure_one()
        ctx = dict(
            self.env.context,
            default_face_id=self.id,
            default_person_id=self.person_id.id,
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Identify Person",
            "res_model": "lensmemoriae.face.identify",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }

    def action_ignore(self):
        self.write({"state": "ignored"})
        return True

    def action_accept_suggestion(self):
        self.ensure_one()
        if self.suggested_person_id:
            person = self.suggested_person_id
            self.write(
                {
                    "person_id": person.id,
                    "state": "identified",
                    "identified_by": self.env.user.id,
                    "identified_date": fields.Datetime.now(),
                    "suggested_person_id": False,
                }
            )
            self._add_to_person_images()
        return True

    def action_clear_suggestion(self):
        self.write({"suggested_person_id": False, "state": "detected"})
        return True

    def _add_to_person_images(self):
        self.ensure_one()
        if self.person_id and self.image_id:
            self.person_id.write({"image_ids": [(4, self.image_id.id)]})
