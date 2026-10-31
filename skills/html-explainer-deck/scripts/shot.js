#!/usr/bin/env node
/* shot.js — screenshot every slide and report layout defects.
 usage: node shot.js deck.html [--out shots] [--wait 3400] [--desktop 1600x900] [--mobile 390x844]
                    [--mobile-pages all|1,3,5] [--only 2,7] [--safe-bottom 60] [--min-font 16]
 Output: shots/d01.png… (desktop), shots/m01.png… (mobile). Prints one line per defect:
   OUT   element sticks out of the slide (or into the footer safe zone)
   CLIP  element content is cut off (scrollWidth/Height > client size with overflow hidden/auto)
   SMALL visible text below --min-font px on desktop (12px on mobile); SVG <text> measured at rendered size
   OVERLAP SVG <text> crossing a filled box edge or another text
   HSCROLL mobile slide scrolls sideways
   JSERR page error / console error
 Exit code 0 only when nothing is printed except the summary.
 Slide discovery: elements matching .slide (override --selector). Navigation: window.__go(i) if present,
 else location.hash = '#'+(i+1), else scrollIntoView. Elements with [data-overflow-ok] (and their children) are skipped. */
const path = require('path'), fs = require('fs');
const { launch, arg } = require('./chrome');
const file = process.argv[2];
if (!file || file.startsWith('--')) { console.error('usage: node shot.js deck.html [--out dir]'); process.exit(2); }
const url = 'file://' + path.resolve(file);
const out = path.resolve(arg('out', path.join(path.dirname(path.resolve(file)), 'shots')));
const wait = +arg('wait', 3400), safe = +arg('safe-bottom', 60), minFont = +arg('min-font', 16);
const [dw, dh] = arg('desktop', '1600x900').split('x').map(Number);
const mob = arg('mobile', '390x844'), mpages = arg('mobile-pages', 'all'), only = arg('only', '');
const sel = arg('selector', '.slide');
fs.mkdirSync(out, { recursive: true });
let problems = 0;
const say = (...a) => { problems++; console.log(...a); };

async function goTo(p, i) {
  return p.evaluate(([i, sel]) => {
    const s = document.querySelectorAll(sel);
    if (typeof window.__go === 'function') { window.__go(i, true); return '__go'; }
    location.hash = '#' + (i + 1);
    window.dispatchEvent(new HashChangeEvent('hashchange'));
    if (!s[i].classList.contains('active') && getComputedStyle(s[i]).visibility !== 'hidden') s[i].scrollIntoView();
    return 'hash';
  }, [i, sel]);
}

