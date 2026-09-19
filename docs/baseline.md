# 基线说明（实验03）

## 一、上游选型与理由

| 项 | 值 |
| --- | --- |
| 上游项目 | Shlink |
| 上游地址 | https://github.com/shlinkio/shlink |
| 固定版本 | **5.1.6** |
| 上游许可证 | MIT |
| 官方镜像 | `shlinkio/shlink:5.1.6` |
| 数据库镜像 | `postgres:16.14-alpine` |

**为什么选 Shlink**：实验要求以成熟开源项目为基线，重点放在编排、集成和扩展。
Shlink 已经把短码生成、重定向、访问记录这些核心能力做完了（PHP + RoadRunner + SQL），
我可以把精力花在自己该做的事上——Web 管理界面、服务端密钥隔离、规则校验、
Dockerfile 和扩展测试。自己从零写一个短链服务只能证明我会写 CRUD，
证明不了我会「用开源项目搭系统」。

**为什么不选 `stable` / `latest`**：这两个标签会移动。今天验证过的行为，
明天拉到的可能是另一个版本。所以镜像标签写死到小版本。

## 二、基线启动前必须确定的事

| 项 | 取值 | 理由 |
| --- | --- | --- |
| `DEFAULT_DOMAIN` | `localhost:8080` | 短链的对外域名，必须和实际访问地址一致，否则生成的短链点不开 |
| `IS_HTTPS_ENABLED` | `false` | 本地 http，设 true 生成的是 https 短链 |
| `AUTO_RESOLVE_TITLES` | `false` | 关掉。否则 Shlink 会去服务器端抓 localhost 长链，抓不到还刷错误日志 |
| `SKIP_INITIAL_GEOLITE_DOWNLOAD` | `true` | 跳过 GeoLite 下载，离线也能起来。代价：没有 IP 地理定位 |
| Shlink 端口 | `127.0.0.1:8080:8080` | 只绑回环，管理 API 不暴露到局域网 |
| Web 端口 | `127.0.0.1:8501:8501` | 同上 |

## 三、环境

| 软件 | 要求 | 本机 |
| --- | --- | --- |
| Docker Engine / Desktop | 25+ | **未安装**（见第四节） |
| Docker Compose | v2 | **未安装** |
| Git | 2.40+ | 2.54.0.windows.1 |
| Python | 3.11+ | 3.13.14 |
| Node.js | 非必需 | 22.22.2 |

## 四、★ 未验证边界（如实记录）

**本次开发机器上没有 Docker**，所以下面这些只能保证「写法对照文档核对过」，
**不能**说成「已在本机实测」：

- `docker compose up -d` 三个服务真正启动并变 healthy
- 容器删除重建后短链与访问记录保留
- `scripts/ceshi-api.ps1`、`scripts/ceshi-bushu.ps1` 的运行输出

已经**实际执行并留下证据**的：

| 项 | 命令 | 结果 |
| --- | --- | --- |
| Web 层自动化测试 | `.\.venv\Scripts\python -m pytest tests -q` | **68 passed in 6.90s** |
| Python 版本 | `python --version` | 3.13.14 |
| 镜像标签存在性 | 核对 Docker Hub | `5.1.6` / `16.14-alpine` 均存在 |
| Compose 语法 | 对照 5.1.6 文档逐项核对环境变量名 | 变量名与文档一致 |

这个做法和指导书里写的边界口径一致：
「本机没有 Docker，未执行容器启动、短链跳转和数据卷重建，
不将文档核对表述为容器实测。」

## 五、目录职责

| 目录 | 谁负责 | 说明 |
| --- | --- | --- |
| `web/` | 本人 | 管理台、校验、限流、Shlink 客户端 |
| `compose.yaml` | 本人 | 三服务编排、网络、卷、健康检查 |
| `scripts/` | 本人 | 启动/停止/备份/恢复/测试/清理 |
| `tests/` | 本人 | 68 条 pytest |
| `demo-target/` | 本人 | 离线演示用长网址目标 |
| shlink 镜像内部 | 上游 | 短码生成、重定向、访问记录 |
| postgres 镜像内部 | 上游 | 数据存储 |
