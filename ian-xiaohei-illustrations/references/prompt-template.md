# 生图提示词模板

每张图单独生成。根据正文内容替换变量，不要把多张图拼在一起。

```text
Generate one standalone 16:9 horizontal Chinese article illustration.

Visual DNA:
Minimalist flat vector illustration, geometric vector style, clean outlines, solid color blocks. Pure white or very light background. Lots of empty white space. Corporate startup illustration feel, modern and clean. No gradients, no shadows, no paper texture, no complex background, no hand-drawn wobbly lines, no sketch feeling. Use a clean sans-serif font for any text.

Recurring IP character required (keep these features EXACTLY consistent in every image):
A minimalist flat vector character based on an Asian male entrepreneur. Short black buzz cut hair, strong eyebrows, narrow eyes, defined jawline, calm confident expression. Black hoodie, royal blue pants (hex #4A78F0), clean white chest badge with the number 34. Geometric vector illustration, clean outlines, high consistency character design. The character must perform the core conceptual action of this illustration, not stand beside it as decoration. No anime, no manga, no Pixar, no 3D render, no photorealistic style.

Theme:
{正文配图主题}

Structure type:
{结构类型：Workflow / 系统局部 / 前后对比 / 角色状态 / 概念隐喻 / 方法分层 / 地图路线 / 小漫画分镜}

Core idea:
{这张图要表达的核心意思}

Composition:
{具体画面：KATONG 在哪里、正在做什么、主要物件是什么、信息如何流动}

Suggested elements:
{元素1} / {元素2} / {元素3} / {元素4}

Chinese labels (use clean sans-serif font, not handwritten):
{标注词1} / {标注词2} / {标注词3} / {标注词4} / {可选标注词5}

Color use:
Black for the character's hoodie, main outlines, structures, main objects and main text. Royal blue (#4A78F0) for the character's pants, main flow, paths and arrows. Red only for key warnings/problems/results. Light blue only for secondary notes or feedback/system state. Neutral grey for auxiliary lines and secondary structures.

Constraints:
One image explains only one core structure. Keep the main subject around 40%-60% of the canvas. Preserve at least 35% blank white space. Use at most 5-8 short Chinese labels. Do not write a title in the top-left corner. Do not write the structure type on the image. Do not make it a formal diagram, course slide, or dense explainer. Do not copy prior examples or reuse known case compositions unless explicitly requested; invent a fresh visual metaphor for this specific article. It should be clean, professional, modern and clear.
```

## 图像编辑提示

去掉左上角标题：

```text
Edit the provided image. Remove only the text "{要删除的文字}" and its underline from the top-left corner. Fill that area with the same clean white background, matching the surrounding blank area. Preserve everything else exactly: the character, labels, paths, line style, composition, aspect ratio, and image quality. Do not add any new text or objects.
```

修正角色一致性（当生成的 KATONG 偏离原型时）：

```text
Edit the provided image. Keep the core meaning and simple layout, but fix the main character to match this spec EXACTLY: Asian male entrepreneur, short black buzz cut hair, strong eyebrows, narrow eyes, defined jawline, calm confident expression, black hoodie, royal blue pants (#4A78F0), white chest badge with number 34, minimalist flat vector style, clean outlines. Make the character the main actor performing the core action. No anime, no manga, no 3D, no photorealistic.
```

增强主角参与感（当 KATONG 太装饰时）：

```text
Regenerate this illustration with the same core meaning and simple layout, but make the character (Asian male entrepreneur, black hoodie, royal blue pants, white badge "34") more central to the conceptual action. The character should be doing the work that explains the idea, not standing beside the diagram. Keep it clean, flat vector, professional, not cute.
```
