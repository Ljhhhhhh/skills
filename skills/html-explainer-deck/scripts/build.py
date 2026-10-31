#!/usr/bin/env python3
"""build.py — render a deck.md (structured copy) into one self-contained HTML deck.

usage: python3 build.py deck.md [-o out.html] [--template path/to/deck.html] [--strict]

deck.md grammar (see SKILL.md §2 for the full spec):
  ---                      optional front matter: title / brand / lang
  ## <type>                starts a slide. types: cover statement agenda section point
                           full loop end html  (+ aliases: compare table flow steps
                           stats cards vs lanes bars list chips quote)
  key: value               a field (ASCII key). Following non-key lines are appended.
  - a | b | c              a row for the slide's visual (cells split by " | ")
  ```html ... ```          raw HTML for the slide / visual (escape hatch)
inline: **bold**  *accent*  ==highlight==  <br> (line break). Everything else is escaped.
"""
import argparse, html, math, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TPL = os.path.join(HERE, '..', 'template', 'deck.html')
ACCENTS = ['var(--coral)', 'var(--violet)', 'var(--teal)', 'var(--amber)']
HEX = ['#FF5B3A', '#6C5CE7', '#0FA394', '#E39400']
ALIASES = {'compare': 'table', 'table': 'table', 'flow': 'steps', 'steps': 'steps', 'stats': 'stats',
           'cards': 'cards', 'vs': 'vs', 'lanes': 'lanes', 'bars': 'bars', 'list': 'list',
           'chips': 'chips', 'quote': 'quote'}
TYPES = {'cover', 'statement', 'agenda', 'section', 'point', 'full', 'loop', 'end', 'html'} | set(ALIASES)
WARN = []


def warn(slide, msg):
    WARN.append(f"slide {slide['_idx']} ({slide['type']}): {msg}")


def width(s):
    """visual width: CJK/fullwidth = 1, others = 0.55; tags/markup ignored."""
    s = re.sub(r'<[^>]+>|\*\*|==|\*', '', s or '')
    return sum(1 if unicodedata.east_asian_width(c) in 'WF' else 0.55 for c in s)


