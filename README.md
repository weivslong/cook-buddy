# how-to-cook · 做饭查证技能

一个 AI Agent 技能（SKILL.md 通用格式，WorkBuddy / CodeBuddy / Claude Code / Cursor / DeepSeek Harness 等均可安装）：把《程序员做饭指南》(HowToCook) 变成可查证的菜谱库。

**373 道菜 + 18 篇基本功**，所有数字照抄原方、精确到克/毫升，按人数自动换算——禁止「少许适量」，禁止编数字。

装完先问一句 **「西红柿炒鸡蛋 2 人份怎么做」**，能答出精确克数就是装好了。

---

## 功能

**查菜**

- 报菜名：「红烧肉怎么做」
- 报食材：「冰箱里只剩土豆和豆腐能做什么」（多食材交集筛选）
- 报约束：「简单点 / 低卡 / 只要 1 星」（按难度、卡路里排序）
- 问基本功和厨具：「焯水怎么弄」「高压锅怎么用」（18 篇）
- 按分类直查：`grep '|汤羹|'` 出全部 24 道汤
- 口味词有固定翻译策略：「清淡」→ 素菜+汤羹按卡路里升序，「想吃辣」→ 食材列搜辣椒/花椒/麻椒，「下饭 / 硬菜」「想喝汤」「早上吃什么」都有对应查询路径

**算用量**

- 每道菜自带精确计算段，报人数直接给总量，不用你自己乘
- 换算规则写死：「一份够 2 人」按人数除、「1.5-2g 盐/份」区间乘份数不重复乘上限、「油按鸡蛋个数」等特例都接得住
- 上游没写的就如实说没写，不替你假定

**管纪律**

- 所有数字照抄原方，**禁止用「少许 / 适量」顶替，禁止凭记忆编数字**
- 忌口 / 过敏硬过滤：不吃猪肉、素食、过敏原——检索阶段直接筛掉踩雷的菜，不是提醒完就完
- 安全前置：豆角、泡发木耳、未熟豆浆、高压锅、过敏原等风险，先提醒再教做法

**配菜与采购**

- 配一桌菜：报人数自动定菜数（人数+1，荤素各半，≥8 人加水产，有小孩加蛋菜甜口，肉类不重样），每道菜分开换算克数
- 购物清单：定完菜拆「家里常备 / 要买的」两截，多菜同名食材合并数量
- 买菜单文件：要打印就生成 `买菜单-日期.md`，一行一项带数量，截图或打印直接去超市

**跟着做**

- 跟做模式：说「我开做了」就一次只报一步，说「下一步」再给下一条；跳步、复述、中途换人数都接得住
- 懒人模式：说「随便 / 你定」直接拍一道给完整做法，不甩清单让你再选

**排版**

- 灶台友好：步骤一条一行、手机不用横滑表格，末尾固定「技术总结」收尾
- 难菜（≥12 步或 5 星）自动切分步卡片版

**离线**

- 菜谱正文内置，日常查询零联网
- 正文缺失时自动从上游拉取自举（需 git + 网络）

---

## 安装

**任何能读写文件、跑 shell 命令的 Agent 都能用**——把本仓库放进对应 Agent 的技能目录即可：

| Agent / 工具 | 技能目录 |
|---|---|
| WorkBuddy | `~/.workbuddy/skills/how-to-cook/`（或在技能页「添加技能」导入 zip） |
| CodeBuddy | `~/.codebuddy/skills/how-to-cook/` |
| Claude Code | `~/.claude/skills/how-to-cook/` |
| Cursor | `~/.cursor/skills/how-to-cook/` |
| DeepSeek Harness | `~/.dsh/skills/how-to-cook/`（项目级放 `.dsh/skills/`） |
| Codex | `~/.codex/skills/how-to-cook/` 或项目级 `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/how-to-cook/` |
| Windsurf | `~/.codeium/windsurf/skills/how-to-cook/` |
| 其他支持 SKILL.md 的 Agent | 放到它扫描技能的目录下，保持 `SKILL.md` 在 `how-to-cook/` 根层 |

```bash
git clone https://github.com/weivslong/how-to-cook.git ~/.dsh/skills/how-to-cook   # 以 DeepSeek Harness 为例，其他 Agent 换对应目录
```

- **运行要求**：Agent 须能执行 bash + grep（检索和自举都靠它）
- **语言**：菜谱库为中文，**目前仅支持中文查询**

## 结构

```
SKILL.md                  # 技能定义：检索流程、人数换算规则、排版规范
references/HowToCook/     # 上游菜谱正文（只含 .md）
references/INDEX.md       # 菜名|分类|难度|卡路里|食材|路径 索引
scripts/build_index.py    # 重建索引
scripts/refresh.sh        # 从上游拉最新版 / 首次自举
```

## 出处与许可

菜谱正文来自 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)，**Unlicense（公有领域）**，可自由使用与再分发。技能部分（SKILL.md、脚本、索引）同样以 Unlicense 发布。
