# YueluDate 项目指南

## 项目概况
- **品牌**: YueluDate（原 CSU Date）
- **定位**: 岳麓山三校（中南大学、湖南大学、湖南师范大学）匹配平台
- **域名**: yueludate.cn / csudate.com（双域名）
- **服务器**: 66.6.58.60（root / CYFf2lzEbnGSmy54ncll）

## 技术栈
- **后端**: FastAPI + SQLite，位于 `csu-datedrop-backend/`
- **前端**: 纯 HTML/JS，位于 `stitch/`
- **部署**: GitHub Actions 自动部署（push main → SSH 服务器 → 拉代码 → 重启）
- **服务管理**: systemd `csudate.service`
- **数据库备份**: 每日 4:00 自动备份到 `/opt/csudate/backups/`

## 部署流程
1. 本地改代码
2. `git push fork2 main` 触发自动部署
3. 约 15 秒后服务器自动更新

## 关键配置
- **教育邮箱**: @csu.edu.cn / @hnu.edu.cn / @hunnu.edu.cn
- **Resend API**: 发验证码，被抑制时回退 QQ SMTP（2573891909@qq.com）
- **服务器项目路径**: `/opt/csudate/`
- **Nginx 配置**: `/etc/nginx/sites-available/csudate`
- **环境变量**: `/opt/csudate/csu-datedrop-backend/.env`

## 常用命令（在服务器上）
```bash
systemctl restart csudate   # 重启后端
journalctl -u csudate -f    # 查看后端日志
systemctl reload nginx       # 重载 nginx
```

## 注意事项
- 数据库文件 `datedrop.db` 已从 git 追踪中移除，部署不会覆盖
- 部署脚本用 `git checkout + git reset`（不是 reset --hard），不会删未追踪文件
- 公告更新只需编辑 `csu-datedrop-backend/announcements.json`
