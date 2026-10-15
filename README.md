# cook-buddy · 做饭搭子

[![License](https://img.shields.io/badge/license-Unlicense-blue)](./LICENSE.txt)
[![Upstream](https://img.shields.io/badge/基于-HowToCook_77k★-orange)](https://github.com/Anduin2017/HowToCook)
[![菜谱](https://img.shields.io/badge/菜谱-372道-green)](#能力总览)
[![格式](https://img.shields.io/badge/格式-SKILL.md_通用标准-8A2BE2)](https://agentskills.io)

把《程序员做饭指南》变成给 AI 用的**可查证菜谱库**。

上游解决的是「盐少许、油适量」没法照着做——这个技能解决的是另一件事：**你问 AI 做饭，它最爱编**。「盐适量」「炒到断生」「大约 10 分钟」……看着像回事，全是它现场编的。装上这个技能，AI 必须先翻菜谱库，数字照抄原方，查不到就说查不到。

**372 道菜（同名重复已去重）+ 18 篇基本功，全部精确到克/毫升，报人数直接算好总量。**

---

## 装完是什么样

问：「**西红柿炒鸡蛋，3 个人吃**」

> 西红柿炒鸡蛋 · ★★ · 约 15 分钟 · 整份约 252 大卡（上游总量）
>
> **用料**（已按 3 人份算好）：西红柿 3 个（约 540g）｜鸡蛋 4.5 个｜食用油 20ml｜盐 4.5–6g（其中 3g 打进蛋液）｜糖 0–6g 可选
>
> 1. 西红柿洗净去皮，切 **4cm 以内**的块
> 2. 鸡蛋 4.5 个加 **3g 盐**、可选 **1ml 醋**打匀
> 3. 热锅倒 **18ml** 油，炒蛋至微黄盛出
> 4. **不洗锅**，下西红柿翻炒 **20 秒**至软烂
> 5. 倒回鸡蛋炒匀，加剩余盐糖出锅
>
> **技术总结**
> - **不洗锅**——锅底那点油是留给西红柿的
> - 想要汤汁：加 30ml 番茄酱 + 150ml 清水
> - 只用熟红西红柿，**青的有中毒风险**

没有「适量」，没有编的数字，每一条都出自菜谱原文。

## 快速开始

任何能跑 shell 命令的 AI Agent（Claude Code、Cursor、WorkBuddy、DeepSeek Harness 等）都能装，一条命令：

```bash
git clone https://github.com/weivslong/cook-buddy.git ~/.claude/skills/cook-buddy
# 其他 Agent 换对应目录，见下表
```

| Agent | 技能目录 |
|---|---|
| Claude Code | `~/.claude/skills/cook-buddy/` |
| Cursor | `~/.cursor/skills/cook-buddy/` |
| WorkBuddy | `~/.workbuddy/skills/cook-buddy/`（或在技能页导入 zip） |
| CodeBuddy | `~/.codebuddy/skills/cook-buddy/` |
| DeepSeek Harness | `~/.dsh/skills/cook-buddy/` |
| Codex | `~/.codex/skills/cook-buddy/` |
| Gemini CLI | `~/.gemini/skills/cook-buddy/` |
| 其他支持 SKILL.md 的 Agent | 放到它扫描技能的目录，保持 `SKILL.md` 在根层 |

装完问一句「西红柿炒鸡蛋 2 人份怎么做」——能答出精确克数就是装好了。

## 能力总览

| 你说 | 它做 |
|---|---|
| 「红烧肉怎么做」 | 翻原方，精确到克，报人数自动换算 |
| 「冰箱只剩土豆和豆腐」 | 食材交集筛选，没有就说没有 |
| 「想吃点清淡的」 | 翻译成素菜+汤羹按卡路里升序，给前几道挑 |
| 「不吃辣，对虾过敏」 | 检索阶段直接筛掉踩雷的菜，硬过滤 |
| 「随便 / 你定」 | 直接拍一道给完整做法，不甩清单让你选 |
| 「今晚 4 个人配几个菜」 | 人数+1、荤素各半、肉类不重样，每道分开算量 |
| 「列个买菜单，我去超市」 | 生成 `买菜单-日期.md`，常备调料不列、要买的带量 |
| 「我开做了」 | 一次只报一步，说「下一步」继续，跳步复述都接得住 |

## 几条纪律

- **数字照抄原方**：禁止「少许/适量」顶替，禁止凭记忆编数字
- **换算有规则**：「一份够 2 人」按人数除、调味范围乘份数不重复乘上限
- **安全前置**：豆角、泡发木耳、高压锅、过敏原——先提醒再教做法
- **查不到就说查不到**：库里没有的菜，不编

排版为灶台场景优化：步骤一条一行、手机不横滑表格、末尾固定「技术总结」；难菜自动切分步卡片版。

## 结构与维护

```
SKILL.md                    # 技能定义：检索流程、换算规则、输出规范
references/菜谱-*.md        # 372 道菜正文，按 10 个分类合并（锚点定位单菜）
references/基本功.md        # 18 篇技巧正文
references/INDEX.md         # 菜名|分类|难度|卡路里|主要食材|合并文件 索引
scripts/merge_library.py    # 上游原文 → 分类合并 + 建索引
scripts/build_index.py      # 从合并库重建/校验索引
scripts/refresh.sh          # 从上游拉最新版 / 首次自举
```

- **日常查询零联网**（正文内置）；正文缺失时自动从上游拉取自举（需 git + 网络）
- 想同步上游最新菜谱：`bash scripts/refresh.sh`（先 `--dry-run` 看差异）
- 菜谱库为中文，目前仅支持中文查询

## 出处与许可

菜谱正文来自 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)（**Unlicense 公有领域**）。技能部分（SKILL.md、脚本、索引）同样以 Unlicense 发布。