def fmt(s):
    s = html.escape(s or '', quote=False)
    s = re.sub(r'&lt;br\s*/?&gt;', '<br>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'==(.+?)==', r'<span class="mark">\1</span>', s)
    s = re.sub(r'(?<![A-Za-z0-9*])\*(?!\s)(.+?)(?<!\s)\*(?![A-Za-z0-9*])', r'<em>\1</em>', s)
    return s


def plain(s):
    return re.sub(r'<[^>]+>', ' ', fmt(s)).replace('  ', ' ').strip()


def bold_last(s):
    """emphasise the conclusion: wrap the last sentence in <strong> unless the writer already used **."""
    if '**' in s:
        return fmt(s)
    parts = [p for p in re.split(r'(?<=[。！？!?])|(?<=\.)\s+', s) if p and p.strip()]
    if len(parts) >= 2:
        return fmt(''.join(parts[:-1]) if re.search(r'[\u4e00-\u9fff]', s) else ' '.join(parts[:-1]) + ' ') + '<strong>' + fmt(parts[-1]) + '</strong>'
    return fmt(s)


# ---------------------------------------------------------------- parse
def parse(text):
    meta, slides = {}, []
    lines = text.replace('\r\n', '\n').split('\n')
    i = 0
    if lines and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            m = re.match(r'^([A-Za-z_]+):\s*(.*)$', lines[i])
            if m:
                meta[m.group(1).lower()] = m.group(2).strip()
            i += 1
        i += 1
    cur, last = None, None
    while i < len(lines):
        ln = lines[i]
        h = re.match(r'^##\s+([A-Za-z]+)\s*(.*)$', ln)
        if h:
            t = h.group(1).lower()
            if t not in TYPES:
                sys.exit(f'line {i+1}: unknown slide type "{t}". Allowed: {", ".join(sorted(TYPES))}')
            cur = {'type': t, 'rows': [], '_idx': len(slides) + 1, '_line': i + 1}
            if h.group(2).strip():
                cur['title'] = h.group(2).strip()
            slides.append(cur); last = None; i += 1; continue
        if cur is None:
            i += 1; continue
        if ln.strip().startswith('```'):
            buf = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                buf.append(lines[i]); i += 1
            cur['html'] = '\n'.join(buf); i += 1; last = None; continue
        m = re.match(r'^([A-Za-z_]+):\s*(.*)$', ln)
        r = re.match(r'^\s*[-*]\s+(.*)$', ln)
        if m:
            last = m.group(1).lower(); cur[last] = m.group(2).strip()
        elif r:
            cur['rows'].append([c.strip() for c in re.split(r'\s+\|\s+|\s+\|$|^\|\s+', r.group(1))]); last = None
        elif ln.strip() and last:
            sep = '' if re.search(r'[\u4e00-\u9fff]$', cur[last]) else ' '
            cur[last] = (cur[last] + sep + ln.strip()).strip()
        i += 1
    return meta, slides


# ---------------------------------------------------------------- visuals
def A(kind=''):
    return f' data-a="{kind}"' if kind else ' data-a'


def cells(row, n):
    return (row + [''] * n)[:n]


def v_bars(s, ctx):
    rows = s['rows']
    out = [f'<div class="panel"{A("s")}>']
    if s.get('vtitle'):
        out.append(f'<h4>{fmt(s["vtitle"])}</h4>')
    out.append('<div class="bars">')
    for k, r in enumerate(rows):
        label, w, shown = cells(r, 3)
        weak = label.startswith('~')
        label = label.lstrip('~').strip()
        w = w if w.endswith('%') else (w + '%' if w else '50%')
        out.append(f'<div class="bar"><span>{fmt(label)}</span><div class="track"><div class="fill{" weak" if weak else ""}" style="--w1:{w};--k:{k}"></div></div><span class="v">{fmt(shown)}</span></div>')
    out.append('</div></div>')
    return ''.join(out)


def v_vs(s, ctx):
    L = [r[0] for r in s['rows'] if r and r[0]]
    R = [r[1] for r in s['rows'] if len(r) > 1 and r[1]]
    def side(cls, title, items, note, a):
        h = f'<div class="sp {cls}"{A(a)}><h5>{fmt(title)}</h5><div class="layers">' + ''.join(f'<div>{fmt(x)}</div>' for x in items) + '</div>'
        if note:
            h += f'<p class="verdict">{fmt(note)}</p>'
        return h + '</div>'
    return '<div class="vs">' + side('bad', s.get('left', ''), L, s.get('leftnote'), 'l') + side('good', s.get('right', ''), R, s.get('rightnote'), 'r') + '</div>'


def v_lanes(s, ctx):
    rows = s['rows']; out = ['<div class="lanes">']
    for k, r in enumerate(rows):
        muted = len(rows) > 1 and k < len(rows) - 1
        steps = '<span class="ar">→</span>'.join(f'<span class="c">{fmt(x)}</span>' for x in r[1:] if x)
        out.append(f'<div class="lane{" muted" if muted else ""}"{A("r")}><h5>{fmt(r[0])}</h5><div class="chain">{steps}</div></div>')
    return ''.join(out) + '</div>'


def v_steps(s, ctx):
    rows = s['rows']; vert = ctx == 'point' or s.get('dir') == 'v'
    out = [f'<div class="steps{" v" if vert else ""}" style="--n:{len(rows)}">']
    for k, r in enumerate(rows):
        t, d = cells(r, 2)
        out.append(f'<div class="stp"{A("r" if vert else "")}><b>{k+1}</b><div class="bx"><h5>{fmt(t)}</h5>' + (f'<p>{fmt(d)}</p>' if d else '') + '</div></div>')
    return ''.join(out) + '</div>'


def v_cards(s, ctx):
    rows = s['rows']; multi = s.get('colors', 'multi') != 'single'
    out = [f'<div class="cards" style="--n:{len(rows)}">']
    for k, r in enumerate(rows):
        tag, t, items, note = cells(r, 4)
        c = f' style="--c:{ACCENTS[k % 4]}"' if multi else ''
        v = ''.join(f'<span>{fmt(x.strip())}</span>' for x in items.split(' / ') if x.strip())
        out.append(f'<div class="cd"{c}{A("s")}>' + (f'<div class="ic">{fmt(tag)}</div>' if tag else '') + f'<h5>{fmt(t)}</h5>' + (f'<div class="v">{v}</div>' if v else '') + (f'<p class="ex">{fmt(note)}</p>' if note else '') + '</div>')
    return ''.join(out) + '</div>'


def v_stats(s, ctx):
    rows = s['rows']; multi = s.get('colors', 'single') == 'multi'
    out = [f'<div class="stats" style="--n:{len(rows)}">']
    for k, r in enumerate(rows):
        num, label, note = cells(r, 3)
        m = re.match(r'^([~≈<>+\-]?[\d.,]+)\s*(.*)$', num)
        nb = f'{html.escape(m.group(1))}<small>{fmt(m.group(2))}</small>' if m and m.group(2) else fmt(num)
        c = f'--c:{ACCENTS[k % 4]};' if multi else ''
        out.append(f'<div class="st" style="{c}--k:{k}"{A("s")}><b>{nb}</b><h5>{fmt(label)}</h5>' + (f'<p>{fmt(note)}</p>' if note else '') + '</div>')
    return ''.join(out) + '</div>'


def v_table(s, ctx):
    cols = [c.strip() for c in s.get('cols', '').split(' | ')] if s.get('cols') else None
    win = s.get('win', '').strip()
    wi = None
    if cols and win:
        wi = int(win) if win.isdigit() else (cols.index(win) if win in cols else None)
    def cell(tag, x, j):
        cls = []
        if wi is not None and j == wi:
            cls.append('w')
        if tag == 'td' and re.match(r'^[✓✔]', x):
            cls.append('y')
        if tag == 'td' and re.match(r'^[✗✘×—-]$|^[✗✘×]', x):
            cls.append('x')
        c = f' class="{" ".join(cls)}"' if cls else ''
        return f'<{tag}{c}>{fmt(x)}</{tag}>'
    if wi is not None and s.get('_idx'):
        wc = [r[wi].strip() for r in s['rows'] if len(r) > wi]
        nx = sum(1 for x in wc if re.match(r'^[✗✘×]', x)); ny = sum(1 for x in wc if re.match(r'^[✓✔]', x))
        if nx and nx >= ny:
            warn(s, f"win column '{cols[wi]}' has {nx} ✗ vs {ny} ✓ — highlighted winner reads as losing. ✓/✗ mean 'this option is good at this row'; flip the marks or drop win:")
    roomy = len(s['rows']) <= 4 and len(cols or s['rows'][0]) <= 4
    out = [f'<div class="tblw"{A("s")}><table class="tbl{" roomy" if roomy else ""}">']
    if cols:
        out.append('<thead><tr>' + ''.join(cell('th', x, j) for j, x in enumerate(cols)) + '</tr></thead>')
    out.append('<tbody>')
    for r in s['rows']:
        out.append('<tr>' + ''.join(cell('td', x, j) for j, x in enumerate(r)) + '</tr>')
    return ''.join(out) + '</tbody></table></div>'


def v_list(s, ctx):
    out = [f'<div class="lst"{A("r")}>']
    if s.get('vtitle'):
        out.append(f'<h4>{fmt(s["vtitle"])}</h4>')
    for k, r in enumerate(s['rows']):
        t, d = cells(r, 2)
        out.append(f'<div class="row"><b>{k+1}</b><div><h5>{fmt(t)}</h5>' + (f'<p>{fmt(d)}</p>' if d else '') + '</div></div>')
    return ''.join(out) + '</div>'


def v_chips(s, ctx):
    return f'<div class="chips"{A()}>' + ''.join(f'<span class="chip"><i></i>{fmt(r[0])}</span>' for r in s['rows']) + '</div>'


def v_quote(s, ctx):
    return f'<blockquote class="qt"{A()}>{fmt(s.get("quote", ""))}' + (f'<cite>— {fmt(s["cite"])}</cite>' if s.get('cite') else '') + '</blockquote>'


def v_html(s, ctx):
    return s.get('html', '')


VIS = {'bars': v_bars, 'vs': v_vs, 'lanes': v_lanes, 'chain': v_lanes, 'steps': v_steps, 'flow': v_steps,
       'cards': v_cards, 'stats': v_stats, 'table': v_table, 'compare': v_table, 'list': v_list,
       'chips': v_chips, 'quote': v_quote, 'html': v_html}

LIMITS = {  # visual: (max rows in a full-width slide, max rows next to text on a point slide)
    'bars': (5, 4), 'vs': (5, 4), 'lanes': (3, 2), 'chain': (3, 2), 'steps': (6, 5), 'flow': (6, 5),
    'cards': (4, 3), 'stats': (4, 3), 'table': (7, 5), 'compare': (7, 5), 'list': (6, 5), 'chips': (10, 8)}


def visual(s, ctx):
    v = s.get('visual')
    if not v:
        return ''
    if v not in VIS:
        sys.exit(f'slide {s["_idx"]}: unknown visual "{v}". Allowed: {", ".join(sorted(VIS))}')
    if v in LIMITS:
        lim = LIMITS[v][1 if ctx == 'point' else 0]
        if len(s['rows']) > lim:
            warn(s, f'visual "{v}" has {len(s["rows"])} rows; max {lim} in a {ctx} slide — split the slide or cut rows')
        if not s['rows'] and v not in ('quote', 'html'):
            warn(s, f'visual "{v}" has no "- a | b" rows')
    if v in ('table', 'compare'):
        cols = len(s.get('cols', '').split(' | ')) if s.get('cols') else max((len(r) for r in s['rows']), default=0)
        if cols > (5 if ctx != 'point' else 3):
            warn(s, f'table has {cols} columns; keep ≤ {5 if ctx != "point" else 3}')
    for r in s['rows']:
        for c in r:
            lim = 26 if ctx == 'point' else 34
            if v in ('table', 'compare'):
                lim = 30
            if width(c) > lim and v not in ('cards',):
                warn(s, f'cell too long ({width(c):.0f} > {lim}): "{c[:24]}…"')
    out = VIS[v](s, ctx)
    if s.get('note'):
        out += f'<div class="talk"{A("r")}>{fmt(s["note"])}</div>'
    return out


# ---------------------------------------------------------------- layouts
def kicker(s, default=''):
    k = s.get('kicker', default)
    return f'<div class="kicker"{A()}>{fmt(k)}</div>' if k else ''


def L_cover(s, d):
    orb = s.get('orb', '0') or '0'
    rows_n = d['npoints'] if orb == 'auto' else int(orb)
    if orb != 'auto' and rows_n and rows_n != d['npoints'] and d['npoints']:
        warn(s, f'orb: {rows_n} but deck has {d["npoints"]} point slides — use "orb: auto" or fix the count')
    has_orb = rows_n > 0 or bool(s.get('core'))
    t = s.get('title', '')
    for line in t.split('<br>'):
        if width(line) > (7.5 if has_orb else 10.5):
            warn(s, f'cover title line "{line}" too wide for 118px type; break it with <br> or shorten')
    if t.count('<br>') > 2:
        warn(s, 'cover title > 3 lines')
    if width(s.get('thesis', '')) > 90:
        warn(s, 'thesis > 90 chars')
    sub = fmt(s.get('sub', '')).replace(' · ', ' <span>·</span> ')
    h = [f'<section class="slide cover g1{"" if has_orb else " solo"}" data-title="{html.escape(plain(t))}">',
         '<div class="l">', kicker(s), f'<h1{A()}>{fmt(t)}</h1>']
    if sub:
        h.append(f'<div class="sub"{A()}>{sub}</div>')
    if s.get('thesis'):
        h.append(f'<p class="thesis"{A()}>{fmt(s["thesis"])}</p>')
    h.append('</div>')
    if has_orb:
        groups = d.get('groups') or []
        if rows_n and sum(groups) != rows_n:
            q = math.ceil(rows_n / 4); groups = [min(q, rows_n - q * k) for k in range(4) if rows_n - q * k > 0]
        col = []
        for gi, gsz in enumerate(groups):
            col += [HEX[gi % 4]] * gsz
        dots = ''
        for k in range(rows_n):
            a = k / rows_n * math.pi * 2
            dots += f'<div class="dot" style="left:{50+50*math.sin(a):.2f}%;top:{50-50*math.cos(a):.2f}%;background:{col[k] if k < len(col) else HEX[0]}"><span>{k+1}</span></div>'
        small, big = (cells([c.strip() for c in s.get('core', '').split(' | ')], 2))
        if not big:
            small, big = '', small
        big = fmt(big).replace(' / ', '<br>')
        h.append(f'<div class="orb" data-a="s" aria-hidden="true"><div class="ring"></div><div class="ring2"></div><div class="spin">{dots}</div>'
                 f'<div class="core">' + (f'<small>{fmt(small)}</small>' if small else '') + f'<b>{big}</b></div></div>')
    return ''.join(h) + '</section>'


def L_statement(s, d):
    if width(s.get('title', '')) > 44:
        warn(s, 'statement title > 44 chars (2 lines at 62px)')
    h = [f'<section class="slide statement {d["g"]}" data-title="{html.escape(plain(s.get("short", s.get("title", ""))))}">', kicker(s),
         f'<h2{A()}>{fmt(s.get("title", ""))}</h2>']
    if s.get('lead'):
        h.append(f'<p class="lead"{A()}>{fmt(s["lead"])}</p>')
    vis = visual(s, 'full')
    if vis:
        h.append(f'<div class="body">{vis}</div>')
    return ''.join(h) + '</section>'


def L_agenda(s, d):
    rows = s['rows'] or d['auto_agenda']
    groups, order = {}, []
    for r in rows:
        g, it = (r[0], r[1]) if len(r) > 1 else ('', r[0])
        if g not in groups:
            groups[g] = []; order.append(g)
        groups[g].append(it)
    if len(order) > 4:
        warn(s, f'{len(order)} groups; agenda fits 4 columns')
    n_items = sum(len(v) for v in groups.values())
    if n_items > 16:
        warn(s, f'{n_items} agenda items; >16 will overflow — group or trim')
    def item(it, num):
        tgt = d['titles'].get(plain(it))
        if not tgt:
            warn(s, f'agenda item has no matching page title: {plain(it)}')
        go = f' data-go="{tgt}" role="button" tabindex="0"' if tgt else ''
        return f'<div class="item"{go}{A()}><i>{num}</i><p>{fmt(it)}</p></div>'
    h = [f'<section class="slide agenda full {d["g"]}" data-title="{html.escape(plain(s.get("title", "")))}"><div class="hd">', kicker(s),
         f'<h2{A()}>{fmt(s.get("title", ""))}</h2></div><div class="body">']
    num = 0
    if order == ['']:
        cols = 2 if n_items > 4 else 1
        h.append(f'<div class="ovg flat" style="--cols:{cols}">')
        for it in groups['']:
            num += 1; h.append(item(it, num))
        h.append('</div>')
    else:
        h.append(f'<div class="ovg" style="--cols:{len(order)}">')
        for gi, g in enumerate(order):
            h.append(f'<div class="col g{gi % 4 + 1}"><div class="gh"{A()}><b>{gi+1:02d}</b><span>{fmt(g)}</span></div>')
            for it in groups[g]:
                num += 1; h.append(item(it, num))
            h.append('</div>')
        h.append('</div>')
    return ''.join(h) + '</div></section>'


def L_section(s, d):
    rows = s['rows'] or [[str(n), t] for n, t in d['sec_points'].get(s['_idx'], [])]
    if width(s.get('title', '')) > 8:
        warn(s, 'section title > 8 chars at 110px')
    h = [f'<section class="slide sec {d["g"]}" data-title="{html.escape(plain(s.get("title", "")))}">',
         f'<div class="big"{A("s")}>{d["secno"]:02d}</div><div><h2{A()}>{fmt(s.get("title", ""))}</h2>']
    if s.get('sub'):
        h.append(f'<p{A()}>{fmt(s["sub"])}</p>')
    if rows:
        h.append('<ul>' + ''.join(f'<li{A()}><b>{fmt(r[0])}</b>{fmt(r[1])}</li>' if len(r) > 1 else f'<li{A()}>{fmt(r[0])}</li>' for r in rows) + '</ul>')
    return ''.join(h) + '</div></section>'


def L_point(s, d):
    t = s.get('title', '')
    has_vis = bool(s.get('visual'))
    if width(t) > 21:
        warn(s, f'point title {width(t):.0f} wide > 21 (one line at 54px)')
    lim_p, lim_c = (80, 75) if has_vis else (170, 150)
    if width(s.get('problem', '')) > lim_p:
        warn(s, f'problem {width(s.get("problem", "")):.0f} > {lim_p} chars')
    if width(s.get('action', '')) > lim_c:
        warn(s, f'action {width(s.get("action", "")):.0f} > {lim_c} chars')
    num = s.get('num', f'{d["pointno"]:02d}')
    h = [f'<section class="slide point {d["g"]}" data-title="{html.escape(plain(t))}">',
         f'<div class="mh"><div class="n"{A("l")}>{fmt(num)}</div><div class="t">{kicker(s, d["sec_title"])}<h2{A()}>{fmt(t)}</h2></div></div>',
         f'<div class="mw{"" if has_vis else " solo"}"><div>']
    if s.get('problem'):
        h.append(f'<p class="prob"{A()}>{bold_last(s["problem"])}</p>')
    if s.get('action'):
        h.append(f'<div class="card"{A()}><span class="lab">{fmt(s.get("label", d["label"]))}</span><p>{fmt(s["action"])}</p></div>')
    h.append('</div>')
    if has_vis:
        h.append(f'<div class="dg">{visual(s, "point")}</div>')
    return ''.join(h) + '</div></section>'


def L_full(s, d, vis_name=None):
    if vis_name:
        s.setdefault('visual', vis_name)
    if width(s.get('title', '')) > 24:
        warn(s, 'title > 24 chars (one line at 54px)')
    if width(s.get('lead', '')) > 90:
        warn(s, 'lead > 90 chars (2 lines)')
    h = [f'<section class="slide full {d["g"]}" data-title="{html.escape(plain(s.get("title", s.get("cite", ""))))}">']
    if s.get('title') or s.get('kicker'):
        h.append('<div class="hd">' + kicker(s, d['sec_title']) + (f'<h2{A()}>{fmt(s["title"])}</h2>' if s.get('title') else '') +
                 (f'<p class="lead"{A()}>{fmt(s["lead"])}</p>' if s.get('lead') else '') + '</div>')
    h.append(f'<div class="body">{visual(s, "full")}</div>')
    return ''.join(h) + '</section>'


def L_loop(s, d):
    rows = s['rows']; n = len(rows)
    if not 3 <= n <= 8:
        warn(s, f'loop needs 3–8 steps, got {n}')
    nodes, chev = '', ''
    for i, r in enumerate(rows):
        a = i / max(n, 1) * math.pi * 2
        nodes += (f'<div class="wn" style="left:{50+34.3*math.sin(a):.2f}%;top:{50-34.3*math.cos(a):.2f}%;transition-delay:{0.6+i*0.3:.1f}s">'
                  f'<b style="background:{HEX[min(3, i * 4 // max(n,1))]}">{i+1}</b><span>{fmt(r[0])}</span></div>')
        chev += f'<path transform="rotate({(i+0.5)*360/max(n,1):.1f} 350 350)" d="M341 100 L355 110 L341 120" fill="none" stroke="#17183B" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity=".55"/>'
    small, big = cells([c.strip() for c in s.get('core', '').split(' | ')], 2)
    if not big:
        small, big = '', small
    tags = ''.join(f'<span>{fmt(x.strip())}</span>' for x in s.get('tags', '').split(' / ') if x.strip())
    return (f'<section class="slide {d["g"]}" data-title="{html.escape(plain(s.get("title", "")))}"><div class="loop"><div>' + kicker(s) +
            f'<h2{A()}>{fmt(s.get("title", ""))}</h2>' + (f'<p class="lead"{A()}>{fmt(s["lead"])}</p>' if s.get('lead') else '') +
            (f'<div class="tags"{A()}>{tags}</div>' if tags else '') +
            '</div><div class="wheel" aria-hidden="true"><svg viewBox="0 0 700 700"><circle cx="350" cy="350" r="240" fill="none" stroke="#EFEAE1" stroke-width="22"/>'
            '<circle class="ringp" cx="350" cy="350" r="240" fill="none" stroke="url(#wg)" stroke-width="6" stroke-linecap="round" transform="rotate(-90 350 350)"/>'
            f'<defs><linearGradient id="wg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF5B3A"/><stop offset=".5" stop-color="#0FA394"/><stop offset="1" stop-color="#6C5CE7"/></linearGradient></defs><g>{chev}</g>'
            '<g class="orbit"><circle cx="350" cy="110" r="10" fill="#FFC23C" stroke="#fff" stroke-width="4"/></g></svg>'
            f'{nodes}<div class="wc">' + (f'<small>{fmt(small)}</small>' if small else '') + f'<p>{fmt(big).replace(" / ", "<br>")}</p></div></div></div></section>')


def L_end(s, d):
    rows = [r[0] for r in s['rows']]
    arrow = s.get('rail', 'arrow') != 'chips'
    rail = ('<i>→</i>' if arrow else '').join(f'<span>{fmt(x)}</span>' for x in rows)
    return (f'<section class="slide end" data-title="{html.escape(plain(s.get("short", s.get("kicker", "")) or "End"))}"><div class="in">' + kicker(s) +
            f'<h2{A()}>{fmt(s.get("title", ""))}</h2>' + (f'<div class="rail"{A()}>{rail}</div>' if rows else '') +
            (f'<p class="ty"{A()}>{fmt(s["ty"])}</p>' if s.get('ty') else '') + '</div></section>')


def L_html(s, d):
    return (f'<section class="slide full {d["g"]}" data-title="{html.escape(plain(s.get("title", "")))}">' +
            ('<div class="hd">' + kicker(s, d['sec_title']) + f'<h2{A()}>{fmt(s["title"])}</h2></div>' if s.get('title') else '') +
            f'<div class="body">{s.get("html", "")}</div></section>')


# ---------------------------------------------------------------- main
def build(md_text, tpl_text, extra_css=''):
    meta, slides = parse(md_text)
    if not slides:
        sys.exit('no slides found (each slide starts with "## <type>")')
    # pre-pass: numbering, groups, titles → slide index
    titles, sec_points, auto_agenda, groups = {}, {}, [], []
    pno, cur_sec, cur_sec_title = 0, None, ''
    for k, s in enumerate(slides):
        title = plain(s.get('title', ''))
        if title and s['type'] != 'agenda':
            if title in titles:
                warn(s, f'duplicate page title makes agenda targets ambiguous: {title}')
            titles[title] = k + 1
        if s['type'] == 'section':
            cur_sec, cur_sec_title = s['_idx'], s.get('title', ''); sec_points[cur_sec] = []; groups.append(0)
        if s['type'] == 'point':
            pno += 1
            titles[plain(s.get('title', ''))] = k + 1
            if cur_sec:
                sec_points[cur_sec].append((pno, s.get('title', ''))); groups[-1] += 1
            auto_agenda.append([plain(cur_sec_title), s.get('title', '')] if cur_sec else [s.get('title', '')])
    if len(groups) > 1 and not any(s['type'] == 'agenda' for s in slides):
        warn(slides[0], 'multi-section deck needs an agenda before the first section')
    for s in slides:
        if s['type'] == 'agenda' and any(x['type'] == 'section' for x in slides[:s['_idx']-1]):
            warn(s, 'place the topic agenda before the first section')
    # count claims like "9 条" / "12 points" must match the real number of point slides
    for s in slides:
        if s['type'] in ('cover', 'agenda', 'statement', 'loop', 'end') and pno:
            for f in ('title', 'sub', 'thesis', 'lead'):
                for m in re.finditer(r'(\d+)\s*(条|个要点|个原则|条原则|points?\b|principles?\b|tips?\b|rules?\b)', s.get(f, ''), re.I):
                    if int(m.group(1)) != pno:
                        warn(s, f'{f} says "{m.group(0)}" but there are {pno} point slides')
    d = {'npoints': pno, 'titles': titles, 'sec_points': sec_points, 'auto_agenda': auto_agenda, 'groups': [g for g in groups if g],
         'label': meta.get('label', '做法' if meta.get('lang', 'zh-CN').startswith('zh') else 'Do this'),
         'g': 'g1', 'secno': 0, 'pointno': 0, 'sec_title': ''}
    out = []
    for s in slides:
        t = s['type']
        if t == 'section':
            d['secno'] += 1; d['g'] = f'g{(d["secno"]-1) % 4 + 1}'; d['sec_title'] = plain(s.get('title', ''))
        if t == 'point':
            d['pointno'] += 1
        g_saved = d['g']
        if s.get('accent', '').isdigit():
            d['g'] = f'g{(int(s["accent"])-1) % 4 + 1}'
        if t in ALIASES:
            html_s = L_full(s, d, ALIASES[t])
        else:
            html_s = {'cover': L_cover, 'statement': L_statement, 'agenda': L_agenda, 'section': L_section, 'point': L_point,
                      'full': L_full, 'loop': L_loop, 'end': L_end, 'html': L_html}[t](s, d)
        if t != 'section':
            d['g'] = g_saved
        out.append(f'<!-- {s["_idx"]} {t} -->\n{html_s}\n')
    title = meta.get('title') or plain(slides[0].get('title', 'Deck'))
    page = (tpl_text.replace('{{TITLE}}', html.escape(title)).replace('{{LANG}}', html.escape(meta.get('lang', 'zh-CN')))
            .replace('{{BRAND}}', html.escape(meta.get('brand', title))).replace('{{SLIDES}}', '\n'.join(out))
            .replace('{{EXTRA_CSS}}', extra_css))
    left = re.findall(r'\{\{[A-Z_]+\}\}', page)
    if left:
        sys.exit(f'unfilled template placeholders: {left}')
    return page, len(slides)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('md'); ap.add_argument('-o', '--out')
    ap.add_argument('--template', default=DEFAULT_TPL)
    ap.add_argument('--css', help='extra CSS file appended to the design system (deck-specific overrides)')
    ap.add_argument('--strict', action='store_true', help='exit 1 if any content-budget warning')
    a = ap.parse_args()
    md = open(a.md, encoding='utf-8').read()
    tpl = open(a.template, encoding='utf-8').read()
    css = open(a.css, encoding='utf-8').read() if a.css else ''
    page, n = build(md, tpl, css)
    out = a.out or os.path.splitext(a.md)[0] + '.html'
    open(out, 'w', encoding='utf-8').write(page)
    for w in WARN:
        print('WARN', w)
    print(f'built {out}: {n} slides, {len(page)//1024} KB, {len(WARN)} warnings')
    sys.exit(1 if a.strict and WARN else 0)


if __name__ == '__main__':
    main()
