#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把上游 HowToCook 原始库（一菜一文件）合并成少量分类文件。

为什么有这个脚本：
  SkillHub 等平台限制单技能 ≤200 个文件、目录深度 ≤2 级。
  上游 dishes 目录是一菜一文件（373 个），代入技能后整个包达 398 个文件、深 5 层，直接打包会被拒。
  本脚本按分类把菜谱合并成 10 个 md + 基本功 1 个 md，
  菜谱正文一字不动（仅去除上游 HTML 编辑注释），菜与菜之间加锚点：

      <!-- dish:菜名 -->
      （菜谱原文）
      <!-- /dish -->

  同时生成 references/INDEX.md（菜名|分类|难度|卡路里|主要食材|合并文件）。

用法：
  python3 merge_library.py --src <HowToCook原始库> [--out <references目录>] [--expect N]

断言（任一不满足即中止，不产出半成品）：
  - 合并锚点数 == 去重后菜数 == INDEX 菜谱行数
  - 每道菜含「必备原料和工具 / 计算 / 操作」三段
  - 同一合并文件内锚点名唯一
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)

PANTRY = {
    "燃气灶", "饮用水", "锅", "食用油", "碗与盘子", "筷子", "炒勺",
    "洗涤剂", "抹布", "钢丝球", "菜刀", "水", "盐",
}

# 目录名 → 中文分类（也是合并文件名与 INDEX 分类列，三者保持一致）
CATEGORY_LABEL = {
    "meat_dish": "荤菜",
    "vegetable_dish": "素菜",
    "aquatic": "水产",
    "breakfast": "早餐",
    "staple": "主食",
    "soup": "汤羹",
    "dessert": "甜品",
    "drink": "饮料",
    "condiment": "调料",
    "semi-finished": "半成品",
    "semi_finished": "半成品",
}
CAT_ORDER = ["荤菜", "素菜", "水产", "早餐", "主食", "汤羹", "甜品", "饮料", "调料", "半成品"]

MANDATORY_SECTIONS = ["必备原料和工具", "计算", "操作"]


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def section(text: str, title: str) -> str:
    m = re.search(r"^##\s*" + re.escape(title) + r"\s*$(.*?)(?=^##\s|\Z)",
                  text, re.S | re.M)
    return m.group(1) if m else ""


