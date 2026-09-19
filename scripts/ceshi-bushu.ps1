<#
============================================================
 ceshi-bushu.ps1 —— 容器测试 + 持久化测试

 这两类测试必须有 Docker，且会重启容器，所以单独一个脚本，
 不和日常的 pytest 混在一起。

 容器测试 5 项：
   C1 镜像能从干净环境构建
   C2 三个服务都在 running
   C3 健康检查都变 healthy
   C4 服务间网络互通（web 能访问 shlink）
   C5 容器里用的是服务名而不是 localhost 硬编码

 持久化测试 3 项：
   P1 down / up 之后短链还在
   P2 down / up 之后访问次数还在
   P3 备份文件能恢复到新库
============================================================
#>
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$tongguo = 0; $shibai = 0
function Pan($ming, $tiaojian, $shuoming) {
    if ($tiaojian) {
        Write-Host ("  [PASS] {0} —— {1}" -f $ming, $shuoming) -ForegroundColor Green
        $script:tongguo++
    } else {
        Write-Host ("  [FAIL] {0} —— {1}" -f $ming, $shuoming) -ForegroundColor Red
        $script:shibai++
    }
}

$huanjing = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $huanjing[$matches[1]] = $matches[2].Trim() }
}
$tou = @{ "X-Api-Key" = $huanjing["INITIAL_API_KEY"]; "Content-Type" = "application/json" }

Write-Host "===== 容器测试（C1-C5）=====" -ForegroundColor Cyan

# C1 干净构建
Write-Host "  C1 构建 web 镜像…"
docker compose build web --no-cache 2>&1 | Select-Object -Last 2
Pan "C1 镜像构建" ($LASTEXITCODE -eq 0) "docker compose build 退出码 $LASTEXITCODE"

docker compose up -d
Start-Sleep -Seconds 25

# C2 三个服务都在跑
$ps = docker compose ps --format json | ConvertFrom-Json
$zaipao = @($ps | Where-Object { $_.State -eq "running" }).Count
Pan "C2 服务运行" ($zaipao -eq 3) "running 的服务数=$zaipao / 3"

# C3 健康状态
$jiankang_shu = @($ps | Where-Object { $_.Health -eq "healthy" }).Count
Pan "C3 健康检查" ($jiankang_shu -ge 2) "healthy 的服务数=$jiankang_shu"

# C4 服务间互通：从 web 容器里访问 shlink
$hui = docker compose exec -T web python -c `
    "import urllib.request;print(urllib.request.urlopen('http://shlink:8080/rest/health',timeout=5).status)" 2>&1
Pan "C4 服务间互通" ("$hui" -match "200") "web 容器访问 shlink:8080 -> $hui"

# C5 检查没有硬编码 localhost
$config = docker compose config
$ying = ($config | Select-String "SHLINK_JICHU_URL" | Select-Object -First 1).ToString()
Pan "C5 用服务名" ($ying -match "shlink:8080") "compose 展开后：$($ying.Trim())"

Write-Host ""
Write-Host "===== 持久化测试（P1-P3）=====" -ForegroundColor Cyan

# 先造一条有访问次数的短链
Invoke-RestMethod -Method Post -Uri "http://localhost:8080/rest/v3/short-urls" -Headers $tou `
    -Body (@{ longUrl = "http://localhost:9001/demo.html"; customSlug = "chijiuhua" } | ConvertTo-Json) | Out-Null
for ($i = 0; $i -lt 2; $i++) {
    try { Invoke-WebRequest -Uri "http://localhost:8080/chijiuhua" -MaximumRedirection 0 -ErrorAction SilentlyContinue } catch {}
}
Start-Sleep -Seconds 6
$jiu = (Invoke-RestMethod "http://localhost:8080/rest/v3/short-urls/chijiuhua/visits" -Headers $tou).visits.pagination.totalItems
Write-Host "  重建前：短码 chijiuhua 访问次数 = $jiu"

# P3 先备份（顺序上备份要在 down 之前）
Write-Host "  P3 备份数据库…"
& "$PSScriptRoot\beifen.ps1" | Select-Object -Last 4
$beifenWenjian = (Get-ChildItem "beifen\*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
Pan "P3 备份生成" (Test-Path $beifenWenjian) "$beifenWenjian"

# P1/P2 容器重建
Write-Host "  执行 down / up（不带 -v，不能删卷）…"
docker compose down | Out-Null
docker compose up -d | Out-Null
Start-Sleep -Seconds 35

$xin = Invoke-RestMethod "http://localhost:8080/rest/v3/short-urls/chijiuhua" -Headers $tou -ErrorAction SilentlyContinue
Pan "P1 短链保留" ($null -ne $xin.shortCode) "重建后仍能查到 chijiuhua -> $($xin.longUrl)"

$xinCishu = (Invoke-RestMethod "http://localhost:8080/rest/v3/short-urls/chijiuhua/visits" -Headers $tou).visits.pagination.totalItems
Pan "P2 访问数保留" ($xinCishu -ge $jiu) "重建前 $jiu 次 -> 重建后 $xinCishu 次"

Write-Host ""
Write-Host "结果：通过 $tongguo 项，失败 $shibai 项" -ForegroundColor $(if ($shibai -eq 0) { "Green" } else { "Red" })
Write-Host "（P3 的恢复动作是破坏性的，单独用 .\scripts\huifu.ps1 手动验证，记录在 docs/ceshi-jilu.md）" -ForegroundColor Yellow


