# 个人开发过程与 Git 证据对照表（实验03）

仓库：https://github.com/remchang/shlink-shorturl-platform

---

## 一、Issue 与任务拆解

| Issue | 标题 | 内容 | 关联 Commit |
| --- | --- | --- | --- |
| #1 | 基线选型与环境准备 | 固定 Shlink 5.1.6 / postgres 16.14-alpine，确定端口、白名单、`.env` 结构 | `chore: 固定基线版本…` |
| #2 | 短链主流程打通 | Compose 编排 + Flask 管理台 + 校验层 + Shlink 客户端 | `feat(web): …` |
| #3 | 自主功能：二维码与有效期 | 二维码生成下载、有效期天数与上限 | `feat(ext): …` |
| #4 | 自主功能：创建频率限制 + 测试与文档 | 滑动窗口限流、68 条 pytest、README 与报告 | `feat(xianzhi): …` / `test: …` / `docs: …` |

Issue 正文留档在 `docs/issue/`。

## 二、Commit 对照表

> 实际 SHA 见 `git log --oneline`。下表按提交顺序。

| 序号 | 类型 | 覆盖阶段 | 主要内容 |
| --- | --- | --- | --- |
| 1 | `chore` | 基线 | 固定镜像标签、`.env.example`、`.gitignore`、LICENSE、NOTICE |
| 2 | `feat(compose)` | 核心功能 | `compose.yaml`：三服务、命名卷、健康检查、depends_on 条件 |
| 3 | `feat(web)` | 核心功能 | Flask 管理台、校验层、Shlink 客户端、前端页面 |
| 4 | `feat(ext)` | 自主功能 | 二维码、有效期上限 |
| 5 | `feat(xianzhi)` | 自主功能 | 滑动窗口频率限制 + 非法请求也计数 |
| 6 | `test` | 测试 | conftest 假 Shlink、68 条 pytest |
| 7 | `docs` | 文档 | README、接口表、测试记录、实验报告、Issue |

覆盖了实验要求的五类：**基线 / 核心功能 / 自主功能 / 测试 / 文档**。

## 三、分支与 PR

```powershell
git switch -c feature/shortlink-extension
# …开发…
git push -u origin feature/shortlink-extension
```

- 特性分支：`feature/shortlink-extension`
- PR：关联 Issue #2 #3 #4，PR 描述里附了 `pytest` 输出和接口示例
- 合并前完成了**一次有文字记录的自我 Code Review**，见下节

验证命令：

```powershell
git log --oneline --graph --decorate --all -n 30
git shortlog -sne HEAD
```

## 四、自我 Code Review 检查清单（合并前逐项过）

| # | 检查项 | 结论 |
| --- | --- | --- |
| 1 | API Key 有没有出现在任何前端文件里？ | ✅ 没有。`test_qianmian_ye_meiyou_api_key` 断言首页/JS/CSS 全文无 `X-Api-Key` |
| 2 | 容器里访问 Shlink 用的是服务名还是 localhost？ | ✅ `http://shlink:8080`，`ceshi-bushu.ps1` C5 有断言 |
| 3 | 镜像标签是不是写死的具体版本？ | ✅ `5.1.6` / `16.14-alpine` / `python:3.12.7-slim` |
| 4 | 有没有 `sleep` 等启动的写法？ | ✅ 没有，用 `depends_on: condition: service_healthy` |
| 5 | 数据库口令有没有硬编码？ | ✅ 只走 `.env` → 环境变量 |
| 6 | 用户输入的 URL 有没有直接拼进 HTML？ | ✅ 前端所有接口文本都过 `zhuanYi()`，用 `execCommand` 兜底剪贴板 |
| 7 | 白名单比对会不会被前缀伪造绕过？ | ✅ 用 hostname 等于/子域比对，有反例测试 |
| 8 | 限流放在校验之前还是之后？ | ✅ 之前（否则非法请求白嫖配额） |
| 9 | 错误提示是不是中文、能不能照着修？ | ✅ 400/409/429/500/502 各有一句可操作的中文 |
| 10 | `.env` 有没有被 `.gitignore` 排除？ | ✅ `git check-ignore -v .env` 有输出 |
| 11 | 单元测试需不需要 Docker？ | ✅ 不需要，假 Shlink 客户端替代 |
| 12 | 有没有把上游的能力写成自己的成果？ | ✅ 没有，README 和 NOTICE 里明确区分了 |

## 五、我踩过的坑（写进报告更有说服力）

1. **分页字段在嵌套里**：Shlink 的 `totalPages` 藏在 `shortUrls.pagination`，
   按顶层读会一直 `undefined`，翻页按钮永远点不动。
2. **白名单被前缀伪造绕过**：`startswith` 挡住了 `www.baidu.com`，
   但放过了 `evil-localhost.com`。改成按 hostname 比对并加了反例测试。
3. **限流顺序错了**：放在校验之后就等于没限，因为非法请求提前 return 了。
4. **HEAD 不计数**：`curl -I` 测统计永远是 0，是测试方法的问题不是代码的问题，
   已经写进 README 的统计口径。
5. **`localhost` 在容器里是它自己**：这是本实验最经典的坑，
   Web 容器里写 `127.0.0.1:8080` 会连到 Web 自己身上。
