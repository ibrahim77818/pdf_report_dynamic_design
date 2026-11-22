# -*- coding: utf-8 -*-
"""Page margins derived from the dynamic header / footer heights.

The dynamic layouts write ``data-dyn-margin-top|bottom|header-spacing`` on their
``.header`` node. Odoo already lifts that node into the wkhtmltopdf header HTML;
here we read the values back and pass them as Odoo's own ``data-report-*``
paperformat overrides (all three are supported natively since Odoo 17), so the
body always starts below the header and ends above the footer. Standard layouts
are untouched.
"""
import re

from odoo import models

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
        if not margins:
            return res
        specific_args = dict(specific_args or {})
        for key in ('margin-top', 'header-spacing', 'margin-bottom'):
            if key in margins:
                specific_args['data-report-%s' % key] = margins[key]
        return bodies, res_ids, header, footer, specific_args
