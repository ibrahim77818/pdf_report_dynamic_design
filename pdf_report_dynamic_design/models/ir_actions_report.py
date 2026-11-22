# -*- coding: utf-8 -*-
"""Page margins derived from the dynamic header / footer heights.

The dynamic layouts write ``data-dyn-margin-top|bottom|spacing`` on their
``.header`` / ``.footer`` nodes. Odoo already lifts those nodes into the
wkhtmltopdf header/footer HTML; here we read the values back and feed them to
wkhtmltopdf, so the body always starts below the header and ends above the
footer - whatever the paper format says. Standard layouts are untouched.
"""
import re

from odoo import api, models

_DYN_ATTR_RE = re.compile(r'data-dyn-(margin-top|margin-bottom|header-spacing)="([0-9]+(?:\.[0-9]+)?)"')


def _dyn_extract_margins(*html_parts):
    """Return {'margin-top': x, 'margin-bottom': y, 'header-spacing': z} (max per key)."""
    found = {}
    for part in html_parts:
        if not part:
            continue
        text = part.decode() if isinstance(part, bytes) else str(part)
        for key, value in _DYN_ATTR_RE.findall(text):
            found[key] = max(found.get(key, 0.0), float(value))
    return found


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _prepare_html(self, html, *args, **kwargs):
        res = super()._prepare_html(html, *args, **kwargs)
        try:
            bodies, res_ids, header, footer, specific_args = res
        except (TypeError, ValueError):
            return res
        margins = _dyn_extract_margins(header, footer)
        if margins:
            specific_args = dict(specific_args or {})
            if 'margin-top' in margins:
                specific_args['data-report-margin-top'] = margins['margin-top']
            if 'header-spacing' in margins:
                specific_args['data-report-header-spacing'] = margins['header-spacing']
            if 'margin-bottom' in margins:
                specific_args['data-dyn-margin-bottom'] = margins['margin-bottom']
            return bodies, res_ids, header, footer, specific_args
        return res

    @api.model
    def _build_wkhtmltopdf_args(self, paperformat_id, landscape, specific_paperformat_args=None,
                                set_viewport_size=False):
        args = super()._build_wkhtmltopdf_args(
            paperformat_id, landscape, specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size)
        bottom = (specific_paperformat_args or {}).get('data-dyn-margin-bottom')
        if bottom and '--margin-bottom' in args:
            idx = args.index('--margin-bottom')
            if idx + 1 < len(args):
                args[idx + 1] = str(bottom)
        return args
