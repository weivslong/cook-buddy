# how-to-cook · 做饭查证技能

一个 AI Agent 技能（SKILL.md 通用格式，WorkBuddy / CodeBuddy / Claude Code / Cursor / DeepSeek Harness 等均可安装）：把《程序员做饭指南》(HowToCook) 变成可查证的菜谱库。

- **373 道菜 + 18 篇基本功**，全部用量精确到克/毫升，按人数自动换算
- 回答时先查本地菜谱库，**禁止凭记忆编数字、禁止用"少许/适量"顶替原方**
- 正文缺失时自动从上游拉取自举（需 git + 网络），日常查询完全离线

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
- **验证**：装完问一句「西红柿炒鸡蛋 2 人份怎么做」——能答出精确克数就是装好了

## 结构

```
SKILL.md                  # 技能定义：检索流程、人数换算规则、排版规范
references/HowToCook/     # 上游菜谱正文（只含 .md）
references/INDEX.md       # 菜名|难度|卡路里|食材|路径 索引
scripts/build_index.py    # 重建索引
scripts/refresh.sh        # 从上游拉最新版 / 首次自举
```

## 出处与许可

菜谱正文来自 [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook)，**Unlicense（公有领域）**，可自由使用与再分发。技能部分（SKILL.md、脚本、索引）同样以 Unlicense 发布。
