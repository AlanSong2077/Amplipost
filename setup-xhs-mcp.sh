#!/bin/bash
# ============================================================
# setup-xhs-mcp.sh
# 首次部署：自动 clone xiaohongshu-mcp、编译二进制、写入环境变量
# 用法：bash scripts/setup-xhs-mcp.sh
# ============================================================

set -e

REPO_URL="https://github.com/xpzouying/xiaohongshu-mcp.git"
DEFAULT_INSTALL_DIR="$HOME/xiaohongshu-mcp"
SHELL_RC=""

# ── 检测 shell 配置文件 ───────────────────────────────────────
detect_shell_rc() {
  if [ -n "$ZSH_VERSION" ] || [ "$(basename "$SHELL")" = "zsh" ]; then
    echo "$HOME/.zshrc"
  elif [ -n "$BASH_VERSION" ] || [ "$(basename "$SHELL")" = "bash" ]; then
    echo "$HOME/.bashrc"
  else
    echo "$HOME/.profile"
  fi
}

SHELL_RC=$(detect_shell_rc)

echo "======================================================"
echo "  xiaohongshu-mcp 安装向导"
echo "======================================================"
echo ""

# ── 检查 Git ──────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
  echo "❌ 未找到 git，请先安装 Git："
  echo "   macOS: brew install git"
  exit 1
fi

# ── 检查 Go ───────────────────────────────────────────────────
if ! command -v go &>/dev/null; then
  echo "❌ 未找到 Go 环境，请先安装 Go 1.21+："
  echo "   macOS: brew install go"
  echo "   或访问 https://go.dev/dl/"
  exit 1
fi

GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
echo "✅ Go 版本：$GO_VERSION"

# ── 确定安装目录 ──────────────────────────────────────────────
# 优先使用已有的 XHS_MCP_DIR 环境变量，否则用默认值
INSTALL_DIR="${XHS_MCP_DIR:-$DEFAULT_INSTALL_DIR}"

echo "📁 安装目录：$INSTALL_DIR"
echo ""

# ── Clone 或更新项目 ──────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "📦 项目已存在，拉取最新代码..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "📦 正在 clone xiaohongshu-mcp..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

echo ""

# ── 编译二进制 ────────────────────────────────────────────────
echo "🔨 正在编译..."
cd "$INSTALL_DIR"
go build -o xiaohongshu-mcp-server .
echo "✅ 编译完成：$INSTALL_DIR/xiaohongshu-mcp-server"
echo ""

# ── 写入环境变量 ──────────────────────────────────────────────
ENV_LINE="export XHS_MCP_DIR=\"$INSTALL_DIR\""

if grep -q "XHS_MCP_DIR" "$SHELL_RC" 2>/dev/null; then
  # 已存在则更新
  sed -i.bak "s|export XHS_MCP_DIR=.*|$ENV_LINE|" "$SHELL_RC"
  echo "✅ 已更新 $SHELL_RC 中的 XHS_MCP_DIR"
else
  echo "" >> "$SHELL_RC"
  echo "# xiaohongshu-mcp MCP Server（由 Amplipost setup 写入）" >> "$SHELL_RC"
  echo "$ENV_LINE" >> "$SHELL_RC"
  echo "✅ 已写入 $SHELL_RC：$ENV_LINE"
fi

# 当前 shell 立即生效
export XHS_MCP_DIR="$INSTALL_DIR"

echo ""
echo "======================================================"
echo "  安装完成！"
echo ""
echo "  下一步："
echo "  1. 重新加载 shell 配置（或新开终端）："
echo "     source $SHELL_RC"
echo ""
echo "  2. 首次登录小红书（扫码，只需一次）："
echo "     bash scripts/start-xhs-mcp.sh --login"
echo ""
echo "  3. 之后直接启动服务："
echo "     bash scripts/start-xhs-mcp.sh"
echo "======================================================"
