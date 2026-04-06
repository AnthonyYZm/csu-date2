# CSU Date

中南大学校园匹配平台原型。产品核心理念是：

**不刷屏，每周只遇见一个人，然后认真了解 TA。**

当前仓库不是已接后端的正式产品，而是一套可直接在浏览器打开的高保真静态原型，用于展示完整用户流程、问卷结构、仪表盘、匹配报告和站内消息体验。

## 项目现状

当前实现已经覆盖：

- 首页 Landing Page
- 登录 / 注册页
- 7 模块完整版问卷
- 用户仪表盘
- 本周匹配报告页
- 打招呼页
- 信箱页
- 个人主页

当前尚未实现：

- 真实后端 API
- 数据库持久化
- 邮箱验证码发送
- 真实匹配算法跑批
- 真实消息存储
- 真实报告生成

仓库中所有业务状态目前主要通过浏览器 `localStorage` 模拟。

## 体验流程

建议按下面顺序体验：

1. 打开 `index.html`
2. 点击“开始匹配”
3. 跳转 `login.html`
4. 登录后进入 7 模块问卷
5. 提交后进入 `dashboard.html`
6. 再查看 `report.html`、`greet.html`、`inbox.html`、`profile.html`

## 主要页面

| 页面 | 文件 | 说明 |
|---|---|---|
| 首页 + 问卷 | `index.html` | 产品介绍、7 模块问卷、问卷状态管理 |
| 登录 / 注册 | `login.html` | 原型级登录注册流程，验证码和账号体系为前端模拟 |
| 仪表盘 | `dashboard.html` | 本周匹配、历史匹配、匹配洞察、倒计时、 Shoot Your Shot |
| 打招呼 | `greet.html` | 向本周匹配对象发送首条消息 |
| 信箱 | `inbox.html` | 双向匹配、等待回应、过期消息的展示原型 |
| 个人主页 | `profile.html` | 基础资料、价值观标签、微信号、暂停匹配 |
| 匹配报告 | `report.html` | 契合度、维度分析、共同点、互补点、叙事化报告 |

## 问卷结构

当前问卷已经不是早期 3 步简版，而是 7 模块完整版：

1. 基本信息
2. 人生观与事业观
3. 性格与价值观
4. 生活方式
5. 亲密关系观
6. 兴趣爱好
7. 外貌气质与核心特质

问卷中包含以下能力：

- 单选题
- 下拉题
- 滑块题
- 双轨题：自己 / 希望伴侣
- 多选兴趣
- 多选特质
- “设为重要”权重标记
- 季节性破冰题

## 当前前端数据模型

原型主要使用两个本地存储键：

### `csudate_user`

用于保存当前登录用户、资料、统计信息和部分 UI 状态，例如：

- `id`
- `email`
- `name`
- `campus`
- `grade`
- `major`
- `bio`
- `values`
- `wechat`
- `stats`
- `loggedIn`
- `quizCompleted`
- `weeklyMatch`
- `paused`

### `csudate_quiz`

用于保存问卷提交结果，例如：

- 完整问卷答案 `responses`
- 重要题标记 `importance`
- 提交时间 `completedAt`

## 演示账号

`login.html` 中内置了两个演示账号，方便直接体验仪表盘：

| 账号 | 密码 | 说明 |
|---|---|---|
| `test` | `test` | 有本周匹配 |
| `test2` | `test` | 本周暂未匹配 |

注意：

- 这只是前端演示逻辑
- 不代表真实认证系统
- 注册验证码也只是本地模拟，不会真正发送邮件

## 技术实现

当前仓库采用极简静态实现：

- 原生 HTML
- 原生 CSS
- 原生 JavaScript
- Google Fonts
- `localStorage` 本地状态

特点：

- 无构建步骤
- 无框架依赖
- 多页面静态原型
- 可直接部署到任意静态托管平台

## 设计风格

设计系统见 `DESIGN.md`，当前视觉方向可以概括为：

- Academic Romanticism
- 慢节奏、编辑感、留白感
- 深靛蓝 + 珊瑚橙 + 奶油白
- 大圆角、无硬分割线
- 校园文学气质 + 低频高质量社交

## 本地运行

直接双击 HTML 文件即可打开。

如果需要更接近真实部署环境，建议起一个静态服务器：

```bash
npx serve .
```

然后访问相应页面，例如：

- `http://localhost:3000/index.html`
- `http://localhost:3000/login.html`

## 仓库结构

```text
stitch/
├── index.html
├── login.html
├── dashboard.html
├── greet.html
├── inbox.html
├── profile.html
├── report.html
├── DESIGN.md
├── BACKEND_HANDOFF.md
├── ALGORITHM_DESIGN_HANDOFF.md
├── datedrop-frontend-prompt.md
├── csu-datedrop-improvement-prompt.md
├── csu-datedrop-improvement-prompt2.md
├── csu-datedrop-full-questionnaire-prompt.md
├── screen.png
└── vercel.json
```

## 配套文档

- `DESIGN.md`
  - 设计系统与视觉语言说明
- `BACKEND_HANDOFF.md`
  - 面向后端的现状分析、领域模型、API 与落地建议
- `ALGORITHM_DESIGN_HANDOFF.md`
  - 面向算法设计的问卷拆解、特征分类、打分与匹配策略建议
- `datedrop-frontend-prompt.md`
  - 初版前端需求来源
- `csu-datedrop-improvement-prompt*.md`
  - 中南版本和问卷扩展的迭代需求来源

## 当前限制

这套原型目前最重要的限制如下：

- 旧需求文档里存在历史版本信息，需以当前页面代码为准
- 页面之间的数据一致性仍是原型级别
- 匹配对象、历史、信箱、报告等大量内容仍为写死 demo 数据
- 消息和微信号解锁规则只做了前端表达，未有服务端真值
- 登录、注册、验证码、匹配周期都未进入生产可用状态

## 下一步建议

如果要把这个仓库继续推进成可上线产品，建议优先做：

1. 真实邮箱注册登录
2. 问卷版本化与持久化
3. 周期管理与 opt-in 状态
4. 第一版匹配算法
5. 匹配报告生成
6. 信箱与双向消息闭环
7. 微信号互惠解锁

其中后端和算法方案的拆解已经分别写在：

- `BACKEND_HANDOFF.md`
- `ALGORITHM_DESIGN_HANDOFF.md`

## 说明

本项目为学生自主开发原型，非学校官方项目。
