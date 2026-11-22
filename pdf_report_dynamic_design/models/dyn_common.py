# -*- coding: utf-8 -*-
"""Shared constants of the dynamic PDF design engine.

Everything here is plain Python data so it can be imported by models, tests and
the report engine without touching the ORM.
"""

# --------------------------------------------------------------------------
# Document types handled by the engine.
#   model        : main model printed
#   line_field   : one2many holding the detail lines
#   line_model   : comodel of ``line_field``
#   report       : xmlid of the report action used by "Preview"
# --------------------------------------------------------------------------
DOC_TYPES = {
    'sale_quotation': {
        'model': 'sale.order', 'line_field': 'order_line', 'line_model': 'sale.order.line', 'line_label_field': 'name',
        'report': 'sale.action_report_saleorder',
    },
    'sale_order': {
        'model': 'sale.order', 'line_field': 'order_line', 'line_model': 'sale.order.line', 'line_label_field': 'name',
        'report': 'sale.action_report_saleorder',
    },
    'purchase_rfq': {
        'model': 'purchase.order', 'line_field': 'order_line', 'line_model': 'purchase.order.line', 'line_label_field': 'name',
        'report': 'purchase.report_purchase_quotation',
    },
    'purchase_order': {
        'model': 'purchase.order', 'line_field': 'order_line', 'line_model': 'purchase.order.line', 'line_label_field': 'name',
        'report': 'purchase.action_report_purchase_order',
    },
    'stock_picking': {
        'model': 'stock.picking', 'line_field': 'move_ids', 'line_model': 'stock.move', 'line_label_field': 'product_id',
        'report': 'stock.action_report_delivery',
    },
    'account_invoice': {
        'model': 'account.move', 'line_field': 'invoice_line_ids', 'line_model': 'account.move.line', 'line_label_field': 'name',
        'report': 'account.account_invoices',
    },
    'journal_entry': {
        'model': 'account.move', 'line_field': 'line_ids', 'line_model': 'account.move.line', 'line_label_field': 'name',
        'report': 'pdf_report_dynamic_design.action_report_journal_entry',
    },
}

DOC_TYPE_SELECTION = [
    ('sale_quotation', 'Sales Quotation'),
    ('sale_order', 'Sales Order'),
    ('purchase_rfq', 'Request for Quotation'),
    ('purchase_order', 'Purchase Order'),
    ('stock_picking', 'Transfer / Delivery Slip'),
    ('account_invoice', 'Invoice / Bill'),
    ('journal_entry', 'Journal Entry'),
]

# Field types an end user may put on a PDF.
ALLOWED_TTYPES = (
    'char', 'text', 'html', 'integer', 'float', 'monetary', 'date', 'datetime',
    'boolean', 'selection', 'many2one', 'many2many',
)

# Technical fields hidden from the field picker.
HIDDEN_FIELD_NAMES = (
    'id', 'create_uid', 'write_uid', 'create_date', 'write_date', '__last_update',
    'display_name', 'message_ids', 'message_follower_ids', 'activity_ids',
    'website_message_ids', 'access_token', 'access_url', 'message_main_attachment_id',
)

# Default fields loaded into a new profile (only the ones that exist are used).
DEFAULT_FIELDS = {
    'sale_quotation': {
        'header': ['date_order', 'validity_date', 'user_id', 'client_order_ref', 'payment_term_id'],
        'summary': [],
        'line': ['name', 'product_uom_qty', 'price_unit', 'discount', 'tax_ids', 'price_subtotal'],
    },
    'sale_order': {
        'header': ['date_order', 'user_id', 'client_order_ref', 'payment_term_id'],
        'summary': [],
        'line': ['name', 'product_uom_qty', 'price_unit', 'discount', 'tax_ids', 'price_subtotal'],
    },
    'purchase_rfq': {
        'header': ['date_order', 'partner_ref', 'user_id'],
        'summary': [],
        'line': ['name', 'date_planned', 'product_qty', 'uom_id'],
    },
    'purchase_order': {
        'header': ['date_approve', 'partner_ref', 'user_id', 'payment_term_id'],
        'summary': [],
        'line': ['name', 'date_planned', 'product_qty', 'price_unit', 'tax_ids', 'price_subtotal'],
    },
    'stock_picking': {
        'header': ['scheduled_date', 'origin', 'date_done', 'picking_type_id'],
        'summary': [],
        'line': ['product_id', 'product_uom_qty', 'quantity', 'uom_id'],
    },
    'account_invoice': {
        'header': ['invoice_date', 'invoice_date_due', 'ref', 'invoice_origin', 'payment_reference'],
        'summary': [],
        'line': ['name', 'quantity', 'price_unit', 'discount', 'tax_ids', 'price_subtotal'],
    },
    'journal_entry': {
        'header': ['date', 'journal_id', 'ref'],
        'summary': [],
        'line': ['account_id', 'partner_id', 'name', 'debit', 'credit'],
    },
}

