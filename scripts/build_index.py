#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 references/HowToCook/ 下的菜谱 Markdown，生成 references/INDEX.md。

索引每行格式：菜名|分类|难度|卡路里|主要食材|正文路径
用法：grep 这个文件定位菜，再去读正文。不要整篇读。
刷新上游正文后需要重跑本脚本。
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REPO = os.path.join(SKILL_DIR, "references", "HowToCook")
OUT = os.path.join(SKILL_DIR, "references", "INDEX.md")

# 与上游模板一致：这些属于厨房常备，不算"特色食材"，检索时滤掉降噪
PANTRY = {
    "燃气灶", "饮用水", "锅", "食用油", "碗与盘子", "筷子", "炒勺",
    "洗涤剂", "抹布", "钢丝球", "菜刀", "水", "盐",
}

CATEGORY_LABEL = {
    "vegetable_dish": "素菜",
    "meat_dish": "荤菜",
    "aquatic": "水产",
    "breakfast": "早餐",
    "staple": "主食",
    "soup": "汤羹",
    "dessert": "甜品",
    "drink": "饮料",
    "condiment": "调料",
    "semi_finished": "半成品",
    "semi-finished": "半成品",
    "template": "模板",
}


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def section(text: str, title: str) -> str:
    m = re.search(r"^##\s*" + re.escape(title) + r"\s*$(.*?)(?=^##\s|\Z)",
                  text, re.S | re.M)
    return m.group(1) if m else ""


def clean_ingredient(line: str) -> str:
    s = line.strip().lstrip("-*").strip()
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)      # 去 markdown 链接
    s = re.sub(r"[`*_]", "", s)
    s = re.split(r"[（(]", s)[0].strip()                    # 去掉括注
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

    # 分类只看 dishes/ 下面那一层目录名。
    # 旧写法用直接父目录名，遇到 dishes/soup/陈皮排骨汤/陈皮排骨汤.md
    # 这种「一道菜一个文件夹」的结构就会把菜名当分类（201/373 行踩过这个坑）。
    cat_dir = ""
    p = os.path.dirname(path)
    while p and p != os.sep:
        b = os.path.basename(p)
        if b in CATEGORY_LABEL:
            cat_dir = b
            break
        if b == "dishes":
            break
        p = os.path.dirname(p)

    return name, CATEGORY_LABEL.get(cat_dir, cat_dir or "未分类"), \
        difficulty, cal, ingredients


def main() -> int:
    if not os.path.isdir(REPO):
        sys.stderr.write("找不到正文目录：%s\n" % REPO)
        return 1

    recipes = []  # (rel_path, name, difficulty, cal, ingredients)
    for root, _dirs, files in os.walk(os.path.join(REPO, "dishes")):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, REPO)
            if rel.startswith("dishes/template/"):
                continue
            name, cat, diff, cal, ing = parse_recipe(full)
            recipes.append((rel, name, cat, diff, cal, ing))

    tips = []
    tips_root = os.path.join(REPO, "tips")
    for root, _dirs, files in os.walk(tips_root):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, REPO)
            title = re.search(r"^#\s*(.+?)\s*$",
                              strip_comments(open(full, encoding="utf-8").read()), re.M)
            tips.append((rel, title.group(1) if title else fn[:-3]))

    # 按菜名+分类去重（上游存在「文件夹 + 同名旧文件」并存的情况，
    # 如陈皮排骨汤同时有难度 3/4 两条）。保留信息更全的，丢弃的打到 stderr。
    dedup = {}
    for rel, name, cat, diff, cal, ing in recipes:
        key = (name, cat)
        if key not in dedup:
            dedup[key] = (rel, name, cat, diff, cal, ing)
        else:
            old = dedup[key]
            score = lambda r: (bool(r[4]), len(r[5] or ""), bool(r[3]))  # cal, ing, diff
            if score(dedup[key]) < score((rel, name, cat, diff, cal, ing)):
                sys.stderr.write("去重丢弃：%s（与 %s 同菜同名）\n" % (rel, old[0]))
                dedup[key] = (rel, name, cat, diff, cal, ing)
            else:
                sys.stderr.write("去重丢弃：%s（与 %s 同菜同名）\n" % (rel, old[0]))
    recipes = [(r, n, c, d, cal, i) for (r, n, c, d, cal, i) in dedup.values()]

    # 按分类归组
    groups = {}
    for rel, name, cat, diff, cal, ing in recipes:
        parts = rel.split(os.sep)
        cat_key = parts[1] if len(parts) > 2 else "(未分类)"
        groups.setdefault(cat_key, []).append((name, cat, diff, cal, ing, rel.replace(os.sep, "/")))

    order = ["vegetable_dish", "meat_dish", "aquatic", "breakfast", "staple",
             "soup", "dessert", "drink", "condiment", "semi-finished", "semi_finished"]
    cats = [c for c in order if c in groups] + [c for c in sorted(groups) if c not in order]

    L = []
    L.append("<!-- 本文件由 scripts/build_index.py 自动生成，请勿手改。 -->")
    L.append("# 菜谱索引（自动生成）")
    L.append("")
    L.append("每行格式：`菜名|分类|难度|卡路里|主要食材|正文路径`")
    L.append("")
    L.append("- **分类**：素菜/荤菜/水产/早餐/主食/汤羹/甜品/饮料/调料/半成品。按分类筛请用**路径列**：`grep 'dishes/soup/'`，比 `grep '|汤羹|'` 稳。")
    L.append("- **难度**：1–5，★ 的个数。1 星最简单（约 5 分钟），5 星最难。")
    L.append("- **卡路里**：上游给的**整份预估总量**，单位大卡，**不是人均**；上游没给人均就不要自己折算。空白表示原作者未填。")
    L.append("- **主要食材**：取自正文「必备原料和工具」，已滤掉锅碗油盐这类厨房常备。")
    L.append("- **正文路径**：相对 `references/HowToCook/`。")
    L.append("- **用法**：grep 本文件定位，再读正文。不要整篇读本文件。")
    L.append("")
    L.append("## 分类速查")
    L.append("")
    L.append("| 分类 | 目录 | 道数 |")
    L.append("|---|---|---|")
    for c in cats:
        L.append("| %s | `dishes/%s/` | %d |" % (
            CATEGORY_LABEL.get(c, c), c, len(groups[c])))
    L.append("")

    L.append("## 基本功与工具（`tips/`，非菜谱）")
    L.append("")
    for rel, title in tips:
        L.append("- %s → `%s`" % (title, rel.replace(os.sep, "/")))
    L.append("")

    L.append("## 菜谱明细")
    L.append("")
    for c in cats:
        rows = sorted(groups[c], key=lambda x: (x[2], x[0]))
        L.append("### %s · `dishes/%s/`（%d 道）" % (
            CATEGORY_LABEL.get(c, c), c, len(rows)))
        L.append("")
        L.append("```")
        for name, cat, diff, cal, ing, rel in rows:
            L.append("%s|%s|%s|%s|%s|%s" % (name, cat, diff or "-", cal or "-", ing, rel))
        L.append("```")
        L.append("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    total = sum(len(v) for v in groups.values())
    print("已生成 %s：%d 道菜谱 / %d 类，%d 条 tips" % (OUT, total, len(cats), len(tips)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
