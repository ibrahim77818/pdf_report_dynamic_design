# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .dyn_common import (
    DENSITY_SELECTION, HEADER_ALIGN_SELECTION, PALETTES, PALETTE_SELECTION, TABLE_STYLE_SELECTION,
)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ---- colors -------------------------------------------------------------
    # primary_color / secondary_color (accent) already exist on res.company.
    dyn_palette = fields.Selection(
        PALETTE_SELECTION, string='Color Palette', default='custom',
        help='Pick a preset to fill the primary, accent, surface and border colors.')
    dyn_surface_color = fields.Char(
        string='Surface Color', default='#F4F5F7',
        help='Background of table headers, totals and information panels.')
    dyn_border_color = fields.Char(
        string='Border Color', default='#D9DDE3',
        help='Color of table borders and separators.')
    dyn_text_color = fields.Char(string='Text Color', default='#1F2328')

    # ---- header -------------------------------------------------------------
    dyn_show_header = fields.Boolean(string='Show Header', default=True)
    dyn_header_show_logo = fields.Boolean(string='Header: Logo', default=True)
    dyn_header_show_details = fields.Boolean(string='Header: Company Details', default=True)
    dyn_header_show_tagline = fields.Boolean(string='Header: Tagline', default=True)
    dyn_header_align = fields.Selection(
        HEADER_ALIGN_SELECTION, string='Header Alignment', default='split')
    dyn_header_height = fields.Float(
        string='Header Height (mm)', default=32.0,
        help='Height reserved for the header. The top page margin is computed from it, '
             'so the header never overlaps the document body.')
    dyn_header_spacing = fields.Float(
        string='Header Spacing (mm)', default=5.0,
        help='Gap between the header and the first line of the body.')

    # ---- footer -------------------------------------------------------------
    dyn_show_footer = fields.Boolean(string='Show Footer', default=True)
    dyn_footer_show_page_number = fields.Boolean(string='Footer: Page Numbers', default=True)
    dyn_footer_show_details = fields.Boolean(string='Footer: Footer Text', default=True)
    dyn_footer_thanks = fields.Boolean(
        string='Footer: Thank-you Line', default=True,
        help='Print "Thank you for your business!" in the designs that have one.')
    dyn_footer_height = fields.Float(
        string='Footer Height (mm)', default=18.0,
        help='Height reserved for the footer. The bottom page margin is computed from it.')
    dyn_auto_margins = fields.Boolean(
        string='Auto Page Margins', default=True,
        help='Compute the top and bottom page margins from the header and footer heights '
             '(dynamic layouts only). Disable to keep the paper format margins.')

    # ---- body ---------------------------------------------------------------
    dyn_table_style = fields.Selection(
        TABLE_STYLE_SELECTION, string='Tables', default='auto',
        help='Look of the lines tables (dynamic body and Odoo\'s own report body). '
             '"Layout Default" lets the chosen layout decide.')
    dyn_density = fields.Selection(
        DENSITY_SELECTION, string='Table Density', default='comfortable')
    dyn_zebra = fields.Boolean(string='Striped Lines', default=True)
    dyn_show_line_numbers = fields.Boolean(string='Line Numbers', default=False)
    dyn_base_font_size = fields.Float(string='Base Font Size (pt)', default=10.0)

    # ---- fonts per language ---------------------------------------------------
    dyn_font_rule_ids = fields.One2many(
        'pdf.design.font.rule', 'company_id', string='Fonts per Language')

    @api.constrains('dyn_header_height', 'dyn_header_spacing', 'dyn_footer_height',
                    'dyn_base_font_size', 'dyn_surface_color', 'dyn_border_color',
                    'dyn_text_color')
    def _check_dyn_values(self):
        engine = self.env['pdf.design.engine']
        for company in self:
            engine._dyn_check_values(
                company,
                heights=('dyn_header_height', 'dyn_footer_height'),
                spacings=('dyn_header_spacing',),
                sizes=('dyn_base_font_size',),
                # primary_color / secondary_color belong to core: sanitized at render
                # time instead of blocking other modules that write them.
                colors=('dyn_surface_color', 'dyn_border_color', 'dyn_text_color'))

    @api.onchange('dyn_palette')
    def _onchange_dyn_palette(self):
        for company in self:
            colors = PALETTES.get(company.dyn_palette)
            if colors:
                (company.primary_color, company.secondary_color,
                 company.dyn_surface_color, company.dyn_border_color) = colors

    def action_dyn_generate_font_rules(self):
        """Create one font rule per active language that has none yet."""
        Rule = self.env['pdf.design.font.rule']
        langs = self.env['res.lang'].search([('active', '=', True)])
        for company in self:
            existing = set(company.dyn_font_rule_ids.filtered(
                lambda r: not r.document_type).mapped('lang_id').ids)
            vals_list = []
            for lang in langs:
                if lang.id in existing:
                    continue
                rtl = lang.direction == 'rtl'
                vals_list.append({
                    'company_id': company.id,
                    'lang_id': lang.id,
                    'font': 'Tajawal' if rtl else (company.font or 'Lato'),
                    'direction': 'auto',
                })
            if vals_list:
                Rule.create(vals_list)
        return True
