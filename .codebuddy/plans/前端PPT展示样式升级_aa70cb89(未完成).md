---
name: 前端PPT展示样式升级
overview: 将前端 PptViewer.vue 从深蓝学术风格升级为与后端PPT生成一致的温暖橙色插画风格，并新增 two_column、chart、summary 三种布局支持，以及键盘快捷键切换功能。
design:
  architecture:
    framework: vue
  styleKeywords:
    - Illustration Style
    - Warm Orange
    - Educational
    - Playful
    - Gradient Background
    - Rounded Corners
    - Decorative Circles
    - Numbered Badges
    - Two-column Layout
    - Chart Visualization
  fontSystem:
    fontFamily: Microsoft YaHei
    heading:
      size: 38px
      weight: 700
    subheading:
      size: 26px
      weight: 700
    body:
      size: 17px
      weight: 400
  colorSystem:
    primary:
      - "#FF8C42"
      - "#FFBF80"
      - "#E06A1E"
    background:
      - "#FFF8F0"
      - "#FFF5EB"
      - "#E8F9F3"
    text:
      - "#3D2C2C"
      - "#FFFFFF"
    functional:
      - "#4ECDC4"
      - "#FFE66D"
      - "#FF6B6B"
todos:
  - id: extend-types
    content: 扩展 PptSlide TypeScript 接口，新增 layout/left_bullets/right_bullets/chart 等字段
    status: pending
  - id: redesign-title
    content: 重写 title 布局样式为温暖橙色插画风格，匹配后端渐变背景和装饰圆形
    status: pending
    dependencies:
      - extend-types
  - id: redesign-content
    content: 升级 content 布局样式，添加编号徽章和温暖橙色配色
    status: pending
    dependencies:
      - extend-types
  - id: add-two-column
    content: 新增 two_column 布局模板和样式，实现左右两栏对比展示
    status: pending
    dependencies:
      - extend-types
  - id: add-chart-layout
    content: 新增 chart 布局，集成 echarts 渲染柱状图/饼图/折线图
    status: pending
    dependencies:
      - extend-types
  - id: add-summary-layout
    content: 新增 summary 布局，实现渐变背景+总结卡片+图标徽章
    status: pending
    dependencies:
      - extend-types
  - id: add-keyboard-shortcuts
    content: 添加键盘快捷键支持（左右箭头/空格/Home/End）和幻灯片切换动画
    status: pending
    dependencies:
      - add-summary-layout
---

## 产品概述

将前端 PPT 展示组件（PptViewer.vue）从现有的深蓝学术风格升级为与后端 PPT 生成文件完全一致的温暖橙色插画风格，并新增三种布局类型和键盘快捷键支持，使前端展示效果与后端生成的 .pptx 文件视觉风格保持一致。

## 核心功能

- **风格统一**：将前端 PPT 展示从深蓝学术风格（#1a56a8）改为温暖橙色插画风格（#FF8C42），与后端 ppt_generator.py 生成的 .pptx 文件配色完全一致
- **two_column 布局**：前端渲染左右两栏对比布局，左栏橙色系、右栏绿色系，中间黄色分隔线
- **chart 布局**：使用项目已安装的 echarts 在前端渲染柱状图/饼图/折线图，左侧图表右侧说明
- **summary 布局**：渲染总结页，渐变背景 + 彩色总结卡片 + 图标徽章
- **键盘快捷键**：支持左右箭头键、Space、Home、End 切换幻灯片

## 技术栈

- 前端框架：Vue 3 + TypeScript（现有）
- UI 组件库：Element Plus（现有）
- 图表库：echarts ^5.5.0（项目已安装，无需额外依赖）
- 样式方案：Scoped CSS + CSS 变量

## 实现方案

### 核心策略

完全重写 `PptViewer.vue` 组件的模板和样式，使其支持后端生成的全部 5 种布局类型，并与后端 `ppt_generator.py` 的配色系统保持一致。

### 关键技术决策

1. **类型定义扩展**：扩展 `PptSlide` 接口，新增 `layout`、`left_title`、`left_bullets`、`right_title`、`right_bullets`、`chart` 字段，与后端 `ppt_generator.py` 的 `_PPT_SYSTEM` prompt 中定义的 JSON 格式完全对齐。

2. **布局渲染策略**：使用 `v-if="currentSlide?.layout === 'xxx'"` 条件渲染五种布局，每种布局独立编写模板，确保样式精确匹配后端设计。

