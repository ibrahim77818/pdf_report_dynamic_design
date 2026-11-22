# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .dyn_common import DOC_TYPE_SELECTION, FONT_SELECTION


class PdfDesignFontRule(models.Model):
    _name = 'pdf.design.font.rule'
    _description = 'PDF Font per Language'
    _order = 'company_id, document_type, sequence, id'

    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        'res.company', required=True, ondelete='cascade', index=True,
        default=lambda self: self.env.company)
    lang_id = fields.Many2one(
        'res.lang', string='Language', required=True, ondelete='cascade',
        domain=[('active', '=', True)])
    lang_code = fields.Char(related='lang_id.code', store=True, index=True)
    document_type = fields.Selection(
        DOC_TYPE_SELECTION, string='Only for Document',
        help='Leave empty to apply the rule to every document type.')
    font = fields.Selection(FONT_SELECTION, required=True, default='Lato')
    custom_font = fields.Char(
        string='Custom Font Name',
        help='Exact family name of a font installed on the Odoo server.')
    direction = fields.Selection(
        [('auto', 'Automatic (from language)'), ('ltr', 'Left to Right'), ('rtl', 'Right to Left')],
        default='auto', required=True)
    font_size = fields.Float(string='Font Size (pt)', help='Leave 0 to use the company size.')

    @api.constrains('company_id', 'lang_id', 'document_type')
    def _check_unique_rule(self):
        # Python check: a SQL unique() would let several NULL document types through.
        for rule in self:
            duplicate = self.search_count([
                ('id', '!=', rule.id),
                ('company_id', '=', rule.company_id.id),
                ('lang_id', '=', rule.lang_id.id),
                ('document_type', '=', rule.document_type or False),
            ])
            if duplicate:
                raise ValidationError(_(
                    'Only one font rule per company, language and document type is allowed.'))

    @api.constrains('font_size')
    def _check_font_size(self):
        engine = self.env['pdf.design.engine']
        for rule in self:
            engine._dyn_check_values(rule, sizes=('font_size',), sizes_allow_zero=True)

    @api.constrains('font', 'custom_font')
    def _check_custom_font(self):
        for rule in self:
            if rule.font == 'custom' and not (rule.custom_font or '').strip():
                raise ValidationError(_('Please enter the custom font name.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env['pdf.design.engine'].dyn_clear_cache()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.env['pdf.design.engine'].dyn_clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['pdf.design.engine'].dyn_clear_cache()
        return res