# Fields Odoo's own report body already prints. In "standard body" mode these are
# skipped, so selecting them never prints the same information twice.
_COMMON_HEADER = ('name', 'partner_id', 'company_id', 'currency_id', 'amount_untaxed',
                  'amount_tax', 'amount_total', 'note', 'notes', 'narration', 'state')
ODOO_BODY_FIELDS = {
    'sale_quotation': {
        'header': _COMMON_HEADER + ('date_order', 'validity_date', 'user_id', 'client_order_ref',
                                    'payment_term_id', 'partner_invoice_id', 'partner_shipping_id',
                                    'tax_totals', 'fiscal_position_id', 'signature', 'signed_by',
                                    'commitment_date', 'incoterm', 'incoterm_location'),
        'line': ('name', 'label', 'product_id', 'product_uom_qty', 'product_uom_id', 'price_unit',
                 'discount', 'tax_ids', 'price_subtotal', 'price_total'),
    },
    'purchase_rfq': {
        'header': _COMMON_HEADER + ('date_order', 'partner_ref', 'user_id', 'dest_address_id',
                                    'date_planned', 'incoterm_id', 'fiscal_position_id',
                                    'incoterm_location'),
        'line': ('name', 'label', 'product_id', 'date_planned', 'product_qty', 'uom_id'),
    },
    'purchase_order': {
        'header': _COMMON_HEADER + ('date_order', 'date_approve', 'partner_ref', 'user_id',
                                    'payment_term_id', 'dest_address_id', 'incoterm_id', 'tax_totals',
                                    'date_planned', 'fiscal_position_id', 'incoterm_location'),
        'line': ('name', 'label', 'product_id', 'date_planned', 'product_qty', 'uom_id', 'price_unit',
                 'tax_ids', 'price_subtotal', 'discount'),
    },
    'stock_picking': {
        'header': _COMMON_HEADER + ('scheduled_date', 'origin', 'date_done', 'picking_type_id',
                                    'location_id', 'location_dest_id', 'backorder_ids',
                                    'signature', 'user_id'),
        'line': ('product_id', 'description_picking', 'product_uom_qty', 'quantity',
                 'uom_id', 'lot_ids', 'packaging_uom_id', 'packaging_uom_qty'),
    },
    'account_invoice': {
        'header': _COMMON_HEADER + ('invoice_date', 'invoice_date_due', 'ref', 'invoice_origin',
                                    'payment_reference', 'invoice_payment_term_id',
                                    'partner_shipping_id', 'amount_residual', 'tax_totals',
                                    # printed by Odoo 18's invoice body as well
                                    'delivery_date', 'invoice_incoterm_id', 'incoterm_location',
                                    'partner_bank_id', 'fiscal_position_id', 'amount_total_words',
                                    'taxable_supply_date', 'journal_id', 'invoice_cash_rounding_id'),
        'line': ('name', 'label', 'product_id', 'quantity', 'product_uom_id', 'price_unit', 'discount',
                 'tax_ids', 'price_subtotal', 'price_total'),
    },
    'journal_entry': {
        'header': _COMMON_HEADER + ('date', 'journal_id', 'ref'),
        'line': ('account_id', 'partner_id', 'name', 'debit', 'credit'),
    },
}
ODOO_BODY_FIELDS['sale_order'] = ODOO_BODY_FIELDS['sale_quotation']

