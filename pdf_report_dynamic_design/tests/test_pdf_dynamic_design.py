# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.pdf_report_dynamic_design.models.ir_actions_report import _dyn_extract_margins

ENGINE_LOGGER = 'odoo.addons.pdf_report_dynamic_design.models.pdf_design_engine'


@tagged('post_install', '-at_install')
class TestPdfDynamicDesign(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.engine = cls.env['pdf.design.engine']
        cls.Profile = cls.env['pdf.design.profile']
        cls.DesignField = cls.env['pdf.design.field']

        # ---- custom fields on header and line models -------------------------
        IrFields = cls.env['ir.model.fields']
        cls.x_order_field = IrFields.create({
            'name': 'x_dyn_project_code', 'field_description': 'Project Code',
            'model_id': cls.env['ir.model']._get_id('sale.order'), 'ttype': 'char', 'state': 'manual',
        })
        cls.x_line_field = IrFields.create({
            'name': 'x_dyn_line_note', 'field_description': 'Line Note',
            'model_id': cls.env['ir.model']._get_id('sale.order.line'), 'ttype': 'char', 'state': 'manual',
        })

        # ---- master data ------------------------------------------------------
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.receivable = cls.env['account.account'].create({
            'name': 'Dyn Receivable', 'code': 'DYN121', 'account_type': 'asset_receivable', 'reconcile': True})
        cls.payable = cls.env['account.account'].create({
            'name': 'Dyn Payable', 'code': 'DYN211', 'account_type': 'liability_payable', 'reconcile': True})
        cls.income = cls.env['account.account'].create({
            'name': 'Dyn Income', 'code': 'DYN400', 'account_type': 'income'})
        cls.expense = cls.env['account.account'].create({
            'name': 'Dyn Expense', 'code': 'DYN600', 'account_type': 'expense'})
        cls.partner = cls.env['res.partner'].create({
            'name': 'Dyn Customer', 'lang': 'en_US', 'street': 'King Fahd Road', 'city': 'Riyadh',
            'property_account_receivable_id': cls.receivable.id,
            'property_account_payable_id': cls.payable.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Dyn Product', 'type': 'consu', 'list_price': 100.0,
            'property_account_income_id': cls.income.id,
            'property_account_expense_id': cls.expense.id,
            'taxes_id': [(6, 0, [])], 'supplier_taxes_id': [(6, 0, [])],
        })
        cls.sale_journal = cls.env['account.journal'].create({
            'name': 'Dyn Sales', 'code': 'DYNS', 'type': 'sale', 'default_account_id': cls.income.id})
        cls.misc_journal = cls.env['account.journal'].create({
            'name': 'Dyn Misc', 'code': 'DYNM', 'type': 'general'})

        cls.sale_order = cls._create_sale_order(3)

        # ---- quotation design: modern layout + dynamic body + custom fields ---
        cls.modern_layout = cls.env.ref('pdf_report_dynamic_design.report_layout_dyn_modern')
        cls.quotation_profile = cls.Profile.create({
            'name': 'Quotation', 'document_type': 'sale_quotation', 'body_mode': 'dynamic',
            'report_layout_id': cls.modern_layout.id,
        })
        cls.header_custom = cls.DesignField.create({
            'profile_id': cls.quotation_profile.id, 'section': 'header',
            'field_id': cls.x_order_field.id, 'sequence': 1})
        cls.line_custom = cls.DesignField.create({
            'profile_id': cls.quotation_profile.id, 'section': 'line',
            'field_id': cls.x_line_field.id, 'sequence': 99})

    def setUp(self):
        super().setUp()
        # ORM caches survive the per-test savepoint rollback: start and end clean.
        self.engine.dyn_clear_cache()
        self.addCleanup(self.engine.dyn_clear_cache)

    @classmethod
    def _create_sale_order(cls, line_count, partner=None):
        return cls.env['sale.order'].create({
            'partner_id': (partner or cls.partner).id,
            'x_dyn_project_code': 'PRJ-42',
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': i + 1,
                'price_unit': 50.0,
                'x_dyn_line_note': 'Handle with care %s' % i,
            }) for i in range(line_count)],
        })

    def _raw_write(self, record, vals):
        """Store values the constraints refuse (data saved before validation existed),
        to prove they are still sanitized when printing."""
        for fname, value in vals.items():
            self.env.cr.execute('UPDATE "%s" SET "%s" = %%s WHERE id = %%s'
                                % (record._table, fname), (value, record.id))
        record.invalidate_recordset(list(vals))
        self.engine.dyn_clear_cache()

    def _render(self, report_ref, records):
        html, _fmt = self.env['ir.actions.report']._render_qweb_html(report_ref, records.ids)
        return html.decode() if isinstance(html, bytes) else html

    # ======================================================================
    # Multi-model generation
    # ======================================================================
    def test_01_sale_quotation_dynamic_body_with_custom_fields(self):
        html = self._render('sale.action_report_saleorder', self.sale_order)
        self.assertIn('o_dyn_page', html, 'dynamic body expected')
        self.assertIn('o_dyn_header', html, 'Dynamic Modern layout expected')
        self.assertIn('PRJ-42', html, 'custom header field missing')
        self.assertIn('Handle with care 2', html, 'custom line field missing')
        self.assertIn('Project Code', html)
        self.assertIn('data-dyn-margin-top', html)
        self.assertIn('Dyn Customer', html)

    def test_02_multi_model_generation(self):
        # Sales order (no profile for confirmed orders -> standard Odoo body + layout)
        so = self._create_sale_order(2)
        so.action_confirm()
        html = self._render('sale.action_report_saleorder', so)
        self.assertIn(so.name, html)
        self.assertNotIn('o_dyn_page', html, 'no sale_order profile: standard body expected')

        # Purchase: RFQ and PO
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_qty': 4, 'price_unit': 10.0})],
        })
        self.Profile.create({'name': 'RFQ', 'document_type': 'purchase_rfq', 'body_mode': 'dynamic'})
        self.assertIn(po.name, self._render('purchase.report_purchase_quotation', po))
        po.button_confirm()
        self.Profile.create({'name': 'PO', 'document_type': 'purchase_order', 'body_mode': 'standard'})
        self.assertIn(po.name, self._render('purchase.action_report_purchase_order', po))

        # Stock picking: delivery slip and operations
        # Odoo 19 ships stock.picking_type_out as demo data only: search it instead.
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'), ('company_id', '=', self.company.id)], limit=1)
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3, 'uom_id': self.uom_unit.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            })],
        })
        self.Profile.create({'name': 'Picking', 'document_type': 'stock_picking', 'body_mode': 'dynamic'})
        html = self._render('stock.action_report_delivery', picking)
        self.assertIn('o_dyn_page', html)
        self.assertIn('Dyn Product', html)
        self.assertIn(picking.name, self._render('stock.action_report_picking', picking))

        # Customer invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id, 'journal_id': self.sale_journal.id,
            'invoice_line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 2, 'price_unit': 75.0})],
        })
        self.Profile.create({'name': 'Invoice', 'document_type': 'account_invoice', 'body_mode': 'dynamic'})
        html = self._render('account.account_invoices', invoice)
        self.assertIn('o_dyn_page', html)
        self.assertIn('Dyn Product', html)

        # Journal entry (report shipped by this module)
        entry = self.env['account.move'].create({
            'move_type': 'entry', 'journal_id': self.misc_journal.id, 'ref': 'DYN-JE',
            'line_ids': [
                (0, 0, {'account_id': self.expense.id, 'debit': 120.0, 'name': 'Dyn debit'}),
                (0, 0, {'account_id': self.payable.id, 'credit': 120.0, 'name': 'Dyn credit',
                        'partner_id': self.partner.id}),
            ],
        })
        html = self._render('pdf_report_dynamic_design.action_report_journal_entry', entry)
        self.assertIn('Dyn debit', html, 'standard journal entry body (no profile)')
        self.Profile.create({'name': 'JE', 'document_type': 'journal_entry', 'body_mode': 'dynamic'})
        html = self._render('pdf_report_dynamic_design.action_report_journal_entry', entry)
        self.assertIn('o_dyn_page', html)
        self.assertIn('Total Debit', html)
        self.assertIn('Dyn credit', html)

    def test_03_pdf_entry_point(self):
        """_render_qweb_pdf goes through _prepare_html (HTML in test mode, PDF otherwise)."""
        content, _fmt = self.env['ir.actions.report']._render_qweb_pdf(
            'sale.action_report_saleorder', self.sale_order.ids)
        self.assertTrue(content)

    # ======================================================================
    # Languages, fonts, direction
    # ======================================================================
    def test_10_arabic_rtl_font_and_direction(self):
        self.env['res.lang']._activate_lang('ar_001')
        partner_ar = self.partner.copy({'name': 'عميل تجريبي', 'lang': 'ar_001'})
        order = self._create_sale_order(2, partner=partner_ar)

        # No font rule: RTL language must switch to an Arabic-capable stack.
        ctx = self.engine._dyn_context(order)
        self.assertEqual(ctx['lang'], 'ar_001')
        self.assertEqual(ctx['direction'], 'rtl')
        self.assertTrue(ctx['style']['font_family'].startswith("'Tajawal'"))
        self.assertIn("'DynFallback'", ctx['style']['font_family'])
        self.assertEqual(ctx['style']['align_start'], 'right')

        # Generic rule, then a document-specific rule which must win.
        lang_ar = self.env['res.lang']._lang_get('ar_001')
        self.env['pdf.design.font.rule'].create({'lang_id': lang_ar.id, 'font': 'Cairo'})
        self.assertTrue(self.engine._dyn_context(order)['style']['font_family'].startswith("'Cairo'"))
        self.env['pdf.design.font.rule'].create({
            'lang_id': lang_ar.id, 'font': 'Amiri', 'document_type': 'sale_quotation'})
        self.assertTrue(self.engine._dyn_context(order)['style']['font_family'].startswith("'Amiri'"))

        # Translated label follows the document language.
        self.header_custom.label = 'Project Code'
        self.header_custom.with_context(lang='ar_001').label = 'رمز المشروع'
        ctx = self.engine._dyn_context(order)
        self.assertIn('رمز المشروع', [f['label'] for f in ctx['header_fields']])
        en_ctx = self.engine._dyn_context(self.sale_order)
        self.assertIn('Project Code', [f['label'] for f in en_ctx['header_fields']])
        self.assertEqual(en_ctx['direction'], 'ltr')

        html = self._render('sale.action_report_saleorder', order)
        self.assertIn('dir="rtl"', html)
        self.assertIn('عميل تجريبي', html)

    def test_11_forced_direction_and_custom_font_sanitized(self):
        lang_en = self.env['res.lang']._lang_get('en_US')
        self.env['pdf.design.font.rule'].create({
            'lang_id': lang_en.id, 'font': 'custom', 'custom_font': "Bad'Font;}</style>", 'direction': 'rtl'})
        ctx = self.engine._dyn_context(self.sale_order)
        self.assertEqual(ctx['direction'], 'rtl')
        self.assertNotIn('<', ctx['css'])
        self.assertNotIn(';}', ctx['style']['font_family'])
        with self.assertRaises(ValidationError):
            self.env['pdf.design.font.rule'].create({'lang_id': lang_en.id, 'font': 'Lato',
                                                     'document_type': False})

    # ======================================================================
    # Fallback & safety
    # ======================================================================
    def test_20_fallback_to_company_defaults(self):
        self.company.write({'primary_color': '#112233', 'secondary_color': '#445566',
                            'dyn_surface_color': '#F0F0F0', 'dyn_header_height': 40.0})
        so = self._create_sale_order(1)
        so.action_confirm()  # sale_order type: no profile
        ctx = self.engine._dyn_context(so)
        self.assertFalse(ctx['has_profile'])
        self.assertEqual(ctx['body_mode'], 'standard')
        self.assertFalse(ctx['layout_key'])
        self.assertEqual(ctx['style']['primary'], '#112233')
        self.assertEqual(ctx['header']['height'], 40.0)

        # Quotation profile inherits company colors until switched to custom.
        ctx = self.engine._dyn_context(self.sale_order)
        self.assertEqual(ctx['style']['accent'], '#445566')
        self.assertEqual(ctx['layout_key'], 'pdf_report_dynamic_design.external_layout_dyn_modern')
        self.quotation_profile.write({'color_mode': 'custom', 'primary_color': '#AA0000'})
        self._raw_write(self.quotation_profile, {'accent_color': 'javascript:alert(1)'})
        ctx = self.engine._dyn_context(self.sale_order)
        self.assertEqual(ctx['style']['primary'], '#AA0000')
        self.assertEqual(ctx['style']['accent'], '#445566', 'invalid color must fall back')

        # Archived profile -> company defaults again.
        self.quotation_profile.active = False
        self.assertFalse(self.engine._dyn_context(self.sale_order)['has_profile'])

    def test_21_missing_and_inaccessible_fields_never_crash(self):
        cfgs = (
            {'name': 'x_field_that_does_not_exist', 'label': 'Ghost', 'align': 'auto', 'show_if_empty': True},
            {'name': 'x_dyn_project_code', 'label': 'Project', 'align': 'auto', 'show_if_empty': False},
            {'name': 'date_order', 'label': 'Date', 'align': 'auto', 'show_if_empty': False},
        )
        values = self.engine._dyn_record_values(self.sale_order, cfgs)
        self.assertEqual([v['label'] for v in values], ['Project', 'Date'])

        # A field restricted to a group the user does not have is skipped.
        user = self.env['res.users'].create({
            'name': 'Dyn Sales Manager', 'login': 'dyn_sales_manager',
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_manager').id])],
        })
        field = self.sale_order._fields['date_order']
        with patch.object(field, 'groups', 'base.group_system'):
            values = self.engine.with_user(user)._dyn_record_values(self.sale_order.with_user(user), cfgs)
        self.assertEqual([v['label'] for v in values], ['Project'])

        # Formatting a bad value returns '' instead of raising.
        self.assertEqual(self.engine._dyn_format(self.sale_order, field, 'not-a-date'), '')
        # Binary fields are never printable.
        self.assertFalse(self.engine._dyn_can_read(self.partner, self.partner._fields['image_1920']))

    def test_22_engine_failure_keeps_pdf_alive(self):
        Engine = type(self.engine)
        with patch.object(Engine, '_dyn_build_context', side_effect=ValueError('boom')), \
                self.assertLogs(ENGINE_LOGGER, level='ERROR'):
            ctx = self.engine._dyn_context(self.sale_order)
            self.assertFalse(ctx['ok'])
            self.assertEqual(ctx['body_mode'], 'standard')
            self.assertTrue(ctx['css'])
            html = self._render('sale.action_report_saleorder', self.sale_order)
        self.assertIn(self.sale_order.name, html)

    def test_23_value_formatting(self):
        order = self.sale_order
        f = order._fields
        self.assertEqual(self.engine._dyn_format(order, f['state'], 'draft'),
                         dict(f['state']._description_selection(self.env))['draft'])
        self.assertEqual(self.engine._dyn_format(order, f['partner_id'], order.partner_id),
                         order.partner_id.display_name)
        self.assertIn('50', self.engine._dyn_format(order.order_line[0], order.order_line._fields['price_unit'], 50.0))
        money = self.engine._dyn_format(order, f['amount_total'], order.amount_total)
        self.assertTrue(money and order.currency_id.symbol in money)
        self.assertTrue(self.engine._dyn_format(order, f['date_order'], order.date_order))
        self.assertEqual(self.engine._dyn_format(order, f['require_signature'], False), 'No')

    # ======================================================================
    # Configuration
    # ======================================================================
    def test_30_profile_defaults_and_constraints(self):
        profile = self.Profile.create({'name': 'SO', 'document_type': 'sale_order'})
        self.assertTrue(profile.header_field_ids)
        self.assertIn('price_subtotal', profile.line_field_ids.mapped('field_name'))
        with self.assertRaises(ValidationError):
            self.Profile.create({'name': 'Duplicate', 'document_type': 'sale_order'})
        with self.assertRaises(ValidationError):
            # sale.order field used as a sale.order.line column
            self.DesignField.create({'profile_id': profile.id, 'section': 'line',
                                     'field_id': self.x_order_field.id})

    def test_24_standard_body_prints_no_duplicates(self):
        """Standard body: fields Odoo already prints are not repeated."""
        self.quotation_profile.body_mode = 'standard'
        ctx = self.engine._dyn_context(self.sale_order)
        labels = [f['label'] for f in ctx['header_fields']]
        self.assertEqual(labels, ['Project Code'], 'only the extra (custom) header field expected')
        # Line details: description + the extra column only, no repeated qty/price/subtotal.
        self.assertEqual(len(ctx['line_columns']), 2)
        self.assertEqual(ctx['line_rows'][0]['cells'][1]['v'], 'Handle with care 0')
        html = self._render('sale.action_report_saleorder', self.sale_order)
        self.assertNotIn('o_dyn_page', html)
        self.assertEqual(html.count('Handle with care 0'), 1)

        # Without extra fields nothing at all is added to the Odoo body.
        (self.header_custom | self.line_custom).unlink()
        ctx = self.engine._dyn_context(self.sale_order)
        self.assertFalse(ctx['header_fields'] or ctx['line_columns'])

    def test_31_margins_from_header_footer(self):
        html = ('<div class="header" data-dyn-margin-top="37.0" data-dyn-header-spacing="5.0" '
                'data-dyn-margin-bottom="22.0"></div><div class="header" data-dyn-margin-top="41.5">')
        margins = _dyn_extract_margins(html, b'')
        self.assertEqual(margins, {'margin-top': 41.5, 'header-spacing': 5.0, 'margin-bottom': 22.0})

        report = self.env.ref('sale.action_report_saleorder')
        # Odoo 17 reads data-report-margin-bottom natively.
        args = report._build_wkhtmltopdf_args(
            report.get_paperformat(), False,
            specific_paperformat_args={'data-report-margin-top': 41.5, 'data-report-margin-bottom': 22.0})
        self.assertEqual(args[args.index('--margin-top') + 1], '41.5')
        self.assertEqual(args[args.index('--margin-bottom') + 1], '22.0')

        # Header height + spacing drive the top margin.
        self.company.write({'dyn_header_height': 30.0, 'dyn_header_spacing': 6.0, 'dyn_footer_height': 15.0})
        self.quotation_profile.header_mode = 'company'
        ctx = self.engine._dyn_context(self.sale_order)
        # wkhtmltopdf draws the header from (margin_top - header_spacing): the spacing must
        # cover the whole header band, otherwise the header lands on the body.
        self.assertEqual(ctx['margins']['top'], 41.0)      # 5 pad + 30 header + 6 gap
        self.assertEqual(ctx['margins']['spacing'], 36.0)  # header + gap
        self.assertEqual(ctx['margins']['top'] - ctx['margins']['spacing'], 5.0)
        self.assertEqual(ctx['margins']['bottom'], 19.0)
        # Absurd values are clamped.
        self._raw_write(self.company, {'dyn_header_height': 500})
        self.assertLessEqual(self.engine._dyn_context(self.sale_order)['header']['height'], 90)

    def test_32_document_layout_wizard_preview(self):
        layout = self.modern_layout
        wizard = self.env['base.document.layout'].create({
            'company_id': self.company.id,
            'report_layout_id': layout.id,
            'external_report_layout_id': layout.view_id.id,
            'dyn_palette': 'emerald',
        })
        wizard._onchange_dyn_palette()
        self.assertEqual(wizard.dyn_surface_color, '#F1FAF6')
        self.assertIn('o_dyn_header', str(wizard.preview))

    def test_33_reference_designs_render(self):
        """Every built-in design renders the dynamic body with its own arrangement."""
        expected = {
            'banner': 'dyn-fromto', 'teal': 'dyn-kv', 'accent': 'dyn-kv', 'angled': 'dyn-kv',
            'chevron': 'dyn-kv', 'wave': 'dyn-strip', 'geometric': 'dyn-kv',
            'modern': 'dyn-panel',
        }
        for design, marker in expected.items():
            layout = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_%s' % design)
            self.quotation_profile.report_layout_id = layout
            ctx = self.engine._dyn_context(self.sale_order)
            self.assertEqual(ctx['design'], design)
            html = self._render('sale.action_report_saleorder', self.sale_order)
            self.assertIn(marker, html, design)
            self.assertIn('PRJ-42', html, design)
            if design in ('angled', 'chevron', 'wave', 'geometric'):
                self.assertTrue(ctx['deco']['header'].startswith('data:image/svg+xml;base64,'))
                self.assertIn('dyn-deco', html, design)

    def test_34_design_preset_and_rtl_mirror(self):
        layout = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_wave')
        wizard = self.env['base.document.layout'].create({'company_id': self.company.id})
        wizard.report_layout_id = layout
        wizard._onchange_dyn_layout_preset()
        self.assertEqual(wizard.dyn_palette, 'charcoal_orange')
        self.assertEqual(wizard.secondary_color, '#F28C1E')
        self.assertEqual(wizard.dyn_header_height, layout.dyn_header_height)

        self.env['res.lang']._activate_lang('ar_001')
        partner_ar = self.partner.copy({'lang': 'ar_001'})
        order = self._create_sale_order(1, partner=partner_ar)
        self.quotation_profile.report_layout_id = layout
        ctx = self.engine._dyn_context(order)
        self.assertTrue(ctx['deco']['mirror'], 'shapes are mirrored for right-to-left documents')
        self.assertIn('dyn-flip', self._render('sale.action_report_saleorder', order))

    def test_35_odoo20_layouts_and_tables(self):
        """Odoo 20 layouts: 8 offered (Odoo's own are replaced), table look chosen independently."""
        Layout = self.env['report.layout']
        offered = Layout.search([('dyn_hidden', '=', False)], order='sequence')
        self.assertEqual(offered[:8].mapped('name'),
                         ['Light', 'Bubble', 'Wave', 'Folder', 'Center', 'Dual', 'Lines', 'Compact'])
        self.assertTrue(self.env.ref('pdf_report_dynamic_design.report_layout_dyn_modern').dyn_hidden,
                        'legacy layouts are hidden from the picker but kept')

        for name in ('light', 'bubble', 'wave', 'folder', 'center', 'dual', 'lines', 'compact'):
            layout = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_v20_%s' % name)
            self.quotation_profile.report_layout_id = layout
            html = self._render('sale.action_report_saleorder', self.sale_order)
            self.assertIn('PRJ-42', html, name)
            self.assertEqual(self.engine._dyn_context(self.sale_order)['design'], 'v20_%s' % name)

        # Company table look, then a per-document override.
        self.quotation_profile.report_layout_id = self.env.ref(
            'pdf_report_dynamic_design.report_layout_dyn_v20_light')
        self.company.dyn_table_style = 'boxed'
        ctx = self.engine._dyn_context(self.sale_order)
        self.assertEqual(ctx['table_style'], 'boxed')
        self.assertIn('table.o_main_table', ctx['css'], 'Odoo body tables are styled too')
        self.quotation_profile.table_style = 'bubble'
        ctx = self.engine._dyn_context(self.sale_order)
        self.assertEqual(ctx['table_style'], 'bubble')
        self.assertIn('border-radius', ctx['css'])
        # "Layout Default" lets the layout decide.
        self.quotation_profile.table_style = 'company'
        self.company.dyn_table_style = 'auto'
        self.assertEqual(self.engine._dyn_context(self.sale_order)['table_style'], 'light')

        # Odoo 20: the native "Tables" badge drives the table look...
        wizard = self.env['base.document.layout'].create({'company_id': self.company.id})
        wizard.report_tables_id = 'striped'
        wizard._onchange_dyn_native_tables()
        self.assertEqual(wizard.dyn_table_style, 'striped')
        # ...picking an Odoo 20 layout keeps it...
        wizard.report_layout_id = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_v20_dual')
        wizard._onchange_dyn_layout_preset()
        self.assertEqual(wizard.dyn_table_style, 'striped')
        # ...and a template design switches back to its own table look.
        wizard.report_layout_id = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_banner')
        wizard._onchange_dyn_layout_preset()
        self.assertEqual(wizard.dyn_table_style, 'auto')
        # Writing only the native setting (other code, imports) keeps both in step.
        self.company.write({'report_tables_id': 'bold'})
        self.assertEqual(self.company.dyn_table_style, 'bold')

    def test_36_every_layout_prints_every_document(self):
        """Regression: Folder, Chevron and Swoosh crashed (string formatting in templates)."""
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_qty': 2, 'price_unit': 10.0})],
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id, 'journal_id': self.sale_journal.id,
            'invoice_line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 1, 'price_unit': 75.0})],
        })
        reports = [('sale.action_report_saleorder', self.sale_order),
                   ('purchase.report_purchase_quotation', po),
                   ('account.account_invoices', invoice)]
        layouts = self.env['report.layout'].search([('view_id.key', '=like', 'pdf_report_dynamic_design.%')])
        self.assertGreaterEqual(len(layouts), 19)
        for layout in layouts:
            # Company default layout (no profile involved) ...
            self.company.external_report_layout_id = layout.view_id
            for report, record in reports[1:]:
                html = self._render(report, record)
                self.assertIn('o_dyn_header', html, '%s / %s' % (layout.name, report))
            # ... and per-document layout with the dynamic body.
            self.quotation_profile.report_layout_id = layout
            self.assertIn('PRJ-42', self._render(*reports[0]), layout.name)

    def test_37_arabic_bidi_dates_and_strips(self):
        self.env['res.lang']._activate_lang('ar_001')
        partner_ar = self.partner.copy({'name': 'شركة اختبار', 'lang': 'ar_001', 'phone': '+966 11 555 0000'})
        order = self._create_sale_order(2, partner=partner_ar)
        ctx = self.engine._dyn_context(order)
        # Default title and labels in the document language.
        self.assertEqual(ctx['title'], 'عرض سعر')
        self.assertEqual(ctx['company_label'], 'من')
        # Left-to-right runs (amounts, phones, codes) are isolated inside RTL text.
        self.assertIn('dir="ltr"', str(ctx['totals'][0]['value']))
        self.assertIn('dir="ltr"', str(ctx['partners'][0]['html']))
        self.assertNotIn('dir="ltr"', str(self.engine._dyn_context(self.sale_order)['totals'][0]['value']))

        # Date-times: no seconds.
        value = self.engine._dyn_format(order, order._fields['date_order'], order.date_order)
        self.assertEqual(value.count(':'), 1, value)

        # Strips: one cell per field, no empty trailing cell.
        dual = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_v20_dual')
        self.quotation_profile.report_layout_id = dual
        ctx = self.engine._dyn_context(self.sale_order)
        count = len(ctx['header_fields'])
        if 0 < count <= 4:
            self.assertEqual(len(ctx['strip_rows'][0]), count)
            self.assertNotIn(None, ctx['strip_rows'][0])

    def test_38_layout_heights_follow_the_layout(self):
        compact = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_v20_compact')
        self.quotation_profile.report_layout_id = compact
        ctx = self.engine._dyn_context(self.sale_order)
        self.assertEqual(ctx['header']['height'], compact.dyn_header_height,
                         'a short layout must not keep the 32 mm default band (big gap)')
        # An explicit company height wins when the layout is the company's own.
        self.company.write({'external_report_layout_id': compact.view_id.id, 'dyn_header_height': 24.0})
        self.quotation_profile.report_layout_id = False
        self.assertEqual(self.engine._dyn_context(self.sale_order)['header']['height'], 24.0)

    def test_39_unhooked_templates_get_the_document_design(self):
        """A report body this module does not hook (e.g. l10n_sa's bilingual invoice)
        still uses the document's design for layout / header / footer."""
        teal = self.env.ref('pdf_report_dynamic_design.report_layout_dyn_teal')
        self.Profile.create({'name': 'Invoice', 'document_type': 'account_invoice',
                             'body_mode': 'dynamic', 'report_layout_id': teal.id})
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id, 'journal_id': self.sale_journal.id,
            'invoice_line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 1, 'price_unit': 75.0})],
        })
        ctx = self.engine._dyn_context_for_layout(invoice, self.company)
        self.assertEqual(ctx['layout_key'], teal.view_id.key)
        self.assertEqual(ctx['body_mode'], 'standard', 'the foreign body is kept')
        self.assertIsNone(self.engine._dyn_context_for_layout(self.partner, self.company))

        view = self.env['ir.ui.view'].create({
            'name': 'dyn foreign body', 'type': 'qweb', 'key': 'pdf_report_dynamic_design.test_foreign',
            'arch': '<t t-name="pdf_report_dynamic_design.test_foreign">'
                    '<t t-call="web.external_layout"><div class="page">FOREIGN BODY</div></t></t>',
        })
        html = str(self.env['ir.qweb']._render(view.id, {'o': invoice, 'doc': invoice}))
        self.assertIn('FOREIGN BODY', html)
        self.assertIn('Thank you for your business!', html, 'Teal Block footer expected')

    # ======================================================================
    # Performance
    # ======================================================================
    def _line_cfgs(self):
        names = ['name', 'product_id', 'product_uom_qty', 'tax_ids', 'price_subtotal', 'x_dyn_line_note']
        return tuple({'name': n, 'label': n, 'align': 'auto', 'show_if_empty': False} for n in names)

    def _count_line_queries(self, order, style):
        self.env.invalidate_all()
        lines = order.order_line
        start = self.cr.sql_log_count
        columns, rows = self.engine._dyn_line_table(lines, self._line_cfgs(), style)
        self.assertEqual(len(columns), 6)
        self.assertEqual(len(rows), len(lines))
        return self.cr.sql_log_count - start

    def test_40_query_count_does_not_grow_with_lines(self):
        style = self.engine._dyn_context(self.sale_order)['style']
        small = self._create_sale_order(3)
        big = self._create_sale_order(40)
        small_count = self._count_line_queries(small, style)
        big_count = self._count_line_queries(big, style)
        self.assertLessEqual(big_count, small_count + 2,
                             'N+1 detected: %s queries for 40 lines vs %s for 3' % (big_count, small_count))

        # Whole context: still flat.
        def ctx_queries(order):
            self.env.invalidate_all()
            start = self.cr.sql_log_count
            self.engine._dyn_context(order)
            return self.cr.sql_log_count - start
        ctx_queries(small)  # warm the configuration caches
        self.assertLessEqual(ctx_queries(big), ctx_queries(small) + 3)

    def test_41_configuration_is_cached(self):
        lang = self.env.lang or 'en_US'
        self.engine._dyn_profile_config(self.company.id, 'sale_quotation', lang)
        start = self.cr.sql_log_count
        cfg = self.engine._dyn_profile_config(self.company.id, 'sale_quotation', lang)
        self.assertEqual(self.cr.sql_log_count - start, 0, 'cached config must not query')
        self.assertEqual(cfg['id'], self.quotation_profile.id)
        # Editing the profile invalidates the cache.
        self.quotation_profile.title = 'Offer'
        cfg = self.engine._dyn_profile_config(self.company.id, 'sale_quotation', lang)
        self.assertEqual(cfg['title'], 'Offer')

    # ======================================================================
    # v17 test report fixes
    # ======================================================================
    def _create_invoice(self, partner=None):
        return self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': (partner or self.partner).id,
            'journal_id': self.sale_journal.id, 'payment_reference': 'INV/2026/00042',
            'invoice_line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 2,
                                         'price_unit': 75.0, 'name': 'Dyn invoice line'})],
        })

    def test_42_invoice_keeps_payment_communication(self):
        invoice = self._create_invoice()
        profile = self.Profile.create({'name': 'Invoice', 'document_type': 'account_invoice',
                                       'body_mode': 'dynamic'})
        # New profiles print the payment reference as a header field...
        self.assertIn('payment_reference', profile.header_field_ids.mapped('field_name'))
        ctx = self.engine._dyn_context(invoice)
        self.assertFalse(ctx['payment_ref'], 'already a header field: not printed twice')
        self.assertIn('INV/2026/00042', ''.join(str(f['value']) for f in ctx['header_fields']))
        # ...and profiles created before the fix (no such field) still print it.
        profile.header_field_ids.filtered(lambda f: f.field_name == 'payment_reference').unlink()
        ctx = self.engine._dyn_context(invoice)
        self.assertIn('INV/2026/00042', str(ctx['payment_ref']))
        html = self._render('account.account_invoices', invoice)
        self.assertIn('Payment Communication', html)
        # Vendor bills have no payment communication block.
        bill = self.env['account.move'].new({'move_type': 'in_invoice',
                                             'payment_reference': 'BILL-REF'})
        self.assertFalse(self.engine._dyn_invoice_extras(bill, ())['payment_ref'])

    def test_43_line_description_label_is_not_odoo_label(self):
        """account.move.line.name is called "Label" ("بطاقة عنوان" in Arabic):
        the column is titled "Description" ("الوصف") instead."""
        self.env['res.lang']._activate_lang('ar_001')
        partner_ar = self.partner.copy({'name': 'عميل', 'lang': 'ar_001'})
        invoice = self._create_invoice(partner=partner_ar)
        self.Profile.create({'name': 'Invoice', 'document_type': 'account_invoice',
                             'body_mode': 'dynamic'})
        expected_ar = self.engine.with_context(lang='ar_001')._dyn_description_label()
        odoo_label_ar = self.env['account.move.line'].with_context(
            lang='ar_001')._fields['name']._description_string(self.env(context={'lang': 'ar_001'}))
        labels = [c['label'] for c in self.engine._dyn_context(invoice)['line_columns']]
        self.assertIn(expected_ar, labels)
        if odoo_label_ar != expected_ar:
            self.assertNotIn(odoo_label_ar, labels)
        labels_en = [c['label'] for c in self.engine._dyn_context(self._create_invoice())['line_columns']]
        self.assertIn('Description', labels_en)
        self.assertNotIn('Label', labels_en)

    def test_44_datetimes_follow_the_document_language(self):
        self.env['res.lang']._activate_lang('ar_001')
        partner_ar = self.partner.copy({'name': 'عميل', 'lang': 'ar_001'})
        order = self._create_sale_order(1, partner=partner_ar).with_context(lang='ar_001')
        value = self.engine._dyn_format(order, order._fields['date_order'], order.date_order)
        self.assertEqual(value.count(':'), 1, 'no seconds: %s' % value)
        self.assertFalse(any('a' <= c.lower() <= 'z' for c in value),
                         'English month / AM-PM in an Arabic document: %s' % value)
        local_date = fields.Datetime.context_timestamp(
            order.with_context(tz=self.env.user.tz or 'UTC'), order.date_order).date()
        date_only = self.engine._dyn_format(order, order._fields['validity_date'], local_date)
        self.assertIn(date_only, value, 'date part identical to the Arabic date fields')

    def test_45_settings_reject_invalid_values(self):
        for vals in ({'dyn_header_height': -5}, {'dyn_footer_height': 500},
                     {'dyn_header_spacing': -1}, {'dyn_base_font_size': -10},
                     {'dyn_surface_color': 'red'}, {'dyn_text_color': '#12345G'}):
            with self.assertRaises(ValidationError, msg=vals), self.cr.savepoint():
                self.company.write(vals)
        self.company.write({'dyn_header_height': 40, 'dyn_surface_color': '#abc'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.quotation_profile.write({'header_height': -3})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.quotation_profile.write({'primary_color': 'blue;}'})
        lang = self.env['res.lang']._lang_get(self.env.lang or 'en_US')
        rule = self.env['pdf.design.font.rule'].create({'lang_id': lang.id, 'font': 'Lato'})
        self.assertFalse(rule.font_size, '0 = company size is allowed')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            rule.font_size = -2

    def test_46_saudi_zatca_qr_and_footer(self):
        """ZATCA (l10n_sa): the QR string and the issue date are rendered when the
        localization provides them; nothing breaks when it is not installed."""
        invoice = self._create_invoice()
        self.assertFalse([c for c in self.engine._dyn_qr_codes(invoice) if c['kind'] == 'zatca'],
                         'draft / non-Saudi invoice: no ZATCA QR')
        self.assertFalse(self.engine._dyn_zatca_footer(None))

        class FakeMove:
            _fields = {'l10n_sa_qr_code_str': True, 'l10n_sa_confirmation_datetime': True}
            l10n_sa_qr_code_str = 'AQ1EeW4gQ29tcGFueQ=='
            l10n_sa_confirmation_datetime = '2026-11-21 15:14:00'

            def get_l10n_sa_confirmation_datetime_sa_tz(self):
                return '2026-11-21\n18:14:00'

        fake = FakeMove()
        codes = self.engine._dyn_qr_codes(fake)
        self.assertEqual(len(codes), 1)
        self.assertEqual(codes[0]['kind'], 'zatca')
        self.assertIn('barcode_type=QR', codes[0]['src'])
        self.assertIn('AQ1EeW4gQ29tcGFueQ%3D%3D', codes[0]['src'], 'value must be URL-encoded')
        self.assertEqual(str(self.engine._dyn_zatca_footer(fake)), '2026-11-21 18:14:00')

        # Rendering: the QR image and the legal footer line reach the PDF HTML.
        self.Profile.create({'name': 'Invoice', 'document_type': 'account_invoice',
                             'body_mode': 'dynamic'})
        Engine = type(self.engine)
        with patch.object(Engine, '_dyn_qr_codes', lambda s, r: codes), \
                patch.object(Engine, '_dyn_zatca_footer', lambda s, r: 'ZATCA-ISSUE-2026'):
            html, _fmt = self.env['ir.actions.report']._render_qweb_html(
                'account.account_invoices', invoice.ids, data={'report_type': 'pdf'})
            html = html.decode() if isinstance(html, bytes) else html
        self.assertIn('barcode_type=QR', html)
        self.assertIn('dyn-qr-zatca', html)
        self.assertIn('ZATCA-ISSUE-2026', html)

    # ======================================================================
    # Odoo 18
    # ======================================================================
    def test_47_standard_body_keeps_odoo18_document_title(self):
        """Odoo 18 bodies set ``layout_document_title`` and let the layout print it:
        the module's layouts must print it once in standard mode, never in dynamic mode."""
        self.quotation_profile.body_mode = 'standard'
        html = self._render('sale.action_report_saleorder', self.sale_order)
        self.assertIn('dyn-doc-title', html)
        self.assertEqual(html.count('Quotation # '), 1)
        self.quotation_profile.body_mode = 'dynamic'
        html = self._render('sale.action_report_saleorder', self.sale_order)
        self.assertNotIn('dyn-doc-title', html)
        self.assertIn('o_dyn_page', html)

    def test_48_saudi_not_legal_banner_and_qr(self):
        """l10n_sa (Odoo 18): no QR and a bilingual "not a legal document" banner until
        the invoice is legal."""
        from types import SimpleNamespace

        def fake(legal):
            move = SimpleNamespace(
                _name='account.move',
                _fields={'l10n_sa_qr_code_str': True},
                l10n_sa_qr_code_str='AQ1EeW4=',
                company_id=SimpleNamespace(country_id=SimpleNamespace(code='SA')),
                is_sale_document=lambda: True,
                _l10n_sa_is_legal=lambda: legal,
            )
            return move

        self.assertEqual(self.engine._dyn_qr_codes(fake(False)), [])
        self.assertIn('THIS IS NOT A LEGAL DOCUMENT', str(self.engine._dyn_zatca_banner(fake(False))))
        self.assertEqual(len(self.engine._dyn_qr_codes(fake(True))), 1)
        self.assertFalse(self.engine._dyn_zatca_banner(fake(True)))
        # Saudi localization not installed: nothing.
        if not hasattr(self.env['account.move'], '_l10n_sa_is_legal'):
            self.assertFalse(self.engine._dyn_zatca_banner(self._create_invoice()))

        self.Profile.create({'name': 'Invoice', 'document_type': 'account_invoice',
                             'body_mode': 'dynamic'})
        banner = self.engine._dyn_zatca_banner(fake(False))
        with patch.object(type(self.engine), '_dyn_zatca_banner', lambda s, r: banner):
            html = self._render('account.account_invoices', self._create_invoice())
        self.assertEqual(html.count('THIS IS NOT A LEGAL DOCUMENT'), 1)

    # ======================================================================
    # Odoo 19
    # ======================================================================
    def test_49_odoo19_renamed_line_fields_and_operations_sheet(self):
        # Odoo 19 renamed tax_id / taxes_id; Odoo 20 renamed the purchase line and stock move unit to uom_id.
        so_profile = self.Profile.create({'name': 'SO', 'document_type': 'sale_order'})
        self.assertIn('tax_ids', so_profile.line_field_ids.mapped('field_name'))
        po_profile = self.Profile.create({'name': 'PO', 'document_type': 'purchase_order'})
        self.assertIn('tax_ids', po_profile.line_field_ids.mapped('field_name'))
        rfq_profile = self.Profile.create({'name': 'RFQ', 'document_type': 'purchase_rfq'})
        self.assertIn('uom_id', rfq_profile.line_field_ids.mapped('field_name'))

        # The operations sheet has no company layout any more: only its body is designed.
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'), ('company_id', '=', self.company.id)], limit=1)
        customers = self.env.ref('stock.stock_location_customers')
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id, 'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id, 'location_dest_id': customers.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id, 'product_uom_qty': 2, 'uom_id': self.uom_unit.id,
                'location_id': picking_type.default_location_src_id.id, 'location_dest_id': customers.id,
            })],
        })
        self.Profile.create({'name': 'Picking', 'document_type': 'stock_picking', 'body_mode': 'dynamic'})
        html = self._render('stock.action_report_picking', picking)
        self.assertIn('o_dyn_page', html)
        self.assertIn('Dyn Product', html)

    def test_50_payment_link_qr(self):
        from types import SimpleNamespace
        move = SimpleNamespace(
            _fields={'display_link_qr_code': True}, display_link_qr_code=True, amount_residual=10.0,
            _generate_portal_payment_qr=lambda: '/report/barcode/?barcode_type=QR&value=pay')
        codes = self.engine._dyn_qr_codes(move)
        self.assertEqual([c['kind'] for c in codes], ['payment_link'])
        move.amount_residual = 0.0
        self.assertEqual(self.engine._dyn_qr_codes(move), [], 'paid invoice: no payment QR')

    # ======================================================================
    # Odoo 20
    # ======================================================================
    def test_51_odoo20_pdf_engines_get_the_margins(self):
        """Odoo 20 splits PDF engines: wkhtmltopdf (base_report_wkhtmltox) and Paper
        Muncher prepare the HTML separately; both must receive the header/footer margins."""
        html = ('<html><head></head><body><main>'
                '<div class="header" data-dyn-margin-top="41.0" data-dyn-header-spacing="36.0" '
                'data-dyn-margin-bottom="22.0">H</div>'
                '<div class="article" data-oe-model="sale.order" data-oe-id="%s">B</div>'
                '<div class="footer">F</div></main></body></html>') % self.sale_order.id
        report = self.env.ref('sale.action_report_saleorder')
        for method in ('_prepare_wkhtmltopdf_html', '_prepare_html'):
            res = getattr(report, method)(html, report_model='sale.order')
            args = res[4]
            self.assertEqual(float(args['data-report-margin-top']), 41.0, method)
            self.assertEqual(float(args['data-report-header-spacing']), 36.0, method)
            self.assertEqual(float(args['data-report-margin-bottom']), 22.0, method)
            self.assertEqual(res[1], [self.sale_order.id], method)

    def test_52_odoo20_line_label_column_title(self):
        """Odoo 20 adds a computed ``label`` on lines ("Label"): titled "Description" too."""
        label_field = self.env['ir.model.fields']._get('sale.order.line', 'label')
        if not label_field:
            self.skipTest('no label field on sale.order.line')
        self.DesignField.create({'profile_id': self.quotation_profile.id, 'section': 'line',
                                 'field_id': label_field.id, 'sequence': 0})
        labels = [c['label'] for c in self.engine._dyn_context(self.sale_order)['line_columns']]
        self.assertIn('Description', labels)
        self.assertNotIn('Label', labels)

    def test_53_arabic_code_labels_are_translated(self):
        """Odoo 18+ loads Python translations only when the .po entry is marked
        ``#. odoo-python``: titles, partner labels and totals must be Arabic."""
        from odoo.tools.translate import code_translations
        self.env['res.lang']._activate_lang('ar_001')
        translations = code_translations.get_python_translations('pdf_report_dynamic_design', 'ar_001')
        expected = {'Description': 'الوصف', 'Quotation': 'عرض سعر', 'Customer': 'العميل',
                    'Untaxed Amount': 'المبلغ قبل الضريبة', 'Taxes': 'الضرائب',
                    'Total': 'الإجمالي', 'Tax ID': 'الرقم الضريبي', 'Vendor': 'المورد',
                    'Delivery Slip': 'إيصال التسليم'}
        for source, arabic in expected.items():
            self.assertEqual(translations.get(source), arabic, source)
        # End to end: an Arabic customer's quotation printed by an English user.
        partner_ar = self.partner.copy({'name': 'عميل', 'lang': 'ar_001'})
        order = self._create_sale_order(1, partner=partner_ar)
        self.quotation_profile.body_mode = 'dynamic'
        ctx = self.engine._dyn_context(order)
        self.assertEqual(ctx['title'], 'عرض سعر')
        self.assertIn('الوصف', [c['label'] for c in ctx['line_columns']])
        html = self._render('sale.action_report_saleorder', order)
        for arabic in ('عرض سعر', 'الوصف', 'الإجمالي'):
            self.assertIn(arabic, html)
        self.assertNotIn('Untaxed Amount', html)
