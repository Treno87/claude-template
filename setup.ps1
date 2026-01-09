# Claude Template Setup Script for Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "🚀 Claude Template Setup" -ForegroundColor Green
Write-Host ""

# Get the script directory (where setup.ps1 is located)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetDir = Join-Path (Get-Location) ".claude"

Write-Host "📂 Source: $ScriptDir\.claude"
Write-Host "📂 Target: $TargetDir"
Write-Host ""

# Backup existing .claude directory
if (Test-Path $TargetDir) {
    $BackupDir = "$TargetDir.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "⚠️  .claude directory already exists" -ForegroundColor Yellow
    Write-Host "📦 Creating backup: $BackupDir"
    Move-Item $TargetDir $BackupDir
    Write-Host ""
}

# Copy .claude directory
Write-Host "📋 Copying .claude template..."
Copy-Item -Path "$ScriptDir\.claude" -Destination $TargetDir -Recurse

# Create settings.local.json if it doesn't exist
$SettingsLocalPath = Join-Path $TargetDir "settings.local.json"
if (-not (Test-Path $SettingsLocalPath)) {
    Write-Host "📝 Creating settings.local.json..."
    @"
{
  "permissions": {
    "allow": [],
    "deny": []
  }
}
"@ | Out-File -FilePath $SettingsLocalPath -Encoding UTF8
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Next steps:"
Write-Host "  1. Edit .claude\CLAUDE.md to customize for your project"
Write-Host "  2. Update .claude\settings.json permissions if needed"
Write-Host "  3. Use .claude\settings.local.json for machine-specific settings"
Write-Host ""
Write-Host "💡 Tips:"
Write-Host "  - settings.local.json is gitignored by default"
Write-Host "  - Hooks work in WSL/Git Bash (not native PowerShell)"
Write-Host "  - Add project-specific commands in .claude\commands\"
Write-Host ""
