# Issue #2 短链主流程打通

**标签**：`核心功能`

## 用户价值

用户输一个长网址，能拿到一条短链；点短链能跳回去；能查到被点了几次。
这是本实验的 MVP，做不出来后面都不用谈。

## 验收条件

- [x] Compose 能起 db + shlink 两个服务，Shlink 健康检查为 pass
- [x] 长 URL 校验：协议只允许 http/https，host 必须命中白名单
- [x] 创建短链走 `POST /rest/v3/short-urls`
- [x] 访问短链返回 302 且 Location 正确
- [x] 能查访问次数
- [x] 非法协议、空输入、白名单外、未知短码、重复短码各有明确反馈
- [x] 浏览器 F12 里看不到 `X-Api-Key`

## 关键技术决策

**决策：浏览器不直接调 Shlink。**

Shlink 管理 API 需要 `X-Api-Key`。让浏览器直接调，密钥就必须下发到前端，
F12 一看就有。改成服务端代理，浏览器只跟我们自己的 `/api/*` 说话。

**决策：短链跳转不经过 Web 服务。**

高频路径不该穿过 Flask。访问者直打 Shlink 的 8080，统计也在那里写库。

**决策：容器内用服务名 `http://shlink:8080`。**

容器里的 `localhost` 是它自己。这是本实验最容易踩的坑。

## 涉及的文件

- `compose.yaml`
- `web/url_yanzheng.py`、`web/shlink_kehuduan.py`、`web/app.py`
- `web/templates/index.html`、`web/static/*`

## 结果

已完成。相关测试在 `tests/test_web.py`，不需要 Docker 即可运行。

**过程记录**：写完之后才发现 `app.py` 用模块级 `app` 导致测试没法注入假客户端，
改成了工厂函数 `chuangjian_app()`。
