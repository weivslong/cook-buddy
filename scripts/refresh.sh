#!/usr/bin/env bash
# 从上游重新拉取《程序员做饭指南》的全部 Markdown 正文，并重建索引。
#
# 只拉 .md（上游仓库带 100MB+ 图片，全量克隆很慢），用稀疏检出跳过图片。
#
# 用法：
#   bash scripts/refresh.sh            # 拉最新并重建索引
#   bash scripts/refresh.sh --dry-run  # 只报告差异，不落盘
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$HERE")"
DEST="$SKILL_DIR/references/HowToCook"
UPSTREAM="https://github.com/Anduin2017/HowToCook.git"
PY="${PYTHON:-python3}"
command -v git >/dev/null 2>&1 || { echo "错误：需要 git（拉取上游用）。请先安装 git。" >&2; exit 1; }
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

# rsync 不可用时退回 cp（保证云端/精简环境也能自举）
sync_dir() { # sync_dir <src>/ <dest> [--delete]
  if command -v rsync >/dev/null 2>&1; then
    rsync -a "$@"
  else
    local src="$1" dest="$2"; shift 2 || true
    mkdir -p "$dest"
    if [ "${1:-}" = "--delete" ]; then shift; rm -rf "${dest:?}"/*; fi
    (cd "$src" && cp -R . "$dest/")
  fi
}

TMP="$(mktemp -d "${TMPDIR:-/tmp}/howtocook.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "[1/4] 稀疏克隆上游 Markdown …"
git clone --depth 1 --filter=blob:none --no-checkout --quiet "$UPSTREAM" "$TMP/src"
git -C "$TMP/src" sparse-checkout set --no-cone '*.md' 'LICENSE' >/dev/null 2>&1
git -C "$TMP/src" checkout --quiet
rm -rf "$TMP/src/.git" "$TMP/src/.github" "$TMP/src/CODE_OF_CONDUCT.md"

mkdir -p "$TMP/clean"
sync_dir "$TMP/src/" "$TMP/clean/"

echo "[2/4] 与本地比对 …"
if [ ! -d "$DEST" ] || [ -z "$(ls -A "$DEST" 2>/dev/null)" ]; then
  echo "  本地无正文，首次自举。"
  if [ "$DRY" = "1" ]; then
    echo "  （--dry-run，未落盘）"
    exit 0
  fi
  mkdir -p "$DEST"
  sync_dir "$TMP/src/" "$DEST/"
  echo "[4/4] 重建索引 …"
  "$PY" "$HERE/build_index.py"
  echo "自举完成。"
  exit 0
fi
DIFF="$(diff -rq "$DEST" "$TMP/clean" 2>/dev/null || true)"
if [ -z "$DIFF" ]; then
  echo "  上游与本地产物一致，无需更新。"
  exit 0
fi
echo "$DIFF" | sed 's/^/  /'
if [ "$DRY" = "1" ]; then
  echo "  （--dry-run，未落盘）"
  exit 0
fi

echo "[3/4] 覆盖本地正文 …"
sync_dir "$TMP/src/" "$DEST/" --delete

echo "[4/4] 重建索引 …"
"$PY" "$HERE/build_index.py"
echo "完成。"
