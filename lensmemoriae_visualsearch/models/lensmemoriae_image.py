import base64
import io
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageOps

    import imagehash
except ImportError:
    _logger.warning(
        "imagehash/PIL not available. Visual search features will be disabled."
    )
    Image = None
    ImageOps = None
    imagehash = None

# Working image size for the region index (keeps hashing fast).
WORK_MAX_DIM = 512

# Default search parameters.
DEFAULT_THRESHOLD = 14
DEFAULT_LIMIT = 20


def _region_specs():
    """Return (kind, region, box) tuples.

    ``box`` is a 4-tuple of relative normalized coordinates in [0..1].
    """
    specs = []
    specs.append(("full", "", (0.0, 0.0, 1.0, 1.0)))
    specs.append(("center", "", (0.25, 0.25, 0.75, 0.75)))
    for r in range(2):
        for c in range(2):
            specs.append(
                ("quad", "r%dc%d" % (r, c), (c / 2, r / 2, (c + 1) / 2, (r + 1) / 2))
            )
    for r in range(3):
        for c in range(3):
            specs.append(
                ("ninth", "r%dc%d" % (r, c), (c / 3, r / 3, (c + 1) / 3, (r + 1) / 3))
            )
    for r in range(2):
        for c in range(2):
            specs.append(
                ("ov2x2", "r%dc%d" % (r, c), (c / 3, r / 3, c / 3 + 2 / 3, r / 3 + 2 / 3))
            )
    for r in range(3):
        for c in range(3):
            specs.append(
                ("ov3x3", "r%dc%d" % (r, c), (c / 4, r / 4, c / 4 + 0.5, r / 4 + 0.5))
            )
    return specs


_IMAGE_MAGIC = (
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG",       # PNG
    b"GIF8",          # GIF
    b"RIFF",          # WEBP
    b"BM",            # BMP
    b"\xff\x0a",      # TIFF (8-bit) - first bytes variant
    b"II*\x00",       # TIFF LE
    b"MM\x00*",       # TIFF BE
)


def _looks_like_raw_image(raw):
    return any(raw.startswith(magic) for magic in _IMAGE_MAGIC)


def _decode_image(data):
    """Decode raw image bytes, base64 bytes or a base64/data-URL string into a PIL RGB image."""
    if isinstance(data, str):
        if data.startswith("data:"):
            data = data.split(",", 1)[1]
        raw = base64.b64decode(data)
    elif isinstance(data, bytes):
        if data.startswith(b"data:"):
            data = data.split(b",", 1)[1]
            raw = base64.b64decode(data)
        elif _looks_like_raw_image(data):
            raw = data
        else:
            # Odoo Binary fields return base64-encoded bytes.
            raw = base64.b64decode(data)
    else:
        raw = data
    pil_img = Image.open(io.BytesIO(raw))
    if ImageOps and getattr(ImageOps, "exif_transpose", None):
        pil_img = ImageOps.exif_transpose(pil_img)
    return pil_img.convert("RGB")


def _phash(pil_img):
    """Return a 64-bit pHash as a hex string."""
    return str(imagehash.phash(pil_img))


def _hamming(a_hex, b_hex):
    return (int(a_hex, 16) ^ int(b_hex, 16)).bit_count()


