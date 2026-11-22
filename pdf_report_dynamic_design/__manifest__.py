# -*- coding: utf-8 -*-
{
    'name': 'PDF Report Dynamic Design',
    'version': '20.0.1.2.1',
    'summary': 'Modern PDF layouts, color palettes, per-language fonts (RTL/Arabic), '
               'header/footer controls and per-document field selection for '
               'quotations, orders, RFQs, POs, pickings, invoices and journal entries.',
    'description': """
PDF Report Dynamic Design
=========================
Extends the standard *Configure Document Layout* experience without touching Odoo core:

* Extends Odoo 20's "Configure Document Layout": its Layout list gets layouts with
  header-aware margins (Light, Bubble, Wave, Folder, Center, Dual, Lines, Compact) and
  template designs (Banner, Teal Block, Accent Strip, Angled, Chevron, Swoosh, Geometric)
  that apply their own palette; its Tables setting (Light, Boxed, Bold, Striped, Bubble,
  Column, Compact) can be overridden per document.
* Color palettes: primary, accent, surface and border colors, with presets.
* Font per activated language (including Arabic / RTL) with safe font fallbacks and
  automatic text direction.
* Header / footer visibility, content, alignment and height controls. Page margins
  are computed from those heights so the header and footer never overlap the body.
* Design profiles per document type (Quotation, Sales Order, RFQ, Purchase Order,
  Transfer, Invoice, Journal Entry) with clean fallback to the company defaults.
* End users choose header, summary and line fields - custom (x_) fields included.
* Batch prefetching and ORM caching: the query count stays flat whatever the
  number of lines.
""",
    'category': 'Productivity/Reporting',
    'author': 'Ibrahim Yahia',
    'website': 'https://www.linkedin.com/in/ibrahim-yahia',
    'maintainer': 'Ibrahim Yahia',
    'support': 'ibrahim.yahiah@gmail.com',
    'license': 'LGPL-3',
    'depends': ['web', 'sale', 'purchase', 'stock', 'account', 'base_report_wkhtmltox'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/report_layouts.xml',
        'views/report_layouts_designs.xml',
        'views/report_layouts_v20.xml',
        'data/report_layout_data.xml',
        'views/report_body.xml',
        'views/report_hooks.xml',
        'views/report_journal_entry.xml',
        'views/pdf_design_profile_views.xml',
        'views/pdf_design_font_rule_views.xml',
        'views/res_company_views.xml',
        'views/base_document_layout_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'pdf_report_dynamic_design/static/src/scss/dyn_report.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
