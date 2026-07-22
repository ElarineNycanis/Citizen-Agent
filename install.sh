#!/usr/bin/env bash
set -e

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$HOME/CitizenAgentConfig.json"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TOTAL_STEPS=6
CURRENT=0

progress_bar() {
    local pct=$((CURRENT * 100 / TOTAL_STEPS))
    local fill=$((pct * 40 / 100))
    local bar=""
    for ((i=0; i<40; i++)); do
        [ "$i" -lt "$fill" ] && bar="${bar}█" || bar="${bar}▒"
    done
    echo -e "${BLUE}┌────────────────────────────────────────────────────────────┐${NC}"
    printf "${BLUE}│${NC}  [%3d%%] %s\n" "$pct" "$bar"
    echo -e "${BLUE}│${NC}  ▶ 步骤 ${CURRENT}/${TOTAL_STEPS}: $1"
    echo -e "${BLUE}└────────────────────────────────────────────────────────────┘${NC}"
}

step() {
    CURRENT=$((CURRENT + 1))
    progress_bar "$1"
}

run() {
    local msg="$1"; shift
    ("$@" >/dev/null 2>&1) &
    local pid=$!
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  ${spin:$i:1} %s" "$msg"
        i=$(( (i+1) % ${#spin} ))
        sleep 0.1
    done
    wait "$pid" && printf "\r  ${GREEN}✓${NC} %s\n" "$msg" || {
        printf "\r  ${RED}✗${NC} %s\n" "$msg"
        return 1
    }
}

if [ ! -d /data/data/com.termux ]; then
    echo -e "${RED}[-] 请在 Termux 中运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════╗"
echo "║         CitizenAgent 一键安装脚本            ║"
echo "║         国内镜像加速 + 进度显示              ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

step "配置国内镜像源（清华）"
if grep -q "mirrors.tuna.tsinghua.edu.cn" "$PREFIX/etc/apt/sources.list" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} 镜像源已配置"
else
    sed -i 's|https://packages.termux.dev|https://mirrors.tuna.tsinghua.edu.cn/termux|g; s|https://termux.net|https://mirrors.tuna.tsinghua.edu.cn/termux|g' "$PREFIX/etc/apt/sources.list" 2>/dev/null
    echo -e "  ${GREEN}✓${NC} 已切换为清华镜像源"
fi

step "更新软件包索引"
run "更新 apt 缓存..." pkg update -y -qq

step "安装 Python"
run "安装 Python 环境..." pkg install -y -qq python

step "安装 Python 依赖"
run "安装 requests..." pip install requests -q
run "安装 textual..." pip install "textual>=0.52.0" -q
pip install prompt_toolkit -q 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} 安装 prompt_toolkit"

step "配置项目文件"
if [ ! -f "$CONFIG_FILE" ]; then
    cp "$INSTALL_DIR/config.example.json" "$CONFIG_FILE"
    echo -e "  ${GREEN}✓${NC} 已创建配置文件: ${CONFIG_FILE}"
    echo -e "  ${YELLOW}⚠${NC} 请编辑 ${CONFIG_FILE} 填入 API Key"
else
    echo -e "  ${GREEN}✓${NC} 配置文件已存在"
fi

step "注册 citizen 命令"
if grep -q "alias citizen=" "$HOME/.bashrc" 2>/dev/null; then
    sed -i "/alias citizen=/d" "$HOME/.bashrc"
fi
echo "alias citizen='cd $INSTALL_DIR && python CitizenAgent.py 2>/dev/null'" >> "$HOME/.bashrc"
echo -e "  ${GREEN}✓${NC} 已添加 citizen 命令到 .bashrc"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗"
echo "║              安装完成！                          ║"
echo "╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}▶${NC} 启动项目: ${GREEN}citizen${NC}"
echo -e "  ${BLUE}▶${NC} 配置 Key: ${GREEN}nano ${CONFIG_FILE}${NC}"
echo ""
echo -e "  ${YELLOW}⚠${NC} 执行 ${GREEN}source ~/.bashrc${NC} 使命令立即生效"
echo ""
