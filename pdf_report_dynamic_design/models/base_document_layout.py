# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .dyn_common import PALETTES


class BaseDocumentLayout(models.TransientModel):
    """Expose the dynamic design options inside "Configure Document Layout".

    Related fields (readonly=False) write straight through to the company when
    the wizard is saved, exactly like the standard color/font fields.
    """
    _inherit = 'base.document.layout'

    dyn_palette = fields.Selection(related='company_id.dyn_palette', readonly=False)
    dyn_surface_color = fields.Char(related='company_id.dyn_surface_color', readonly=False)
    dyn_border_color = fields.Char(related='company_id.dyn_border_color', readonly=False)
    dyn_text_color = fields.Char(related='company_id.dyn_text_color', readonly=False)
    dyn_show_header = fields.Boolean(related='company_id.dyn_show_header', readonly=False)
    dyn_header_show_logo = fields.Boolean(related='company_id.dyn_header_show_logo', readonly=False)
    dyn_header_show_details = fields.Boolean(related='company_id.dyn_header_show_details', readonly=False)
    dyn_header_show_tagline = fields.Boolean(related='company_id.dyn_header_show_tagline', readonly=False)
    dyn_header_align = fields.Selection(related='company_id.dyn_header_align', readonly=False)
    dyn_header_height = fields.Float(related='company_id.dyn_header_height', readonly=False)
    dyn_header_spacing = fields.Float(related='company_id.dyn_header_spacing', readonly=False)
    dyn_show_footer = fields.Boolean(related='company_id.dyn_show_footer', readonly=False)
    dyn_footer_show_page_number = fields.Boolean(
        related='company_id.dyn_footer_show_page_number', readonly=False)
    dyn_footer_show_details = fields.Boolean(related='company_id.dyn_footer_show_details', readonly=False)
    dyn_footer_height = fields.Float(related='company_id.dyn_footer_height', readonly=False)
    dyn_footer_thanks = fields.Boolean(related='company_id.dyn_footer_thanks', readonly=False)
    dyn_auto_margins = fields.Boolean(related='company_id.dyn_auto_margins', readonly=False)
    dyn_density = fields.Selection(related='company_id.dyn_density', readonly=False)
    dyn_table_style = fields.Selection(related='company_id.dyn_table_style', readonly=False)
    dyn_zebra = fields.Boolean(related='company_id.dyn_zebra', readonly=False)
    dyn_show_line_numbers = fields.Boolean(related='company_id.dyn_show_line_numbers', readonly=False)
    dyn_base_font_size = fields.Float(related='company_id.dyn_base_font_size', readonly=False)

    @api.onchange('dyn_palette')
    def _onchange_dyn_palette(self):
        for wizard in self:
            colors = PALETTES.get(wizard.dyn_palette)
            if colors:
                (wizard.primary_color, wizard.secondary_color,
                 wizard.dyn_surface_color, wizard.dyn_border_color) = colors

    @api.onchange('report_layout_id')
    def _onchange_dyn_layout_preset(self):
        """Picking a dynamic design applies its matching palette and band heights."""
        for wizard in self:
            layout = wizard.report_layout_id
            if not layout:
                continue
            if layout.dyn_palette:
                wizard.dyn_palette = layout.dyn_palette
                colors = PALETTES.get(layout.dyn_palette)
                if colors:
                    (wizard.primary_color, wizard.secondary_color,
                     wizard.dyn_surface_color, wizard.dyn_border_color) = colors
            if layout.dyn_table_style:
                wizard.dyn_table_style = layout.dyn_table_style
            if layout.dyn_header_height:
                wizard.dyn_header_height = layout.dyn_header_height
            if layout.dyn_footer_height:
                wizard.dyn_footer_height = layout.dyn_footer_height

    # Extra dependencies only: Odoo merges @api.depends of every override found
    # in the MRO, so the standard dependencies are kept.
    @api.depends(
        'dyn_surface_color', 'dyn_border_color', 'dyn_text_color', 'dyn_show_header',
        'dyn_header_show_logo', 'dyn_header_show_details', 'dyn_header_show_tagline',
        'dyn_header_align', 'dyn_show_footer', 'dyn_footer_show_page_number',
        'dyn_footer_show_details', 'dyn_footer_thanks', 'dyn_density', 'dyn_table_style', 'dyn_zebra', 'dyn_base_font_size',
    )
    def _compute_preview(self):
        return super()._compute_preview()

    def action_open_dyn_profiles(self):
        return self.env['ir.actions.act_window']._for_xml_id(
            'pdf_report_dynamic_design.action_pdf_design_profile')
