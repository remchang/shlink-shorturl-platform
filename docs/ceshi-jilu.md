# 测试记录（实验03）

> 所有命令都在项目根目录执行。PowerShell 环境。
> **口径声明**：下面「实测」部分是真跑出来的；带 ⚠️ 标记的是本机没有 Docker、
> 只完成写法核对、未在本机实跑的，不能当实测结果引用。

---

## 一、自动化测试（实测 ✅）

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r web\requirements.txt
.\.venv\Scripts\python -m pytest tests -q
```

**实际输出：**

```
....................................................................     [100%]
68 passed in 6.90s
```

环境：Windows，Python 3.13.14，pytest 8.3.3。

### 测试文件分布

| 文件 | 条数 | 覆盖 |
| --- | --- | --- |
| `tests/test_url_yanzheng.py` | 25 | 长 URL 协议/长度/白名单、自定义短码、有效期 |
| `tests/test_xianzhi.py` | 6 | 滑动窗口限流、窗口过期、非法配置兜底 |
| `tests/test_web.py` | 37 | 页面、健康、创建、错误分支、列表、统计、二维码、限流、密钥外泄 |
| **合计** | **68** | |

### 部分关键用例与它的意义

| 用例 | 断言什么 | 为什么要有 |
| --- | --- | --- |
| `test_weizao_qianzhui_de_yuming_bei_jujue` | `evil-localhost.com` 被拒，`a.localhost` 通过 | 白名单用 `startswith` 会漏，必须按 hostname 比对 |
| `test_weixian_xieyi_bei_jujue` | `javascript:` / `data:` / `vbscript:` / `ftp:` / `file:` 全被拒 | 短链当跳板是真实攻击面 |
| `test_duanma_chongfu_fanhui_409` | 重复短码返回 409 且提示含「占用」 | 区分「输入错」(400) 和「来晚了」(409) |
| `test_feifa_qingqiu_yie_ji_ru_xianzhi` | 两次非法请求之后第三次合法请求被 429 | 非法请求也要计数，否则配额可被白嫖 |
| `test_qianmian_ye_meiyou_api_key` | 首页 HTML、JS、CSS 全文搜不到 `X-Api-Key` | 实验明确要求「浏览器 Network 面板中不存在 API Key」 |
| `test_gongkai_peizhi_li_meiyou_api_key` | `/api/peizhi` 只回白名单和上限 | 防止图省事把整个配置对象丢给前端 |
| `test_youxiaoqi_chuandao_kehuduan` | 断言假客户端收到了 `youxiao_tianshu=7` | 防止「只在界面上放个控件、参数根本没传下去」 |
| `test_erweima_fanhui_png` | 校验响应前 8 字节是 PNG 魔数 | 确认真返回图片，不是一段报错 JSON |

---

## 二、现场手工验证（实测 ✅）

### 2.1 直接跑 Flask 开发服务器，打接口

```powershell
cd web
$env:SHLINK_JICHU_URL="http://127.0.0.1:8080"
$env:SHLINK_API_KEY="test-key"
..\.venv\Scripts\python app.py
```

```powershell
Invoke-RestMethod http://127.0.0.1:8501/api/jiankang | ConvertTo-Json
```

结果（Shlink 没起来时的健康灯行为）：

```json
{
  "ok": true,
  "web": "ok",
  "shlink": "bad",
  "shlink_shuoming": "Shlink 不可达：HTTPConnectionPool(host='127.0.0.1', port=8080): Max retries exceeded",
  "api_key_yi_peizhi": true
}
```

**这一步验证了**：Shlink 挂掉时，Web 服务自己不会跟着 500，
而是明确告诉你「Shlink 是坏的」，界面上对应的灯变红。
这正是把两个健康状态分开报的价值。

### 2.2 校验层的手工反例

```powershell
.\.venv\Scripts\python -c "import sys; sys.path.insert(0,'web'); from url_yanzheng import jianyan_chang_url as j; print(j('http://www.baidu.com', ['localhost']))"
```

```
(False, '域名 www.baidu.com 不在白名单内（本实验只允许本地/授权目标）')
```

---

## 三、API 功能测试（⚠️ 需要 Docker，未在本机实跑）

脚本：`scripts\ceshi-api.ps1`，直接打 Shlink REST API，不经过我们的 Web 服务。

| 编号 | 用例 | 期望 |
| --- | --- | --- |
| T01 | `GET /rest/health` | `status=pass` |
| T02 | 创建短链（自动短码） | 返回 `shortCode` / `shortUrl` |
| T03 | 访问短链 | HTTP 302，`Location` 指向原长网址 |
| T04 | 自定义短码 `shiyan03` | 返回短码就是 `shiyan03` |
| T05 | 重复自定义短码 | 被拒，HTTP 400 |
| T06 | 对同一短链发 3 次真实 GET | （准备数据） |
| T07 | 查访问统计 | `totalItems ≥ 3` |
| T08 | 短链列表 | 至少 2 条 |
| T09 | 查询未知短码 | HTTP 404 |
| T10 | 不带 `X-Api-Key` 读列表 | HTTP 401 |

**怎么跑**：

```powershell
.\scripts\qidong.ps1
.\scripts\ceshi-api.ps1
```

---

## 四、容器测试 C1–C5（⚠️ 未在本机实跑）

脚本：`scripts\ceshi-bushu.ps1`

| 编号 | 检查点 | 通过标准 |
| --- | --- | --- |
| C1 | 干净构建 | `docker compose build web --no-cache` 退出码 0 |
| C2 | 三个服务运行 | `running` 数量 = 3 |
| C3 | 健康检查 | `healthy` 服务数 ≥ 2 |
| C4 | 服务间互通 | 在 `web` 容器里访问 `http://shlink:8080/rest/health` 得到 200 |
| C5 | 没有硬编码 localhost | `docker compose config` 展开后 `SHLINK_JICHU_URL` 含 `shlink:8080` |

