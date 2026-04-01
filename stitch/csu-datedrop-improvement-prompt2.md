# CSU DateDrop 完善需求 — AI Prompt

> 基于现有 code.html 进行迭代。以下是需要你完成的全部改动清单。
> 改动原则：**保留现有设计语言和代码架构**，在此基础上做内容替换、功能增补和细节打磨。

---

## 一、中南大学品牌定制

### 1.1 名称与标识

把所有「DateDrop」替换为「**CSU DateDrop**」，副品牌文案统一为：

- Header logo 文字改为：`CSU DateDrop`
- 品牌 Tagline：`中南大学 · 校园匹配`（用于 footer 等位置）

### 1.2 学校信息嵌入

以下是中南大学的关键信息，在合适的地方嵌入：

| 信息项 | 内容 |
|--------|------|
| 学校全称 | 中南大学 (Central South University) |
| 邮箱域名 | @csu.edu.cn 或 @mail.csu.edu.cn |
| 校区 | 岳麓山校区(本部)、潇湘校区(新校区)、南校区、天心校区(铁道)、湘雅校区(开福/杏林) |
| 校训 | 知行合一、经世致用 |
| 校风 | 向善、求真、唯美、有容 |
| 优势学科 | 有色金属、湘雅医学、轨道交通、土木工程、材料科学 |
| 在校生规模 | 约 6.4 万人 |
| 地理位置 | 湖南省长沙市，跨湘江两岸，依岳麓山，临湘水 |
| 学校类型 | 985 / 211 / 双一流 |

### 1.3 需要修改的具体文案

**Hero 区域 — 轮播 Slogan（重要改动）：**

把现有的 Hero 大标题（`不刷屏 每周遇见 一个对的人`）替换为一个**居中轮播 Slogan 组件**，每 3.5 秒自动切换，带淡入淡出 + 上下位移动画。下方有小圆点指示器，可手动点击切换。

整体布局改为**居中对齐**（移除现有的左右分栏 grid），内容垂直堆叠：品牌标签 → 轮播 Slogan → 副标题 → CTA 按钮 → 在线人数。

**5 条轮播 Slogan：**

| 序号 | 主文案（中文） | 副文案（英文/注释，小字灰色斜体） |
|------|--------------|------|
| 1 | 停车坐爱，麓山有你 | Where hearts meet under Yuelu's maple glow |
| 2 | 惟楚有材，于斯遇你 | Among the finest talents, here I find you |
| 3 | 爱晚，不晚 | Love late? Never too late. |
| 4 | 湘江月照两个人 | Moonlight on the Xiang, shining on just us two |
| 5 | 从后湖到湘江，总会遇见对的人 | From Back Lake to the river, the right one awaits |

**HTML 结构：**

```html
<!-- 替换原有 Hero grid 的内容区域 -->
<div class="text-center max-w-2xl mx-auto">
  <p class="text-[10px] font-semibold uppercase tracking-[0.35em] text-secondary mb-8 reveal">
    中南大学 · 岳麓山下的匹配实验
  </p>

  <!-- 轮播主文案 -->
  <div class="relative h-[4.5rem] md:h-[5.5rem] overflow-hidden mb-3" id="slogan-main">
    <!-- JS 动态生成 .slogan-line 子元素 -->
  </div>

  <!-- 轮播副文案（英文） -->
  <div class="relative h-6 overflow-hidden mb-8" id="slogan-sub">
    <!-- JS 动态生成 .sub-line 子元素 -->
  </div>

  <!-- 圆点指示器 -->
  <div class="flex justify-center gap-1.5 mb-10" id="slogan-dots"></div>

  <!-- CTA -->
  <button onclick="startQuiz()" class="bg-secondary text-on-secondary px-10 py-4 rounded-full font-semibold hover:opacity-90 transition-opacity" style="box-shadow:0 8px 36px rgba(164,60,18,.2);">
    开始匹配
  </button>

  <!-- 在线人数 -->
  <div class="flex items-center justify-center gap-1.5 mt-6 text-on-surface-variant/60 text-xs">
    <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
    <span id="live-count">0</span> 人已加入
  </div>
</div>
```

