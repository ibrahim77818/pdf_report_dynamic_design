# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .dyn_common import ALLOWED_TTYPES, DOC_TYPES


class PdfDesignField(models.Model):
    _name = 'pdf.design.field'
    _description = 'PDF Design Field'
    _order = 'profile_id, section, sequence, id'

    sequence = fields.Integer(default=10)
    profile_id = fields.Many2one(
        'pdf.design.profile', required=True, ondelete='cascade', index=True)
    section = fields.Selection(
        [('header', 'Header Information'),
         ('summary', 'Summary'),
         ('line', 'Line Column')],
        required=True, default='header')
    target_model = fields.Char(
        compute='_compute_target_model',
        help='Technical: model whose fields can be picked for this section.')
    field_id = fields.Many2one(
        'ir.model.fields', string='Field', required=True, ondelete='cascade',
        help='Any stored or computed field of the document - custom fields (x_...) included.')
    field_name = fields.Char(related='field_id.name', store=True, string='Technical Name')
    field_type = fields.Selection(related='field_id.ttype', string='Type')
    label = fields.Char(translate=True, help='Leave empty to use the field label.')
    align = fields.Selection(
        [('auto', 'Automatic'), ('start', 'Start'), ('center', 'Center'), ('end', 'End')],
        default='auto', required=True)
    show_if_empty = fields.Boolean(
        string='Show When Empty',
        help='Header/summary only: print the label even if the value is empty.')

    @api.depends('section', 'profile_id.document_type')
    def _compute_target_model(self):
        for line in self:
            spec = DOC_TYPES.get(line.profile_id.document_type) or {}
            line.target_model = spec.get('line_model' if line.section == 'line' else 'model') or False

    @api.constrains('field_id', 'section', 'profile_id')
    def _check_field_model(self):
        for line in self:
            if not line.field_id:
                continue
            if line.target_model and line.field_id.model != line.target_model:
                raise ValidationError(_(
                    'Field "%(field)s" does not belong to %(model)s.',
                    field=line.field_id.field_description, model=line.target_model))
            if line.field_id.ttype not in ALLOWED_TTYPES:
                raise ValidationError(_(
                    'Fields of type "%s" cannot be printed.', line.field_id.ttype))

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
