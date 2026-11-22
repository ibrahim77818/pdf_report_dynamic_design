# -*- coding: utf-8 -*-
"""19.0 -> 20.0: Odoo renamed the unit fields.

    purchase.order.line  product_uom_id -> uom_id
    stock.move           product_uom    -> uom_id

Odoo's upgrade renames the ir.model.fields rows in place, so the design columns
still point to the right field, but our stored ``field_name`` copy keeps the old
name and the column would silently disappear from the PDF. Refresh it.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE pdf_design_field f
           SET field_name = imf.name
          FROM ir_model_fields imf
         WHERE imf.id = f.field_id
           AND f.field_name IS DISTINCT FROM imf.name
    """)
