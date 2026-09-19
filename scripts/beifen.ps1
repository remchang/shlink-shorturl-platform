<#
============================================================
 beifen.ps1 —— 数据库备份
 用 pg_dump 逻辑备份，比自己 copy 数据目录安全
 （直接拷 /var/lib/postgresql/data 在容器运行中可能拷到不一致的状态）。
============================================================
#>
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$shijian = Get-Date -Format "yyyyMMdd-HHmmss"
$beifenMulu = "beifen"
$beifenWenjian = "$beifenMulu\duanlian-$shijian.sql"

New-Item -ItemType Directory -Force -Path $beifenMulu | Out-Null

Write-Host "==> 检查 db 容器是否在跑" -ForegroundColor Cyan
$yunxing = docker compose ps --format json | ConvertFrom-Json |
    Where-Object { $_.Service -eq "db" -and $_.State -eq "running" }
if (-not $yunxing) {
    Write-Host "  x db 容器没在运行，先跑 .\scripts\qidong.ps1" -ForegroundColor Red
    exit 1
}

Write-Host "==> 导出数据库 shlink" -ForegroundColor Cyan
docker compose exec -T db pg_dump -U shlink -d shlink --clean --if-exists 2>$null |
    Out-File -Encoding utf8 $beifenWenjian

if (-not (Test-Path $beifenWenjian)) {
    Write-Host "  x 备份文件没生成" -ForegroundColor Red
    exit 1
}

$daxiao = (Get-Item $beifenWenjian).Length
$hash = (Get-FileHash $beifenWenjian -Algorithm SHA256).Hash

Write-Host ""
Write-Host "备份完成" -ForegroundColor Green
Write-Host "  文件：$beifenWenjian"
Write-Host "  大小：$daxiao 字节"
Write-Host "  摘要：$hash"
Write-Host ""
Write-Host "恢复： .\scripts\huifu.ps1 -Wenjian $beifenWenjian" -ForegroundColor Cyan

# 顺手记一份清单，报告里要用
Add-Content -Path "$beifenMulu\beifen-qingdan.txt" -Encoding utf8 `
    -Value "$shijian`t$beifenWenjian`t$daxiao`t$hash"


