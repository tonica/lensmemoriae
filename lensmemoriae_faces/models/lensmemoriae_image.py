import base64
import io
import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    import numpy as np
    from face_recognition import (
        face_distance,
        face_encodings,
        face_locations,
    )
except ImportError:
    _logger.warning("face_recognition not available. Face features will be disabled.")
    np = None
    face_locations = None
    face_encodings = None
    face_distance = None


class LensMemoriaeImage(models.Model):
    _inherit = "lensmemoriae.image"

    face_ids = fields.One2many("lensmemoriae.face", "image_id")
    face_scan_state = fields.Selection(
        [
            ("pending", "Pending Scan"),
            ("scanning", "Scanning"),
            ("scanned", "Scanned"),
            ("error", "Error"),
        ],
        default="pending",
    )
    face_scan_date = fields.Datetime()
    face_count = fields.Integer(
        compute="_compute_face_count",
    )

    @api.depends("face_ids")
    def _compute_face_count(self):
        for rec in self:
            rec.face_count = len(rec.face_ids)

    def action_scan_faces(self):
        self.ensure_one()
        count = self._detect_faces()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Face Detection",
                "message": f"Detected {count} face(s) in this image.",
                "type": "success" if count else "info",
                "sticky": False,
            },
        }

    def _detect_faces(self):
        self.ensure_one()
        if not self.image:
            _logger.warning("No image data for %s", self.name)
            self.face_scan_state = "error"
            self.face_scan_date = fields.Datetime.now()
            return 0

        try:
            self.face_scan_state = "scanning"
            raw = base64.b64decode(self.image)
            from PIL import Image

            pil_img = Image.open(io.BytesIO(raw))
            img_array = np.array(pil_img.convert("RGB"))

            locations = face_locations(img_array)
            if not locations:
                self.face_scan_state = "scanned"
                self.face_scan_date = fields.Datetime.now()
                return 0

            encodings = face_encodings(img_array, locations)
            h, w, _ = img_array.shape
            Face = self.env["lensmemoriae.face"]
            existing = Face.search(
                [("image_id", "=", self.id), ("state", "!=", "ignored")]
            )
            if len(existing) >= len(locations):
                self.face_scan_state = "scanned"
                self.face_scan_date = fields.Datetime.now()
                return 0

            for i, (top, right, bottom, left) in enumerate(locations):
                if i < len(existing):
                    continue
                encoding_json = (
                    json.dumps(encodings[i].tolist()) if encodings else False
                )
                Face.create(
                    {
                        "image_id": self.id,
                        "top": top / h,
                        "right": right / w,
                        "bottom": bottom / h,
                        "left": left / w,
                        "encoding": encoding_json,
                    }
                )

            self.face_scan_state = "scanned"
            self.face_scan_date = fields.Datetime.now()
            return len(locations)

        except Exception:
            _logger.exception("Face detection failed for %s", self.name)
            self.face_scan_state = "error"
            self.face_scan_date = fields.Datetime.now()
            return 0

    @api.model
    def _cron_scan_faces(self, batch_size=10):
        images = self.search(
            [("face_ids", "=", False), ("image", "!=", False)],
            limit=batch_size,
        )
        scanned = 0
        for img in images:
            img._detect_faces()
            scanned += 1
        _logger.info("Scanned faces for %d images", scanned)
        return scanned

    @api.model
    def _cron_suggest_persons(self, batch_size=50):
        Face = self.env["lensmemoriae.face"]
        faces = Face.search(
            [
                ("state", "=", "detected"),
                ("encoding", "!=", False),
            ],
            limit=batch_size,
        )
        ref_faces = Face.search([("state", "=", "identified")])
        if not ref_faces:
            return 0
        ref_encodings = [json.loads(f.encoding) for f in ref_faces if f.encoding]
        ref_persons = [f.person_id.id for f in ref_faces if f.encoding]
        if not ref_encodings:
            return 0
        matched = 0
        for face in faces:
            try:
                encoding = json.loads(face.encoding)
                distances = face_distance(np.array(ref_encodings), np.array(encoding))
                best_idx = int(np.argmin(distances))
                best_dist = float(distances[best_idx])
                if best_dist < 0.5:
                    face.write(
                        {
                            "suggested_person_id": ref_persons[best_idx],
                            "confidence": 1.0 - best_dist,
                            "state": "suggested",
                        }
                    )
                    matched += 1
            except Exception:
                _logger.exception("Failed to suggest person for face %s", face.id)
        _logger.info("Suggested persons for %d faces", matched)
        return matched

    @api.model
    def _match_person_in_all_images(self, person_id):
        ref_faces = self.env["lensmemoriae.face"].search(
            [("person_id", "=", person_id), ("state", "=", "identified")]
        )
        if not ref_faces:
            return 0
        ref_encodings = [json.loads(f.encoding) for f in ref_faces if f.encoding]
        if not ref_encodings:
            return 0
        ref_encoding_array = np.array(ref_encodings)

        candidates = self.env["lensmemoriae.face"].search(
            [
                ("state", "in", ["detected", "suggested"]),
                ("person_id", "!=", person_id),
                ("suggested_person_id", "!=", person_id),
                ("encoding", "!=", False),
            ]
        )
        matched = 0
        for face in candidates:
            try:
                encoding = json.loads(face.encoding)
                distances = face_distance(ref_encoding_array, np.array(encoding))
                best_idx = int(np.argmin(distances))
                best_dist = float(distances[best_idx])
                if best_dist < 0.5:
                    face.write(
                        {
                            "suggested_person_id": person_id,
                            "confidence": 1.0 - best_dist,
                            "state": "suggested",
                        }
                    )
                    matched += 1
            except Exception:
                _logger.exception(
                    "Failed to match face %s for person %s", face.id, person_id
                )
        _logger.info("Found %d matches for person %s", matched, person_id)
        return matched