3. **图表渲染**：利用项目已安装的 echarts，在 `nextTick` 中初始化图表实例，监听 `currentIndex` 变化重新渲染。图表配置使用后端 `chart` 字段数据，支持 bar/pie/line 三种类型。

4. **键盘快捷键**：在 `onMounted` 中添加 `keydown` 事件监听，`onUnmounted` 中移除，防止内存泄漏。支持 ArrowLeft/ArrowUp（上一页）、ArrowRight/ArrowDown/Space（下一页）、Home（第一页）、End（最后一页）。

5. **向后兼容**：旧数据可能没有 `layout` 字段，使用 `currentSlide?.layout || 'content'` 提供默认值；旧数据只有 title + bullets 结构，确保不报错。

### 性能考虑

- 图表实例在幻灯片切换时复用（setOption 更新数据）而非重新创建，避免重复初始化开销
- 使用 `computed` 缓存当前幻灯片数据，减少重复计算
- CSS 动画使用 `transform` 和 `opacity`（GPU 加速），避免重排重绘

### 配色系统（与后端 ppt_generator.py 完全一致）

| 用途 | 颜色值 | 后端常量 |
| --- | --- | --- |
| 主色（温暖橙） | `#FF8C42` | `_COLOR_PRIMARY` |
| 主色浅 | `#FFBF80` | `_COLOR_PRIMARY_LIGHT` |
| 主色深 | `#E06A1E` | `_COLOR_PRIMARY_DARK` |
| 辅助色（清新绿） | `#4ECDC4` | `_COLOR_SECONDARY` |
| 辅助色浅 | `#7EFFE4` | `_COLOR_SECONDARY_LIGHT` |
| 强调黄 | `#FFE66D` | `_COLOR_ACCENT_YELLOW` |
| 强调粉 | `#FF6B6B` | `_COLOR_ACCENT_PINK` |
| 背景（暖白） | `#FFF8F0` | `_COLOR_BG` |
| 文字（深棕） | `#3D2C2C` | `_COLOR_TEXT` |


## 实现详情

### 文件修改清单

#### [MODIFY] `frontend/src/components/course/PptViewer.vue`

**修改内容**：

1. **扩展 TypeScript 接口（第 105-110 行）**：

- 新增 `layout` 字段：`'title' | 'content' | 'two_column' | 'chart' | 'summary'`
- 新增 `left_title`、`left_bullets`、`right_title`、`right_bullets` 字段（two_column 布局用）
- 新增 `chart` 字段：包含 `type`、`title`、`categories`、`series`

2. **重写模板（第 1-88 行）**：

- 将现有的 `v-if="currentIndex === 0"` 改为 `v-if="currentSlide?.layout === 'title' || (currentIndex === 0 && !currentSlide?.layout)"`
- 新增 `two_column` 布局模板：左右两栏 flex 布局
- 新增 `chart` 布局模板：左侧 echarts 图表容器 + 右侧说明
- 新增 `summary` 布局模板：渐变背景 + 总结卡片列表
- 保留现有 `content` 布局并升级样式

3. **重写样式（第 159-478 行）**：

- 将所有 `#1a56a8`（深蓝）替换为 `#FF8C42`（温暖橙）
- 将所有 `#0f3b78`、`#2566bb`、`#3b7dd8` 等蓝色系替换为橙色系对应色
- 背景色从 `#fafcff`、`#f0f5ff` 改为 `#FFF8F0`（暖白）
- 新增两种布局的样式

4. **新增键盘快捷键（script 部分）**：

- 导入 `onMounted`、`onUnmounted`
- 添加 `handleKeydown` 函数处理键盘事件
- 在 `onMounted` 中 `window.addEventListener('keydown', handleKeydown)`
- 在 `onUnmounted` 中 `window.removeEventListener('keydown', handleKeydown)`

5. **新增 echarts 图表渲染（script 部分）**：

- 导入 `echarts`
- 新增 `chartRef` ref 绑定图表容器 DOM
- 新增 `initChart` 函数，根据 `currentSlide.chart` 数据配置 echarts 选项
- 在 `watch(currentIndex)` 中调用 `initChart`
- 在 `onUnmounted` 中调用 `echarts.dispose()` 清理图表实例

### 目录结构

```
frontend/src/components/course/
└── PptViewer.vue  # [MODIFY] 主要改造文件
```

## 设计风格

