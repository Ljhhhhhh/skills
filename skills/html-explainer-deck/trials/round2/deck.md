---
title: 个人项目数据库怎么选 · SQLite / PostgreSQL / MySQL
brand: 数据库选型
lang: zh-CN
label: 怎么选
---

## cover
kicker: 选型速读
title: 先 SQLite，<br>撑不住再上<br>*PostgreSQL*
sub: 3 个选项 · 6 个维度 · 1 张决策图
thesis: 个人项目和小团队，单机够用就选 SQLite；需要多台机器同时写、要复杂查询和扩展，再换 PostgreSQL。

## statement
kicker: 先说结论
title: 大多数个人项目，<br>卡住你的不是数据库，而是==运维成本==。
visual: bars
vtitle: 上线前要做的运维工作（示意）
- SQLite | 15% | 一个文件
- ~MySQL | 65% | 装服务 + 建账号
- ~PostgreSQL | 70% | 装服务 + 建账号 + 调参

## compare
kicker: 一张表看完
title: 三个选项，六个维度
lead: 绿色勾是这个维度上的优势；推荐列是个人项目的默认选择。
cols: 维度 | SQLite | PostgreSQL | MySQL
win: SQLite
- 部署 | ✓ 嵌入进程，零配置 | 独立服务 | 独立服务
- 并发写 | 同一时刻一个写者 | ✓ 多写者，MVCC | ✓ 多写者
- 复杂查询 | 够用 | ✓ 最强（CTE、窗口、JSONB） | 中等
- 扩展生态 | 少 | ✓ PostGIS、pgvector 等 | 中等
- 备份 | ✓ 复制一个文件 | pg_dump / 流复制 | mysqldump / binlog
- 适合 | **单机应用、原型** | 多服务、重查询 | 传统 Web、托管多

## stats
kicker: 几个关键数字
title: 记住这三个数
- 1 个 | 文件就是整个数据库 | SQLite 的部署单位
- 1 个 | 同一时刻的写者 | WAL 模式下读写可并发
- 5432 | PostgreSQL 默认端口 | 有端口就意味着要管网络和账号

## section 三个关键差异
sub: 决定你选谁的地方

## point 并发写：先算清楚有几个写者
problem: 很多人担心 SQLite 扛不住并发。其实大多数个人项目只有一个进程在写。**真正的分界线是"多台机器同时写"。**
action: 数一数会同时写库的进程和机器：只有一台机器，开 WAL 模式的 SQLite 就够；多台机器要写同一份数据，选 PostgreSQL。
visual: vs
left: SQLite 够用
right: 该换 PostgreSQL
- 单机 Web 应用 | 多台应用服务器
- 后台任务排队写 | 多服务各自直连写库
- 桌面 / 手机应用 | 需要行级锁的高并发写
leftnote: 开 WAL，读写互不阻塞
rightnote: 多写者是它的主场

## point 查询复杂度：看你要不要"在库里算"
problem: 简单增删改查，三者差别不大。**一旦要做地理查询、向量检索、复杂报表，差距就出来了。**
action: 列出你最复杂的三条查询；用到地理、向量、JSON 深度查询或复杂窗口函数的，直接选 PostgreSQL 加对应扩展。
visual: list
vtitle: 出现这些需求就选 PostgreSQL
- 地理位置查询 | PostGIS
- 向量相似度检索 | pgvector
- JSON 文档查询和索引 | JSONB + GIN 索引

## point 运维：备份和迁移谁更省事
problem: 选型时只看功能，上线后才发现要管服务、端口、账号、升级。
action: SQLite 备份就是复制文件（用 .backup 命令或在线备份 API，别在写入时直接拷）；用服务型数据库，就尽量用云厂商的托管版。
visual: lanes
- 服务型自建 | 装服务 | 配账号 | 开端口 | 定时 dump | 升级
- SQLite | 一个文件 | 在线备份 | 完事

## html
kicker: 决策图
title: 30 秒做决定
```html
<div class="wide" style="--mw:760px"><svg viewBox="0 0 1400 600" style="width:100%;height:auto;font-family:var(--sans)" data-a="s">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#8A8BA0"/></marker></defs>
  <g font-size="26" font-weight="700" fill="#17183B" text-anchor="middle">
    <rect x="470" y="10" width="460" height="86" rx="20" fill="#fff" stroke="#E6E1D6" stroke-width="2"/>
    <text x="700" y="64">多台机器要同时写同一份数据？</text>
    <rect x="60" y="210" width="460" height="86" rx="20" fill="#fff" stroke="#E6E1D6" stroke-width="2"/>
    <text x="290" y="264">需要地理 / 向量 / 复杂报表？</text>
    <rect x="900" y="210" width="440" height="86" rx="20" fill="#6C5CE7"/>
    <text x="1120" y="264" fill="#fff">PostgreSQL</text>
    <rect x="30" y="420" width="380" height="86" rx="20" fill="#0FA394"/>
    <text x="220" y="474" fill="#fff">SQLite（开 WAL）</text>
    <rect x="470" y="420" width="420" height="86" rx="20" fill="#6C5CE7"/>
    <text x="680" y="474" fill="#fff">PostgreSQL + 扩展</text>
  </g>
  <g stroke="#8A8BA0" stroke-width="3" fill="none" marker-end="url(#ah)">
    <path d="M600 96 L340 206"/><path d="M800 96 L1060 206"/>
    <path d="M230 296 L220 416"/><path d="M380 296 L620 416"/>
  </g>
  <g font-size="22" font-weight="700" fill="#4A4C66">
    <text x="410" y="150">否</text><text x="960" y="150">是</text>
    <text x="180" y="365">否</text><text x="520" y="365">是</text>
  </g>
  <text x="1120" y="380" text-anchor="middle" font-size="24" fill="#8A8BA0" font-weight="600">已熟悉 MySQL、或托管只给 MySQL</text>
  <text x="1120" y="416" text-anchor="middle" font-size="24" fill="#8A8BA0" font-weight="600">→ 用 MySQL 也行</text>
</svg></div>
```

## cards
kicker: 对号入座
title: 你是哪一种？
- A | 原型 / 单机应用 | 桌面或手机应用 / 单台服务器的网站 / 内部小工具 | 选 SQLite
- B | 多服务 / 重查询 | 多台应用服务器 / 地理或向量检索 / 复杂报表 | 选 PostgreSQL
- C | 已有 MySQL 生态 | 团队熟悉 / 托管服务只给 MySQL / 老项目 | 继续 MySQL

## end
kicker: 带走这一句
title: 先用最省事的，<br>等*真的撑不住*再迁移。
ty: 谢谢
- 数写者
- 看查询
- 算运维
