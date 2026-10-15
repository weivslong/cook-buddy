#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cook-buddy 买菜单对账闸（机械判卷，不用模型）
用法: python3 check_menu.py 对账表.json
对账表格式见 tests/口径与用法.md
退出码: 0=PASS 1=FAIL 2=格式错误
"""
import json
import math
import re
import sys

# ---- 预算常量（唯一口径，SKILL.md 与这里保持一致）----
EQUIV = {"男": 1.0, "女": 0.8, "老": 0.7, "小": 0.5, "幼": 0.3}
MEAT_G = 180      # 荤池：每当量生重（采购重，带骨算带骨）
VEG_G = 220       # 素池：每当量生重
EGG_N = 1.5       # 蛋池：每当量个数
SOUP_BOWL = 1.5   # 汤池：每当量米饭碗
CAP = (0.8, 1.3)  # 修正系数封顶
POOL_TOL = 1.05   # 池子上浮 5% 容差
# 大当量折减：E_raw>8 时，超出部分按 0.8 折（人多尝味，人均食量回落）
FOLD_AT = 8.0
FOLD = 0.8

UNIT = {"kg": 1000, "千克": 1000, "斤": 500, "g": 1, "克": 1}


def parse_grams(s):
    """从 '12个（约1.2kg）' / '600g' / '1斤半' 里解析克数；解析不到返回 None"""
    if s is None:
        return None
    s = str(s)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|千克|斤|g|克)", s)
    if not m:
        return None
    return float(m.group(1)) * UNIT[m.group(2)]


def fold(e_raw):
    return e_raw if e_raw <= FOLD_AT else FOLD_AT + (e_raw - FOLD_AT) * FOLD


def main():
    if len(sys.argv) != 2:
        print("用法: python3 check_menu.py 对账表.json")
        sys.exit(2)
    try:
        d = json.load(open(sys.argv[1], encoding="utf-8"))
    except Exception as e:
        print(f"格式错误：读不了 JSON —— {e}")
        sys.exit(2)

    fails, warns = [], []
    pop = d.get("人群", {})
    unknown = set(pop) - set(EQUIV)
    if unknown or not pop:
        fails.append(f"人群字段不认识或为空：{sorted(unknown) or '空'}")
        print_report(fails, warns, [])
        sys.exit(1)

    e_raw = sum(pop.get(k, 0) * v for k, v in EQUIV.items())
    e_eff = fold(e_raw)
    alcohol = bool(d.get("喝酒"))
    dieting = bool(d.get("控制饮食"))
    has_staple = d.get("有主食", True)

    m = 1.0
    reasons = []
    if alcohol:
        m *= 1.2; reasons.append("喝酒×1.2")
    male_ratio = pop.get("男", 0) / max(sum(pop.values()), 1)
    femold_ratio = (pop.get("女", 0) + pop.get("老", 0)) / max(sum(pop.values()), 1)
    if male_ratio > 0.6:
        m *= 1.1; reasons.append("男性居多×1.1")
    if femold_ratio > 0.6:
        m *= 0.9; reasons.append("女性/老人居多×0.9")
    if dieting:
        m *= 0.9; reasons.append("控制饮食×0.9")
    if not has_staple:
        m *= 1.25; reasons.append("没主食×1.25")
    m = max(CAP[0], min(CAP[1], m))
    if len(reasons) > 1:
        warns.append(f"修正系数叠加后已封顶：{'、'.join(reasons)} → 总修正 ×{m}")

    meat_budget = e_eff * MEAT_G * m
    veg_budget = e_eff * VEG_G * m
    egg_budget = math.ceil(e_eff * EGG_N)
    soup_budget = math.ceil(e_eff * SOUP_BOWL)

    # 用户经验值优先：对账表里给了「预算覆盖」就以它为准（SKILL.md 4.2 经验值条款）
    ov = d.get("预算覆盖", {}) or {}
    if ov.get("荤"):
        meat_budget = float(ov["荤"]); warns.append("荤池预算被用户经验值覆盖")
    if ov.get("素"):
        veg_budget = float(ov["素"]); warns.append("素池预算被用户经验值覆盖")
    if ov.get("蛋"):
        egg_budget = int(ov["蛋"]); warns.append("蛋池预算被用户经验值覆盖")
    if ov.get("汤"):
        soup_budget = float(ov["汤"]); warns.append("汤池预算被用户经验值覆盖")

    mode = d.get("场景", "配桌")
    pool = {"荤": 0.0, "素": 0.0}
    unparsed, eggs, bowls = [], 0, 0
    dishes = d.get("菜品", [])
    for it in dishes:
        p = it.get("池")
        if p not in pool:
            fails.append(f"「{it.get('名','?')}」池字段缺失/不认识（只认 荤/素）")
            continue
        for x in it.get("主料", []):
            g = parse_grams(x.get("量"))
            if g is None:
                unparsed.append(f"{it.get('名','?')}·{x.get('名','?')}")
            else:
                pool[p] += g
        eggs += int(it.get("蛋", 0) or 0)
        bowls += float(it.get("汤碗", 0) or 0)
    eggs = int(d.get("蛋总数", eggs))
    bowls = float(d.get("汤碗数", bowls))

    if unparsed:
        fails.append("这些主料解析不到克数，必须写「约 xxx g」：" + "、".join(unparsed))

    checks = [
        (f"当量：人头 {e_raw:g} → 折减后 {e_eff:g}" + (f"（修正 ×{m:g}）" if m != 1 else ""),
         None),
    ]
    if mode == "单菜":
        # 单菜场景：没有"分摊"，只查这顿总入口别爆（500g×修正/当量为上限）
        total_pc = (pool["荤"] + pool["素"]) / e_eff
        cap = 550 * m
        checks.append((f"荤池：{pool['荤']:.0f}g（参考份额 {meat_budget:.0f}g，单菜可到池满）",
                       pool["荤"] <= meat_budget * 1.6))
        checks.append((f"单菜总入口：{total_pc:.0f}g/当量（上限 {cap:.0f}）",
                       total_pc <= cap))
        if eggs:
            checks.append((f"蛋：{eggs} 个（每当量约 {eggs/e_eff:.1f} 个）", None))
    else:
        checks += [
            (f"荤池：{pool['荤']:.0f}g / 预算 {meat_budget:.0f}g",
             pool["荤"] <= meat_budget * POOL_TOL),
            (f"素池：{pool['素']:.0f}g / 预算 {veg_budget:.0f}g",
             pool["素"] <= veg_budget * POOL_TOL),
            (f"蛋池：{eggs} 个 / 预算 {egg_budget} 个", eggs <= egg_budget + 1),
            (f"汤池：{bowls:g} 碗 / 预算 {soup_budget} 碗", bowls <= soup_budget * POOL_TOL),
        ]
        total_pc = (pool["荤"] + pool["素"]) / e_eff
        lo, hi = 400 * m * 0.8, 400 * m * 1.2
        checks.append((f"人均总量：{total_pc:.0f}g/当量（正常区间 {lo:.0f}-{hi:.0f}）",
                       lo <= total_pc <= hi))

    if mode == "配桌" and dishes:
        n_dish = len({it.get("名") for it in dishes})
        if n_dish < max(2, math.ceil(e_eff) - 1):
            warns.append(f"配桌 {n_dish:g} 道菜偏少（惯例约人数+1）")

    for line, ok in checks:
        if ok is True:
            print(f"  ✅ {line}")
        elif ok is False:
            print(f"  ❌ {line}")
            fails.append(line)
        else:
            print(f"  ℹ️  {line}")

    print_report(fails, warns, [])
    sys.exit(1 if fails else 0)


def print_report(fails, warns, _):
    for w in warns:
        print(f"  ⚠️  {w}")
    if fails:
        print(f"结论：FAIL（{len(fails)} 项超预算）")
    else:
        print("结论：PASS")


if __name__ == "__main__":
    main()
