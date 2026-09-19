<#
============================================================
 tingzhi.ps1 —— 正常停止（不删数据）
 强调：默认就是 down，不带 -v。带 -v 会删掉命名卷，
 短链和访问记录全没。要删卷得用 qingli.ps1 并且手动确认。
============================================================
#>
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "==> 停止容器（保留数据卷）" -ForegroundColor Cyan
docker compose down

Write-Host ""
Write-Host "已停止。数据卷还在：" -ForegroundColor Green
docker volume ls --filter "name=duanlian"
Write-Host ""
Write-Host "下次用 .\scripts\qidong.ps1 重新起来，短链和访问次数都会保留。" -ForegroundColor Green
Write-Host "想彻底清空数据请用 .\scripts\qingli.ps1（有二次确认）。" -ForegroundColor Yellow


