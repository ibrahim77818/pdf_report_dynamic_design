# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .dyn_common import LAYOUT_PREFIX, LEGACY_DESIGNS, PALETTE_SELECTION, TABLE_STYLE_SELECTION


class ReportLayout(models.Model):
    """Presets applied when a dynamic design is picked in Configure Document Layout."""
    _inherit = 'report.layout'

    dyn_palette = fields.Selection(PALETTE_SELECTION, string='Suggested Palette')
    dyn_table_style = fields.Selection(TABLE_STYLE_SELECTION, string='Suggested Tables')
    dyn_header_height = fields.Float(string='Suggested Header Height (mm)')
    dyn_footer_height = fields.Float(string='Suggested Footer Height (mm)')
    dyn_hidden = fields.Boolean(
        string='Hidden in Layout Picker',
        help='Kept for companies already using it, but not offered in Configure Document Layout.')

    def write(self, vals):
        res = super().write(vals)
        self.env['pdf.design.engine'].dyn_clear_cache()
        return res

    @api.model
    def _dyn_hide_legacy_layouts(self):
        """Offer the Odoo 20 style set: hide Odoo's legacy layouts and the first dynamic ones.

        Companies already using a hidden layout keep it; uninstalling the module drops
        the flag and shows every layout again.
        """
        for layout in self.search([]):
            key = layout.view_id.key or ''
            design = key[len(LAYOUT_PREFIX):] if key.startswith(LAYOUT_PREFIX) else None
            layout.dyn_hidden = design is None or design in LEGACY_DESIGNS
