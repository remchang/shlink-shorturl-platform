<#
============================================================
 qidong.ps1 —— 一键启动
 做的事：检查 .env 有没有、检查端口、校验 compose、构建并启动、等健康。
 为什么要等健康而不是 sleep：健康检查是「服务自己说行了」，
 sleep 是「我猜它行了」，后者在小内存机器上必翻车。
============================================================
#>
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "==> [1/5] 检查 docker 环境" -ForegroundColor Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "  x 找不到 docker 命令。请先装 Docker Desktop 并确认它已经启动。" -ForegroundColor Red
    exit 1
}
docker version --format '  Docker 引擎 {{.Server.Version}}'
docker compose version

Write-Host "==> [2/5] 检查 .env" -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Write-Host "  x 没有 .env。请先执行： Copy-Item .env.example .env" -ForegroundColor Red
    Write-Host "    然后把里面的占位口令换成真正的随机值。" -ForegroundColor Red
    exit 1
}
$huanjing = Get-Content ".env" -Raw
foreach ($xiang in @("POSTGRES_PASSWORD", "INITIAL_API_KEY")) {
    if ($huanjing -match "$xiang=__") {
        Write-Host "  x $xiang 还是占位符，没改过。" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  .env 检查通过（口令不会被打印出来）" -ForegroundColor Green

Write-Host "==> [3/5] 检查端口占用" -ForegroundColor Cyan
foreach ($duankou in @(8080, 8501)) {
    $zhan = Get-NetTCPConnection -LocalPort $duankou -State Listen -ErrorAction SilentlyContinue
    if ($zhan) {
        Write-Host "  ! 端口 $duankou 已被占用（PID $($zhan[0].OwningProcess)）。" -ForegroundColor Yellow
        Write-Host "    改 .env 里的端口，或者先停掉占用的程序。" -ForegroundColor Yellow
    } else {
        Write-Host "  端口 $duankou 空闲" -ForegroundColor Green
    }
}

Write-Host "==> [4/5] 校验 compose 插值（不会打印密钥）" -ForegroundColor Cyan
docker compose config --quiet
if ($LASTEXITCODE -ne 0) { Write-Host "  x compose 配置有错" -ForegroundColor Red; exit 1 }
Write-Host "  compose 配置有效" -ForegroundColor Green

Write-Host "==> [5/5] 构建并启动三个服务" -ForegroundColor Cyan
docker compose up -d --build

Write-Host ""
Write-Host "等健康检查通过（最多 120 秒）…" -ForegroundColor Cyan
$shangxian = (Get-Date).AddSeconds(120)
do {
    Start-Sleep -Seconds 4
    $zhuangtai = docker compose ps --format json | ConvertFrom-Json
    $quanhao = $true
    foreach ($fw in $zhuangtai) {
        if ($fw.Health -and $fw.Health -ne "healthy") { $quanhao = $false }
        if ($fw.State -ne "running") { $quanhao = $false }
    }
    Write-Host ("  " + (($zhuangtai | ForEach-Object { "$($_.Service)=$($_.State)/$($_.Health)" }) -join "  "))
} while (-not $quanhao -and (Get-Date) -lt $shangxian)

Write-Host ""
docker compose ps
Write-Host ""
Write-Host "启动完成：" -ForegroundColor Green
Write-Host "  管理台    http://localhost:8501"
Write-Host "  短链跳转  http://localhost:8080/<短码>"
Write-Host "  Shlink 健康  http://localhost:8080/rest/health"
Write-Host ""
Write-Host "演示用的长网址目标页（另开一个窗口跑）：" -ForegroundColor Cyan
Write-Host "  python -m http.server 9001 --bind 127.0.0.1 --directory demo-target"


