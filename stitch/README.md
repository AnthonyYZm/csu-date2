# CSU DateDrop

中南大学专属校园匹配平台。不刷屏，每周为你匹配一个最合拍的中南人。

## 项目简介

CSU DateDrop 是一个面向中南大学在校生的校园匹配平台，核心理念是**每周只遇见一个人，然后认真了解 TA**。用户填写一份涵盖价值观、生活态度的深度问卷后加入匹配池，每周四收到一份专属匹配报告。

仅限 `@csu.edu.cn` / `@mail.csu.edu.cn` 邮箱注册。

> 本项目为学生自主开发，非学校官方项目。

## 产品流程

1. **首页** — 了解产品理念，点击「开始匹配」进入问卷
2. **问卷 Step 1/3** — 基本信息：性别、寻找类型、年级、校区
3. **问卷 Step 2/3** — 从 18 个核心价值观中选择 4 个（含中南特色标签：经世致用、霸蛮精神、共情力）
4. **问卷 Step 3/3** — 8 道态度量表滑块题 + 1 道季节趣味题（选填）
5. **完成页** — 确认提交，展示信息摘要，可分享给室友

## 技术实现

- **单文件 SPA** — 全部代码在 `code.html` 一个文件中，浏览器直接打开即可运行
- **Tailwind CSS (CDN)** — 使用 Material Design 3 色彩体系的自定义 token
- **Google Fonts** — Noto Serif SC（标题）+ Inter（正文）+ Material Symbols Outlined（图标）
- **纯 JavaScript** — 无框架依赖，状态管理、页面路由、动画全部原生实现

## 设计系统

详见 [DESIGN.md](DESIGN.md)，核心要点：

- **风格** — Modern Romanticism & The Academic Soul，灵感来源于「大学图书馆的黄金时刻」
- **配色** — 深靛蓝 `#15157d`（主色）+ 珊瑚橙 `#a43c12`（强调色）+ 奶油白 `#fcf9f2`（底色）
- **No-Line 规则** — 不使用 1px 边框分隔内容，通过背景色阶变化定义层级
- **圆角** — 所有容器至少 2rem 圆角，按钮为全圆角药丸形

## 响应式适配

- 移动端优先，支持 320px - 4K 全尺寸
- 44px 最小触摸目标（滑块、按钮）
- `viewport-fit=cover` + `env(safe-area-inset-bottom)` 适配刘海屏
- `prefers-reduced-motion` 减弱动效支持
- 横屏手机紧凑布局

## 本地运行

浏览器打开 `code.html` 即可，无需构建步骤。

```bash
# 或使用任意静态服务器
npx serve .
```

## 数据结构

问卷收集的数据结构（当前存储在前端 state，未对接后端）：

```typescript
interface QuestionnaireData {
  school: 'csu';
  gender: '男' | '女' | '非二元';
  seeking: '约会对象' | '朋友' | '都行';
  grade: '大一' | '大二' | '大三' | '大四' | '研究生';
  campus: '岳麓山' | '潇湘' | '南校区' | '天心' | '湘雅';
  values: string[];   // 从 18 个中选 4 个
  likert: {
    children: number;   // 1-7
    introvert: number;
    career: number;
    contact: number;
    conflict: number;
    sleep: number;
    spicy: number;
    studyspot: number;
  };
  seasonal: string | null;  // 选填趣味题
}
```

## 文件结构

```
stitch/
├── code.html                        # 完整单文件 SPA
├── DESIGN.md                        # 设计系统文档
├── datedrop-frontend-prompt.md      # 初版前端需求 prompt
├── csu-datedrop-improvement-prompt.md  # CSU 定制迭代需求
├── screen.png                       # 设计参考截图
└── README.md
```

## 未来规划

- [ ] 对接后端 API，问卷数据持久化
- [ ] 用户登录（@csu.edu.cn 邮箱验证）
- [ ] 每周匹配推送邮件系统
- [ ] 长沙高校匹配联盟（湖大、师大跨校匹配）
- [ ] 深色模式
- [ ] 季节主题运营（每季度更换趣味题）
