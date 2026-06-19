---
name: cover-generator
description: "根据文章内容自动生成高点击率封面 Prompt，输出16:9和9:16两套提示词，用于 GPT Image 配合真人头像融合生成封面图。触发词：生成封面、封面提示词、封面prompt、出封面、封面设计、公众号封面、cover prompt。"
---

# Cover Generator

根据用户提供的一篇文章，自动分析内容、判断文章类型、生成封面标题候选，最后输出两套 Prompt（16:9 横版 + 9:16 竖版），专为 GPT Image 配合真人肖像融合生成封面图而设计。

**核心定位**：输出可直接粘贴到 GPT 网页的提示词，用户上传一张真人头像后即可生成融合封面。

---

## 工作流

### 第一步：分析文章

读取用户提供的文章（支持直接粘贴、或提供本地 `.md`/`.txt` 文件路径），提取以下关键信息：

- **核心主题** — 文章在讲什么（一句话概括）
- **工具/产品名称** — 涉及的具体工具或产品
- **用户收益** — 读者看完能获得什么
- **数字信息** — 出现的数字（如 10 个、3 天、5 倍等）
- **情绪触发点** — 文章传递的核心情绪（紧迫、好奇、惊喜、焦虑、启发等）

### 第二步：判断文章类型

从以下三种类型中选择：

| 类型 | 特点 | 封面策略 |
|------|------|---------|
| **A 工具神器型** | 推荐某款工具/产品/资源，强调"好用""强大""必备" | 工具作为视觉主体，人物做推荐/惊讶/展示手势 |
| **B 教程实战型** | 手把手教怎么做，强调"学会""掌握""从零到一" | 人物做操作/演示动作，画面强调过程感、步骤感 |
| **C 系统改造型** | 方法论/认知升级/习惯改变，强调"变了""不一样了" | 抽象对比或前后变化，人物表情有反差感（对比/顿悟） |

### 第三步：生成 5 个封面标题候选

根据文章内容，生成 5 个不同角度的标题候选：

- **方案A** — 直给利益型（如：`Claude 必装的 10 个插件`）
- **方案B** — 损失厌恶型（如：`少装一个都亏`）
- **方案C** — 社会证明型（如：`高手都在用的 10 个插件`）
- **方案D** — 结果承诺型（如：`装完效率翻倍`）
- **方案E** — 故事钩子型（如：`我最后悔没早点装`）

标题要求：
- 不超过 14 字
- 包含核心利益点
- 优先用数字
- 优先提工具名称
- 有情绪钩子

展示 5 个方案让用户选择或修改。

> 如果用户只输了一句话或一段简短描述而非完整文章，跳过标题候选环节，直接基于用户提供的信息生成封面 Prompt。

### 第四步：确定封面标题

用户选择或修改后，确定最终封面标题（和可选的副标题）。

### 第五步：生成封面 Prompt

输出两套 Prompt，供用户在 GPT Image 中使用。

Prompt 的核心设计原则：

1. **必须预留人物区域** — 描述场景时明确留出人物位置（中景偏左/偏右/居中）
2. **不描述具体人物长相** — 用 `Use uploaded portrait as creator image` 指示模型融合上传的人像
3. **围绕文章类型选视觉风格** — A 工具神器型突出工具/产品展示感；B 教程实战型突出操作/过程感；C 系统改造型突出对比/顿悟感
4. **文字渲染** — 封面标题直接在 Prompt 中指定字体样式和位置
5. **适合 GPT Image** — 画面清晰、构图干净、有留白

---

## 输出格式

```
# 封面分析

文章类型：[A 工具神器型 / B 教程实战型 / C 系统改造型]

核心主题：[一句话概括]

推荐标题：[用户选择或确认的标题]

推荐副标题：[可选]


# 16:9 Prompt

Aspect Ratio: 16:9.
Resolution: 1920 x 1080.

Use uploaded portrait as creator image.

Composition: [人物位置和画面布局的详细描述，明确哪一侧留白给标题文字]

Background: [背景描述，用户指定或模型根据选题决定]

Subject: [画面主体描述。如果是工具神器型：工具/产品/UI 作为视觉焦点；如果是教程实战型：操作/演示画面；如果是系统改造型：对比/变化/顿悟的画面]

Style: cinematic lighting, editorial cover design, high detail, premium magazine aesthetic, 8k detail

Text Rendering: Render the following text directly in the image, as part of the artwork:
- Title: "[封面标题]" — placed in the designated negative space, large size, bold, high contrast, clean sans-serif font
- Subtitle (if any): "[副标题]" — smaller size below the title
The text must be rendered natively, no misspellings, no overlay effect.

Prohibit: No extra random words, no logos, no watermarks, no UI screenshots, no text at edges


# 9:16 Prompt

Aspect Ratio: 9:16.
Resolution: 1080 x 1920.

Use uploaded portrait as creator image.

Composition: [竖版布局。通常人物居上或居中偏下，标题在下半部分留白区；或者人物在画面中心，标题在上方/下方夹住人物]

Background: [背景描述，适配竖版画面]

Subject: [画面主体描述，适配竖版比例]

Style: cinematic lighting, editorial cover design, high detail, premium magazine aesthetic, 8k detail

Text Rendering: Render the following text directly in the image, as part of the artwork:
- Title: "[封面标题]" — placed in the designated space, large size, bold, high contrast, clean sans-serif font
- Subtitle (if any): "[副标题]" — smaller size
The text must be rendered natively, no misspellings, no overlay effect.

Prohibit: No extra random words, no logos, no watermarks, no UI screenshots, no text at edges
```

---

## 使用示例

用户说：
```
使用 cover-generator 分析下面这篇文章：

标题：Codex 必装的 10 个插件清单
正文：......
```

你的输出：
1. 分析文章 → 提取关键信息
2. 判断类型 → A 工具神器型
3. 生成 5 个标题候选 → 让用户确认
4. 用户选择后 → 输出 16:9 和 9:16 两套 Prompt

用户复制 Prompt 到 GPT 网页 → 上传人像 → 生成封面图。

---

## 修改请求

用户如果说"换个风格""标题不对""再出一版"，基于已有上下文只改指定的部分，重新输出两套 Prompt。
