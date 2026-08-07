from odoo import api, fields, models


class LensMemoriaeArxiuFonsWizard(models.TransientModel):
    _name = "lensmemoriae.arxiu.fons.wizard"
    _description = "Descarrega un fons d'Arxius en Línia"

    fons_name = fields.Char(string="Nom del fons", required=True)
    fons_ids = fields.Many2many(
        "lensmemoriae.arxiu.fons",
        string="Fons a descarregar",
    )

    @api.onchange("fons_name")
    def _onchange_fons_name(self):
        matches = []
        if self.fons_name:
            try:
                matches = self.env["lensmemoriae.arxiu.fons"]._api_search_fons(self.fons_name)
            except Exception:
                matches = []
        fons_ids = []
        for match in matches:
            fons = self.env["lensmemoriae.arxiu.fons"].search(
                [("codi_referencia", "=", match["value"])], limit=1
            )
            if not fons:
                fons = self.env["lensmemoriae.arxiu.fons"].create(
                    {"name": match["label"], "codi_referencia": match["value"]}
                )
            fons_ids.append(fons.id)
        return {
            "fons_ids": [(6, 0, fons_ids)],
            "domain": {"fons_ids": [("id", "in", fons_ids)]},
        }

    def action_download(self):
        fons_records = self.fons_ids
        if not fons_records:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Arxius en Línia",
                    "message": "Marca a la llista de coincidències els fons que vols descarregar.",
                    "type": "warning",
                    "sticky": False,
                },
            }
        for fons in fons_records:
            fons.action_download()
        return {
            "type": "ir.actions.act_window_close",
        }