**CSS 新增：**

```css
/* ── Slogan rotation ── */
.slogan-line, .sub-line {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transform: translateY(12px);
  transition: opacity .6s cubic-bezier(.16,1,.3,1), transform .6s cubic-bezier(.16,1,.3,1);
}
.slogan-line.active, .sub-line.active { opacity: 1; transform: translateY(0); }
.slogan-line.exit, .sub-line.exit { opacity: 0; transform: translateY(-12px); }
.sub-line { transition-delay: .1s; }

.slogan-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(28,28,24,.15); transition: all .4s; cursor: pointer;
}
.slogan-dot.on { background: rgba(28,28,24,.4); width: 18px; border-radius: 3px; }
```

**Slogan 主文案样式：**
使用 `font-headline`（Noto Serif SC），`font-bold`，`text-primary`，
字号 `text-3xl md:text-5xl`（即 clamp(1.875rem, 5vw, 3rem)）。
第一条最长的"从后湖到湘江..."在移动端也要单行能放下，如果放不下就 `text-2xl`。

**Slogan 副文案样式：**
`text-xs text-on-surface-variant/50 italic font-body`

**JS 逻辑：**

```javascript
/* ── Slogan Carousel ── */
const sloganData = [
  { main: '停车坐爱，麓山有你', sub: "Where hearts meet under Yuelu's maple glow" },
  { main: '惟楚有材，于斯遇你', sub: 'Among the finest talents, here I find you' },
  { main: '爱晚，不晚', sub: 'Love late? Never too late.' },
  { main: '湘江月照两个人', sub: 'Moonlight on the Xiang, shining on just us two' },
  { main: '从后湖到湘江，总会遇见对的人', sub: 'From Back Lake to the river, the right one awaits' },
];

let sloganIdx = 0;
let sloganTimer = null;
const sMain = document.getElementById('slogan-main');
const sSub = document.getElementById('slogan-sub');
const sDots = document.getElementById('slogan-dots');

// 生成 DOM
sloganData.forEach((s, i) => {
  const ml = document.createElement('div');
  ml.className = 'slogan-line' + (i === 0 ? ' active' : '');
  ml.innerHTML = '<span class="font-headline font-bold text-primary" style="font-size:clamp(1.6rem,5vw,2.8rem);">' + s.main + '</span>';
  sMain.appendChild(ml);

  const sl = document.createElement('div');
  sl.className = 'sub-line' + (i === 0 ? ' active' : '');
  sl.innerHTML = '<span class="text-xs text-on-surface-variant/50 italic">' + s.sub + '</span>';
  sSub.appendChild(sl);

  const dot = document.createElement('div');
  dot.className = 'slogan-dot' + (i === 0 ? ' on' : '');
  dot.onclick = () => sloganGoTo(i);
  sDots.appendChild(dot);
});

function sloganGoTo(n) {
  if (n === sloganIdx) return;
  const mains = sMain.children, subs = sSub.children, dots = sDots.children;
  mains[sloganIdx].className = 'slogan-line exit';
  subs[sloganIdx].className = 'sub-line exit';
  dots[sloganIdx].className = 'slogan-dot';
  const prev = sloganIdx;
  setTimeout(() => {
    mains[prev].className = 'slogan-line';
    sloganIdx = n;
    mains[sloganIdx].className = 'slogan-line active';
    subs[sloganIdx].className = 'sub-line active';
    dots[sloganIdx].className = 'slogan-dot on';
  }, 350);
  clearInterval(sloganTimer);
  sloganTimer = setInterval(sloganNext, 3500);
}

function sloganNext() { sloganGoTo((sloganIdx + 1) % sloganData.length); }
sloganTimer = setInterval(sloganNext, 3500);

// 参与人数递增动画
function animateCount(el, target) {
  let n = 0; const step = target / 120;
  const t = setInterval(() => {
    n += step;
    if (n >= target) { n = target; clearInterval(t); }
    el.textContent = Math.floor(n).toLocaleString();
  }, 16);
}
animateCount(document.getElementById('live-count'), 1247);
```

**关键交互细节：**

