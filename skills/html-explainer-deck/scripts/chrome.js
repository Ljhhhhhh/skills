// shared: find a Chrome/Chromium binary and launch it via playwright-core
const fs = require('fs');
function findChrome() {
  const c = [process.env.CHROME_PATH,
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'].filter(Boolean);
  return c.find(p => { try { return fs.statSync(p).isFile(); } catch { return false; } });
}
async function launch() {
  let pw;
  try { pw = require('playwright-core'); } catch { pw = require('playwright'); }
  const exe = findChrome();
  if (!exe) console.error('[warn] no system Chrome found; set CHROME_PATH or install `playwright` browsers');
  return pw.chromium.launch({ executablePath: exe, args: ['--no-sandbox', '--font-render-hinting=none'] });
}
function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i > 0 && process.argv[i + 1] !== undefined ? process.argv[i + 1] : def;
}
module.exports = { launch, arg };