function audit(p, i, mobile) {
  return p.evaluate(([i, sel, safe, minFont, mobile]) => {
    const s = document.querySelectorAll(sel)[i], R = s.getBoundingClientRect(), out = [];
    const name = e => (e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).join('.') : '')) + ' "' + (e.textContent || '').trim().slice(0, 18) + '"';
    const foot = s.querySelector('.foot');
    s.querySelectorAll('*').forEach(e => {
      if (e.closest('[data-overflow-ok],[aria-hidden="true"],.foot') || (e.closest('svg') && e.tagName !== 'svg')) return;
      const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return;
      const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
      if (!mobile) {
        const bottom = R.bottom - safe;
        if (r.right > R.right + 1 || r.left < R.left - 1 || r.top < R.top - 1 || r.bottom > bottom + 1)
          out.push('OUT ' + name(e) + ' [' + [r.left - R.left, r.top - R.top, r.right - R.left, r.bottom - R.top].map(Math.round) + ']');
      } else if (r.right > R.right + 1 || r.left < R.left - 1) {
        if (!e.closest('.tblw,.wide')) out.push('OUT ' + name(e) + ' x[' + Math.round(r.left - R.left) + ',' + Math.round(r.right - R.left) + ']');
      }
      const ov = cs.overflow + cs.overflowX + cs.overflowY;
      if (/hidden|auto|scroll|clip/.test(ov) && e !== s && !e.matches('.tblw,.track,.wide')) {
        // real clipping = a text-bearing descendant pokes outside this box (pseudo-element decoration ignored)
        const bad = [...e.querySelectorAll('*')].find(c => { if (![...c.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return false;
          const q = c.getBoundingClientRect(); return q.width && (q.right > r.right + 2 || q.bottom > r.bottom + 2 || q.left < r.left - 2 || q.top < r.top - 2); });
        if (bad) out.push('CLIP ' + name(e) + ' cuts ' + name(bad));
      }
      const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (own) { // the glyphs themselves may run past the box even when the element's box fits (e.g. a 112px number in a narrow card)
        const rg = document.createRange(); rg.selectNodeContents(e); const t = rg.getBoundingClientRect();
        let a = e.parentElement; while (a && a !== s && !/hidden|clip|auto|scroll/.test(getComputedStyle(a).overflowX + getComputedStyle(a).overflowY)) a = a.parentElement;
        if (a && a !== s && !a.closest('.tblw,.track,.wide') && t.width) { const q = a.getBoundingClientRect();
          if (t.right > q.right + 2 || t.left < q.left - 2) out.push('CLIP text cut: ' + name(e) + ' runs ' + Math.round(Math.max(t.right - q.right, q.left - t.left)) + 'px past ' + name(a)); }
      }
      const lim = mobile ? 12 : minFont;
      if (own && parseFloat(cs.fontSize) < lim - .1 && !e.closest('.chip,.tag,sup,sub'))
        out.push('SMALL ' + name(e) + ' ' + cs.fontSize);
    });
    // SVG diagrams: effective text size and text colliding with boxes / other text
    const lim = mobile ? 12 : minFont;
    s.querySelectorAll('svg').forEach(svg => {
      if (svg.closest('[data-overflow-ok],[aria-hidden="true"]')) return;
      const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim());
      const shapes = [...svg.querySelectorAll('rect,circle,ellipse,polygon')].filter(x => (x.getAttribute('fill') || getComputedStyle(x).fill) !== 'none');
      const bx = el => el.getBoundingClientRect();
      const inter = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 2 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 2;
      const inside = (a, b) => a.left >= b.left - 2 && a.right <= b.right + 2 && a.top >= b.top - 2 && a.bottom <= b.bottom + 2;
      texts.forEach((t, k) => {
        const r0 = bx(t); if (!r0.height) return;
        const r = { left: r0.left - 6, right: r0.right + 6, top: r0.top, bottom: r0.bottom, height: r0.height }; // 6px breathing room
        let bb; try { bb = t.getBBox(); } catch { return; }
        const eff = parseFloat(getComputedStyle(t).fontSize) * (bb.height ? r0.height / bb.height : 1);
        if (eff < lim - .1) out.push('SMALL svg text "' + t.textContent.trim().slice(0, 16) + '" ~' + eff.toFixed(1) + 'px (wrap the svg in .wide or give a .only-m version)');
        shapes.forEach(sh => { const q = bx(sh); if (inter(r, q) && !inside(r0, q) && !inside(q, r0)) out.push('OVERLAP svg text "' + t.textContent.trim().slice(0, 16) + '" crosses/touches a ' + sh.tagName + ' edge'); });
        texts.slice(k + 1).forEach(u => { if (inter(r0, bx(u))) out.push('OVERLAP svg texts "' + t.textContent.trim().slice(0, 12) + '" / "' + u.textContent.trim().slice(0, 12) + '"'); });
      });
    });
    const se = document.scrollingElement; if (mobile && se.scrollWidth > innerWidth + 1) out.push('HSCROLL page ' + se.scrollWidth + '>' + innerWidth);
    // keep only outermost offenders: drop children of already-reported elements
    return [...new Set(out)].slice(0, 15);
  }, [i, sel, safe, minFont, mobile]);
}

(async () => {
  const b = await launch();
  const run = async (vp, prefix, mobile, pick) => {
    const p = await b.newPage(mobile ? { viewport: vp, deviceScaleFactor: 2, hasTouch: true, isMobile: true } : { viewport: vp });
    p.on('pageerror', e => say('JSERR', prefix, e.message));
    p.on('console', m => { if (m.type() === 'error') say('JSERR', prefix, m.text()); });
    await p.goto(url); await p.waitForTimeout(500);
    const N = await p.$$eval(sel, s => s.length);
    if (!N) { say('NOSLIDES no element matches', sel); return 0; }
    let how;
    for (let i = 0; i < N; i++) {
      if (!pick(i + 1, N)) continue;
      how = await goTo(p, i); await p.waitForTimeout(wait);
      const f = path.join(out, `${prefix}${String(i + 1).padStart(2, '0')}.png`);
      await p.screenshot({ path: f });
      const iss = await audit(p, i, mobile);
      iss.forEach(x => say(`${prefix}${String(i + 1).padStart(2, '0')}`, x));
    }
    if (how === 'hash') console.log(`[info] ${prefix}: no window.__go, navigated by #hash`);
    await p.close(); return N;
  };
  const onlySet = only ? new Set(only.split(',').map(Number)) : null;
  const N = await run({ width: dw, height: dh }, 'd', false, n => !onlySet || onlySet.has(n));
  if (mob !== 'off') {
    const [mw, mh] = mob.split('x').map(Number);
    const mset = mpages === 'all' ? null : new Set(mpages.split(',').map(Number));
    await run({ width: mw, height: mh }, 'm', true, n => (!onlySet || onlySet.has(n)) && (!mset || mset.has(n)));
  }
  await b.close();
  console.log(`== ${N} slides → ${out} · ${problems} issue line(s)` + (problems ? '' : ' · CLEAN'));
  process.exit(problems ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