- 每 3.5 秒自动切换下一条，循环播放
- 用户手动点击圆点后重置计时器（防止刚点完立刻自动跳）
- 切换动画：当前文案向上淡出（translateY(-12px) + opacity 0），新文案从下方淡入（translateY(12px→0) + opacity 0→1）
- 副文案动画比主文案延迟 100ms，形成错落感
- 圆点激活态从圆形变为胶囊形（6px→18px 宽），有平滑过渡

**Hero 区域其他调整：**
- 移除右侧图片栏（原来的 3:4 图片），改为纯居中文案布局
- 左下角浮窗卡片可保留，改为绝对定位在轮播区域下方偏左
- Hero 区域改为 `min-h-screen flex items-center justify-center`
- 标签文字：`中南大学 · 岳麓山下的匹配实验`（在轮播上方，小字）

**Manifesto 段落：**
- 保留现有"慢下来"的理念
- 文案替换为：`越过岳麓晚霞，穿过后湖倒影，我们相信在所有概率之外，定有某种默契。每周只遇见一个人，然后认真了解 TA。`

**Testimonial 引用区：**
- 身份改为：`中南大学 · 湘雅医学院研究生`（或其他中南院系）
- 引用内容做微调，体现中南氛围，例如：`"在这里我没有遇到一百个人，但我遇到了一个在后湖散步时能和我讨论加缪的人。CSU DateDrop 像一封来自岳麓山的情书。"`

**CTA 区域：**
- `加入 20,000+ 在校生的行列` → 改为 `加入 6 万中南人的行列`
- `一起讨论电影的人` → 改为 `还能一起爬岳麓山讨论人生的人`

**Footer：**
- `仅限 @edu.cn 邮箱注册` → 改为 `仅限 @csu.edu.cn 邮箱注册`
- 版权改为：`© 2026 CSU DateDrop · 中南大学校园匹配平台`
- 加上一行小字：`本项目为学生自主开发，非学校官方项目`

---

## 二、问卷内容增强

### 2.1 Step 1 基本信息 — 增加校区选择

在「你的年级」下方新增一个问题：

**你住在哪个校区？**
选项（横排按钮组，样式同年级）：
`岳麓山` / `潇湘` / `南校区` / `天心` / `湘雅`

- 把这个字段加入 quiz state 对象，key 为 `campus`
- 把这个字段加入 Step 1 的「下一步」启用判断条件（gender + seeking + grade + campus 全选才能下一步）
- 完成页的信息摘要也展示校区信息

### 2.2 Step 2 核心价值观 — 增加中南特色选项

保留现有 15 个价值观标签，**追加 3 个带有中南/湖湘特色的选项**（总共 18 个，仍只选 4 个）：

| ID | 标签文字 | 含义 |
|----|---------|------|
| `pragmatism` | 经世致用 | 来自中南校训，强调学以致用 |
| `resilience` | 霸蛮精神 | 湖南方言，意为不服输、敢拼 |
| `empathy` | 共情力 | 善于理解他人的感受 |

在 values grid 中追加这三个按钮，同时在 JS 的 `valNames` 字典中加入对应映射。grid 排列建议调整为每行 6 个（桌面端），确保 18 个标签视觉整齐。

### 2.3 Step 3 态度量表 — 增加校园场景题

在现有 6 道题之后**追加 2 道**与中南校园生活相关的题：

| key | 题目文字 | 左端标签 | 右端标签 |
|-----|---------|---------|---------|
| `spicy` | 我对辣的接受程度很高 | 微辣就好 | 无辣不欢 |
| `studyspot` | 约会我更喜欢去安静的地方 | 热闹的街区 | 安静的角落 |

- 在 quiz.likert 对象中加入这两个新 key（默认值 4）
- touched 判断从 6 改为 8（所有 8 题都滑过才能提交）
- 更新 `btn-s3` 的启用条件
- 完成页的问卷摘要也更新为 `8 题已完成`
- 进度条总步数保持 3 步不变（这两道题在同一个 Step 3 里追加即可）

---

## 三、功能与体验完善

### 3.1 Hero 区域图片

