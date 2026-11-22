# PDF Report Dynamic Design

Modern PDF layouts, color palettes, per-language fonts (Arabic / RTL), header and footer controls, and a separate design per document type for Odoo reports.

**This branch: Odoo 16.0** (Community & Enterprise) · License: LGPL-3 · Author: Ibrahim Yahia

## Branches

| Odoo | Branch |
|------|--------|
| 16.0 | [`16.0`](../../tree/16.0) |
| 17.0 | [`17.0`](../../tree/17.0) |
| 18.0 | [`18.0`](../../tree/18.0) |
| 19.0 | [`19.0`](../../tree/19.0) |
| 20.0 | [`20.0`](../../tree/20.0) |

## Features

- 15 layouts (8 modern style layouts + 7 template designs) and 7 table styles
- Color palettes and custom primary / accent / surface / border colors
- A font per language, with automatic right-to-left direction for Arabic
- Header and footer heights, spacing and content controls; margins follow the header so it never overlaps the body
- A design per document: quotation, sales order, RFQ, purchase order, delivery slip, invoice and journal entry, falling back to the company defaults
- Pick the fields to print, including custom `x_` fields, with safe formatting
- Keeps localization content such as the Saudi e-invoice (ZATCA) QR code
- Arabic translation included

## Installation

1. Copy the `pdf_report_dynamic_design` folder into your addons path.
2. Restart Odoo and update the apps list.
3. Install **PDF Report Dynamic Design**.

Depends on: `web`, `sale`, `purchase`, `stock`, `account`.

Configure it in **Settings › Companies › Configure Document Layout** and **Settings › PDF Designs** (Document Designs, Fonts per Language).

## Tests

```
odoo -d <db> -u pdf_report_dynamic_design --test-tags /pdf_report_dynamic_design --stop-after-init
```

## Support

Ibrahim Yahia · ibrahim.yahiah@gmail.com · [LinkedIn](https://www.linkedin.com/in/ibrahim-yahia)
