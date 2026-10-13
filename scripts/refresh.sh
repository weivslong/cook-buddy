#!/usr/bin/env bash
# 从上游 Anduin2017/HowToCook 拉取最新 Markdown，合并成本技能的两级结构合并库。
#
# v1.4.0 起 references/ 下是「分类合并文件 + INDEX.md」，不再存放上游原始目录树；
# 本脚本负责：稀疏克隆上游 → merge_library.py 合并 + 重建 INDEX → 清理。
#
# 用法：
#   bash scripts/refresh.sh            # 拉最新并重建
#   bash scripts/refresh.sh --dry-run  # 只看上游是否有更新，不落盘
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$HERE")"
REF="$SKILL_DIR/references"
UPSTREAM="https://github.com/Anduin2017/HowToCook.git"
PY="${PYTHON:-python3}"
MARKER="$REF/.upstream-commit"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

command -v git >/dev/null 2>&1 || { echo "错误：需要 git（拉取上游用）。请先安装 git。" >&2; exit 1; }
command -v "$PY" >/dev/null 2>&1 || { echo "错误：需要 python3。请先安装。" >&2; exit 1; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/howtocook.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "[1/3] 稀疏克隆上游 Markdown（只拉 .md 和 LICENSE，跳过 100MB+ 图片）…"
git clone --depth 1 --filter=blob:none --no-checkout --quiet "$UPSTREAM" "$TMP/src"
git -C "$TMP/src" sparse-checkout set --no-cone '*.md' 'LICENSE' >/dev/null 2>&1
git -C "$TMP/src" checkout --quiet
HEAD_SHA="$(git -C "$TMP/src" rev-parse HEAD)"
rm -rf "$TMP/src/.git" "$TMP/src/.github" "$TMP/src/CODE_OF_CONDUCT.md"

if [ "$DRY" = "1" ]; then
  echo "  上游最新提交：$HEAD_SHA"
  if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "$HEAD_SHA" ]; then
    echo "  与本地一致，无需更新。"
  else
    echo "  上游有更新（--dry-run，未落盘）。去掉 --dry-run 执行刷新。"
  fi
  exit 0
fi

if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "$HEAD_SHA" ]; then
  echo "  上游无更新（$HEAD_SHA），跳过。"
  exit 0
fi

echo "[2/3] 合并成分类文件并重建索引 …"
"$PY" "$HERE/merge_library.py" --src "$TMP/src" --out "$REF"

# LICENSE 放技能根目录（上游菜谱的版权说明）
[ -f "$TMP/src/LICENSE" ] && cp -f "$TMP/src/LICENSE" "$SKILL_DIR/LICENSE" || true
echo "$HEAD_SHA" > "$MARKER"

echo "[3/3] 清理完成。当前版本：$HEAD_SHA"
echo "完成。"
