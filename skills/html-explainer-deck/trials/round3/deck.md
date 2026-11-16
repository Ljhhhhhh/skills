---
title: 用 Git Worktree 实现多 Agent 并行开发
brand: Worktree 实战
lang: zh-CN
label: 做法
---

## cover
kicker: 实战指南
title: 多 Agent 并行<br>Git Worktree<br>*物理隔离*
sub: 3 组 · 7 条实践
thesis: 一个任务一个 worktree、一个分支、一个端口，做完即清理。
orb: auto
core: 独立目录 | 并行开发 / 互不冲突

## statement
kicker: 核心痛点
title: 多个 Agent 改同一仓库，<br>单工作区必然==互相踩踏==。
lead: 互相覆盖文件、分支切来切去、依赖冲突。解法是给每个 Agent 独立的物理工作目录。
visual: vs
left: 单工作区轮流切分支
right: Worktree 物理隔离
- 互相覆盖修改文件 | 每个 Agent 独立目录
- 分支频繁切换冲突 | 独立分支互不干扰
- node_modules 一团乱 | 依赖环境各自隔离
leftnote: 2 个 Agent 就开始互相踩踏
rightnote: 同一仓库检出多个工作区

## cards
kicker: 前置检查
title: 动手前的 3 项准入条件
lead: 运行环境和代码库必须先就绪，避免在并行过程中产生脏状态。
- Git | 版本检查 | Git ≥ 2.5 / 推荐 2.38+ | 确保 worktree 命令可用
- 仓库 | 状态干净 | git status 无改动 / 工作区清空 | 避免未提交修改丢失
- 拆分 | 任务解耦 | 明确拆分任务 / 独立可验收 | 耦合任务不适合并行

## agenda
kicker: 流程总览
title: 7 条核心操作

## section
title: 环境隔离
sub: 准备独立工作区与端口

## point
title: 新建同级工作区与分支
problem: 在仓库内直接切分支会导致多个 Agent 互相覆盖改动。必须为每个任务建立独立的物理目录。
action: 运行 git worktree add 在同级创建新目录并绑定分支，目录命名为 repo-branch。
visual: steps
dir: v
- 执行创建命令 | 运行 git worktree add
- 设定同级路径 | 推荐命名为 ../<repo>-<branch>
- 绑定独立分支 | 使用 -b 参数检出新分支
note: 目录放在仓库同级，避免嵌套产生递归干扰

## point
title: 各自独立安装依赖
problem: 独立目录不会共享 node_modules。直接启动会因缺少依赖报错。
action: 分别进入各 worktree 目录执行 npm ci，磁盘吃紧可用 pnpm 共享 store。
visual: vs
left: 共享依赖（风险）
right: 独立安装（推荐）
- 软链接共享目录 | 各目录执行 npm ci
- 跨分支依赖混乱 | 依赖环境完全解耦
- 编译产物易冲突 | 或用 pnpm 节约磁盘
note: 物理隔离保障运行稳定，根治模块冲突

## point
title: 分配独立开发端口
problem: 多个 Agent 同时启动默认服务会发生端口冲突。必须为每个工作区分离端口。
action: 为各工作区配置不同端口，比如 PORT=3001 与 PORT=3002。
visual: lanes
- 默认端口冲突 | Agent 1 占用 3000 | Agent 2 启动报错
- 独立端口隔离 | Agent 1 绑定 3001 | Agent 2 绑定 3002
note: 端口互不冲突，多个 Dev Server 即可同时常驻运行

## section
title: 并行开发
sub: 任务分发与本地验证

## point
title: 独立目录启动 Agent
problem: Agent 若缺乏明确的工作目录和边界约束，很容易误改其他任务代码。必须双重限定。
action: 在对应 worktree 根目录启动 Agent，并在 Prompt 中限定单一任务。
visual: steps
dir: v
- 定位工作目录 | cd 进指定 worktree 目录
- 启动 Agent | 在该目录下启动 coding agent
- 明确任务边界 | Prompt 中只派发当前单一任务
note: 物理路径与 Prompt 提示词双重约束，确保不跨界

## point
title: 各自跑测试再提交
problem: 多个 Agent 改完直接提交容易引入断言失败。必须在本地独立验证。
action: 在各自工作区内运行 npm test，确保全部通过后再执行 git commit。
visual: vs
left: 盲目提交
right: 隔离测试
- 缺乏本地独立验证 | 各目录独立跑 npm test
- 错误直接合入分支 | 确保全部测试通过
- 阻塞他人正常开发 | 零缺陷再提交 commit
leftnote: 避免带病代码污染主分支
rightnote: 测试通过后再执行提交

## section
title: 合并清理
sub: 分支合并与资源回收

## point
title: 回到主目录合并分支
problem: 在 worktree 目录内跨分支合并容易混淆上下文。必须在主仓库汇合。
action: 切回主仓库目录，执行 git merge 分支名，或推送到远端发起 PR。
visual: lanes
- 本地合并路径 | cd 回主仓库根目录 | git merge feat/login
- 远端评审路径 | 推送分支到远端 | GitHub 发起 PR 评审
note: 统一在主分支汇合，避免在 worktree 之间交叉合并

## point
title: 安全清理目录与分支
problem: 直接用 rm -rf 删目录会留下 Git 内部脏记录。必须使用官方命令清理。
action: 先用 git worktree remove 移除目录，再删分支；遗漏时用 prune 清理。
visual: list
- worktree remove | 移除工作区并同步内部状态
- branch -d | 安全删除已合并的本地功能分支
- worktree prune | 清理遗留无效索引，重置干净状态
note: 切勿直接使用 rm -rf 物理删除目录

## list
kicker: 踩坑预警
title: 并行开发的 4 个高频陷阱
lead: Worktree 实现了工作区隔离，但未跟踪文件与共享资源仍需人工干预。
vtitle: 必须规避的操作盲区
- 分支互斥检出 | 同分支不可重复检出，Git 会报 already checked out
- 未跟踪文件缺失 | .env 等未跟踪文件不会自动复制，需手动拷贝就绪
- 共享资源冲突 | 共享数据库与缓存仍会冲突，测试库与端口必须分开
- 禁止强删目录 | 直接 rm -rf 会遗留脏记录，务必用 worktree remove

## compare
kicker: 选型边界
title: 什么时候用，什么时候不用
lead: 并行并非银弹。看任务耦合度和改动规模再决定。
cols: 场景 | 单目录串行 | Worktree 并行
- 任务解耦、能各自验收 | ✗ 只能排队 | ✓ 并行省时间
- 强耦合、改同一批文件 | ✓ 一次改对 | ✗ 合并冲突不断
- 一次性小改动 | ✓ 随手改完 | ✗ 开目录成本更高
- 多个 Agent 同时干活 | ✗ 互相覆盖 | ✓ 物理隔离

## loop
kicker: 运转闭环
title: 多 Agent 并行，<br>串成一个==完整闭环==
lead: 一个任务、一个 worktree、一个分支、一个端口；做完就 remove。
tags: 独立工作区 / 独立端口 / 严格测试 / 及早清理
core: 闭环 | 并行开发 / 做完即清
- 独立建工作区
- 隔绝依赖端口
- 独立编码测试
- 主干合并清理

## end
kicker: 带走这一句
title: 一个任务一个工作区，<br>用*物理隔离*告别踩踏。
ty: 谢谢阅读
- 独立目录
- 独立分支
- 独立端口
- 做完即删