class LensMemoriaeImage(models.Model):
    _inherit = "lensmemoriae.image"

    visual_hash_ids = fields.One2many(
        "lensmemoriae.visual.hash", "image_id", string="Visual Hashes"
    )
    visual_index_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("indexed", "Indexed"),
            ("error", "Error"),
        ],
        string="Visual Index State",
        default="pending",
    )
    visual_index_date = fields.Datetime(string="Visual Index Date")
    visual_hash_count = fields.Integer(
        compute="_compute_visual_hash_count",
        string="Hash Count",
        aggregator=False,
    )

    @api.depends("visual_hash_ids")
    def _compute_visual_hash_count(self):
        for rec in self:
            rec.visual_hash_count = len(rec.visual_hash_ids)

    def _load_working_image(self):
        """Return this picture as a PIL image downscaled to WORK_MAX_DIM."""
        self.ensure_one()
        if not self.image:
            return None
        pil_img = _decode_image(self.image)
        w, h = pil_img.size
        scale = min(1.0, WORK_MAX_DIM / max(w, h))
        if scale < 1.0:
            pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        return pil_img

    def _compute_region_hashes(self, pil_img):
        """Compute all region hashes for a working PIL image.

        Returns a list of dicts with kind, region and relative coords and the hash.
        """
        w, h = pil_img.size
        results = []
        for spec in _region_specs():
            kind, region, box = spec
            left, top, right, bottom = box
            crop = pil_img.crop(
                (int(left * w), int(top * h), int(right * w), int(bottom * h))
            )
            results.append(
                {
                    "kind": kind,
                    "region": region,
                    "x": left,
                    "y": top,
                    "width": right - left,
                    "height": bottom - top,
                    "hash": _phash(crop),
                }
            )
        return results

    def _build_visual_index(self):
        """(Re)compute and store all region hashes for ``self``.

        Returns the number of stored hashes or 0 on failure.
        """
        self.ensure_one()
        if not imagehash or not Image:
            return 0
        if not self.image:
            self.write({"visual_index_state": "error", "visual_index_date": fields.Datetime.now()})
            return 0

        self.write({"visual_index_state": "pending"})
        try:
            pil_img = self._load_working_image()
            if pil_img is None:
                raise ValueError("No image data")
            hashes = self._compute_region_hashes(pil_img)
        except Exception:
            _logger.exception("Visual index failed for %s", self.name)
            self.write({"visual_index_state": "error", "visual_index_date": fields.Datetime.now()})
            return 0

        vals_list = []
        for hsh in hashes:
            vals_list.append(
                {
                    "image_id": self.id,
                    "kind": hsh["kind"],
                    "region": hsh["region"],
                    "x": hsh["x"],
                    "y": hsh["y"],
                    "width": hsh["width"],
                    "height": hsh["height"],
                    "hash": hsh["hash"],
                }
            )
        if not vals_list:
            self.write({"visual_index_state": "error", "visual_index_date": fields.Datetime.now()})
            return 0

        VisualHash = self.env["lensmemoriae.visual.hash"].sudo()
        VisualHash.search([("image_id", "=", self.id)]).unlink()
        VisualHash.create(vals_list)
        self.write({"visual_index_state": "indexed", "visual_index_date": fields.Datetime.now()})
        return len(vals_list)

    def action_build_visual_index(self):
        """Manual indexing of the selected image(s)."""
        if not imagehash or not Image:
            return self._index_notify("danger", "Visual dependencies are not installed.")
        indexed = 0
        for rec in self:
            indexed += 1 if rec._build_visual_index() else 0
        return self._index_notify(
            "success", "Visual index built for %d image(s)." % indexed
        )

    def _index_notify(self, icon_type, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Visual Index",
                "message": message,
                "type": icon_type,
                "sticky": False,
            },
        }

    @api.model
    def _cron_visual_index(self, batch_size=15):
        if not imagehash or not Image:
            return 0
        images = self.search(
            [
                ("image", "!=", False),
                ("visual_index_state", "!=", "indexed"),
            ],
            limit=batch_size,
        )
        indexed = 0
        for rec in images:
            if rec._build_visual_index():
                indexed += 1
        _logger.info("Visual index cron processed %d images", indexed)
        return indexed

    @api.model
    def _reindex_all(self):
        if not imagehash or not Image:
            return 0
        images = self.search([("image", "!=", False)])
        indexed = 0
        for rec in images:
            if rec._build_visual_index():
                indexed += 1
        _logger.info("Visual index full reindex rebuilt %d images", indexed)
        return indexed

    def action_reindex_visual(self):
        if not imagehash or not Image:
            return self._index_notify("danger", "Image dependencies are not installed.")
        indexed = self._reindex_all()
        return self._index_notify("success", "Reindexed %d image(s)." % indexed)

    @api.model
    def visual_index_stats(self):
        """Return summary counts for the visual index control screen."""
        base = [("image", "!=", False)]
        total = self.search_count(base + [])
        indexed = self.search_count(base + [("visual_index_state", "=", "indexed")])
        pending = self.search_count(base + [("visual_index_state", "=", "pending")])
        error = self.search_count(base + [("visual_index_state", "=", "error")])
        return {
            "total": total,
            "indexed": indexed,
            "pending": pending,
            "error": error,
            "progress": round(indexed * 100.0 / total, 1) if total else 0.0,
        }

    @api.model
    def visual_search(self, image, limit=DEFAULT_LIMIT, threshold=DEFAULT_THRESHOLD):
        """Search stored images similar to a pasted/attached image or crop.

        ``image`` is raw bytes or a base64 string. Returns a list of dicts ordered
        by similarity, each including the matching region(s).
        """
        if not imagehash or not Image:
            raise UserError(self.env._("Visual search dependencies are not installed."))
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = DEFAULT_LIMIT
        if limit <= 0:
            limit = DEFAULT_LIMIT
        try:
            threshold = int(threshold)
        except (TypeError, ValueError):
            threshold = DEFAULT_THRESHOLD

        query_hash = _phash(_decode_image(image))

        rows = (
            self.env["lensmemoriae.visual.hash"]
            .sudo()
            .search_read([], ["image_id", "kind", "region", "x", "y", "width", "height", "hash"])
        )
        matches = {}
        for row in rows:
            dist = _hamming(query_hash, row["hash"])
            if dist > threshold:
                continue
            image_id = row["image_id"][0]
            entry = matches.setdefault(image_id, {"distance": dist, "regions": []})
            region = {
                "kind": row["kind"],
                "region": row["region"],
                "x": row["x"],
                "y": row["y"],
                "width": row["width"],
                "height": row["height"],
            }
            if dist < entry["distance"]:
                entry["distance"] = dist
                entry["best_region"] = region
            entry["regions"].append(region)

        if not matches:
            return []

        ordered_ids = sorted(matches, key=lambda i: matches[i]["distance"])[:limit]
        images = self.browse(ordered_ids)
        rec_map = {rec.id: rec for rec in images}
        results = []
        for image_id in ordered_ids:
            rec = rec_map.get(image_id)
            if not rec:
                continue
            dist = matches[image_id]["distance"]
            results.append(
                {
                    "id": rec.id,
                    "name": rec.name,
                    "relpath": rec.relpath,
                    "codi_referencia": rec.codi_referencia,
                    "similarity": round((1 - dist / 64.0) * 100, 1),
                    "best_region": matches[image_id].get("best_region"),
                    "regions": matches[image_id]["regions"],
                    "thumb_url": "/lens-memoriae/thumbnail/%d/400x400" % rec.id,
                }
            )
        return results