def clean_ingredient(line: str) -> str:
    s = line.strip().lstrip("-*").strip()
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[`*_]", "", s)
    s = re.split(r"[（(]", s)[0].strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^推荐|^可选", "", s).strip()
    return s


def parse_recipe(path: str):
    text = strip_comments(open(path, encoding="utf-8").read())
    title_m = re.search(r"^#\s*(.+?)\s*$", text, re.M)
    name = title_m.group(1) if title_m else os.path.basename(path)[:-3]
    name = re.sub(r"的做法$", "", name).strip()

    diff_m = re.search(r"预估烹饪难度\s*[:：]\s*(★+)", text)
    difficulty = len(diff_m.group(1)) if diff_m else 0
    cal_m = re.search(r"预估卡路里\s*[:：]\s*([0-9]+)", text)
    cal = cal_m.group(1) if cal_m else ""

    items = []
    for raw in section(text, "必备原料和工具").splitlines():
        if raw.strip().startswith(("-", "*")):
            ing = clean_ingredient(raw)
            if ing and ing not in PANTRY and ing not in items:
                items.append(ing)
    ingredients = "/".join(items[:8])
    return name, difficulty, cal, ingredients, text


def category_of(rel_path: str) -> str:
    parts = rel_path.split(os.sep)
    # rel 形如 dishes/meat_dish/xxx.md 或 dishes/meat_dish/xxx/xxx.md
    if len(parts) >= 2 and parts[0] == "dishes":
        return CATEGORY_LABEL.get(parts[1], parts[1])
    return "未分类"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="上游 HowToCook 原始库目录")
    ap.add_argument("--out", default=os.path.join(SKILL_DIR, "references"),
                    help="输出目录（默认技能 references/）")
    ap.add_argument("--expect", type=int, default=0,
                    help="校验总菜数（如 372），0 表示不校验")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    out = os.path.abspath(args.out)
    dishes_root = os.path.join(src, "dishes")
    if not os.path.isdir(dishes_root):
        sys.stderr.write("错误：找不到 %s\n" % dishes_root)
        return 2
    os.makedirs(out, exist_ok=True)

    # ---- 收集菜谱 ----
    recipes = []  # (rel, name, cat, diff, cal, ing, text)
    for root, _dirs, files in os.walk(dishes_root):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, src)
            if rel.startswith("dishes" + os.sep + "template"):
                continue
            name, diff, cal, ing, text = parse_recipe(full)
            recipes.append((rel, name, category_of(rel), diff, cal, ing, text))

    # ---- 按菜名+分类去重（与旧 build_index 口径一致：保留信息更全的） ----
    dedup = {}
    for rel, name, cat, diff, cal, ing, text in recipes:
        key = (name, cat)
        score = (bool(cal), len(ing or ""), bool(diff))
        if key not in dedup or score > dedup[key][0]:
            if key in dedup:
                sys.stderr.write("去重丢弃：%s（与 %s 同菜同名）\n" % (rel, dedup[key][1]))
            dedup[key] = (score, rel, name, cat, diff, cal, ing, text)
        else:
            sys.stderr.write("去重丢弃：%s（与 %s 同菜同名）\n" % (rel, dedup[key][1]))

    dishes = list(dedup.values())  # (score, rel, name, cat, diff, cal, ing, text)
    total = len(dishes)
    if args.expect and total != args.expect:
        sys.stderr.write("错误：合并后菜数 %d ≠ 预期 %d，中止。\n" % (total, args.expect))
        return 3

    # ---- 段落完整性检查（硬断言） ----
    bad = []
    for _, rel, name, cat, _d, _c, _i, text in dishes:
        missing = [s for s in MANDATORY_SECTIONS if not section(text, s)]
        if missing:
            bad.append((rel, name, missing))
    if bad:
        for rel, name, missing in bad:
            sys.stderr.write("错误：%s（%s）缺段：%s\n" % (rel, name, "、".join(missing)))
        sys.stderr.write("中止：共 %d 道菜段落不齐。\n" % len(bad))
        return 4

    # ---- 写合并文件 ----
    groups = {}
    for _, rel, name, cat, diff, cal, ing, text in dishes:
        groups.setdefault(cat, []).append((name, diff, cal, ing, text))

    written = {}   # 文件名 -> 锚点名列表
    files_meta = []  # (分类, 文件名, 道数)
    for cat in CAT_ORDER:
        rows = sorted(groups.get(cat, []), key=lambda x: (x[1], x[0]))
        if not rows:
            continue
        fname = "菜谱-%s.md" % cat
        L = ["# 程序员做饭指南 · %s（%d 道）" % (cat, len(rows)), "",
             "> 本文件由 scripts/merge_library.py 自动生成；菜谱原文来自",
             "> Anduin2017/HowToCook，内容一字未改（仅去除 HTML 编辑注释）。",
             "> 单菜提取命令见 SKILL.md 第 3 步。", ""]
        anchors = []
        for name, _diff, _cal, _ing, text in rows:
            body = text.strip("\n")
            L.append("<!-- dish:%s -->" % name)
            L.append(body)
            L.append("<!-- /dish -->")
            L.append("")
            anchors.append(name)
        with open(os.path.join(out, fname), "w", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
        if len(set(anchors)) != len(anchors):
            sys.stderr.write("错误：%s 内锚点名重复，中止。\n" % fname)
            return 5
        written[fname] = anchors
        files_meta.append((cat, fname, len(rows)))

    # ---- 基本功（tips） ----
    tips_root = os.path.join(src, "tips")
    tips = []  # (title, text)
    if os.path.isdir(tips_root):
        for root, _dirs, files in os.walk(tips_root):
            for fn in sorted(files):
                if not fn.endswith(".md"):
                    continue
                full = os.path.join(root, fn)
                text = strip_comments(open(full, encoding="utf-8").read())
                t = re.search(r"^#\s*(.+?)\s*$", text, re.M)
                title = t.group(1).strip() if t else fn[:-3]
                tips.append((title, text))
    # 标题去重
    seen = {}
    for title, text in tips:
        if title in seen:
            sys.stderr.write("去重丢弃 tips：%s\n" % title)
        else:
            seen[title] = text
    tips = sorted(seen.items())

    fname = "基本功.md"
    L = ["# 程序员做饭指南 · 基本功与厨房知识（%d 篇）" % len(tips), "",
         "> 本文件由 scripts/merge_library.py 自动生成；原文来自 Anduin2017/HowToCook tips/。",
         ""]
    tip_anchors = []
    for title, text in seen.items():
        L.append("<!-- dish:%s -->" % title)
        L.append(text.strip("\n"))
        L.append("<!-- /dish -->")
        L.append("")
        tip_anchors.append(title)
    with open(os.path.join(out, fname), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    if len(set(tip_anchors)) != len(tip_anchors):
        sys.stderr.write("错误：基本功.md 锚点名重复，中止。\n")
        return 5

    # ---- INDEX.md ----
    I = ["<!-- 本文件由 scripts/merge_library.py 自动生成，请勿手改。 -->",
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
    for cat, fname_, n in files_meta:
        I.append("| %s | `references/%s` | %d |" % (cat, fname_, n))
    I += ["", "## 基本功与工具（`references/基本功.md`，非菜谱）", ""]
    for title in tip_anchors:
        I.append("- %s → `references/基本功.md`" % title)
    I += ["", "## 菜谱明细", ""]
    for cat, fname_, _n in files_meta:
        rows = sorted(groups[cat], key=lambda x: (x[1], x[0]))
        I += ["### %s · `references/%s`（%d 道）" % (cat, fname_, len(rows)), "", "```"]
        for name, diff, cal, ing, _text in rows:
            I.append("%s|%s|%s|%s|%s|references/%s" % (
                name, cat, diff or "-", cal or "-", ing, fname_))
        I += ["```", ""]
    with open(os.path.join(out, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(I) + "\n")

    # ---- 终检 ----
    index_rows = total
    anchor_total = sum(len(v) for v in written.values())
    assert anchor_total == total == index_rows, (anchor_total, total, index_rows)
    print("合并完成：%d 道菜 / %d 个分类文件，%d 篇基本功 → %s"
          % (total, len(files_meta), len(tip_anchors), out))
    for cat, fname_, n in files_meta:
        print("  %-12s %3d 道" % (cat, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
