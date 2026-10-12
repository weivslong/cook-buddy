# how-to-cook · 做饭查证技能

一个 WorkBuddy / CodeBuddy 技能：把《程序员做饭指南》(HowToCook) 变成可查证的菜谱库。

- **373 道菜 + 18 篇基本功**，全部用量精确到克/毫升，按人数自动换算
- 回答时先查本地菜谱库，**禁止凭记忆编数字、禁止用"少许/适量"顶替原方**
- 正文缺失时自动从上游拉取自举（需 git + 网络），日常查询完全离线

## 安装

1. 下载本仓库为 zip，或在 WorkBuddy 技能页「添加技能」导入
2. 解压到 `~/.workbuddy/skills/how-to-cook/`（CodeBuddy 为 `~/.codebuddy/skills/`）
3. 直接问：「西红柿炒鸡蛋 2 人份怎么做」「冰箱里只剩土豆和豆腐能做什么」

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
