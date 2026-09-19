<#
============================================================
 ceshi-api.ps1 —— 对着真实 Shlink 跑一遍 REST 主流程（API 功能测试）

 这是在「已经有容器在跑」的前提下用的，直接打 Shlink 的 REST API，
 不经过我们自己的 Web 服务。目的是把 API 层的问题和 Web 层的问题分开。

 API Key 从 .env 读，不写死在脚本里，也不打印出来。
============================================================
#>
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# 从 .env 读 Key（只在这次会话的内存里）
$huanjing = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $huanjing[$matches[1]] = $matches[2].Trim() }
}
$key = $huanjing["INITIAL_API_KEY"]
$jichu = "http://localhost:8080"
$tou = @{ "X-Api-Key" = $key; "Content-Type" = "application/json" }

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

Write-Host "===== API 功能测试（T01-T10）=====" -ForegroundColor Cyan

# T01 健康检查
$jiankang = Invoke-RestMethod "$jichu/rest/health"
Pan "T01 健康检查" ($jiankang.status -eq "pass") "GET /rest/health 返回 $($jiankang.status)"

# T02 创建短链（自动短码）
$ti2 = Invoke-RestMethod -Method Post -Uri "$jichu/rest/v3/short-urls" -Headers $tou `
    -Body (@{ longUrl = "http://localhost:9001/demo.html" } | ConvertTo-Json)
Pan "T02 创建短链" ($null -ne $ti2.shortCode) "短码=$($ti2.shortCode) 短链=$($ti2.shortUrl)"

# T03 访问短链应 302 且 Location 对
try {
    $tiao = Invoke-WebRequest -Uri $ti2.shortUrl -MaximumRedirection 0 -ErrorAction SilentlyContinue
    $ma = $tiao.StatusCode
    $weizhi = $tiao.Headers.Location
} catch {
    $ma = [int]$_.Exception.Response.StatusCode
    $weizhi = $_.Exception.Response.Headers.Location
}
Pan "T03 短链跳转" ($ma -eq 302 -and "$weizhi" -like "*demo.html*") `
    "HTTP $ma  Location=$weizhi"

# T04 自定义短码
$ti4 = Invoke-RestMethod -Method Post -Uri "$jichu/rest/v3/short-urls" -Headers $tou `
    -Body (@{ longUrl = "http://localhost:9001/demo.html"; customSlug = "shiyan03" } | ConvertTo-Json)
Pan "T04 自定义短码" ($ti4.shortCode -eq "shiyan03") "短码=$($ti4.shortCode)"

# T05 重复短码应被拒
try {
    Invoke-RestMethod -Method Post -Uri "$jichu/rest/v3/short-urls" -Headers $tou `
        -Body (@{ longUrl = "http://localhost:9001/demo.html"; customSlug = "shiyan03" } | ConvertTo-Json) | Out-Null
    Pan "T05 重复短码被拒" $false "居然创建成功了"
} catch {
    Pan "T05 重复短码被拒" ([int]$_.Exception.Response.StatusCode -eq 400) `
        "HTTP $([int]$_.Exception.Response.StatusCode)"
}

# T06 访问 3 次（真实 GET，不是 HEAD）
for ($i = 0; $i -lt 3; $i++) {
    try { Invoke-WebRequest -Uri "http://localhost:8080/shiyan03" -MaximumRedirection 0 -ErrorAction SilentlyContinue } catch {}
}
Start-Sleep -Seconds 6   # 统计是异步落库的，等一会儿再查

# T07 访问统计
$tongji = Invoke-RestMethod "$jichu/rest/v3/short-urls/shiyan03/visits" -Headers $tou
$cishu = $tongji.visits.pagination.totalItems
Pan "T07 访问计数" ($cishu -ge 3) "查到的访问次数=$cishu（发了 3 次 GET）"

# T08 列表接口
$liebiao = Invoke-RestMethod "$jichu/rest/v3/short-urls" -Headers $tou
Pan "T08 短链列表" ($liebiao.shortUrls.data.Count -ge 2) `
    "共 $($liebiao.shortUrls.pagination.totalItems) 条"

# T09 未知短码
try {
    Invoke-RestMethod "$jichu/rest/v3/short-urls/zzzzbucunzai/visits" -Headers $tou | Out-Null
    Pan "T09 未知短码" $false "居然返回了 200"
} catch {
    Pan "T09 未知短码" ([int]$_.Exception.Response.StatusCode -eq 404) `
        "HTTP $([int]$_.Exception.Response.StatusCode)"
}

# T10 无 Key 访问管理接口应 401
try {
    Invoke-RestMethod "$jichu/rest/v3/short-urls" -Headers @{} | Out-Null
    Pan "T10 无 Key 被拒" $false "没带 Key 也读到了列表，密钥边界有问题"
} catch {
    Pan "T10 无 Key 被拒" ([int]$_.Exception.Response.StatusCode -eq 401) `
        "HTTP $([int]$_.Exception.Response.StatusCode)"
}

Write-Host ""
Write-Host "结果：通过 $tongguo 项，失败 $shibai 项" -ForegroundColor $(if ($shibai -eq 0) { "Green" } else { "Red" })
if ($shibai -gt 0) { exit 1 }


