# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .dyn_common import (
    ALLOWED_TTYPES, DEFAULT_FIELDS, DENSITY_SELECTION, DOC_TYPE_SELECTION, DOC_TYPES,
    HEADER_ALIGN_SELECTION, PALETTES, PALETTE_SELECTION, TABLE_STYLE_SELECTION,
)

INHERIT_SELECTION = [('company', 'Company Default'), ('custom', 'Custom for this Document')]


class PdfDesignProfile(models.Model):
    """Design of one document type for one company.

    Every option has an "inherit from company" state, so a profile only
    overrides what it really changes.
    """
    _name = 'pdf.design.profile'
    _description = 'PDF Document Design'
    _order = 'company_id, sequence, id'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        'res.company', required=True, index=True, default=lambda self: self.env.company)
    document_type = fields.Selection(DOC_TYPE_SELECTION, required=True)
    model_name = fields.Char(compute='_compute_models', string='Document Model')
    line_model_name = fields.Char(compute='_compute_models', string='Line Model')

    # ---- layout & body ------------------------------------------------------
    report_layout_id = fields.Many2one(
        'report.layout', string='Layout', domain=[('dyn_hidden', '=', False)],
        help='Leave empty to use the layout chosen in "Configure Document Layout".')
    body_mode = fields.Selection(
        [('dynamic', 'Dynamic body (designed by this module)'),
         ('standard', 'Standard Odoo body + selected fields')],
        default='dynamic', required=True,
        help='Dynamic: the whole document body is rendered from the fields selected below.\n'
             'Standard: Odoo keeps its own body; the selected header/summary fields are added '
             'and line fields are printed in a "Line Details" table.')
    title = fields.Char(translate=True, help='Document title. Leave empty for the default title.')
    show_partner_block = fields.Boolean(string='Partner Address', default=True)
    show_totals = fields.Boolean(string='Totals', default=True)
    show_notes = fields.Boolean(string='Notes / Terms', default=True)
    show_signature = fields.Boolean(string='Signature Boxes', default=False)

    # ---- colors ---------------------------------------------------------------
    color_mode = fields.Selection(INHERIT_SELECTION, default='company', required=True, string='Colors')
    palette = fields.Selection(PALETTE_SELECTION, default='custom')
    primary_color = fields.Char()
    accent_color = fields.Char()
    surface_color = fields.Char()
    border_color = fields.Char()

    # ---- header ---------------------------------------------------------------
    header_mode = fields.Selection(INHERIT_SELECTION, default='company', required=True, string='Header')
    show_header = fields.Boolean(default=True)
    header_show_logo = fields.Boolean(string='Logo', default=True)
    header_show_details = fields.Boolean(string='Company Details', default=True)
    header_show_tagline = fields.Boolean(string='Tagline', default=True)
    header_align = fields.Selection(HEADER_ALIGN_SELECTION, default='split', string='Alignment')
    header_height = fields.Float(string='Height (mm)', default=32.0)
    header_spacing = fields.Float(string='Spacing (mm)', default=5.0)

    # ---- footer ---------------------------------------------------------------
    footer_mode = fields.Selection(INHERIT_SELECTION, default='company', required=True, string='Footer')
    show_footer = fields.Boolean(default=True)
    footer_show_page_number = fields.Boolean(string='Page Numbers', default=True)
    footer_show_details = fields.Boolean(string='Company Footer Text', default=True)
    footer_text = fields.Char(translate=True, help='Extra text printed in the footer of this document.')
    footer_height = fields.Float(string='Height (mm)', default=18.0)

    # ---- table ----------------------------------------------------------------
    density = fields.Selection(
        [('company', 'Company Default')] + DENSITY_SELECTION, default='company', required=True)
    table_style = fields.Selection(
        [('company', 'Company Default')] + TABLE_STYLE_SELECTION, string='Tables',
        default='company', required=True)

    # ---- fields ---------------------------------------------------------------
    field_ids = fields.One2many('pdf.design.field', 'profile_id', string='All Fields')
    header_field_ids = fields.One2many(
        'pdf.design.field', 'profile_id', string='Header Fields',
        domain=[('section', '=', 'header')], context={'default_section': 'header'})
    summary_field_ids = fields.One2many(
        'pdf.design.field', 'profile_id', string='Summary Fields',
        domain=[('section', '=', 'summary')], context={'default_section': 'summary'})
    line_field_ids = fields.One2many(
        'pdf.design.field', 'profile_id', string='Line Columns',
        domain=[('section', '=', 'line')], context={'default_section': 'line'})

    @api.depends('document_type')
    def _compute_models(self):
        for profile in self:
            spec = DOC_TYPES.get(profile.document_type) or {}
            profile.model_name = spec.get('model') or False
            profile.line_model_name = spec.get('line_model') or False

    @api.onchange('palette')
    def _onchange_palette(self):
        for profile in self:
            colors = PALETTES.get(profile.palette)
            if colors:
                (profile.primary_color, profile.accent_color,
                 profile.surface_color, profile.border_color) = colors

    @api.onchange('document_type')
    def _onchange_document_type(self):
        for profile in self:
            if profile.document_type and not profile.name:
                profile.name = dict(self._fields['document_type']._description_selection(
                    self.env)).get(profile.document_type)

    @api.constrains('header_height', 'header_spacing', 'footer_height',
                    'primary_color', 'accent_color', 'surface_color', 'border_color')
    def _check_dyn_values(self):
        engine = self.env['pdf.design.engine']
        for profile in self:
            engine._dyn_check_values(
                profile,
                heights=('header_height', 'footer_height'),
                spacings=('header_spacing',),
                colors=('primary_color', 'accent_color', 'surface_color', 'border_color'))

    @api.constrains('company_id', 'document_type', 'active')
    def _check_single_active(self):
        for profile in self.filtered('active'):
            if self.search_count([
                ('id', '!=', profile.id),
                ('company_id', '=', profile.company_id.id),
                ('document_type', '=', profile.document_type),
            ]):
                raise ValidationError(_(
                    'Only one active design per company and document type is allowed '
                    '(%s). Archive the other design first.', profile.name))

    # ---- cache invalidation ---------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        profiles = super().create(vals_list)
        for profile in profiles:
            if not profile.field_ids and not self.env.context.get('dyn_no_default_fields'):
                profile._dyn_load_default_fields()
        self.env['pdf.design.engine'].dyn_clear_cache()
        return profiles

    def write(self, vals):
        res = super().write(vals)
        self.env['pdf.design.engine'].dyn_clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['pdf.design.engine'].dyn_clear_cache()
        return res

    # ---- actions ----------------------------------------------------------------
    def _dyn_load_default_fields(self):
        IrField = self.env['ir.model.fields'].sudo()
        for profile in self:
            spec = DOC_TYPES[profile.document_type]
            defaults = DEFAULT_FIELDS.get(profile.document_type, {})
            vals_list = []
            for section, names in defaults.items():
                model = spec['line_model' if section == 'line' else 'model']
                if model not in self.env:
                    continue
                ir_fields = IrField.search([('model', '=', model), ('name', 'in', names),
                                            ('ttype', 'in', ALLOWED_TTYPES)])
                by_name = {f.name: f for f in ir_fields}
                for seq, name in enumerate(names, start=1):
                    if name in by_name:
                        vals_list.append({
                            'profile_id': profile.id,
                            'section': section,
                            'field_id': by_name[name].id,
                            'sequence': seq * 10,
                        })
            if vals_list:
                self.env['pdf.design.field'].create(vals_list)

    def action_load_default_fields(self):
        self.field_ids.unlink()
        self._dyn_load_default_fields()
        return True

    def action_preview(self):
        """Print the most recent document of this type with this design."""
        self.ensure_one()
        spec = DOC_TYPES[self.document_type]
        domain = [('company_id', '=', self.company_id.id)]
        domain += {
            'sale_quotation': [('state', 'in', ('draft', 'sent'))],
            'sale_order': [('state', 'not in', ('draft', 'sent'))],
            'purchase_rfq': [('state', 'in', ('draft', 'sent', 'to approve'))],
            'purchase_order': [('state', 'not in', ('draft', 'sent', 'to approve'))],
            'account_invoice': [('move_type', '!=', 'entry')],
            'journal_entry': [('move_type', '=', 'entry')],
        }.get(self.document_type, [])
        record = self.env[spec['model']].search(domain, order='id desc', limit=1)
        if not record:
            raise UserError(_('There is no document of this type to preview yet.'))
        return self.env.ref(spec['report']).report_action(record)
