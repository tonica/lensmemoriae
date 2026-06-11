from odoo import fields, models


class LensMemoriaeScrapWizard(models.TransientModel):
    _name = "lensmemoriae.scrap.wizard"
    _description = "Scrap Wizard"

    limit = fields.Integer(
        string="Maximum records",
        default=10,
        required=True,
        help="Limit the number of XML elements to process. Set to 0 for no limit.",
    )
    filename_filter = fields.Char(
        string="XML filename filter",
        help="Only process XML files whose name contains this text.",
    )

    def action_start_scrap(self):
        return (
            self.env["lensmemoriae.image"]
            .with_context(
                scrap_limit=self.limit,
                scrap_filename_filter=self.filename_filter or None,
            )
            .action_scrap()
        )