**C4 为什么这么写**：容器里的 `localhost` 是它自己，
所以必须在 `web` 容器**内部**去请求 `shlink`，才能证明 Compose 网络和服务名解析是对的。
在宿主机上测是测不出来的。

---

## 五、持久化测试 P1–P3（⚠️ 未在本机实跑）

| 编号 | 检查点 | 通过标准 |
| --- | --- | --- |
| P1 | `down` + `up` 之后短链还在 | 仍能查到 `chijiuhua`，长网址一致 |
| P2 | `down` + `up` 之后访问次数还在 | 重建后次数 ≥ 重建前次数 |
| P3 | 备份可用 | `beifen.ps1` 生成非空 `.sql`，记录 SHA256 |

**为什么备份用 `pg_dump` 而不是直接拷数据目录**：
容器运行中直接拷贝 `/var/lib/postgresql/data` 可能拿到不一致的状态
（写到一半的文件）。`pg_dump` 是逻辑备份，导出的是一致快照。

恢复验证（破坏性，要手动确认）：

```powershell
.\scripts\huifu.ps1 -Wenjian beifen\duanlian-20260919-xxxxxx.sql
# 输入 yes → 恢复后核对表行数：
#   SELECT COUNT(*) FROM short_urls;
#   SELECT COUNT(*) FROM visits;
```

---

## 六、安全边界测试（汇总）

| 检查点 | 用例 | 结果 |
| --- | --- | --- |
| 非法协议被拒 | `test_weixian_xieyi_bei_jujue`（5 种协议） | ✅ 通过 |
| 超长 URL 被拒 | `test_chaochang_url_bei_jujue`（3000 字符） | ✅ 通过 |
| 白名单外被拒 | `test_baimingdan_wai_yuming_bei_jujue` | ✅ 通过 |
| 白名单前缀伪造被拒 | `test_weizao_qianzhui_de_yuming_bei_jujue` | ✅ 通过 |
| Key 不在前端 | `test_qianmian_ye_meiyou_api_key` | ✅ 通过 |
| Key 不在公开配置接口 | `test_gongkai_peizhi_li_meiyou_api_key` | ✅ 通过 |
| 无 Key 访问管理 API 被拒 | `ceshi-api.ps1` T10 | ⚠️ 待 Docker |
| `.env` 不进 Git | `git check-ignore .env` | ✅ 通过（见下） |

`.env` 排除验证：

```powershell
git check-ignore -v .env
# .gitignore:3:.env    .env
```

---

## 七、失败用例与修复记录

### 失败 1：分页永远翻不动

- **现象**：列表只显示第 1 页，点「下一页」没反应，`zongYeShu` 一直是 1。
- **原因**：一开始按顶层读 `ti.totalPages`，但 Shlink 把分页放在
  `shortUrls.pagination` 里嵌着。顶层没有这个字段，取到 `undefined`。
- **定位方式**：`Invoke-RestMethod ... | ConvertTo-Json -Depth 10` 把完整响应打出来，
  才发现结构是嵌套的。
- **修复**：改成 `qu_kuai.get("pagination")`，并加了 `or {}` 兜底。
- **回归**：`test_liebiao_han_ziduan` 断言 `qingdan` 和 `fenye` 字段都存在。

### 失败 2：白名单被 `evil-localhost.com` 绕过

- **现象**：写了 `if zhuji.startswith(tiaomu)`，结果 `evil-localhost.com` 通过了检查。
- **原因**：`startswith` 只比字符串前缀，不管域名边界。
- **修复**：改成 `zhuji == tiaomu or zhuji.endswith("." + tiaomu)`。
- **回归**：`test_weizao_qianzhui_de_yuming_bei_jujue`，
  同时断言正向的 `a.localhost` 仍能通过（防止修过头）。

### 失败 3：限流可以被非法请求白嫖

- **现象**：原本把限流放在参数校验**之后**，结果发一堆非法请求不会消耗配额。
- **原因**：逻辑顺序错了，校验先返回 400，压根走不到限流。
- **修复**：把 `xianzhi_qi.yunxu()` 提到最前面。
- **回归**：`test_feifa_qingqiu_yie_ji_ru_xianzhi`。

### 失败 4：`curl -I` 测统计一直是 0

- **现象**：用 `curl -I` 发请求后查统计，怎么等都是 0。
- **原因**：`-I` 发的是 HEAD 请求。Shlink 只把 GET 记为一次访问。
- **修复**：不是代码问题，是测试方法问题。改用浏览器或 `curl` 不带 `-I`，
  并把这条写进 README 的「统计口径」一节，免得别人也踩。

---

## 八、测试证据清单（提交材料对照）

| 要求的证据 | 在哪 |
| --- | --- |
| 三个服务的 `docker compose ps` 与健康/日志摘要 | ⚠️ 待 Docker，脚本已备 |
| 短码、GET 次数、统计结果对照表 | `ceshi-api.ps1` T03/T06/T07 |
| 容器重建前后同一短链的查询结果 | `ceshi-bushu.ps1` P1/P2 |
| Web Network 面板中不存在 API Key 的检查 | `test_qianmian_ye_meiyou_api_key`（自动化）+ 手工 F12 复核 |
| 可重复执行的测试命令 | `pytest -q`（已实测）+ `ceshi-api.ps1` / `ceshi-bushu.ps1` |
