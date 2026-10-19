# SelfDesk · Spring AI 客服系统定制层

在开源客服系统 [bytedesk](https://github.com/Bytedesk/bytedesk) 之上做的一层**可运行的业务侧定制**：
自写客服工作台、运营仪表盘、统一的品牌与视觉层，以及一键启停 / AI 网关 / 打包补丁。

AI 部分由 **Spring AI** 负责：模型可配多厂商，也可以一键切到本地 Python 编排层（见 [docs/SPRING-AI.md](docs/SPRING-AI.md)）。

![客服工作台](docs/screenshots/agent-console.png)

> 本仓库只包含定制层，不含上游源码与 fat jar。上游许可见 [NOTICE.md](NOTICE.md)（AGPL-3.0）。

---

## 目录

- [界面](#界面)
- [这一层做了什么](#这一层做了什么)
- [架构](#架构)
- [快速开始](#快速开始)
- [打包与部署](#打包与部署)
- [视觉规范](#视觉规范)
- [已知限制](#已知限制)

---

## 界面

| 页面 | 地址 | 说明 |
|---|---|---|
| 访客端 | `http://127.0.0.1:9003/chat/` | 上游自带，套了统一主题 |
| 客服工作台 | `http://127.0.0.1:9003/console/` | **自写**，实时会话、搜索、筛选 |
| 运营仪表盘 | `http://127.0.0.1:8002/` | **自写**，聚合 `/api/v1`，含 AI 用量与费用 |
| 管理后台 | `http://127.0.0.1:9003/admin` | 上游 AntD，套了主题与免密 |
| 坐席移动端 | `http://127.0.0.1:9003/agent/` | 上游自带 |

![运营仪表盘](docs/screenshots/ops-dashboard.png)

![管理后台](docs/screenshots/admin-models.png)

## 这一层做了什么

**1. 客服工作台（`console/`）**
纯静态页（HTML + CSS + 原生 JS），直接调 `/api/v1`，不依赖前端框架：

- 会话列表：搜索、进行中/全部筛选、未读计数
- 消息区：访客/机器人/坐席三种气泡、系统消息、时间
- 回复：Enter 发送、Shift+Enter 换行、失败 toast
- 令牌复用：从同一浏览器的登录态里取 token，取不到才显示登录

**2. 运营仪表盘（`dashboard/`）**
Python 标准库写的轻量聚合服务，零第三方依赖：

- 会话趋势、状态分布、渠道、工作组负载
- AI 用量与费用：解析应用日志里的 token 事件，按 DeepSeek 单价估算
- 30 秒自动刷新，服务端缓存登录令牌

**3. 品牌与主题层（`admin-patch/`）**
- `selfdesk-brand.js`：运行时给 AntD 后台注入一套 CSS token（主色、圆角、表格、菜单、标签…），并清理上游品牌文案
- `selfdesk-admin-dash.js`：把后台首页的「许可检测」占位页替换成仪表盘 iframe（只在该首页挂载）

**4. 运维脚本（`scripts/`）**
- `selfdesk.ps1`：一键拉起 ES / Redis / Embedding / 应用 / 仪表盘
- `ai-gateway.ps1`：Spring AI 的 base-url 在「直连模型」和「本地编排层」之间切换
- `patch_jar.py`：把定制层打进 fat jar，可重复执行
- `verify_selfdesk.py` / `test-selfdesk-chat.py`：冒烟测试

## 架构

```
                    ┌──────────── 9003 ────────────┐
   访客 ──► /chat/  │  上游 Spring Boot (bytedesk) │  /admin  ◄── 管理员
                    │  ├─ 会话/排队/工单/知识库     │
   坐席 ──► /console│  ├─ Spring AI（可配多厂商）   │
                    │  └─ 静态资源（本仓库注入）    │
                    └───────────┬──────────────────┘
                                │ /api/v1
                    ┌───────────▼──────────┐
                    │  8002 仪表盘（本仓库）│
                    └──────────────────────┘
```

## 快速开始

前置：Windows、JDK 21、Maven、WSL（PostgreSQL/ES 可选按你的上游部署方式）。

```powershell
# 1. 准备上游 jar（自行构建 bytedesk）
cd D:\CodexBuild\bytedesk\starter
mvn -DskipTests package

# 2. 配置本地变量
cd D:\CodexBuild\selfdesk-springai
copy .env.example .env.local
#   填 BYTEDESK_ADMIN_PASSWORD / DEEPSEEK_API_KEY

# 3. 把定制层打进 jar
python scripts\patch_jar.py

# 4. 起服务
.\scripts\selfdesk.ps1 start
```

`selfdesk.ps1` 顶部有一段路径配置（jar 位置、JDK 路径、端口），换成你自己的即可。

### 可选：本机免密

正常打开 `/admin` 需要登录。想省掉这一步：

```powershell
# 创建本地私有文件（已被 .gitignore 排除）
'{"username":"admin@email.com","password":"你的密码"}' > .selfdesk-autologin.json
python scripts\patch_jar.py    # 重新打包，凭据只进 jar，不进仓库
```

页面加载时脚本会自动填充并提交登录表单——**这个文件绝对不要提交**。

## 打包与部署

`scripts/patch_jar.py` 做的事：

1. 用 `console/` 覆盖 jar 内 `static/console/`
2. 写入 `static/selfdesk-brand.js`、`static/selfdesk-admin-dash.js`
3. 给 `static/admin/index.html` 补 `<script src="/selfdesk-brand.js" defer>`
4. 若存在 `.selfdesk-autologin.json`，把免密配置前置进 jar 内脚本

打包期间 jar 被 JVM 占用会失败：先 `.\scripts\selfdesk.ps1 stop`，打完再 start。

## 视觉规范

| token | 值 | 用途 |
|---|---|---|
| 品牌主色 | `#0E7A68` | 主按钮、选中态 |
| 人工坐席 | `#6D5AE6` | 人工身份 |
| 页面底色 | `#F1F4F3` | 页面背景 |
| 卡片 | `#FFFFFF` + `#E3E8E6` | 内容卡片 |
| 圆角 | 8 / 12 / 16 / 20 | 按钮 / 卡片 / 面板 / 浮层 |
| 字体 | Inter, Segoe UI, PingFang SC | 全局 |

后台是编译好的 AntD，无法改主题变量，`selfdesk-brand.js` 用同一套 token 做 CSS 覆盖；
自写页面（console / dashboard）直接使用同名变量，两边口径一致。

## 已知限制

- **不含上游源码**：需要自行获取 bytedesk 并构建 jar。
- **jar 补丁是覆盖式**：升级上游后需重新跑 `patch_jar.py`，否则定制层会被覆盖。
- **后台主题是 CSS 覆盖**：AntD 组件结构变化时可能需要补选择器。
- **仪表盘费用是估算**：按 DeepSeek 公开单价折算，不是账单。
- **许可**：与 AGPL-3.0 上游结合运行，本仓库同样以 AGPL-3.0 发布。
