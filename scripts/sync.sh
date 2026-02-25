#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENCODE_DIR="${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}"
SKILLS_DST="$OPENCODE_DIR/skills/self-improve"
COMMANDS_DST="$OPENCODE_DIR/commands"
AGENTS_SRC="$REPO_DIR/AGENTS.md"
AGENTS_DST="$OPENCODE_DIR/AGENTS.md"

echo "=== Self-Improve 知识库同步 ==="
echo "仓库路径: $REPO_DIR"
echo ""

# 1. 注入 AGENTS.md（动态替换 __REPO_PATH__ 为实际路径）
echo "[1/3] 注入 AGENTS.md"

# 生成我们的内容（替换 __REPO_PATH__）
sed "s|__REPO_PATH__|$REPO_DIR|g" "$AGENTS_SRC" > "$AGENTS_DST.tmp"

# 根据目标文件状态决定合并策略
if [ ! -f "$AGENTS_DST" ]; then
    # 情况1: 目标文件不存在 → 直接写入
    mv "$AGENTS_DST.tmp" "$AGENTS_DST"
    echo "  创建新的 AGENTS.md"
elif grep -q "Self-Improve 知识库" "$AGENTS_DST"; then
    # 情况2: 目标文件是我们的（包含标记） → 完全替换
    mv "$AGENTS_DST.tmp" "$AGENTS_DST"
    echo "  更新已有的 AGENTS.md"
else
    # 情况3: 目标文件是用户自己的 → 追加我们的内容
    echo "" >> "$AGENTS_DST"
    cat "$AGENTS_DST.tmp" >> "$AGENTS_DST"
    rm "$AGENTS_DST.tmp"
    echo "  追加到已有 AGENTS.md"
fi
echo "  ✅ $AGENTS_DST"

echo ""
echo "[2/3] 同步 Skills"
mkdir -p "$SKILLS_DST"
find "$SKILLS_DST" -maxdepth 1 -type l -delete
skill_count=0
for category_dir in "$REPO_DIR/skills"/*/; do
    [ -d "$category_dir" ] || continue
    category=$(basename "$category_dir")
    for skill_dir in "$category_dir"*/; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        skill_name=$(basename "$skill_dir")
        link_name="${category}-${skill_name}"
        ln -sf "$skill_dir" "$SKILLS_DST/$link_name"
        echo "  ✅ $link_name"
        skill_count=$((skill_count + 1))
    done
done
echo "  共 $skill_count 个 skills"

echo ""
echo "[3/3] 同步 Commands"
mkdir -p "$COMMANDS_DST"
cmd_count=0
for cmd_file in "$REPO_DIR/scripts"/distill-*.md; do
    [ -f "$cmd_file" ] || continue
    cmd_name=$(basename "$cmd_file")
    ln -sf "$cmd_file" "$COMMANDS_DST/$cmd_name"
    echo "  ✅ $cmd_name"
    cmd_count=$((cmd_count + 1))
done
echo "  共 $cmd_count 个 commands"

echo ""
echo "=== 同步完成 ==="
