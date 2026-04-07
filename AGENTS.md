# YueluDate 运维 Agent 指南

## 项目概况
YueluDate（原 CSU Date）是岳麓山三校（中南大学、湖南大学、湖南师范大学）校园匹配平台。

- **域名**: yueludate.cn / csudate.com
- **后端**: FastAPI + SQLite (`csu-datedrop-backend/`)
- **前端**: 纯 HTML/JS (`stitch/`)
- **服务器**: 66.6.58.60，systemd 管理 (`csudate.service`)
- **部署**: push 到 main 分支自动部署（GitHub Actions → SSH → git pull → restart）

## 技术栈
- Python 3.9 + FastAPI + SQLAlchemy + SQLite
- 邮件: Resend API（被抑制时回退 QQ SMTP）
- Nginx 反代 + Let's Encrypt SSL
- 匹配算法: `precision_matching_engine.py`

## 目录结构
```
csu-datedrop-backend/
  main.py              # FastAPI 主应用
  config.py            # 配置常量
  models.py            # SQLAlchemy ORM 模型
  schemas.py           # Pydantic 请求体
  email_service.py     # 邮件发送（Resend + QQ SMTP 回退）
  matcher_service.py   # 匹配服务（组装数据 → 调用引擎）
  precision_matching_engine.py  # 核心匹配算法
  llm_report.py        # LLM 生成匹配报告
  announcements.json   # 公告数据
  .env                 # 环境变量（不在 git 中）

stitch/
  index.html           # 主页 + 问卷
  login.html           # 登录/注册
  dashboard.html       # 用户仪表盘
  profile.html         # 个人主页
  about.html           # 关于/隐私/免责/邮箱指引
  report.html          # 匹配报告页
  api.js               # API 工具函数
```

## 支持的教育邮箱
- @csu.edu.cn（中南大学）
- @hnu.edu.cn（湖南大学）
- @hunnu.edu.cn（湖南师范大学）

## 关键 API 端点
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `POST /api/auth/send-code` - 发送验证码
- `GET /api/user/me` - 获取当前用户
- `POST /api/quiz/submit` - 提交问卷
- `GET /api/inbox` - 收件箱/匹配列表
- `GET /api/announcements` - 公告列表
- `GET /api/admin/dashboard-stats` - 管理统计
- `POST /api/admin/run-match` - 手动触发匹配

## 部署注意事项
- `datedrop.db` 不在 git 中，部署不会覆盖数据库
- 部署脚本用 `git checkout + git reset`（不是 `reset --hard`）
- 每日 4:00 自动备份数据库到 `/opt/csudate/backups/`
- 公告更新只需编辑 `announcements.json` 并 push

## 常见运维任务
1. **发布公告**: 编辑 `csu-datedrop-backend/announcements.json`
2. **查看用户**: 通过 admin API 或直接查 SQLite
3. **手动匹配**: `POST /api/admin/run-match`（需 admin token）
4. **SSL 证书**: Let's Encrypt 自动续期，certbot 管理
5. **服务重启**: GitHub Actions 自动执行，或 SSH 手动 `systemctl restart csudate`

## 代码规范
- 后端 Python 代码遵循 PEP 8
- 前端为单文件 HTML（内联 CSS + JS），无构建工具
- commit message 用中文，格式：`类型: 简要描述`
- 类型：feat（新功能）、fix（修复）、chore（杂务）、notice（公告）
