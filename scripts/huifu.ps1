<#
============================================================
 huifu.ps1 —— 从 beifen.ps1 产出的 .sql 恢复数据库

 用法：
   .\scripts\huifu.ps1 -Wenjian beifen\duanlian-20260919-120000.sql

 这是个破坏性操作：会把当前库里的短链替换成备份里的那份。
 所以这里要求手打 yes 确认，不做 -Force 跳过。
============================================================
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Wenjian
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path $Wenjian)) {
    Write-Host "找不到文件：$Wenjian" -ForegroundColor Red
    exit 1
}

$hash = (Get-FileHash $Wenjian -Algorithm SHA256).Hash
Write-Host "准备恢复：$Wenjian"
Write-Host "SHA256：$hash"
Write-Host ""
Write-Host "警告：这会用备份覆盖当前数据库里的短链和访问记录。" -ForegroundColor Yellow
$queren = Read-Host '确认请输入 yes'
if ($queren -ne "yes") {
    Write-Host "已取消。" -ForegroundColor Green
    exit 0
}

Write-Host "==> 恢复中" -ForegroundColor Cyan
Get-Content $Wenjian -Raw | docker compose exec -T db psql -U shlink -d shlink 2>&1 |
    Select-Object -Last 5

Write-Host ""
Write-Host "==> 恢复后核对" -ForegroundColor Cyan
docker compose exec -T db psql -U shlink -d shlink -c `
    "SELECT COUNT(*) AS duanlian_shu FROM short_urls;"
docker compose exec -T db psql -U shlink -d shlink -c `
    "SELECT COUNT(*) AS fangwen_shu FROM visits;"


