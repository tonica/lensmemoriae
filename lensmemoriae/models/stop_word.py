from odoo import api, fields, models


class LensMemoriaeStopWord(models.Model):
    _name = "lensmemoriae.stop.word"
    _description = "Word Cloud Stop Word"
    _order = "count desc, name"

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    count = fields.Integer(default=0)
    image_count = fields.Integer(default=0)

    _sql_constraints = [
        ("name_unique", "UNIQUE (name)", "This stop word already exists!"),
    ]

    def _invalidate_wordcloud_cache(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("lensmemoriae.wordcloud_cache", False)
        ICP.set_param("lensmemoriae.wordcloud_last_computed", False)

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._invalidate_wordcloud_cache()
        return recs

    def write(self, vals):
        res = super().write(vals)
        if "active" in vals or "name" in vals:
            self._invalidate_wordcloud_cache()
        return res

    def unlink(self):
        self._invalidate_wordcloud_cache()
        return super().unlink()

    def action_recalculate_wordcloud(self):
        Image = self.env["lensmemoriae.image"]
        words_data = Image._compute_words_from_descriptions()

        existing = {w.name: w for w in self.with_context(active_test=False).search([])}
        new_names = set()
        for w, c, ic in words_data:
            if w in existing:
                existing[w].write({"count": c, "image_count": ic})
            else:
                new_names.add(w)
            existing.pop(w, None)

        if existing:
            self.with_context(active_test=False).search(
                [("name", "in", list(existing.keys()))]
            ).unlink()

        vals_list = [
            {"name": w, "count": c, "image_count": ic, "active": True}
            for w, c, ic in words_data
            if w in new_names
        ]
        if vals_list:
            self.create(vals_list)

        self._invalidate_wordcloud_cache()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Word Cloud",
                "message": "S'ha recalculat el word cloud.",
                "type": "success",
                "sticky": False,
            },
        }
