# -*- coding: utf-8 -*-
"""Design-specific CSS and SVG decorations (pure functions, no ORM).

wkhtmltopdf runs an old WebKit: no CSS variables, no flexbox, no clip-path.
Shapes (angled bands, waves, triangles) are therefore inline SVG images,
generated here with the sanitized palette colors.
"""
import base64

from .dyn_common import DESIGNS, LAYOUT_PREFIX


def design_from_key(view_key):
    """'pdf_report_dynamic_design.external_layout_dyn_wave' -> 'wave'."""
    if view_key and view_key.startswith(LAYOUT_PREFIX):
        name = view_key[len(LAYOUT_PREFIX):]
        if name in DESIGNS:
            return name
    return 'standard'


def mix(color, other, ratio):
    """Blend ``color`` toward ``other`` (ratio 0..1). Both are #RRGGBB."""
    try:
        c1 = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
        c2 = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    except (TypeError, ValueError, IndexError):
        return color
    return '#%02X%02X%02X' % tuple(round(a + (b - a) * ratio) for a, b in zip(c1, c2))


def _svg_uri(svg):
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()


def _svg(view_w, view_h, body):
    return _svg_uri(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="none" '
        'width="%d" height="%d">%s</svg>' % (view_w, view_h, view_w, view_h, body))


def _mosaic(cols, rows, size, colors, corner='top-left'):
    """Triangle mosaic filling a corner: square cells split diagonally, fading out."""
    out = []
    for r in range(rows):
        for c in range(cols):
            if c + r * 2 >= cols:
                continue
            x, y = c * size, r * size
            if corner == 'bottom-right':
                x, y = (cols - 1 - c) * size, (rows - 1 - r) * size
            c1 = colors[(r * 2 + c * 3) % len(colors)]
            c2 = colors[(r * 3 + c * 2 + 1) % len(colors)]
            out.append('<polygon points="%d,%d %d,%d %d,%d" fill="%s"/>' % (
                x, y, x + size, y, x, y + size, c1))
            out.append('<polygon points="%d,%d %d,%d %d,%d" fill="%s"/>' % (
                x + size, y, x + size, y + size, x, y + size, c2))
    return ''.join(out)


def decorations(design, style, rtl=False):
    """{'header': data-uri|False, 'footer': data-uri|False, 'mirror': bool}."""
    p, a, s = style['primary'], style['accent'], style['surface']
    light_a = mix(a, '#FFFFFF', 0.45)
    pale_a = mix(a, '#FFFFFF', 0.7)
    deco = {'header': False, 'footer': False}
    if design == 'angled':
        deco['header'] = _svg(1000, 40, (
            '<polygon points="600,0 1000,0 1000,40 650,40" fill="%s"/>'
            '<polygon points="560,0 590,0 640,40 610,40" fill="%s"/>') % (a, light_a))
        deco['footer'] = _svg(1000, 60, (
            '<polygon points="380,6 1000,6 1000,20 395,20" fill="%s"/>'
            '<polygon points="0,24 560,24 600,60 0,60" fill="%s"/>'
            '<polygon points="610,40 1000,40 1000,60 630,60" fill="%s"/>') % (a, p, a))
    elif design == 'chevron':
        deco['header'] = _svg(1000, 120, (
            '<polygon points="0,0 470,0 540,120 0,120" fill="%s"/>'
            '<polygon points="470,0 490,0 560,120 540,120" fill="%s"/>'
            '<polygon points="500,0 1000,0 1000,26 515,26" fill="%s"/>') % (p, s, a))
        deco['footer'] = _svg(1000, 30, (
            '<rect x="0" y="0" width="1000" height="6" fill="%s"/>'
            '<rect x="0" y="12" width="1000" height="18" fill="%s"/>') % (s, a))
    elif design == 'wave':
        deco['header'] = _svg(1000, 150, (
            '<path d="M0,0 H1000 V58 H620 C540,58 520,122 410,126 H0 Z" fill="%s"/>'
            '<path d="M0,126 H410 C520,122 540,58 620,58 H1000 V76 H632 C556,76 540,146 412,148 H0 Z" '
            'fill="%s"/>') % (p, a))
        deco['footer'] = _svg(1000, 60, (
            '<path d="M0,26 C220,2 420,44 640,20 C780,6 900,10 1000,4 V60 H0 Z" fill="%s"/>'
            '<path d="M0,40 C240,14 440,58 660,34 C800,20 910,26 1000,20 V60 H0 Z" fill="%s"/>')
            % (a, p))
    elif design == 'geometric':
        # Fixed-size corner images (uniform scaling): header 70x28mm, footer 40x8mm.
        colors = [a, light_a, pale_a, mix(p, '#FFFFFF', 0.25), mix(a, p, 0.3)]
        deco['header'] = _svg(700, 280, _mosaic(10, 4, 70, colors))
        deco['footer'] = _svg(400, 80, _mosaic(10, 2, 40, colors, corner='bottom-right'))
    elif design == 'v20_bubble':
        # Fixed size corner images (uniform scaling): header 62x30mm, footer 36x10mm.
        deco['header'] = _svg(620, 300, (
            # every circle stays inside the 620x300 box: no straight cut edges
            '<circle cx="470" cy="150" r="140" fill="%s"/>'
            '<circle cx="285" cy="95" r="62" fill="%s"/>'
            '<circle cx="225" cy="215" r="22" fill="%s"/>') % (p, a, light_a))
        deco['footer'] = _svg(360, 100, (
            '<circle cx="50" cy="52" r="44" fill="%s"/>'
            '<circle cx="140" cy="62" r="28" fill="%s"/>'
            '<circle cx="200" cy="44" r="11" fill="%s"/>') % (a, light_a, p))
    elif design == 'v20_wave':
        deco['header'] = _svg(1000, 100, (
            '<path d="M0,0 H1000 V46 C820,86 640,20 470,46 C300,72 150,78 0,52 Z" fill="%s"/>'
            '<path d="M0,64 C150,90 300,84 470,58 C640,32 820,98 1000,58 V66 C820,106 640,40 470,66 '
            'C300,92 150,98 0,72 Z" fill="%s"/>') % (p, a))
        deco['footer'] = _svg(1000, 60, (
            '<path d="M0,24 C180,0 360,44 560,22 C740,4 880,10 1000,26 V60 H0 Z" fill="%s"/>'
            '<path d="M0,14 C180,-10 360,34 560,12 C740,-6 880,0 1000,16 V22 C880,6 740,0 560,18 '
            'C360,40 180,-4 0,20 Z" fill="%s"/>') % (p, a))
    elif design == 'v20_folder':
        deco['header'] = _svg(1000, 100, (
            '<path d="M0,94 V12 Q0,0 12,0 H330 Q346,0 354,12 L396,82 Q403,94 420,94 Z" fill="%s"/>'
            '<rect x="0" y="94" width="1000" height="6" fill="%s"/>') % (s, p))
    deco['mirror'] = bool(rtl)
    return deco


