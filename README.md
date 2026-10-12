# how-to-cook · 做饭查证技能

一个 AI Agent 技能（SKILL.md 通用格式，WorkBuddy / CodeBuddy / Claude Code / Cursor / DeepSeek Harness 等均可安装）：把《程序员做饭指南》(HowToCook) 变成可查证的菜谱库。

- **四种问法都能查**（可叠加，如「有土豆，要简单点的」）：
  ① 报菜名 →「红烧肉怎么做」｜② 报食材 →「冰箱里只剩土豆和豆腐能做什么」｜③ 报约束 →「简单点 / 低卡 / 只要 1 星」｜④ 问基本功和厨具 →「焯水怎么弄」「高压锅怎么用」（18 篇基本功）
- **用量替你算好**：373 道菜全部自带精确计算段（克/毫升），报人数直接给出总用量——含「一份够几人」「调味料范围不重复乘」「按鸡蛋个数算油」等换算规则的完整处理
- **数字纪律**：所有数字照抄原方，禁止用「少许/适量」顶替，禁止凭记忆编数字；上游没写的就是没写，绝不补
- **安全前置**：豆角、泡发木耳、未熟豆浆、高压锅、过敏原等风险，先提醒再教做法
- **灶台友好排版**：步骤一条一行、手机不用横滑表格，末尾固定「技术总结」收尾；难菜（≥12 步或 5 星）自动切分步卡片版
- **离线可用**：菜谱正文内置，日常查询零联网；正文缺失时自动从上游拉取自举（需 git + 网络）
- **忌口 / 过敏硬过滤**：不吃猪肉、素食、过敏原——检索阶段直接筛掉踩雷的菜，不是提醒完就完
- **配一桌菜**：报人数自动定菜数（人数+1，荤素各半，≥8 人加水产，有小孩加蛋菜甜口），每道菜分开换算克数
- **购物清单**：定完菜后自动拆「家里常备 / 要买的」两截，多菜同名食材合并数量
- **分类 + 口味词检索**：`grep '|汤羹|'` 直查分类；「清淡 / 下饭 / 想吃辣」等口味词有固定翻译策略，不靠临场发挥
- **跟做模式**：说「我开做了」就一次只报一步，说「下一步」再给下一条，跳步、复述、中途换人数都接得住
- **懒人模式**：说「随便 / 你定」直接拍一道给完整做法，不甩清单让你再选
- **买菜单文件**：定完菜可生成 `买菜单-日期.md`，一行一项带数量，直接截图或打印去超市

## 安装

**任何能读写文件、跑 shell 命令的 Agent 都能用**——SKILL.md 是跨平台通用格式，把本仓库放进对应 Agent 的技能目录即可：

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

- **运行要求**：Agent 须能执行 bash + grep（检索和自举都靠它）；首次使用若正文缺失会自动从上游拉取（需 git + 网络），之后完全离线
- **语言**：菜谱库为中文，**目前仅支持中文查询**；英文问法只能靠菜名别名兜底，覆盖不全
- **验证**：装完问一句「西红柿炒鸡蛋 2 人份怎么做」——能答出精确克数就是装好了

## 与同类项目的区别

同一份上游数据已有两个衍生项目，本技能走的是**严谨查证**路线：

| | [jasonbai/howtocook](https://github.com/jasonbai/howtocook)（Claude Code 技能） | [worryzyy/HowToCook-mcp](https://github.com/worryzyy/HowToCook-mcp)（MCP server） | **本技能** |
|---|---|---|---|
| 形态 | SKILL.md + Python 脚本 | MCP server（npm/Docker） | SKILL.md + bash 检索 |
| 用量 | 示例输出只列食材名，**不含克数** | 推荐时问人数，不展示换算 | **按人数逐项换算，含调味料范围、按蛋计油等规则** |
| 数字纪律 | — | — | **禁「少许/适量」顶替、禁编数字**，上游没写就说没写 |
| 忌口/过敏 | 有偏好收集 | 工具参数支持 | 有，且为检索阶段硬过滤 |
| 菜单规划 | 有（人数+1 等公式） | 有一周菜谱推荐 | 有（同类公式 + 每道菜分开换算） |
| 离线 | 内置快照（356 道，2026-03） | 预解析 JSON | 内置最新正文（373 道）+ 一键刷新 |

一句话：规划配菜用同类项目的公式，用量与查证纪律用本技能的——两者叠加比任何单一原版都严。

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
