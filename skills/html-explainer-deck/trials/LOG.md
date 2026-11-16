# 验证记录

| 轮次 | 内容类型 | 谁做 | 自动查出 | 人工看图查出 | 修了什么（skill 层面） |
|---|---|---|---|---|---|
| 1 | 方法论（Building Effective Agents，10 条） | 主 agent 按 SKILL.md | 0 | 封面写"9 条"实际 10 条；point 页 chips 太小；手机底栏压字 | `orb: auto`+数量一致性检查；chips 改 2 列大块；手机底栏加同色底；check.sh 用 --strict |
| 2 | 选型/数据（SQLite vs PG vs MySQL） | 主 agent 按 SKILL.md | 0（旧脚本） | 自绘决策树：桌面说明文字贴住方框；手机 SVG 字只有 ~6px | shot.js 加 SVG 有效字号与 OVERLAP 检查；模板加 `.wide`（手机横滑+提示，滑动不翻页）、`.only-d/.only-m`；SKILL 加自绘图规则 |
| 3 | 教程/中英混排（git worktree 多 agent 并行） | 另一个模型（pi）只读 SKILL.md 独立完成 | 0（旧脚本漏检） | pi 自己发现 4 位数字 stats 被裁；我发现对比表推荐列全是 ✗ | shot.js 加"字形超框"CLIP；模板 stats 数字自动缩放（同组统一字号）；build 查 win 列 ✓/✗ 方向；SKILL 补：steps ≤6 步、被检查的计数词清单、多张总览图都要看 |