# --------------------------------------------------------------------------
# Palettes: (primary, accent, surface, border)
# --------------------------------------------------------------------------
PALETTES = {
    'ocean': ('#0B4F6C', '#20A4F3', '#F2F8FC', '#CFE3EF'),
    'emerald': ('#0F6B4F', '#2BB37E', '#F1FAF6', '#CDEBDD'),
    'royal': ('#3A2E8C', '#7B61FF', '#F5F3FF', '#DCD6FA'),
    'sunset': ('#9C3D1B', '#F28C38', '#FFF6EF', '#F6D9C2'),
    'graphite': ('#22272E', '#5B6B7C', '#F4F5F7', '#D9DDE3'),
    'desert': ('#6B4E2E', '#C59D5F', '#FBF7F0', '#EADBC3'),
    'crimson': ('#7A1328', '#D64561', '#FDF2F4', '#F1CDD5'),
    'teal': ('#0B7F7A', '#14B8A6', '#E3F8F6', '#BFE9E4'),
    'navy_teal': ('#14324A', '#16B3A3', '#EAF7F6', '#CDE9E6'),
    'navy_cyan': ('#13314B', '#12B5EA', '#EAF8FD', '#C3E9F7'),
    'charcoal_orange': ('#262626', '#F28C1E', '#FFF1E2', '#F3D7B8'),
    'navy_yellow': ('#1F2A44', '#F5C400', '#FFF8D6', '#EADFA6'),
    'slate_green': ('#3A3A3A', '#14876A', '#F2F2F2', '#C9C9C9'),
}

PALETTE_SELECTION = [
    ('custom', 'Custom'),
    ('ocean', 'Ocean'),
    ('emerald', 'Emerald'),
    ('royal', 'Royal'),
    ('sunset', 'Sunset'),
    ('graphite', 'Graphite'),
    ('desert', 'Desert Sand'),
    ('crimson', 'Crimson'),
    ('teal', 'Teal'),
    ('navy_teal', 'Navy & Teal'),
    ('navy_cyan', 'Navy & Cyan'),
    ('charcoal_orange', 'Charcoal & Orange'),
    ('navy_yellow', 'Navy & Yellow'),
    ('slate_green', 'Slate & Green'),
]

# --------------------------------------------------------------------------
# Designs. A design = one external layout (header/footer) + how the dynamic
# body arranges its blocks + design specific CSS.
#   arrangement: panels | fromto | split | strip
# --------------------------------------------------------------------------
LAYOUT_PREFIX = 'pdf_report_dynamic_design.external_layout_dyn_'
DESIGNS = {
    'standard': 'panels',
    'modern': 'panels',
    'minimal': 'panels',
    'corporate': 'panels',
    'elegant': 'panels',
    'banner': 'fromto',
    'teal': 'split',
    'accent': 'split',
    'angled': 'split',
    'chevron': 'split',
    'wave': 'strip',
    'geometric': 'split',
    # Odoo 20 style layouts
    'v20_light': 'split',
    'v20_bubble': 'panels',
    'v20_wave': 'panels',
    'v20_folder': 'split',
    'v20_center': 'panels',
    'v20_dual': 'fromto',
    'v20_lines': 'split',
    'v20_compact': 'split',
}

# Odoo 20 style table looks, independent from the layout.
TABLE_STYLE_SELECTION = [
    ('auto', 'Layout Default'),
    ('light', 'Light'),
    ('boxed', 'Boxed'),
    ('bold', 'Bold'),
    ('striped', 'Striped'),
    ('bubble', 'Bubble'),
    ('column', 'Column'),
    ('compact', 'Compact'),
]
# Odoo 20 res.company.report_tables_id values (all of them exist here too).
NATIVE_TABLE_STYLES = ('light', 'boxed', 'bold', 'striped', 'bubble', 'column', 'compact')
# Table style used by "Layout Default" (None = the design's own table CSS).
DESIGN_TABLE_DEFAULT = {
    'standard': None, 'modern': None, 'minimal': None, 'corporate': None, 'elegant': None,
    'banner': None, 'teal': None, 'accent': None, 'angled': None, 'chevron': None,
    'wave': None, 'geometric': None,
    'v20_light': 'light', 'v20_bubble': 'bubble', 'v20_wave': 'striped', 'v20_folder': 'bold',
    'v20_center': 'light', 'v20_dual': 'column', 'v20_lines': 'light', 'v20_compact': 'compact',
}
# Layouts kept for existing companies but not offered any more (Odoo 20 replaced them).
LEGACY_DESIGNS = ('modern', 'minimal', 'corporate', 'elegant')

