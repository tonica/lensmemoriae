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

    def action_download_match(self):
        self.ensure_one()
        fons = self.env["lensmemoriae.arxiu.fons"]
        existing = fons.search(
            [("codi_referencia", "=", self.codi_referencia)], limit=1
        )
        if not existing:
            existing = fons.create(
                {
                    "name": self.name,
                    "codi_referencia": self.codi_referencia,
                }
            )
        existing.action_download()
        return {"type": "ir.actions.act_window_close"}


class LensMemoriaeArxiuFonsWizard(models.TransientModel):
    _name = "lensmemoriae.arxiu.fons.wizard"
    _description = "Descarrega un fons d'Arxius en Línia"

    fons_name = fields.Char(string="Nom del fons")
    result = fields.Char(string="Resultat", readonly=True)
    matches_ids = fields.One2many(
        "lensmemoriae.arxiu.fons.wizard.match",
        "wizard_id",
        string="Fons trobats",
    )

    def _notification(self, message, notif_type="info"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Arxius en Línia",
                "message": message,
                "type": notif_type,
                "sticky": False,
            },
        }

    def _search_fons(self):
        """Return (matches, message). Matches contains every fond whose name
        contains the search term; the caller decides what to do with them."""
        if not self.fons_name:
            return [], "Escriu el nom d'un fons per cercar-lo."
        matches = []
        try:
            matches = self.env["lensmemoriae.arxiu.fons"]._api_search_fons(
                self.fons_name
            )
        except Exception:
            _logger.exception("Error cercant fons a la llista AENL")
        if not matches:
            return [], "No s'ha trobat cap fons «%s»." % self.fons_name
        return matches, ""

    @api.onchange("fons_name")
    def _onchange_fons_name(self):
        matches, message = self._search_fons()
        self.matches_ids = [(5, 0, 0)]
        if not matches:
            self.result = message or ""
        elif len(matches) == 1:
            match = matches[0]
            self.result = "Fons: %s (%s)" % (match["label"], match["value"])
        else:
            self.result = (
                "%d fons trobats: prem «Consulta llista de fons» per veure'ls "
                "o escriu un nom més precís." % len(matches)
            )

    def action_refresh_fons_cache(self):
        return self.env["lensmemoriae.arxiu.fons"].action_refresh_fons_cache()

    def action_show_all_fons(self):
        fons = self.env["lensmemoriae.arxiu.fons"]._get_fons_list()
        if not fons:
            return self._notification(
                "No hi ha llista de fons disponible: prem «Actualitza llista de fons».",
                "warning",
            )
        self.write(
            {
                "fons_name": False,
                "result": "%d fons disponibles:" % len(fons),
                "matches_ids": [
                    (5, 0, 0),
                    *[
                        (0, 0, {"name": item["label"], "codi_referencia": item["value"]})
                        for item in fons
                    ],
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "lensmemoriae.arxiu.fons.wizard.match",
            "name": "Consulta llista de fons",
            "domain": [("wizard_id", "=", self.id)],
            "views": [[False, "list"]],
            "target": "new",
        }

    def action_download(self):
        matches, message = self._search_fons()
        if not matches:
            return self._notification(message or "No s'ha trobat cap fons.", "warning")
        if len(matches) > 1:
            return self._notification(
                "Hi ha %d fons coincidents: prem «Consulta llista de fons» per triar-ne un."
                % len(matches),
                "warning",
            )
        match = matches[0]
        fons = self.env["lensmemoriae.arxiu.fons"]
        existing = fons.search([("codi_referencia", "=", match["value"])], limit=1)
        if not existing:
            existing = fons.create(
                {
                    "name": match["label"],
                    "codi_referencia": match["value"],
                }
            )
        existing.action_download()
        return {"type": "ir.actions.act_window_close"}
