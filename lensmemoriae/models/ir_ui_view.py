from lxml import etree

from odoo import api, models


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    @api.model
    def _lensmemoriae_filter_header_buttons(self, arch):
        user = self.env.user
        if not user.has_group("lensmemoriae.group_moderator"):
            return arch
        prefs = {
            "action_scan": user.lensmemoriae_show_scan,
            "action_open_scrap_wizard": user.lensmemoriae_show_scrap,
            "action_clear_images": user.lensmemoriae_show_clear_all,
            "action_generate_descriptions": user.lensmemoriae_show_generate_desc,
            "action_download_pending": user.lensmemoriae_show_download,
        }
        doc = etree.fromstring(arch)
        for btn in doc.xpath("//header/button"):
            action = btn.get("name")
            if action in prefs and not prefs[action]:
                btn.getparent().remove(btn)
        return etree.tostring(doc, encoding="unicode")
