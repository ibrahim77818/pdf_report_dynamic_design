# -*- coding: utf-8 -*-
"""16.0 -> 17.0: stock.move.quantity_done was replaced by stock.move.quantity.

The upgrade of `stock` drops the old field, which deletes (ondelete=cascade) the
"Done" line column of Transfer designs. Give those designs the new field back so
delivery slips keep showing the done quantity.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    field = env['ir.model.fields']._get('stock.move', 'quantity')
    if not field:
        return
    profiles = env['pdf.design.profile'].with_context(active_test=False).search(
        [('document_type', '=', 'stock_picking')])
    for profile in profiles:
        if 'quantity' in profile.line_field_ids.mapped('field_name'):
            continue
        env['pdf.design.field'].create({
            'profile_id': profile.id, 'section': 'line', 'field_id': field.id, 'sequence': 30,
        })
