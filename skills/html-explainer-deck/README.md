# html-explainer-deck

把文章/方法论/选型/教程做成单文件 HTML 讲解页（16:9 可翻页、手机可读），并用脚本自动验收。
流程和规范见 `SKILL.md`；这里只讲安装和命令。

## 目录

```
SKILL.md                 给 agent 的操作规范（先读这个）
scripts/build.py         deck.md → deck.html（字数预算、要点数与文案一致、对比表 ✓/✗ 方向等检查）
scripts/shot.js          逐页截图（桌面+手机）+ 自动查越界/裁切（含字形超框）/小字/横滑/SVG 文字重叠与过小/JS 报错
scripts/key.js           交互测试（键盘/点击/滑动/#n 直达）
scripts/sheet.py         总览图（Pillow；没有则用 ImageMagick montage）
scripts/check.sh         以上一条龙
scripts/chrome.js        找本机 Chrome 的公共代码
themes/ink.css           冷纸墨色主题（--theme ink 或文首 theme: ink）
themes/drafting.css      工程图纸主题（--theme drafting 或文首 theme: drafting）
template/deck.html       设计系统 + 运行时（占位符 {{TITLE}} {{LANG}} {{BRAND}} {{SLIDES}} {{EXTRA_CSS}}）
template/example.md      覆盖全部页面类型的示例
template/example.html    示例生成结果（默认主题）
template/example-ink.html 同一份示例的 ink 主题成品
template/example-drafting.html 同一份示例的 drafting 主题成品
trials/roundN/           验证用的三套样例（deck.md / deck.html / shots / 总览图）
```

## 安装

```bash
cd <本目录>
npm ci          # 只要 core，不下载浏览器
pip install pillow             # 总览图用；或装 ImageMagick
```

需要本机有 Chrome / Chromium / Edge。脚本自动找常见路径（Linux `/usr/bin/google-chrome`、`chromium`；macOS `/Applications/Google Chrome.app/...`；Windows `Program Files`）。找不到就设：

```bash
export CHROME_PATH="/path/to/chrome"
```

## 一条命令

```bash
bash scripts/check.sh my/deck.md          # build → 截图查错 → 总览图 → 交互测试
# 结果：my/deck.html，my/shots/d01.png… m01.png… sheet-d-1.png sheet-m-1.png
# 最后一行 CHECK PASS 才算过
```

分步：

```bash
python3 scripts/build.py my/deck.md -o my/deck.html --strict
node scripts/shot.js my/deck.html --out my/shots [--wait 80] [--only 2,5] [--mobile off]
python3 scripts/sheet.py my/shots                  # 桌面
python3 scripts/sheet.py my/shots --prefix m --cols 6 --width 300 --per 24   # 手机
node scripts/key.js my/deck.html
```

`shot.js` / `key.js` 也能用在不是本模板生成的 HTML 上：只要每页是 `.slide`（`--selector` 可改），用 `.active` 标当前页、支持 `#n` 或 `window.__go(i)` 跳页。

## 导航与目录

默认模板在右下角依次放置上一页、页码、下一页、网格总览和全屏图标。独立圆角按钮不带外层底座，配色随当前页主题切换；默认底色不透明度为 24%，页码背景透明，悬停或键盘聚焦时增强。全屏时导航自动隐藏，鼠标移入右下角热区或键盘聚焦时显示；退出全屏恢复常驻。`O` 打开全部页面的缩略图目录，选择页面跳转；`Esc` 返回。手机保留同样的图标顺序和至少 44px 点击区，完整支持见 [SKILL.md 的导航规范](SKILL.md#41-主题目录先让读者知道内容结构)。

多章节文稿还需在开场后放 `## agenda` 主题目录，自动按正文分组生成。手写条目须与目标页标题一致，构建会报告缺失或歧义目标。`key.js` 同时检查导航按钮、目录、焦点恢复和手机触控。

## 主题

做新页时三选一：默认（暖纸衬线）、`ink`（冷纸墨色）、`drafting`（工程图纸）。不写 theme 就是默认暖纸衬线主题。

```bash
python3 scripts/build.py deck.md --theme ink -o deck.html
python3 scripts/build.py deck.md --theme drafting -o deck.html
# 或在 deck.md 文首写 theme: ink / theme: drafting
```

`ink`（冷纸墨色）的样式在 `themes/ink.css`，`drafting`（工程图纸：白底细网格、图框标尺、左侧分组色轨，机床绿 / 石油青 / 黄铜 / 青铜）的样式在 `themes/drafting.css`。同一份示例文案的三种成品：`template/example.html`（默认）、`template/example-ink.html`（ink）、`template/example-drafting.html`（drafting）。常驻导航和页面总览会跟随当前页主题。

## 改风格

单篇微调不要改主题文件，把附加 CSS 叠在主题之后：

```bash
python3 scripts/build.py deck.md --theme ink --css brand.css
```

不选主题时，`--css brand.css` 会直接叠在默认设计系统上。
