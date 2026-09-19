# Issue #1 基线选型与环境准备

**标签**：`基线` `环境`

## 背景

实验要求以成熟开源项目为基线。短网址的核心流程（URL 校验、唯一短码、
302 重定向、访问记录、统计查询、持久化）都要覆盖，但重点应该放在
**编排、集成和扩展**上，而不是从零写 CRUD。

## 要做的事

- [x] 确定上游项目与固定版本
- [x] 确定数据库镜像版本
- [x] 确定端口与长 URL 白名单
- [x] 编写 `.env.example`，真实口令只放 `.env`
- [x] 编写 `.gitignore` 把 `.env` 排除

## 选型结论

| 项 | 取值 | 理由 |
| --- | --- | --- |
| 短链 API | `shlinkio/shlink:5.1.6` | 短码、重定向、统计都现成，MIT 许可 |
| 数据库 | `postgres:16.14-alpine` | Shlink 官方支持，alpine 体积小 |
| Web 框架 | Flask 3.0.3 | 自己实现界面，不引前端框架 |
| 端口 | Shlink `127.0.0.1:8080`、Web `127.0.0.1:8501` | 都只绑回环 |

**不用 `stable` / `latest`**：标签会移动，明天拉到的就不是今天验证过的版本。

## 验收条件

- `.env.example` 里 `POSTGRES_PASSWORD` 和 `INITIAL_API_KEY` 都是占位符说明
- `git check-ignore -v .env` 有输出
- 两个镜像标签在 Docker Hub 上确认存在

## 结果

已完成。`docs/baseline.md` 记录了完整的选型与环境说明。

**发现的限制**：本机没有安装 Docker，容器相关验证无法在本机完成，
已如实记录在 `docs/baseline.md` 第四节。
