#!/bin/bash

# 开发记忆管理脚本
# 用法: ./scripts/dev-memory.sh [命令]

DEV_MEMORY_DIR="docs/dev-memory"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助
show_help() {
    echo "开发记忆管理脚本"
    echo ""
    echo "用法: ./scripts/dev-memory.sh [命令]"
    echo ""
    echo "命令:"
    echo "  start     开始工作（拉取最新代码 + 显示上下文）"
    echo "  update    更新今日日志"
    echo "  commit    提交记忆更新"
    echo "  sync      同步远程记忆（拉取）"
    echo "  status    显示当前任务状态"
    echo "  context   显示项目上下文"
    echo "  task      添加新任务"
    echo "  done      标记任务完成"
    echo "  help      显示此帮助"
    echo ""
    echo "示例:"
    echo "  ./scripts/dev-memory.sh start"
    echo "  ./scripts/dev-memory.sh update \"完成用户登录功能\""
    echo "  ./scripts/dev-memory.sh commit"
}

# 开始工作
start_work() {
    echo -e "${BLUE}🚀 开始工作...${NC}"
    echo ""
    
    # 拉取最新代码
    echo -e "${YELLOW}📥 拉取最新代码...${NC}"
    git checkout develop 2>/dev/null || git checkout main 2>/dev/null || git checkout master 2>/dev/null
    git pull
    
    echo ""
    echo -e "${GREEN}✅ 代码已更新${NC}"
    echo ""
    
    # 显示项目上下文
    echo -e "${BLUE}📖 项目上下文：${NC}"
    echo "----------------------------------------"
    if [ -f "$DEV_MEMORY_DIR/CONTEXT.md" ]; then
        head -50 "$DEV_MEMORY_DIR/CONTEXT.md"
    else
        echo "⚠️  未找到项目上下文文件"
    fi
    echo "----------------------------------------"
    echo ""
    
    # 显示当前任务
    echo -e "${BLUE}📋 当前任务：${NC}"
    echo "----------------------------------------"
    if [ -f "$DEV_MEMORY_DIR/CURRENT.md" ]; then
        cat "$DEV_MEMORY_DIR/CURRENT.md"
    else
        echo "⚠️  未找到当前任务文件"
    fi
    echo "----------------------------------------"
    echo ""
    
    echo -e "${GREEN}💡 提示：创建功能分支开始开发${NC}"
    echo "   git checkout -b feature/功能名-你的名字"
}

# 更新今日日志
update_daily() {
    local content="$1"
    local today=$(date +%Y-%m-%d)
    local daily_file="$DEV_MEMORY_DIR/daily/$today.md"
    
    echo -e "${BLUE}📝 更新今日日志...${NC}"
    
    # 创建目录
    mkdir -p "$DEV_MEMORY_DIR/daily"
    
    # 如果文件不存在，从模板创建
    if [ ! -f "$daily_file" ]; then
        if [ -f "$DEV_MEMORY_DIR/templates/daily-update.md" ]; then
            cp "$DEV_MEMORY_DIR/templates/daily-update.md" "$daily_file"
            # 替换日期
            sed -i "s/YYYY-MM-DD/$today/g" "$daily_file"
            sed -i "s/YYYY-MM-DDTHH:MM:SS+08:00/$(date -Iseconds)/g" "$daily_file"
        fi
    fi
    
    # 添加内容
    if [ -n "$content" ]; then
        echo "" >> "$daily_file"
        echo "### $(date +%H:%M) 更新" >> "$daily_file"
        echo "$content" >> "$daily_file"
        echo -e "${GREEN}✅ 已添加：$content${NC}"
    else
        # 打开编辑器
        ${EDITOR:-nano} "$daily_file"
    fi
}

# 提交记忆更新
commit_memory() {
    echo -e "${BLUE}📤 提交记忆更新...${NC}"
    
    # 检查是否有变更
    if git diff --quiet $DEV_MEMORY_DIR/ && git diff --cached --quiet $DEV_MEMORY_DIR/; then
        echo -e "${YELLOW}⚠️  没有需要提交的变更${NC}"
        return
    fi
    
    # 添加文件
    git add $DEV_MEMORY_DIR/
    
    # 获取今日日期
    local today=$(date +%Y-%m-%d)
    
    # 提交
    git commit -m "docs: 更新开发记忆 - $today"
    
    echo -e "${GREEN}✅ 记忆更新已提交${NC}"
    echo ""
    echo -e "${YELLOW}💡 提示：推送到远程仓库${NC}"
    echo "   git push origin \$(git branch --show-current)"
}

# 同步远程记忆
sync_memory() {
    echo -e "${BLUE}🔄 同步远程记忆...${NC}"
    
    # 拉取最新
    git pull
    
    echo -e "${GREEN}✅ 记忆已同步${NC}"
}

# 显示当前状态
show_status() {
    echo -e "${BLUE}📋 当前任务状态${NC}"
    echo "----------------------------------------"
    if [ -f "$DEV_MEMORY_DIR/CURRENT.md" ]; then
        cat "$DEV_MEMORY_DIR/CURRENT.md"
    else
        echo "⚠️  未找到当前任务文件"
    fi
    echo "----------------------------------------"
}

# 显示项目上下文
show_context() {
    echo -e "${BLUE}📖 项目上下文${NC}"
    echo "----------------------------------------"
    if [ -f "$DEV_MEMORY_DIR/CONTEXT.md" ]; then
        cat "$DEV_MEMORY_DIR/CONTEXT.md"
    else
        echo "⚠️  未找到项目上下文文件"
    fi
    echo "----------------------------------------"
}

# 添加新任务
add_task() {
    local task="$1"
    
    if [ -z "$task" ]; then
        echo -e "${RED}❌ 请提供任务描述${NC}"
        echo "用法: ./scripts/dev-memory.sh task \"任务描述\""
        return
    fi
    
    echo -e "${BLUE}➕ 添加新任务...${NC}"
    
    # 在CURRENT.md中添加任务
    local today=$(date +%Y-%m-%d)
    echo "| $task | - | 🟡 待开始 | $today | - |" >> "$DEV_MEMORY_DIR/CURRENT.md"
    
    echo -e "${GREEN}✅ 任务已添加：$task${NC}"
}

# 标记任务完成
done_task() {
    local task_keyword="$1"
    
    if [ -z "$task_keyword" ]; then
        echo -e "${RED}❌ 请提供任务关键词${NC}"
        echo "用法: ./scripts/dev-memory.sh done \"任务关键词\""
        return
    fi
    
    echo -e "${BLUE}✅ 标记任务完成...${NC}"
    
    # 在CURRENT.md中标记完成
    sed -i "s/$task_keyword.*🟡 待开始/$task_keyword ✅ 已完成/g" "$DEV_MEMORY_DIR/CURRENT.md"
    sed -i "s/$task_keyword.*🔄 进行中/$task_keyword ✅ 已完成/g" "$DEV_MEMORY_DIR/CURRENT.md"
    
    echo -e "${GREEN}✅ 任务已标记完成${NC}"
}

# 主逻辑
case "$1" in
    start)
        start_work
        ;;
    update)
        update_daily "$2"
        ;;
    commit)
        commit_memory
        ;;
    sync)
        sync_memory
        ;;
    status)
        show_status
        ;;
    context)
        show_context
        ;;
    task)
        add_task "$2"
        ;;
    done)
        done_task "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
