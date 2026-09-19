# NOTICE —— 第三方代码、数据与许可证

本仓库是《开源软件与新技术》实验03 的**二次开发成品**。
上游项目的版权归各自作者所有，本人没有重新分发它们，
只是在 `compose.yaml` 里以固定版本标签引用了官方镜像。

## 一、运行时依赖（容器镜像）

| 项目 | 来源链接 | 作者 / 组织 | 本仓库用的版本 | 许可证 |
| --- | --- | --- | --- | --- |
| Shlink | https://github.com/shlinkio/shlink | Shlink.io / Alejandro Celaya | `shlinkio/shlink:5.1.6` | MIT |
| PostgreSQL | https://hub.docker.com/_/postgres | PostgreSQL Global Development Group | `postgres:16.14-alpine` | PostgreSQL License |

固定版本的依据：`shlinkio/shlink:5.1.6` 与 `postgres:16.14-alpine` 两个标签在
Docker Hub 上均存在（2026-09-09 核对）。**不使用 `stable` / `latest`**，
这两个标签会移动，无法复现。

## 二、参考过的项目（没有直接使用其代码）

| 项目 | 来源链接 | 用途 | 许可证 |
| --- | --- | --- | --- |
| docker/awesome-compose | https://github.com/docker/awesome-compose | 参考了 Web + 数据库多容器编排的结构写法 | CC0-1.0 |
| Shlink REST API 文档 | https://api-spec.shlink.io/ | 核对接口路径与字段名 | 文档，随上游 |

**说明**：`compose.yaml` 是本人在对照 awesome-compose 的样例结构后自己写的，
没有整文件复制；服务名、卷、健康检查和网络都是按本实验的需要重新组织的。

## 三、第三方 Python 库

| 库 | 来源链接 | 版本 | 许可证 | 用途 |
| --- | --- | --- | --- | --- |
| Flask | https://github.com/pallets/flask | 3.0.3 | BSD-3-Clause | Web 框架 |
| Werkzeug | https://github.com/pallets/werkzeug | 随 Flask | BSD-3-Clause | WSGI |
| requests | https://github.com/psf/requests | 2.32.3 | Apache-2.0 | 调 Shlink API |
| qrcode | https://github.com/lincolnloop/python-qrcode | 7.4.2 | BSD-3-Clause | 二维码生成 |
| Pillow | https://github.com/python-pillow/Pillow | 10.4.0 | HPND | qrcode 的图片后端 |
| gunicorn | https://github.com/benoitc/gunicorn | 22.0.0 | MIT | 生产 WSGI 服务器 |
| pytest | https://github.com/pytest-dev/pytest | 8.3.3 | MIT | 测试 |

以上依赖均为**通过 pip 正常安装的开源库**，没有复制其源码到本仓库。

## 四、数据

本实验**没有使用任何数据集**。

演示用的长网址目标是本人写的 `demo-target/demo.html`（一个静态页面），
不涉及第三方数据、不含个人信息、不含真实凭据。

## 五、图片与字体

- 界面图标使用 Unicode 字符和 CSS 绘制，没有引入图标库或字体文件。
- 样式表 `web/static/zhuti.css` 为本人手写，未使用任何 CSS 框架或模板。

## 六、本仓库的许可证

**MIT**，见 [LICENSE](LICENSE)。

选择理由：与上游 Shlink（MIT）兼容。本仓库不包含上游源码，
所以不涉及 AGPL 那种网络部署时的源码提供义务；
但如果将来直接把 Shlink 源码改后一起分发，必须保留其 MIT 许可证与版权声明。

## 七、安全声明

- 本实验**只扫描/访问本人自己搭建的本地服务**，没有对任何公网目标做过测试。
- 长 URL 白名单默认只放开 `localhost` / `127.0.0.1` / `host.docker.internal` / `shlink`。
- 仓库内不含真实 API Key、数据库口令或任何个人数据。
  `.env` 已被 `.gitignore` 排除。
