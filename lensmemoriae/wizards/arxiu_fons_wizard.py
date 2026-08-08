import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class LensMemoriaeArxiuFonsMatch(models.TransientModel):
    _name = "lensmemoriae.arxiu.fons.wizard.match"
    _description = "Coincidència de fons a descarregar"

    wizard_id = fields.Many2one(
        "lensmemoriae.arxiu.fons.wizard", ondelete="cascade", required=True
    )
    name = fields.Char(string="Fons", readonly=True)
    codi_referencia = fields.Char(string="Codi de referència", readonly=True)
    selected = fields.Boolean(string="Descarregar", default=True)


class LensMemoriaeArxiuFonsWizard(models.TransientModel):
    _name = "lensmemoriae.arxiu.fons.wizard"
    _description = "Descarrega un fons d'Arxius en Línia"

    fons_name = fields.Char(string="Nom del fons")
    matches_ids = fields.One2many(
        "lensmemoriae.arxiu.fons.wizard.match",
        "wizard_id",
        string="Fons trobats",
    )

    @api.onchange("fons_name")
    def _onchange_fons_name(self):
        matches = []
        if self.fons_name:
            try:
                matches = self.env["lensmemoriae.arxiu.fons"]._api_search_fons(
                    self.fons_name
                )
            except Exception:
                _logger.exception("Error cercant fons a la llista AENL")
                matches = []
        self.matches_ids = [
            (5, 0, 0),
            *[
                (0, 0, {"name": match["label"], "codi_referencia": match["value"]})
                for match in matches
            ],
        ]

    def action_refresh_fons_cache(self):
        return self.env["lensmemoriae.arxiu.fons"].action_refresh_fons_cache()

    def action_show_all(self):
        fons = self.env["lensmemoriae.arxiu.fons"]._get_fons_list()
        shown = fons[:300]
        self.matches_ids = [
            (5, 0, 0),
            *[
                (0, 0, {"name": match["label"], "codi_referencia": match["value"]})
                for match in shown
            ],
        ]
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Llista de fons",
                "message": (
                    "Es mostren les primeres %d coincidències de %d. "
                    "Escriu al camp per filtrar."
                )
                % (len(shown), len(fons)),
                "type": "info",
                "sticky": False,
            },
        }

    def action_download(self):
        selected = self.matches_ids.filtered("selected")
        if not selected:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Arxius en Línia",
                    "message": "Selecciona els fons que vols descarregar.",
                    "type": "warning",
                    "sticky": False,
                },
            }
        fons = self.env["lensmemoriae.arxiu.fons"]
        for match in selected:
            existing = fons.search(
                [("codi_referencia", "=", match.codi_referencia)], limit=1
            )
            if not existing:
                existing = fons.create(
                    {
                        "name": match.name or match.codi_referencia,
                        "codi_referencia": match.codi_referencia,
                    }
                )
            existing.action_download()
        return {"type": "ir.actions.act_window_close"}
