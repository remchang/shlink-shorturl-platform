# 接口表（实验03）

分两层：**自己对外的接口**（浏览器调）和**调 Shlink 的接口**（服务端内部）。

---

## 一、对外接口（浏览器 → 我们的 Web 服务）

基地址：`http://localhost:8501`

所有响应都是 JSON，统一带 `ok` 字段。失败时 `ok=false` 且有 `xiaoxi`。

| # | 方法 | 路径 | 作用 | 成功 | 失败码 |
| --- | --- | --- | --- | --- | --- |
| A1 | GET | `/` | 管理台页面 | 200 HTML | — |
| A2 | GET | `/api/jiankang` | 健康检查（分别报 Web 和 Shlink） | 200 | — |
| A3 | GET | `/api/peizhi` | 公开配置（白名单、各项上限） | 200 | — |
| A4 | POST | `/api/duanlian` | 创建短链 | 200 | 400 / 409 / 429 / 500 / 502 |
| A5 | GET | `/api/duanlian` | 短链列表（分页） | 200 | 502 |
| A6 | GET | `/api/duanlian/{duanma}/tongji` | 单条统计 | 200 | 404 / 502 |
| A7 | DELETE | `/api/duanlian/{duanma}` | 删除短链 | 200 | 404 / 502 |
| A8 | GET | `/api/erweima/{duanma}` | 二维码 PNG | 200 | 404 / 500 |
| A9 | GET | `/api/huizong` | 汇总数字 | 200 | 502 |

### A4 创建短链 —— 请求

`Content-Type: application/json`（也接受表单）：

```json
{
  "chang_url": "http://localhost:9001/demo.html",
  "zidingyi_duanma": "demo01",
  "youxiao_tianshu": 30
}
```

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `chang_url` | string | 是 | 非空；≤2048 字符；协议必须是 http/https；host 必须命中白名单 |
| `zidingyi_duanma` | string | 否 | 空 = 自动生成；否则 3~32 位 `A-Za-z0-9-_`，不能是系统保留字 |
| `youxiao_tianshu` | int | 否 | 0 或空 = 永久；范围 0~365 |

### A4 创建短链 —— 响应

```json
{
  "ok": true,
  "duan_url": "http://localhost:8080/demo01",
  "duanma": "demo01",
  "chang_url": "http://localhost:9001/demo.html",
  "chuangjian_shijian": "2026-09-19T10:00:00+08:00",
  "youxiaoqi_tianshu": 30,
  "shengyu_cishu": 19
}
```

### 错误码约定

| HTTP | 含义 | 触发条件 | `xiaoxi` 例子 |
| --- | --- | --- | --- |
| 400 | 我们自己的校验不通过 | 空输入、协议不对、超长、白名单外、短码非法、有效期越界 | 「域名 www.baidu.com 不在白名单内（本实验只允许本地/授权目标）」 |
| 404 | 短码不存在 | 查/删一个不存在的短码 | 「没有找到短码 zzz」 |
| 409 | 短码冲突 | 自定义短码已被占用 | 「短码 demo01 已经被占用了，换一个吧」 |
| 429 | 触发限流 | 同 IP 在 60s 内超过 20 次 | 「创建太频繁了，请 37 秒后再试」 |
| 500 | 服务端配置问题 | API Key 无效等 | 「服务端 API Key 无效，请检查 .env 里的 INITIAL_API_KEY」 |
| 502 | 依赖不可用 | 连不上 Shlink | 「创建失败：连不上 Shlink，服务可能没起来或地址配错了」 |
| 504 | Shlink 响应超时 | 读超时 | 「Shlink 响应超时，稍后重试」 |

> **设计取舍**：把 400 和 409 分开，是因为这两件事对用户的意义完全不同——
> 400 是「你写错了」，改输入就行；409 是「你来晚了」，得换个短码。
> 统一返回 400 会让用户一脸懵。

---

## 二、内部调用接口（我们的 Web → Shlink REST API）

基地址：`http://shlink:8080`（容器内必须用服务名）
认证：请求头 `X-Api-Key: <INITIAL_API_KEY>`，**只在服务端发出**。

| # | 方法 | 路径 | 用途 |
| --- | --- | --- | --- |
| S1 | GET | `/rest/health` | 健康检查，期望 `status=pass` |
| S2 | POST | `/rest/v3/short-urls` | 创建短链 |
| S3 | GET | `/rest/v3/short-urls` | 列表（`page` / `itemsPerPage` / `orderBy`） |
| S4 | GET | `/rest/v3/short-urls/{shortCode}` | 单条详情 |
| S5 | GET | `/rest/v3/short-urls/{shortCode}/visits` | 访问记录 |
| S6 | DELETE | `/rest/v3/short-urls/{shortCode}` | 删除 |

### S2 请求体（我们用到的字段）

```json
{
  "longUrl": "http://localhost:9001/demo.html",
  "customSlug": "demo01",
  "validUntil": "2026-10-19T02:00:00Z"
}
```

| Shlink 字段 | 来自我们的哪个参数 | 备注 |
| --- | --- | --- |
| `longUrl` | `chang_url` | — |
| `customSlug` | `zidingyi_duanma` | 为空就不传这个 key |
| `validUntil` | `youxiao_tianshu` | 换算成 UTC、`Z` 结尾的 ISO8601 |

### S2 响应（我们读的字段）

```json
{
  "shortCode": "demo01",
  "shortUrl": "http://localhost:8080/demo01",
  "longUrl": "http://localhost:9001/demo.html",
  "dateCreated": "2026-09-19T10:00:00+08:00",
  "visitsSummary": { "total": 0 },
  "meta": { "isValid": true }
}
```

### S3 响应结构（注意是嵌套的）

```json
{
  "shortUrls": {
    "data": [ { "shortCode": "...", "visitsSummary": { "total": 3 } } ],
    "pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 25 }
  }
}
```

**踩过的坑**：分页不在顶层，在 `shortUrls.pagination` 里。
一开始按顶层读 `totalPages`，拿不到就一直 `undefined`，翻页按钮永远点不动。

### S5 响应结构

```json
{
  "visits": {
    "data": [
      { "date": "2026-09-19T11:00:00+08:00", "referer": null, "userAgent": "Mozilla/5.0 ..." }
    ],
    "pagination": { "currentPage": 1, "totalPages": 1, "totalItems": 3 }
  }
}
```

### Shlink 的错误响应

```json
{ "type": "https://shlink.io/api/error/invalid-data", "title": "Invalid data", "detail": "Provided short code is already in use" }
```

我们只把 `detail` 挑出来翻译，不把整段英文糊给用户。

---

## 三、短链跳转（不经过我们的服务）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `http://localhost:8080/{短码}` | Shlink 直接返回 302 + `Location: <长网址>` |

**统计口径**：只有 GET 才计数。`curl -I` 发的是 HEAD，不算一次访问。
访问记录异步落库，跳转完立刻查可能还是旧值。

---

## 四、自主功能涉及的数据字段

| 自主功能 | 用到的字段 | 谁产生的 |
| --- | --- | --- |
| 二维码 | `shortUrl`（S4 响应） | 上游 |
| 有效期 | `validUntil`（S2 请求）/ `validUntil`、`meta.isValid`（S3 响应） | 上游 |
| 创建限流 | 无需 API 字段，按客户端 IP + 请求时间戳在进程内计算 | **本人** |
