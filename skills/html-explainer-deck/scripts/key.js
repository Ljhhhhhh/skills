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
  // Persistent controls and the page directory must work without whole-page click navigation.
  ok(await p.locator('#directory').count() === 1, 'persistent directory control exists');
  if (await p.locator('#directory').count()) {
    await p.keyboard.press('Home');
    ok(await p.locator('#prev').isDisabled(), 'previous disabled on first slide');
    await p.locator('#next').click();
    ok((await st()).idx === 2, 'next button advances exactly once');
    await p.locator('#prev').click();
    ok((await st()).idx === 1, 'previous button goes back exactly once');
    await p.locator('#directory').click();
    ok(await p.locator('#overview').evaluate(d => d.open) && await p.locator('#directory').getAttribute('aria-expanded') === 'true', 'directory button opens overview');
    ok(await p.locator('.overview-card').count() === N, 'overview includes every slide');
    await p.locator('.overview-card').nth(2).press('Enter');
    ok((await st()).idx === 3 && !(await p.locator('#overview').evaluate(d => d.open)), 'keyboard selects overview page and returns to presentation');
    await p.keyboard.press('o');
    await p.keyboard.press('Escape');
    ok((await st()).idx === 3 && await p.locator('#directory').evaluate(e => e === document.activeElement), 'Escape preserves page and returns focus to directory');
    const agenda = p.locator('.slide.agenda [data-go]').first();
    if (await agenda.count()) {
      const target = Number(await agenda.getAttribute('data-go'));
      await p.evaluate(() => window.__go([...document.querySelectorAll('.slide')].findIndex(s => s.classList.contains('agenda')), true));
      await agenda.press('Enter');
      ok((await st()).idx === target, 'agenda item supports Enter without extra page turn');
    }
    await p.keyboard.press('End');
    ok(await p.locator('#next').isDisabled(), 'next disabled on last slide');
  }
  if (await p.locator('#controls').count()) {
    await p.keyboard.press('Home');
    await p.mouse.move(800, 100);
    await p.locator('#next').evaluate(e => e.blur());
    await p.waitForTimeout(300);
    const controls = await p.evaluate(() => {
      const nav = document.querySelector('#controls'), button = document.querySelector('#next');
      const alpha = color => { const slash = color.match(/\/\s*([\d.]+)/); return slash ? Number(slash[1]) : color.startsWith('rgba') ? Number(color.slice(color.indexOf('(') + 1, -1).split(',')[3]) : color === 'transparent' ? 0 : 1; };
      const rect = nav.getBoundingClientRect(), buttonRect = button.getBoundingClientRect();
      return { order: [...nav.children].map(e => e.id).join(','), icons: nav.querySelectorAll('button svg').length, width: buttonRect.width, height: buttonRect.height,
        right: innerWidth - rect.right, background: getComputedStyle(button).backgroundColor, alpha: alpha(getComputedStyle(button).backgroundColor), countAlpha: alpha(getComputedStyle(document.querySelector('#page-count')).backgroundColor), navAlpha: alpha(getComputedStyle(nav).backgroundColor) };
    });
    ok(controls.order === 'prev,page-count,next,directory,fs' && controls.icons === 4, 'icon controls retain navigation order');
    ok(controls.width >= 44 && controls.height >= 44 && controls.right < 40 && controls.navAlpha === 0, 'controls sit at right with 44px targets and no outer base');
    ok(controls.alpha > 0 && controls.alpha <= .3 && controls.countAlpha === 0, 'default buttons are translucent and page count has no fill');
    await p.locator('#next').hover(); await p.waitForTimeout(300);
    ok(await p.locator('#next').evaluate(e => getComputedStyle(e).backgroundColor) !== controls.background, 'hover strengthens button background');
    const light = await p.locator('#next').evaluate(e => getComputedStyle(e).color);
    await p.keyboard.press('End'); await p.mouse.move(800, 100);
    const dark = await p.locator('#prev').evaluate(e => getComputedStyle(e).color);
    ok(light !== dark, 'navigation foreground adapts between light and dark slides');
  }
  if (await p.locator('#controls').count()) {
    await p.mouse.move(800, 100);
    await p.evaluate(() => document.activeElement.blur());
    await p.keyboard.press('f');
    await p.waitForTimeout(400);
    ok(await p.evaluate(() => !!document.fullscreenElement), 'F enters browser fullscreen');
    const opacity = () => p.locator('#controls').evaluate(e => Number(getComputedStyle(e).opacity));
    ok(await opacity() < .05, 'fullscreen hides idle navigation');
    const box = await p.locator('#controls').boundingBox();
    await p.mouse.move(box.x - 12, box.y + box.height / 2);
    await p.waitForTimeout(400);
    ok(await opacity() > .95, 'fullscreen navigation fades in over the expanded hotspot');
    await p.mouse.move(800, 100); await p.waitForTimeout(400);
    ok(await opacity() < .05, 'fullscreen navigation fades out when pointer leaves');
    await p.locator('#directory').focus(); await p.waitForTimeout(400);
    ok(await opacity() > .95, 'keyboard focus reveals fullscreen controls');
    await p.keyboard.press('f'); await p.waitForTimeout(400);
    ok(await p.evaluate(() => !document.fullscreenElement) && await opacity() > .95, 'F exits fullscreen and restores visible navigation');
  }
  ok(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.join(' | ') : ''));
  const m = await b.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  await m.goto(url); await m.waitForTimeout(400);
  await m.evaluate(() => { const t = x => new Touch({ identifier: 1, target: document.body, clientX: x, clientY: 400 }); document.dispatchEvent(new TouchEvent('touchstart', { touches: [t(300)] })); document.dispatchEvent(new TouchEvent('touchmove', { touches: [t(150)] })); document.dispatchEvent(new TouchEvent('touchend', { changedTouches: [t(100)] })); });
  await m.waitForTimeout(300);
  const ms = await m.evaluate(s => [...document.querySelectorAll(s)].findIndex(x => x.classList.contains('active')) + 1, sel);
  ok(ms === 2, `mobile swipe left → ${ms}`);
  const mm = await m.evaluate(() => document.body.classList.contains('m')); ok(mm, 'mobile layout class applied at 390px');
  if (await m.locator('#directory').count()) {
    ok(await m.locator('#fs').isVisible(), 'mobile keeps fullscreen icon visible');
    await m.locator('#directory').click();
    const mobileOverview = await m.evaluate(() => ({ width: document.querySelector('#overview').clientWidth, scroll: document.querySelector('#overview').scrollWidth, size: document.querySelector('#directory').getBoundingClientRect().height }));
    ok(mobileOverview.scroll <= mobileOverview.width + 1 && mobileOverview.size >= 44, 'mobile directory has no horizontal overflow and 44px touch target');
    await m.locator('.overview-card').last().click();
    ok(await m.evaluate(() => window.__deck.index + 1) === N, 'mobile directory can reach the final slide');
  }
  await b.close();
  console.log(fails ? `== ${fails} FAIL` : '== ALL PASS'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
