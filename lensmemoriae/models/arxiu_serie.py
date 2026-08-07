from odoo import fields, models


class LensMemoriaeArxiuSerie(models.Model):
    _name = "lensmemoriae.arxiu.serie"
    _description = "Arxius en Línia - Sèrie d'un fons"
    _order = "codi_classificacio, id"

    fons_id = fields.Many2one("lensmemoriae.arxiu.fons", string="Fons", ondelete="cascade", required=True)
    name = fields.Char(string="Sèrie", required=True)
    codi_classificacio = fields.Char(string="Codi de classificació", index=True)
    unit_count = fields.Integer(string="Unitats")
    xml_attachment_id = fields.Many2one("ir.attachment", string="Fitxer XML", readonly=True)

    def action_download_xml(self):
        self.ensure_one()
        attachment = self.xml_attachment_id
        if not attachment:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Arxius en Línia",
                    "message": "El fitxer XML d'aquesta sèrie encara no s'ha generat.",
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=1" % attachment.id,
            "target": "self",
        }