目前 Hero 右侧使用的是一张外链 Google 占位图。做以下处理：
- 替换为一张中南大学校园场景图（岳麓山、后湖、图书馆等）
  - 如果不方便获取真实图片，用 Unsplash 上的校园/秋天/湖景照片替代，URL 格式：
    `https://images.unsplash.com/photo-xxx?w=800&q=80`
  - 或者直接用一个纯色 + 校训文字的装饰性区块替代图片
- 同理处理 "Why DateDrop" 区域的图片

### 3.2 匹配报告预览卡（Hero 区域左下角浮窗）

现有文案是 `"你们对《局外人》的见解惊人地一致..."`，做微调：
- 改为 `"你们都把《百年孤独》列为最爱，而且都喜欢在后湖边散步思考..."`
- 标签改为 `CSU 周报`

### 3.3 "Why DateDrop" 区域标题

- `为什么数万名学生选择 DateDrop？` → `为什么中南人选择 CSU DateDrop？`

### 3.4 移动端底部导航

现有底部 nav 有「发现」「匹配」「我的」三个 tab，对应 icon 分别是 auto_stories / favorite / person。保留不变，但给中间的「匹配」加一个小红点 badge 样式（表示有新匹配），CSS 做一个小红圆点在 icon 右上角：

```css
.badge-dot {
  position: absolute;
  top: -2px;
  right: -4px;
  width: 7px;
  height: 7px;
  background: #a43c12;
  border-radius: 50%;
  border: 1.5px solid #fcf9f2;
}
```

给「匹配」tab 的 icon 父容器加 `position:relative`，然后在 icon 旁边追加一个 `<span class="badge-dot"></span>`。

### 3.5 问卷「返回首页」确认

在 quiz 页点「← 返回」且 step === 1 时，目前直接跳回首页。改为弹一个原生 `confirm()` 确认框：

```javascript
function quizBack() {
  if (step > 1) {
    goToStep(step - 1);
  } else {
    if (confirm('确定离开问卷吗？你的填写进度将不会保存。')) {
      navigateTo('page-landing');
    }
  }
}
```

### 3.6 滑块优化

目前滑块默认值都是 4（正中间），用户不主动拖动就不会触发 touched。这有个问题：如果用户确实觉得某题是 4 分，不会去拖它，导致永远凑不到所有题。

解决方案：
- 给每个滑块的 thumb 初始设置为**不可见（opacity: 0）**
- 用户首次触摸/点击该滑块时，才让 thumb 显示并加入 touched
- 具体实现：给每个 `<input type="range">` 加一个 class `untouched`，CSS 中 `.untouched::-webkit-slider-thumb { opacity: 0.3; }` `.untouched::-moz-range-thumb { opacity: 0.3; }`
- 在 `onSlide()` 中首次触发时移除 `untouched` class

### 3.7 完成页增强

在完成页的信息摘要区块下方、提醒文字上方，加一个 **「分享给室友」** 按钮：

```html
<button onclick="shareToClipboard()" class="mt-4 text-secondary font-medium hover-line text-sm">
  复制链接，分享给室友 →
</button>
```

```javascript
function shareToClipboard() {
  navigator.clipboard.writeText(window.location.href).then(() => {
    alert('链接已复制！快发给室友一起来匹配吧 🎉');
  });
}
```

---

## 四、SEO 和元信息

在 `<head>` 中加入以下 meta 标签：

```html
<title>CSU DateDrop · 中南大学校园匹配平台</title>
<meta name="description" content="中南大学专属校园匹配平台。不刷屏，每周为你匹配一个最合拍的中南人。仅限 @csu.edu.cn 邮箱注册。">
<meta name="keywords" content="中南大学,CSU,校园匹配,约会,DateDrop,大学社交">
<meta property="og:title" content="CSU DateDrop · 不刷屏，每周遇见一个对的人">
<meta property="og:description" content="中南大学专属校园匹配平台，每周四给你发送最佳匹配。">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💌</text></svg>">
```

---

## 五、样式微调

### 5.1 品牌色微调（可选）

目前 primary 是 `#15157d`（深紫蓝），secondary 是 `#a43c12`（深橙）。如果想更贴近中南大学的品牌色（中南校徽主色为深蓝 + 红色），可以把 tailwind.config 中的配色方案做如下微调：

