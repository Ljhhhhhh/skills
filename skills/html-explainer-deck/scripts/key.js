#!/usr/bin/env node
/* key.js — interaction test for a slide deck. usage: node key.js deck.html [--selector .slide]
 Checks: deep link #3 opens slide 3; Space/→/PageDown advance; ← goes back; End/Home; click right 70% advances,
 click left 30% goes back; mobile swipe left advances; exactly one active slide at every step; no JS errors.
 Prints PASS/FAIL per check; exit 1 on any FAIL. Assumes the deck marks the current slide with .active and
 keeps location.hash = #<1-based index> (the template does both). */
const path = require('path');
const { launch, arg } = require('./chrome');
const file = process.argv[2]; if (!file) { console.error('usage: node key.js deck.html'); process.exit(2); }
const url = 'file://' + path.resolve(file), sel = arg('selector', '.slide');
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
(async () => {
  const b = await launch();
  const p = await b.newPage({ viewport: { width: 1600, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  const st = () => p.evaluate(s => { const a = [...document.querySelectorAll(s)]; return { n: a.length, act: a.filter(x => x.classList.contains('active')).length, idx: a.findIndex(x => x.classList.contains('active')) + 1, hash: location.hash }; }, sel);
  await p.goto(url + '#3'); await p.waitForTimeout(400);
  let s = await st(); const N = s.n;
  ok(s.idx === 3 && s.act === 1, `deep link #3 → slide ${s.idx} (active=${s.act})`);
  await p.keyboard.press('Home'); await p.waitForTimeout(200);
  for (const k of ['Space', 'ArrowRight', 'PageDown']) { const before = (await st()).idx; await p.keyboard.press(k); await p.waitForTimeout(250); s = await st(); ok(s.idx === before + 1 && s.act === 1, `${k}: ${before} → ${s.idx}`); }
  await p.keyboard.press('ArrowLeft'); await p.waitForTimeout(250); s = await st(); ok(s.idx === 3, `ArrowLeft → ${s.idx}`);
  await p.keyboard.press('End'); await p.waitForTimeout(250); s = await st(); ok(s.idx === N && s.hash === '#' + N, `End → ${s.idx}/${N} hash ${s.hash}`);
  await p.keyboard.press('ArrowRight'); await p.waitForTimeout(250); s = await st(); ok(s.idx === N, `past last stays at ${s.idx}`);
  await p.keyboard.press('Home'); await p.waitForTimeout(250); s = await st(); ok(s.idx === 1, `Home → ${s.idx}`);
  await p.mouse.click(1200, 450); await p.waitForTimeout(300); s = await st(); ok(s.idx === 2, `click right → ${s.idx}`);
  await p.mouse.click(200, 450); await p.waitForTimeout(300); s = await st(); ok(s.idx === 1, `click left → ${s.idx}`);
  for (let i = 0; i < N + 2; i++) { await p.keyboard.press('ArrowRight'); await p.waitForTimeout(60); }
  s = await st(); ok(s.act === 1 && s.idx === N, `rapid ${N + 2}× → stays single-active at ${s.idx}`);
  ok(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.join(' | ') : ''));
  const m = await b.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  await m.goto(url); await m.waitForTimeout(400);
  await m.evaluate(() => { const t = x => new Touch({ identifier: 1, target: document.body, clientX: x, clientY: 400 }); document.dispatchEvent(new TouchEvent('touchstart', { touches: [t(300)] })); document.dispatchEvent(new TouchEvent('touchmove', { touches: [t(150)] })); document.dispatchEvent(new TouchEvent('touchend', { changedTouches: [t(100)] })); });
  await m.waitForTimeout(300);
  const ms = await m.evaluate(s => [...document.querySelectorAll(s)].findIndex(x => x.classList.contains('active')) + 1, sel);
  ok(ms === 2, `mobile swipe left → ${ms}`);
  const mm = await m.evaluate(() => document.body.classList.contains('m')); ok(mm, 'mobile layout class applied at 390px');
  await b.close();
  console.log(fails ? `== ${fails} FAIL` : '== ALL PASS'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