DEFAULT_COLORS = {
    'primary': '#22272E',
    'accent': '#5B6B7C',
    'surface': '#F4F5F7',
    'border': '#D9DDE3',
    'text': '#1F2328',
}

# --------------------------------------------------------------------------
# Fonts. Key -> CSS family name. Odoo (16, 17) ships the first seven with the report
# assets; "DynFallback" is DejaVu Sans bundled by this module (Latin, Arabic,
# Hebrew, Cyrillic, Greek...) so a glyph is always available.
# --------------------------------------------------------------------------
FONT_SELECTION = [
    ('Lato', 'Lato'),
    ('Roboto', 'Roboto'),
    ('Open_Sans', 'Open Sans'),
    ('Montserrat', 'Montserrat'),
    ('Oswald', 'Oswald'),
    ('Raleway', 'Raleway'),
    ('Tajawal', 'Tajawal (Arabic)'),
    ('Noto_Sans_Mono', 'Noto Sans Mono'),  # shipped with the report assets since Odoo 20
    ('DynFallback', 'DejaVu Sans (bundled, multi-script)'),
    ('Noto Naskh Arabic', 'Noto Naskh Arabic (server font)'),
    ('Noto Kufi Arabic', 'Noto Kufi Arabic (server font)'),
    ('Amiri', 'Amiri (server font)'),
    ('Cairo', 'Cairo (server font)'),
    ('custom', 'Custom server font'),
]

FONT_CSS_NAMES = {
    'Open_Sans': 'Open Sans',
    'Noto_Sans_Mono': 'Noto Sans Mono',
}

RTL_FALLBACK_STACK = ("'Tajawal'", "'Noto Naskh Arabic'", "'Amiri'", "'DynFallback'",
                      "'DejaVu Sans'", 'sans-serif')
LTR_FALLBACK_STACK = ("'Lato'", "'DynFallback'", "'DejaVu Sans'", 'sans-serif')

# Header / footer
HEADER_ALIGN_SELECTION = [
    ('split', 'Logo start / details end'),
    ('start', 'All at start'),
    ('center', 'Centered'),
    ('end', 'All at end'),
]
DENSITY_SELECTION = [
    ('compact', 'Compact'),
    ('comfortable', 'Comfortable'),
    ('spacious', 'Spacious'),
]
DENSITY_PADDING = {'compact': '3px 5px', 'comfortable': '6px 8px', 'spacious': '9px 10px'}

# Safety bounds (mm) so a typo cannot produce an unusable page.
MIN_BAND_MM, MAX_BAND_MM = 8, 90
MIN_SPACING_MM, MAX_SPACING_MM = 0, 30
MIN_FONT_PT, MAX_FONT_PT = 6, 16


def clamp(value, low, high):
    try:
        value = float(value or 0.0)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


def sanitize_color(value, default):
    """Return a safe ``#RRGGBB`` color; anything else falls back to ``default``.

    Colors are injected in a <style> block, so they must never carry CSS/HTML.
    """
    if not value or not isinstance(value, str):
        return default
    value = value.strip()
    if len(value) in (4, 7) and value.startswith('#') and all(
            c in '0123456789abcdefABCDEF' for c in value[1:]):
        if len(value) == 4:
            value = '#' + ''.join(c * 2 for c in value[1:])
        return value.upper()
    return default


def sanitize_font_name(value):
    """Keep only characters valid in a CSS font-family name."""
    if not value:
        return ''
    return ''.join(c for c in value if c.isalnum() or c in ' -_').strip()[:60]