```
primary: "#1a237e"        → 保持不变或微调为中南蓝
secondary: "#c62828"      → 中南红（可选，如果想更"中南"的话）
```

不确定就**不改**，当前配色已经很和谐。

### 5.2 滑块问题区间距优化

现有 Step 3 的 `space-y-9` 在移动端题目较多时需要大量滚动。加了 2 道题后建议改为 `space-y-7`，让间距稍紧凑一些。

### 5.3 价值观标签网格

追加 3 个标签后变成 18 个，当前是 `grid-cols-3 md:grid-cols-5`。18 个在 5 列下排 4 行（最后一行 3 个，留 2 个空位略不整齐）。建议桌面端改为 `md:grid-cols-6`，这样 18 个正好排满 3 行，视觉更整齐。

---

## 六、借鉴 THU-PKU Date 的改进

> THU-PKU Date（datethupku.com）是清华北大联合的校园匹配平台，以下是分析其设计后值得我们吸收的改进点。

### 6.1 首页加实时参与人数计数器

在 Header 的 logo 右侧，或 Hero 区域的统计数字区，新增一个**动态在线/参与人数**展示：

```html
<span class="inline-flex items-center gap-1.5 text-xs text-on-surface-variant">
  <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
  <span id="live-count">1,247</span> 人已加入
</span>
```

用 JS 做一个缓慢递增的动画效果（页面加载时从 0 数到目标值），制造社区活跃感：

```javascript
function animateCount(el, target, duration = 2000) {
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start += step;
    if (start >= target) { start = target; clearInterval(timer); }
    el.textContent = Math.floor(start).toLocaleString();
  }, 16);
}
// 页面加载时触发
animateCount(document.getElementById('live-count'), 1247);
```

初期用注册人数，后期改为实时 opt-in 人数。

### 6.2 Manifesto 文案诗意升级

THU-PKU Date 用"越过未名落日 荷塘清影，寻找算法定义之外的心动"这种校园意象文案，情感穿透力很强。

把现有 Manifesto 段落（`<section class="py-20 ... bg-surface-container-low">`）的文案替换为：

```
越过岳麓晚霞，穿过后湖倒影，
我们相信在所有概率之外，定有某种默契。
每周只遇见一个人，然后认真了解 TA。
```

保持原有的 `font-headline` 和 `text-center` 样式不变。

### 6.3 匹配推送时间改为周四

THU-PKU Date 选择周四下午推送，临近周末，用户收到匹配后有周五周六可以直接约出来，转化率更高。

全站所有提到「周二」的地方统一改为「周四」：

- Hero 副标题：`每周四，一个和你最合拍的人会出现在你的邮箱`
- Process 第二步：`周四晚 9 点前 Opt-in`
- 完成页提醒：`记得每周四晚 9 点前点「我参加」才会被匹配哦`
- SEO meta description：将 `每周二` 改为 `每周四`

### 6.4 预留跨校扩展能力

THU-PKU Date 做清华+北大联合匹配，极大扩展了匹配池。为未来联合长沙其他高校（湖南大学、湖南师范大学等）做准备：

在 quiz state 对象中增加一个 `school` 字段（当前默认值为 `'csu'`，不需要用户手动选）：

```javascript
const quiz = {
  school: 'csu',  // 预留：未来可扩展 'hnu'(湖大), 'hunnu'(师大) 等
  gender: null,
  seeking: null,
  // ...
};
```

在 Footer 区域加一行预告文案：

```html
<p class="text-on-surface-variant/40 text-xs mt-2">
  长沙高校匹配联盟 · 即将开放湖大、师大
</p>
```

### 6.5 季节主题运营机制

THU-PKU Date 文案中用"将你的色彩留给春天"暗示季节性活动。在 Step 3 问卷最后追加一道**季节轮换趣味题**（不参与匹配算法，纯粹增加趣味和话题性）：

| key | 题目文字 | 类型 | 选项 |
|-----|---------|------|------|
| `seasonal` | 这个春天，你最想和匹配对象一起做什么？ | 单选按钮组 |  `爬岳麓山` / `逛太平街` / `后湖边散步` / `图书馆自习` |

