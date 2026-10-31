# Skills

我的个人 Agent Skills 集合：把实践中反复有用的方法，整理成可复用的指引、脚本和模板。

## 技能目录

| 技能 | 用途 |
| --- | --- |
| [shareable-lessons](skills/shareable-lessons/SKILL.md) | 从经历、对话和复盘中提炼可分享、可迁移的方法，保留证据与适用边界。 |
| [html-explainer-deck](skills/html-explainer-deck/SKILL.md) | 把文章、方法论和报告做成可离线翻页的 HTML 讲解页，检查桌面、手机排版与交互。 |
| [work-intelligence](skills/work-intelligence/SKILL.md) | 复盘工作、回看改进效果，把有依据的重复方法沉淀为技能。 |
| [reality-check](skills/reality-check/SKILL.md) | 围绕会改变取舍的关键未知，取得实际证据，检验假设。 |
| [independent-design-research](skills/independent-design-research/SKILL.md) | 提取目标和约束后独立重设计、做方案调研，避免默认继承旧方案。 |
| [user-facing-only](skills/user-facing-only/SKILL.md) | 检查成品只包含受众需要的内容，避免制作过程和内部说明混入交付。 |

## 安装与使用

可以将需要的 `skills/<技能名>` 文件夹完整复制到 Agent 的技能目录，保留其中的 `references/`、`scripts/`、`template/` 和 `agents/`。Codex 用户技能目录通常为 `~/.codex/skills/`。已有同名技能时，先比较内容再决定是否替换。

也可以使用支持 GitHub 技能集合的 skills CLI 按需安装：

```bash
npx skills add Ljhhhhhh/skills --skill shareable-lessons -g
npx skills add Ljhhhhhh/skills --skill html-explainer-deck -g
```

在对话中显式调用：

```text
用 $shareable-lessons 从这段复盘里提炼可分享的方法，保留依据和适用边界。
用 $html-explainer-deck 把这篇方法论做成可离线打开的 HTML 分享页。
```


## 依赖

大部分技能只提供方法指引；实际执行需要 Agent 具备相应文件、浏览器或外部资料访问能力。

- **html-explainer-deck**：Python 3、Node.js 20+、系统 Chrome/Chromium/Edge、`playwright-core`；总览图需要 Pillow。进入技能目录执行 `npm ci` 安装锁定的 Node 依赖，完整步骤见其 [README](skills/html-explainer-deck/README.md)。
- **work-intelligence**：历史复盘需要可访问且在用户授权范围内的工作记录。

## 来源与许可

本集合使用 [MIT License](LICENSE)。技能中已有的许可证和来源说明继续适用。

- `user-facing-only` 收录本地维护版本，原仓库为 [user-facing-only-skill](https://github.com/Ljhhhhhh/user-facing-only-skill)。

技能是执行指引。安装成功、触发成功和长期有效是不同的验证状态；请结合实际任务判断适用性。