def table_css(key, st, sc):
    """Odoo 20 style table looks for the dynamic lines table and Odoo's own tables.

    Odoo's body tables (``o_main_table``) are not inside the scoped wrapper, so they are
    targeted through ``.article``; ``!important`` beats the stock report styles.
    """
    if not key:
        return ''
    p, a, s, b, t = st['primary'], st['accent'], st['surface'], st['border'], st['text']
    on_p = st['on_primary']
    rtl = st.get('direction') == 'rtl'
    start_side, end_side = ('right', 'left') if rtl else ('left', 'right')
    r_start = '6px 0 0 6px' if not rtl else '0 6px 6px 0'
    r_end = '0 6px 6px 0' if not rtl else '6px 0 0 6px'
    tables = ['%s table.dyn-lines' % sc, '.article table.o_main_table']
    rules = {
        'light': [
            "{t} thead th{{background-color:transparent !important;color:{p} !important;border:0 !important;"
            "border-bottom:2px solid {p} !important;}}",
            "{t} tbody td{{background-color:transparent !important;border:0 !important;"
            "border-bottom:1px solid {b} !important;}}",
        ],
        'boxed': [
            "{t}{{border-collapse:collapse !important;}}",
            "{t} thead th{{background-color:{s} !important;color:{tx} !important;border:1px solid {b} !important;}}",
            "{t} tbody td{{background-color:transparent !important;border:1px solid {b} !important;}}",
        ],
        'bold': [
            "{t} thead th{{background-color:{p} !important;color:{on_p} !important;border:0 !important;"
            "text-transform:uppercase;}}",
            "{t} tbody td{{background-color:transparent !important;border:0 !important;"
            "border-bottom:1px solid {b} !important;}}",
            "{t} tbody tr:last-child td{{border-bottom:2px solid {p} !important;}}",
        ],
        'striped': [
            "{t} thead th{{background-color:transparent !important;color:{tx} !important;border:0 !important;"
            "border-bottom:2px solid {p} !important;}}",
            "{t} tbody td{{background-color:transparent !important;border:0 !important;}}",
            "{t} tbody tr:nth-child(odd) td{{background-color:{s} !important;}}",
        ],
        'bubble': [
            "{t}{{border-collapse:separate !important;border-spacing:0 3px !important;}}",
            "{t} thead th{{background-color:{p} !important;color:{on_p} !important;border:0 !important;}}",
            "{t} thead th:first-child,{t} tbody td:first-child{{border-radius:{r_start};}}",
            "{t} thead th:last-child,{t} tbody td:last-child{{border-radius:{r_end};}}",
            "{t} tbody td{{background-color:{s} !important;border:0 !important;}}",
        ],
        'column': [
            "{t}{{border-collapse:collapse !important;}}",
            "{t} thead th{{background-color:transparent !important;color:{p} !important;border:0 !important;"
            "border-bottom:2px solid {p} !important;}}",
            "{t} tbody td{{background-color:transparent !important;border:0 !important;}}",
            "{t} thead th + th,{t} tbody td + td{{border-{start}:1px solid {b} !important;}}",
            "{t} tbody tr:last-child td{{border-bottom:1px solid {b} !important;}}",
        ],
        'compact': [
            "{t} thead th,{t} tbody td{{padding:2px 4px !important;font-size:0.88em;}}",
            "{t} thead th{{background-color:transparent !important;color:{p} !important;border:0 !important;"
            "border-bottom:1px solid {p} !important;}}",
            "{t} tbody td{{background-color:transparent !important;border:0 !important;"
            "border-bottom:1px solid {b} !important;}}",
        ],
    }.get(key)
    if not rules:
        return ''
    out = []
    for table in tables:
        for rule in rules:
            out.append(rule.format(t=table, p=p, a=a, s=s, b=b, tx=t, on_p=on_p, r_start=r_start,
                                   r_end=r_end, start=start_side, end=end_side))
    # Totals follow the table look.
    if key in ('bold', 'bubble'):
        out.append("%s table.dyn-totals tr.dyn-strong td{background-color:%s !important;color:%s !important;}"
                   % (sc, p, on_p))
    if key == 'boxed':
        out.append("%s table.dyn-totals td{border:1px solid %s !important;}" % (sc, b))
    if key == 'bubble':
        out.append("%s table.dyn-totals tr.dyn-strong td:first-child{border-radius:%s;}" % (sc, r_start))
        out.append("%s table.dyn-totals tr.dyn-strong td:last-child{border-radius:%s;}" % (sc, r_end))
    return ''.join(out)