这道题不加入 touched 判断（即不强制作答），但选了的话在匹配邮件里展示为破冰话题："TA 春天最想和你一起去后湖边散步"。

每个季度换一次题目内容（夏天换成"一起吃小龙虾/去橘子洲看烟花"等）。

实现方式：在 Step 3 的滑块题下方、提交按钮上方插入：

```html
<div class="mt-10 mb-4">
  <p class="font-headline font-semibold text-primary text-[15px] mb-1">这个春天，你最想和匹配对象一起做什么？</p>
  <p class="text-on-surface-variant text-xs mb-4">选填 · 你的回答会出现在匹配报告中作为破冰话题</p>
  <div class="grid grid-cols-2 gap-2">
    <button class="opt-btn" data-q="seasonal" data-v="爬岳麓山" onclick="pickOpt('seasonal','爬岳麓山',this)">爬岳麓山</button>
    <button class="opt-btn" data-q="seasonal" data-v="逛太平街" onclick="pickOpt('seasonal','逛太平街',this)">逛太平街</button>
    <button class="opt-btn" data-q="seasonal" data-v="后湖散步" onclick="pickOpt('seasonal','后湖散步',this)">后湖散步</button>
    <button class="opt-btn" data-q="seasonal" data-v="图书馆自习" onclick="pickOpt('seasonal','图书馆自习',this)">图书馆自习</button>
  </div>
</div>
```

在 quiz state 中加入 `seasonal: null`，在完成页摘要中展示（如果用户选了的话）。

---

## 七、改动清单一览（给 AI 的 checklist）

请按以下顺序逐项完成：

- [ ] `<head>` 中加入 `<title>` 和 meta 标签
- [ ] 全局替换 `DateDrop` → `CSU DateDrop`（logo、footer、标题等所有出处）
- [ ] Hero 标签文案、副标题、Manifesto、Testimonial、CTA、Footer 文案全部替换为上述中南版本
- [ ] Hero 区域改为居中布局 + 5 条轮播 Slogan 组件（3.5 秒切换，圆点指示器，淡入淡出动画）
- [ ] Hero 浮窗和图片替换
- [ ] "Why" 区域标题替换
- [ ] Footer 邮箱域名和版权信息替换，加非官方声明
- [ ] Step 1 新增「校区」问题，更新 state 和验证逻辑
- [ ] Step 2 追加 3 个价值观标签，更新 grid 列数和 valNames
- [ ] Step 3 追加 2 道滑块题，更新 touched 判断为 8 题
- [ ] Step 3 末尾追加季节趣味题（选填），加入 state
- [ ] 滑块未触摸状态视觉优化（untouched class）
- [ ] 移动端底部导航「匹配」tab 加红点 badge
- [ ] 问卷返回首页加 confirm 确认
- [ ] 完成页加校区信息展示、题数改为 8、加「分享给室友」按钮、展示季节题回答
- [ ] 滑块间距和价值观 grid 样式微调
- [ ] 首页加实时参与人数计数器（带递增动画）
- [ ] Manifesto 文案替换为诗意版（岳麓晚霞/后湖倒影）
- [ ] 全站「周二」→「周四」（推送时间、opt-in 截止、SEO meta 等）
- [ ] quiz state 加 `school: 'csu'` 预留字段
- [ ] Footer 加「长沙高校匹配联盟 · 即将开放湖大、师大」预告

---

## 八、不要改动的部分

以下内容已经做得很好，请保持原样：

- 整体设计语言（字体选择、配色体系、间距节奏）
- 页面切换动画和问卷步骤过渡动画
- 滑块的自定义样式和颜色填充效果（fillSlider 函数）
- Reveal 滚动动画系统
- Glass 毛玻璃 header 效果
- 完成页的弹出动画（checkPop）和渐入效果
- 三步问卷的整体流程结构
- 所有的 Tailwind 配色 token（surface / on-surface 等 Material Design 3 色系）

---

**输出要求：** 直接给我修改后的完整 HTML 文件，可以在浏览器中直接打开运行。不需要拆分成多文件，保持原有的单文件架构。
