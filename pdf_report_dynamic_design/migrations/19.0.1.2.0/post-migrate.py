# -*- coding: utf-8 -*-
"""18.0 -> 19.0: Odoo renamed several line fields.

    sale.order.line      tax_id      -> tax_ids,  product_uom -> product_uom_id
    purchase.order.line  taxes_id    -> tax_ids,  product_uom -> product_uom_id

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
