<#
============================================================
 qingli.ps1 —— 破坏性清理：删容器 + 删数据卷

 ★★ 危险操作 ★★
 down -v 会把命名卷 duanlian-shlink-db 一起删掉，
 短链和全部访问记录不可恢复。只在下面两种情况用：
   ① 实验做完、报告写完了，要交还机器；
   ② 数据被自己搞脏了，有备份在手，想从零重来。

 脚本故意不做 -Force 跳过确认，也不接受参数绕过。
============================================================
#>
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "=====================================================" -ForegroundColor Red
Write-Host " 警告：此操作非常危险，可能导致不可逆的数据丢失！" -ForegroundColor Red
Write-Host "=====================================================" -ForegroundColor Red
Write-Host ""
Write-Host "即将删除："
Write-Host "  · 容器 duanlian-db / duanlian-api / duanlian-web"
Write-Host "  · 命名卷 duanlian-shlink-db（所有短链 + 访问记录）" -ForegroundColor Red
Write-Host ""

# 先问一遍有没有备份，这是最后一道防线
$youBeifen = Read-Host "你手上有 beifen\ 目录下的 .sql 备份吗？(yes/no)"
if ($youBeifen -ne "yes") {
    Write-Host ""
    Write-Host "先去备份： .\scripts\beifen.ps1" -ForegroundColor Yellow
    Write-Host "已取消清理。" -ForegroundColor Green
    exit 0
}

$queren = Read-Host "再确认一次，输入 DELETE-VOLUME 才会继续"
if ($queren -ne "DELETE-VOLUME") {
    Write-Host "已取消清理，什么都没删。" -ForegroundColor Green
    exit 0
}

Write-Host "==> 执行清理" -ForegroundColor Cyan
docker compose down -v

Write-Host ""
docker volume ls --filter "name=duanlian"
Write-Host ""
Write-Host "清理完成。卷已经删掉了，下次 qidong.ps1 会是全新的空库。" -ForegroundColor Green


