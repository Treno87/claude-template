#!/bin/bash
# Claude Template Setup Script for WSL/Linux/Mac

set -e

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_GREEN}🚀 Claude Template Setup${COLOR_RESET}"
echo ""

# Get the script directory (where setup.sh is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$(pwd)/.claude"

echo "📂 Source: $SCRIPT_DIR/.claude"
echo "📂 Target: $TARGET_DIR"
echo ""

# Backup existing .claude directory
if [ -d "$TARGET_DIR" ]; then
    BACKUP_DIR="${TARGET_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${COLOR_YELLOW}⚠️  .claude directory already exists${COLOR_RESET}"
    echo "📦 Creating backup: $BACKUP_DIR"
    mv "$TARGET_DIR" "$BACKUP_DIR"
    echo ""
fi

# Copy .claude directory
echo "📋 Copying .claude template..."
cp -r "$SCRIPT_DIR/.claude" "$TARGET_DIR"

# Make hooks executable
if [ -d "$TARGET_DIR/hooks" ]; then
    echo "🔧 Making hooks executable..."
    chmod +x "$TARGET_DIR/hooks"/*
fi

# Create settings.local.json if it doesn't exist
if [ ! -f "$TARGET_DIR/settings.local.json" ]; then
    echo "📝 Creating settings.local.json..."
    cat > "$TARGET_DIR/settings.local.json" << 'EOF'
{
  "permissions": {
    "allow": [],
    "deny": []
  }
}
EOF
fi

echo ""
echo -e "${COLOR_GREEN}✅ Setup complete!${COLOR_RESET}"
echo ""
echo "📚 Next steps:"
echo "  1. Edit .claude/CLAUDE.md to customize for your project"
echo "  2. Update .claude/settings.json permissions if needed"
echo "  3. Use .claude/settings.local.json for machine-specific settings"
echo ""
echo "💡 Tips:"
echo "  - settings.local.json is gitignored by default"
echo "  - Hooks are automatically executable"
echo "  - Add project-specific commands in .claude/commands/"
echo ""
