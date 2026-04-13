# install.ps1 - sets up all 13 digital-chip-design-agents plugins for Claude Code
# Run from the repo root in PowerShell:  .\install.ps1
#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoDir    = $PSScriptRoot
$Marketplace = "digital-chip-design-agents"
$Version    = "1.0.0"

# ── Locate Claude config dir ──────────────────────────────────────────────────
$ClaudeDir = if ($env:CLAUDE_CONFIG_DIR) {
    $env:CLAUDE_CONFIG_DIR
} else {
    Join-Path $env:USERPROFILE ".claude"
}

$CacheDir = Join-Path $ClaudeDir "plugins\cache\$Marketplace"
$Settings = Join-Path $ClaudeDir "settings.json"

Write-Host "Claude config : $ClaudeDir"
Write-Host "Plugin cache  : $CacheDir"
Write-Host ""

# ── Sanity checks ─────────────────────────────────────────────────────────────
if (-not (Test-Path $ClaudeDir)) {
    Write-Error "Claude config directory not found at '$ClaudeDir'.`nMake sure Claude Code is installed and has been run at least once."
    exit 1
}

if (-not (Test-Path (Join-Path $RepoDir ".claude-plugin\marketplace.json"))) {
    Write-Error "Run this script from the repo root."
    exit 1
}

# ── Plugin list ───────────────────────────────────────────────────────────────
$Plugins = @(
    "chip-design-architecture",  "chip-design-rtl",
    "chip-design-verification",  "chip-design-formal",
    "chip-design-synthesis",     "chip-design-dft",
    "chip-design-sta",           "chip-design-hls",
    "chip-design-pd",            "chip-design-soc",
    "chip-design-compiler",      "chip-design-firmware",
    "chip-design-fpga"
)

# ── Plugin → source directory mapping ────────────────────────────────────────
$PluginDirs = @{
    "chip-design-architecture" = "architecture"
    "chip-design-rtl"          = "rtl-design"
    "chip-design-verification" = "verification"
    "chip-design-formal"       = "formal"
    "chip-design-synthesis"    = "synthesis"
    "chip-design-dft"          = "dft"
    "chip-design-sta"          = "sta"
    "chip-design-hls"          = "hls"
    "chip-design-pd"           = "pd"
    "chip-design-soc"          = "soc"
    "chip-design-compiler"     = "compiler"
    "chip-design-firmware"     = "firmware"
    "chip-design-fpga"         = "fpga"
}

# ── Populate plugin cache ─────────────────────────────────────────────────────
Write-Host "Installing plugin cache..."
foreach ($Plugin in $Plugins) {
    $Subdir = $PluginDirs[$Plugin]
    $Src    = Join-Path $RepoDir "plugins\$Subdir"
    $Dest   = Join-Path $CacheDir "$Plugin\$Version"

    if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force }
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null

    Copy-Item (Join-Path $Src "agents")         $Dest -Recurse -Force
    Copy-Item (Join-Path $Src "skills")         $Dest -Recurse -Force
    Copy-Item (Join-Path $Src ".claude-plugin") $Dest -Recurse -Force

    $Readme  = Join-Path $RepoDir "README.md"
    if (Test-Path $Readme)  { Copy-Item $Readme  $Dest -Force }
    $License = Join-Path $RepoDir "LICENSE"
    if (Test-Path $License) { Copy-Item $License $Dest -Force }

    Write-Host "  [OK] $Plugin"
}

# ── Update settings.json ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "Updating $Settings ..."

$Cfg = if (Test-Path $Settings) {
    Get-Content $Settings -Raw | ConvertFrom-Json
} else {
    [PSCustomObject]@{}
}

# Ensure enabledPlugins exists
if (-not ($Cfg.PSObject.Properties.Name -contains "enabledPlugins")) {
    $Cfg | Add-Member -MemberType NoteProperty -Name "enabledPlugins" -Value ([PSCustomObject]@{})
}
foreach ($Plugin in $Plugins) {
    $Key = "${Plugin}@${Marketplace}"
    if (-not ($Cfg.enabledPlugins.PSObject.Properties.Name -contains $Key)) {
        $Cfg.enabledPlugins | Add-Member -MemberType NoteProperty -Name $Key -Value $true
    } else {
        $Cfg.enabledPlugins.$Key = $true
    }
}

# Ensure extraKnownMarketplaces exists
if (-not ($Cfg.PSObject.Properties.Name -contains "extraKnownMarketplaces")) {
    $Cfg | Add-Member -MemberType NoteProperty -Name "extraKnownMarketplaces" -Value ([PSCustomObject]@{})
}
# Always overwrite the marketplace source so it points to the current clone location
$MarketplaceSource = [PSCustomObject]@{
    source = [PSCustomObject]@{
        source = "directory"
        path   = $RepoDir
    }
}
if ($Cfg.extraKnownMarketplaces.PSObject.Properties.Name -contains $Marketplace) {
    $Cfg.extraKnownMarketplaces.$Marketplace = $MarketplaceSource
} else {
    $Cfg.extraKnownMarketplaces | Add-Member -MemberType NoteProperty -Name $Marketplace -Value $MarketplaceSource
}

$Cfg | ConvertTo-Json -Depth 10 | Set-Content $Settings -Encoding UTF8
Write-Host "  [OK] $($Plugins.Count) plugins enabled in settings.json"

Write-Host ""
Write-Host "Done! Restart Claude Code to activate all 13 plugins."
