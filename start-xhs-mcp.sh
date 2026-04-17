#!/bin/bash
# ============================================================
# start-xhs-mcp.sh
# 启动 xiaohongshu-mcp MCP Server（小红书发布底层服务）
#
# 用法：
#   bash scripts/start-xhs-mcp.sh            # 正常启动（无头模式）
#   bash scripts/start-xhs-mcp.sh --login    # 首次登录（显示浏览器扫码）
#   bash scripts/start-xhs-mcp.sh --headed   # 有界面模式（调试用）
#   bash scripts/start-xhs-mcp.sh --bg       # 后台静默启动（供 Agent 自动调用）
# ============================================================

XHS_MCP_PORT=18060
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AMPLIPOST_DIR="$(dirname "$SCRIPT_DIR")"

# ── 解析参数 ──────────────────────────────────────────────────
MODE="headless"
BG=false
for arg in "$@"; do
  case "$arg" in
    --login)  MODE="login" ;;
    --headed) MODE="headed" ;;
    --bg)     BG=true ;;
  esac
done

# ── 加载环境变量（兼容非交互式 shell）────────────────────────
# Agent 调用时可能没有 source ~/.zshrc，手动加载
for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
  [ -f "$rc" ] && source "$rc" 2>/dev/null && break
done

# ── 确定项目目录 ──────────────────────────────────────────────
# 优先级：$XHS_MCP_DIR 环境变量 > $HOME/xiaohongshu-mcp > 同级目录
if [ -n "$XHS_MCP_DIR" ] && [ -d "$XHS_MCP_DIR" ]; then
  MCP_DIR="$XHS_MCP_DIR"
elif [ -d "$HOME/xiaohongshu-mcp" ]; then
  MCP_DIR="$HOME/xiaohongshu-mcp"
else
  MCP_DIR=""
fi

# ── 自动安装（项目不存在时）──────────────────────────────────
if [ -z "$MCP_DIR" ] || [ ! -d "$MCP_DIR" ]; then
  echo "📦 xiaohongshu-mcp 未安装，正在自动安装..."
  bash "$SCRIPT_DIR/setup-xhs-mcp.sh"
  # setup 完成后重新加载环境变量
  for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
    [ -f "$rc" ] && source "$rc" 2>/dev/null && break
  done
  MCP_DIR="${XHS_MCP_DIR:-$HOME/xiaohongshu-mcp}"
fi

# ── 检查是否已在运行 ──────────────────────────────────────────
EXISTING=$(curl -s --max-time 2 -X POST "http://localhost:$XHS_MCP_PORT/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_login_status","arguments":{}},"id":1}' 2>/dev/null)

if [ -n "$EXISTING" ] && [ "$MODE" != "login" ]; then
  if [ "$BG" = false ]; then
    echo "✅ xiaohongshu-mcp 已在运行（端口 $XHS_MCP_PORT）"
  fi
  exit 0
fi

# ── 确定可执行文件 ────────────────────────────────────────────
BINARY="$MCP_DIR/xiaohongshu-mcp-server"
if [ ! -f "$BINARY" ]; then
  # 没有预编译二进制，检查 go 是否可用
  if command -v go &>/dev/null; then
    echo "🔨 未找到编译产物，正在编译..."
    cd "$MCP_DIR" && go build -o xiaohongshu-mcp-server .
  else
    echo "❌ 未找到可执行文件且 Go 未安装，请先运行："
    echo "   bash scripts/setup-xhs-mcp.sh"
    exit 1
  fi
fi

# ── 登录模式 ──────────────────────────────────────────────────
if [ "$MODE" = "login" ]; then
  echo "🔑 启动登录模式（浏览器将弹出，请扫码登录小红书）..."
  LOGIN_BINARY="$MCP_DIR/xiaohongshu-login-darwin-arm64"
  if [ -f "$LOGIN_BINARY" ]; then
    cd "$MCP_DIR" && "$LOGIN_BINARY"
  else
    # 没有预编译登录工具，用 go run
    cd "$MCP_DIR" && go run cmd/login/main.go 2>/dev/null || \
      echo "❌ 未找到登录工具，请参考 $MCP_DIR/README.md"
  fi
  exit 0
fi

# ── 检查 Cookie（登录态）──────────────────────────────────────
COOKIE_FILE="$MCP_DIR/cookies.json"
if [ ! -f "$COOKIE_FILE" ]; then
  echo "⚠️  未找到 cookies.json，需要先登录小红书。"
  echo ""
  echo "请运行：bash scripts/start-xhs-mcp.sh --login"
  exit 1
fi

# ── 启动服务 ──────────────────────────────────────────────────
HEADLESS_FLAG="--headless=true"
[ "$MODE" = "headed" ] && HEADLESS_FLAG="--headless=false"

if [ "$BG" = true ]; then
  # 后台静默启动（Agent 自动调用时使用）
  cd "$MCP_DIR" && nohup "$BINARY" "$HEADLESS_FLAG" \
    > "$HOME/.amplipost/logs/xhs-mcp.log" 2>&1 &
  MCP_PID=$!
  # 等待服务就绪（最多 10 秒）
  for i in $(seq 1 10); do
    sleep 1
    RESP=$(curl -s --max-time 1 -X POST "http://localhost:$XHS_MCP_PORT/mcp" \
      -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_login_status","arguments":{}},"id":1}' 2>/dev/null)
    if [ -n "$RESP" ]; then
      echo "✅ xiaohongshu-mcp 已启动（PID: $MCP_PID，端口: $XHS_MCP_PORT）"
      exit 0
    fi
  done
  echo "❌ 服务启动超时，请检查日志：$HOME/.amplipost/logs/xhs-mcp.log"
  exit 1
else
  # 前台启动
  echo "🚀 启动 xiaohongshu-mcp MCP Server..."
  echo "   目录: $MCP_DIR"
  echo "   端口: $XHS_MCP_PORT"
  echo "   模式: $HEADLESS_FLAG"
  echo "   按 Ctrl+C 停止"
  echo ""
  mkdir -p "$HOME/.amplipost/logs"
  cd "$MCP_DIR" && "$BINARY" "$HEADLESS_FLAG"
fi