def design_css(design, st, sc):
    """Extra CSS rules for ``design`` (all values already sanitized)."""
    p, a, s, b = st['primary'], st['accent'], st['surface'], st['border']
    on_p, on_a = st['on_primary'], st['on_accent']
    v = {'sc': sc, 'p': p, 'a': a, 's': s, 'b': b, 'on_p': on_p, 'on_a': on_a,
         'p_mid': mix(p, '#FFFFFF', 0.45), 'a_pale': mix(a, '#FFFFFF', 0.82),
         'a_tint': mix(a, '#FFFFFF', 0.65), 'start': st['align_start'], 'end': st['align_end']}
    common = []
    rules = {
        'banner': [
            "%(sc)s .dyn-titlebox{border:7px solid %(p)s;background-color:%(p_mid)s;"
            "text-align:center;padding:8px 6px;margin-bottom:12px;}",
            "%(sc)s .dyn-titlebox .dyn-title{color:#FFFFFF;font-size:2.1em;}",
            "%(sc)s .dyn-titlebox .dyn-docname{color:#FFFFFF;}",
            "%(sc)s .dyn-bar{display:none;}",
            "%(sc)s table.dyn-strip td{border:0;}",
            "%(sc)s .dyn-fromto{border-bottom:3px solid %(p)s;padding-bottom:8px;margin-bottom:12px;}",
            "%(sc)s table.dyn-lines th{background-color:transparent;color:%(p)s;"
            "text-transform:uppercase;border-bottom:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-lines td{border:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-lines tr.dyn-odd td{background-color:transparent;}",
            "%(sc)s table.dyn-totals td{border:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-totals tr.dyn-strong td{background-color:%(a)s;color:%(on_a)s;"
            "font-size:1.2em;}",
        ],
        'teal': [
            "%(sc)s .dyn-titlebox{background-color:%(p)s;padding:12px 14px;margin-bottom:12px;}",
            "%(sc)s .dyn-titlebox .dyn-title{color:%(on_p)s;font-size:2.1em;}",
            "%(sc)s .dyn-titlebox .dyn-docname{color:%(on_p)s;}",
            "%(sc)s .dyn-section-head{border-bottom:2px solid %(b)s;padding-bottom:2px;}",
            "%(sc)s table.dyn-kv td.dyn-kv-value{border-bottom:1px solid %(b)s;}",
            "%(sc)s .dyn-bar{display:none;}",
            "%(sc)s .dyn-bar-lines{display:block;height:7px;background-color:%(p)s;margin:4px 0 12px 0;}",
            "%(sc)s table.dyn-lines th{background-color:transparent;color:%(p)s;"
            "text-transform:uppercase;border-bottom:3px solid %(p)s !important;}",
            "%(sc)s table.dyn-lines{border-bottom:3px solid %(p)s;}",
            "%(sc)s table.dyn-lines td{border-bottom:0 !important;}",
            "%(sc)s table.dyn-lines tr.dyn-odd td{background-color:%(a_pale)s;}",
            "%(sc)s table.dyn-totals td{border-bottom:0 !important;}",
            "%(sc)s table.dyn-totals tr.dyn-strong td{background-color:%(a_pale)s;color:%(p)s;"
            "font-size:1.35em;}",
        ],
        'accent': [
            "%(sc)s .dyn-titlebox{background-color:%(a)s;padding:6px 10px;margin-bottom:12px;"
            "text-align:center;}",
            "%(sc)s .dyn-titlebox .dyn-title{color:%(on_a)s;font-size:1.5em;text-transform:uppercase;}",
            "%(sc)s .dyn-titlebox .dyn-docname{color:%(on_a)s;}",
            "%(sc)s .dyn-bar{display:none;}",
            "%(sc)s table.dyn-lines th{background-color:%(a)s;color:%(on_a)s;"
            "border:1px solid %(p)s !important;}",
            "%(sc)s table.dyn-lines td{border:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-totals td{border:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-totals tr.dyn-strong td{background-color:%(a)s;color:%(on_a)s;}",
        ],
        'angled': [
            "%(sc)s .dyn-titlebox{text-align:%(end)s;margin-bottom:8px;}",
            "%(sc)s .dyn-titlebox .dyn-title{color:%(p)s;font-size:2.5em;text-transform:uppercase;"
            "letter-spacing:1px;}",
            "%(sc)s .dyn-bar{display:none;}",
            "%(sc)s table.dyn-lines th{background-color:%(a)s;color:%(on_a)s;}",
            "%(sc)s table.dyn-lines td{border-right:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-totals td{border-bottom:0 !important;}",
            "%(sc)s table.dyn-totals tr.dyn-strong td{background-color:%(a)s;color:%(on_a)s;}",
        ],
        'chevron': [
            "%(sc)s .dyn-titlebox{text-align:%(end)s;margin-bottom:8px;}",
            "%(sc)s .dyn-titlebox .dyn-title{color:%(p)s;font-size:2.5em;text-transform:uppercase;}",
            "%(sc)s .dyn-bar{display:none;}",
            "%(sc)s .dyn-section-head{color:%(a)s;font-size:1.3em;}",
            "%(sc)s table.dyn-lines th{background-color:%(a)s;color:%(on_a)s;}",
            "%(sc)s table.dyn-lines td{border:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-lines tr.dyn-odd td{background-color:transparent;}",
            "%(sc)s table.dyn-totals td{border-bottom:0 !important;}",
            "%(sc)s table.dyn-totals tr.dyn-strong td{background-color:%(a)s;color:%(on_a)s;}",
        ],
        'wave': [
            "%(sc)s .dyn-titlebox{text-align:%(end)s;margin-bottom:8px;}",
            "%(sc)s .dyn-titlebox .dyn-title{color:%(p)s;font-size:2.5em;text-transform:uppercase;}",
            "%(sc)s .dyn-bar{display:none;}",
            "%(sc)s .dyn-section-head{color:%(a)s;}",
            "%(sc)s table.dyn-strip td{background-color:%(a_pale)s;}",
            "%(sc)s table.dyn-strip td.dyn-strip-alt{background-color:%(a_tint)s;}",
            "%(sc)s table.dyn-lines th{background-color:%(a)s;color:%(on_a)s;}",
            "%(sc)s table.dyn-lines td{border-right:1px solid %(b)s !important;}",
            "%(sc)s table.dyn-lines tr.dyn-odd td{background-color:transparent;}",
            "%(sc)s table.dyn-totals td{border-bottom:0 !important;}",
            "%(sc)s table.dyn-totals tr.dyn-strong td{background-color:%(a)s;color:%(on_a)s;}",
        ],
        'geometric': [
            "%(sc)s .dyn-titlebox{text-align:center;margin-bottom:10px;}",
            "%(sc)s .dyn-titlebox .dyn-title{color:%(p)s;font-size:2.4em;font-weight:normal;}",
            "%(sc)s .dyn-bar{display:none;}",
            "%(sc)s table.dyn-lines{border-collapse:separate;border-spacing:0 3px;}",
            "%(sc)s table.dyn-lines th{background-color:%(a)s;color:%(on_a)s;}",
            "%(sc)s table.dyn-lines td{background-color:%(a_pale)s;border:0 !important;}",
            "%(sc)s table.dyn-lines tr.dyn-odd td{background-color:%(a_tint)s;}",
            "%(sc)s table.dyn-totals tr.dyn-strong td{background-color:%(a)s;color:%(on_a)s;}",
        ],
    }
    selected = rules.get(design)
    if not selected:
        return ''
    return ''.join(rule % v for rule in common + selected)
