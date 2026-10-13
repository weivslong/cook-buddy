#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从合并库（references/菜谱-*.md、references/基本功.md）重建 references/INDEX.md。

v1.4.0 起菜谱库是合并文件结构（每菜一个 <!-- dish:菜名 --> 锚点），
本脚本扫描锚点、从锚点内正文重新提取字段，生成与 merge_library.py 相同格式的 INDEX。
用途：手动改过合并文件、或怀疑 INDEX 与正文不同步时，跑一遍重建并 git diff 校验。

用法：python3 build_index.py [--check]
  默认重建 INDEX.md；--check 只比对不写盘，不一致时退出码 1。
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REF = os.path.join(SKILL_DIR, "references")
OUT = os.path.join(REF, "INDEX.md")

PANTRY = {
    "燃气灶", "饮用水", "锅", "食用油", "碗与盘子", "筷子", "炒勺",
    "洗涤剂", "抹布", "钢丝球", "菜刀", "水", "盐",
}

CAT_ORDER = ["荤菜", "素菜", "水产", "早餐", "主食", "汤羹", "甜品", "饮料", "调料", "半成品"]

ANCHOR_RE = re.compile(r"^<!-- dish:(.*?) -->\s*$", re.M)
END = "<!-- /dish -->"


def anchor_block(text: str, name: str) -> str:
    """按锚点名提取单菜正文（与 SKILL.md 第 3 步的 awk 命令同逻辑）。"""
    m = re.search(r"^<!-- dish:" + re.escape(name) + r" -->\s*\n(.*?)^<!-- /dish -->",
                  text, re.S | re.M)
    return m.group(1) if m else ""


def parse_dish(text: str):
    diff_m = re.search(r"预估烹饪难度\s*[:：]\s*(★+)", text)
    difficulty = len(diff_m.group(1)) if diff_m else 0
    cal_m = re.search(r"预估卡路里\s*[:：]\s*([0-9]+)", text)
    cal = cal_m.group(1) if cal_m else ""

    m = re.search(r"^##\s*必备原料和工具\s*$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    items = []
    if m:
        for raw in m.group(1).splitlines():
            if raw.strip().startswith(("-", "*")):
                s = raw.strip().lstrip("-*").strip()
                s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
                s = re.sub(r"[`*_]", "", s)
                s = re.split(r"[（(]", s)[0].strip()
                s = re.sub(r"\s+", " ", s)
                s = re.sub(r"^推荐|^可选", "", s).strip()
                if s and s not in PANTRY and s not in items:
                    items.append(s)
    return difficulty, cal, "/".join(items[:8])


def build_index_rows():
    """扫描所有合并文件，返回 (菜谱行列表, 基本功标题列表)。"""
    rows = []   # (name, cat, diff, cal, ing, fname)
    tips = []
    for fn in sorted(os.listdir(REF)):
        if not fn.endswith(".md") or fn == "INDEX.md":
            continue
        text = open(os.path.join(REF, fn), encoding="utf-8").read()
        names = ANCHOR_RE.findall(text)
        if fn == "基本功.md":
            tips = names
            continue
        cat_m = re.match(r"菜谱-(.+)\.md$", fn)
        cat = cat_m.group(1) if cat_m else fn[:-3]
        for name in names:
            block = anchor_block(text, name)
            if not block:
                sys.stderr.write("错误：%s 的锚点「%s」没有结束标记\n" % (fn, name))
                return None, None
            diff, cal, ing = parse_dish(block)
            rows.append((name, cat, diff, cal, ing, "references/" + fn))
    return rows, tips


def render(rows, tips) -> str:
    groups = {}
    for name, cat, diff, cal, ing, fname in rows:
        groups.setdefault(cat, []).append((name, diff, cal, ing, fname))
    cats = [c for c in CAT_ORDER if c in groups] + \
        [c for c in sorted(groups) if c not in CAT_ORDER]

    I = ["<!-- 本文件由 scripts/build_index.py 自动生成，请勿手改。 -->",
         "# 菜谱索引（自动生成）", "",
         "每行格式：`菜名|分类|难度|卡路里|主要食材|合并文件`", "",
         "- **分类**：%s。按分类筛用**分类列**：`awk -F'|' '$2==\"汤羹\"'`。" % "/".join(CAT_ORDER),
         "- **难度**：1–5，★ 的个数。1 星最简单，5 星最难。",
         "- **卡路里**：上游给的**整份预估总量**，不是人均；上游没给人均就不要自己折算。空白表示原作者未填。",
         "- **主要食材**：取自正文「必备原料和工具」，已滤掉锅碗油盐等厨房常备。",
         "- **合并文件**：相对技能根目录。用 SKILL.md 第 3 步的 awk 命令按菜名锚点提取单菜。",
         "- **用法**：grep 本文件定位 → awk 提取单菜正文。不要整篇读本文件和合并文件。", "",
         "## 分类速查", "",
         "| 分类 | 文件 | 道数 |", "|---|---|---|"]
    for c in cats:
        fname = groups[c][0][4]
        I.append("| %s | `%s` | %d |" % (c, fname, len(groups[c])))
    I += ["", "## 基本功与工具（`references/基本功.md`，非菜谱）", ""]
    for t in tips:
        I.append("- %s → `references/基本功.md`" % t)
    I += ["", "## 菜谱明细", ""]
    for c in cats:
        rws = sorted(groups[c], key=lambda x: (x[1], x[0]))
        I += ["### %s · `%s`（%d 道）" % (c, rws[0][4], len(rws)), "", "```"]
        for name, diff, cal, ing, fname in rws:
            I.append("%s|%s|%s|%s|%s|%s" % (name, c, diff or "-", cal or "-", ing, fname))
        I += ["```", ""]
    return "\n".join(I) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只比对不写盘")
    args = ap.parse_args()

    if not os.path.isfile(os.path.join(REF, "基本功.md")):
        sys.stderr.write("错误：%s 下没有合并库（缺 基本功.md）。先跑 merge_library.py。\n" % REF)
        return 2

    rows, tips = build_index_rows()
    if rows is None:
        return 3
    content = render(rows, tips)

    if args.check:
        old = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        if old == content:
            print("校验通过：INDEX.md 与合并库一致（%d 道菜 / %d 篇基本功）" % (len(rows), len(tips)))
            return 0
        sys.stderr.write("不一致：INDEX.md 与合并库有出入，去掉 --check 重跑可修复。\n")
        return 1

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(content)
    print("已重建 %s：%d 道菜 / %d 篇基本功" % (OUT, len(rows), len(tips)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