采用与后端 PPT 生成完全一致的**温暖橙色插画风格**（Illustration Style），整体视觉温暖、活泼、有亲和力。设计灵感来源于现代教育类 APP 的插画风格。

## 页面设计

### 整体布局

PPT 查看器占据主内容区域，上方为幻灯片展示区（460px 高度），下方为导航控件和旁白区域。整体圆角 12px，阴影柔和。

### 五种幻灯片布局设计

#### 1. title（标题页）

- **背景**：温暖渐变，`linear-gradient(160deg, #E06A1E 0%, #FF8C42 40%, #FFBF80 100%)`
- **装饰元素**：两个半透明圆形（浅橙色 + 温暖黄），模拟后端的装饰圆形
- **标题卡片**：圆角矩形，白色文字，居中显示，字体大小 38px
- **副标题**：章节名称，温暖黄色 `#FFE66D`，字体大小 18px

#### 2. content（内容页）

- **背景**：暖白 `#FFF8F0`
- **顶部标题栏**：橙色渐变 `#FF8C42 → #FFBF80`，白色文字，左侧有 4px 橙色边框装饰
- **内容卡片**：白色背景，圆角 10px，轻微阴影
- **编号徽章**：每个要点前有一个橙色圆形徽章，内含数字（1,2,3...），白色文字
- **要点文字**：深棕色 `#3D2C2C`，行高 1.7，字体大小 17px

#### 3. two_column（两栏对比页）

- **背景**：暖白 `#FFF8F0`
- **顶部标题栏**：橙色，白色文字
- **左栏**：背景 `#FFF5EB`（极浅橙色），顶部标题栏 `#FF8C42`，要点圆点橙色
- **右栏**：背景 `#E8F9F3`（极浅绿色），顶部标题栏 `#4ECDC4`，要点圆点绿色
- **中间分隔线**：温暖黄 `#FFE66D`，宽度 3px，贯穿上下
- **两栏比例**：左栏 48%，右栏 48%，中间分隔 4%

#### 4. chart（图表页）

- **背景**：暖白 `#FFF8F0`
- **顶部标题栏**：橙色，白色文字
- **左侧图表区**（55% 宽度）：echarts 渲染区域，背景白色圆角卡片
- **右侧说明区**（40% 宽度）：白色卡片，标题"📊 数据分析"，要点前用绿色箭头 "→" 引导
- **图表配色**：使用与后端一致的调色板（橙、绿、黄、粉、浅绿）

#### 5. summary（总结页）

- **背景**：温暖渐变（与 title 页类似但更浅）
- **标题区**：居中橙色圆角卡片，白色文字，字体 30px
- **总结卡片**：每个要点一个卡片，交替使用浅橙/浅绿/浅黄背景，圆角 8px
- **图标徽章**：每个卡片左侧有一个彩色圆形徽章，内含图标（💡✓★⚙♥）
- **底部装饰**：黄色波浪形装饰条

### 导航控件设计

- **上一页/下一页按钮**：橙色边框，悬停时橙色填充 + 白色文字，圆角 8px
- **导航点**：默认灰色，激活状态为橙色长条（width: 28px），过渡动画 0.25s
- **下载按钮**：橙色边框，悬停时填充橙色

### 旁白区域设计

- **背景**：渐变 `#FFF5EB → #FFF8F0`，左侧 4px 橙色边框
- **标题**：深棕色文字，橙色图标
- **讲稿文本**：白色背景卡片，虚线边框，文字 15px，行高 1.8
- **音频播放器**：紧凑模式，与现有 AudioPlayer 组件集成

### 交互设计

- **幻灯片切换**：淡入淡出过渡动画（opacity 0 → 1，0.3s ease）
- **键盘快捷键**：
- `ArrowLeft` / `ArrowUp`：上一页
- `ArrowRight` / `ArrowDown` / `Space`：下一页
- `Home`：跳到第一页
- `End`：跳到最后一页
- **悬停效果**：导航按钮、导航点、下载按钮均有 hover 效果

### 响应式设计

- 幻灯片最小高度 420px，适应不同内容量
- 两栏布局在内容过多时自动滚动
- 图表容器自适应宽度

## Agent Extensions

### SubAgent: code-explorer

- **用途**：在方案执行阶段，需要深入读取 `PptViewer.vue` 的完整内容，以及参考后端 `ppt_generator.py` 的配色和设计细节，确保前端实现与后端完全一致。
- **预期结果**：获取完整的代码上下文，指导具体的代码修改。