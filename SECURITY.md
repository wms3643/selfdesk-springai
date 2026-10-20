# 安全说明

## 不会提交的内容

以下文件已在 `.gitignore` 中，提交前请确认：

| 文件 | 内容 |
|---|---|
| `.env.local` | 管理员密码、模型密钥 |
| `.deepseek-key` | 模型密钥 |
| `.selfdesk-autologin.json` | 本机免密用的账号密码 |
| `*.jar` | 上游构建产物 |
| `runtime/`、`logs/` | 运行期数据与日志 |

CI 会扫描 `sk-` 长串与私钥块，并检查上述文件是否被跟踪。

## 演示免密（默认开启）

构建时 `SELFDESK_DEMO_AUTOLOGIN` 默认为 `1`：`scripts/patch_jar.py` 会把演示账号写入 jar 内的
`selfdesk-brand.js`，后台登录页自动填入并提交，访问 `/admin` 无需输入密码。

- 只适合本地演示；对外部署前用 `SELFDESK_DEMO_AUTOLOGIN=0` 重新打补丁
- 密码取自 `SELFDESK_DEMO_PASSWORD`，应与首次建库的 `BYTEDESK_ADMIN_PASSWORD` 一致
- 该凭据是**已知的演示值**，不要当作安全机制

## 免密的边界

`.selfdesk-autologin.json` 会把凭据写进 jar，只适合本机演示。

- 不要提交该文件
- 不要把打了免密的 jar 分发出去
- 公网部署前删掉该文件并重新打包

## 报告问题

发现凭据泄漏或注入风险，请在仓库开一个 Issue（不要贴真实凭据），或直接联系维护者。
