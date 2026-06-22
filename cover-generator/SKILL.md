---
name: cover-generator
description: "根据文章内容或选题直接生成高点击率短视频封面图，默认输出16:9横屏和9:16竖屏两版，使用固定真人头像融图，保存到本地归档目录。触发词：生成封面、封面提示词、封面prompt、出封面、封面设计、短视频封面、B站封面、小红书封面、抖音封面、cover prompt。"
---

# Cover Generator

根据用户提供的一篇文章、选题或简短描述，自动分析内容、判断文章类型、确定封面标题，并直接生成两张短视频封面图（16:9 横版 + 9:16 竖版），专为小红书、抖音、视频号、B 站、YouTube 等短视频/视频平台封面而设计。

**核心定位**：直接生成图片，而不是只解释或只输出 Prompt。封面必须包含标题文字、真人头像融合、强视觉冲击，并适配视频号、B 站等平台裁切规则。

**固定融图头像**：每次生成封面时，必须使用 `D:\data\images\头像\297.png` 作为真人头像参考图进行融图。

**人物融合方式**：默认采用“身份保持的全场景商业封面生成”，让人物像真实参与拍摄一样自然出现在场景中；不要把原始照片简单裁切、圆角、贴到背景里，除非用户明确要求“照片拼贴/证件照合成/保持原照片不变”。如果用户额外提供了指定人物图，应优先使用用户提供的人物图作为身份参考，并在 Prompt 中强调保留面部身份、短发/服装气质、自然姿态、电影级布光和整图一致的拍摄质感。

**效果优先级**：短视频封面应优先追求“高点击率商业封面感”：大标题、强光效、真实人物入镜、科技/产品场景完整、人物与背景光影统一。人物相似度很重要，但不能为了完全保留原照片而退化成明显的拼贴感。若生成图“效果好但不像本人”，下一轮应基于该成品风格做身份修正，而不是改用简单照片贴图。

**输出目录**：生成后的横屏和竖屏封面必须归档到 `D:\data\images\Article-illustrations`。

**图床规则**：`cover-generator` 生成的是短视频封面，不上传图床，只保存本地。如用户另有明确要求，再单独处理。

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

> 如果用户只输了一句话或一段简短描述而非完整文章，跳过标题候选环节，直接基于用户提供的信息生成横屏和竖屏封面图。

### 第四步：确定封面标题

用户选择或修改后，确定最终封面标题（和可选的副标题）。

### 第五步：生成封面图

直接生成两张封面图：

- **16:9 横版**：用于 B 站、YouTube、视频号个人空间等横版场景。
- **9:16 竖版**：用于小红书、抖音、视频号竖屏场景。

生成后保存到 `D:\data\images\Article-illustrations`，文件名应包含选题关键词、比例和日期，便于检索。

生图核心设计原则：

1. **必须使用固定头像融图** — 使用 `D:\data\images\头像\297.png`，只融合人物身份和脸部特征，不改变选题场景
2. **必须预留人物区域** — 描述场景时明确留出人物位置（中景偏左/偏右/居中），人物脸部、手势和身体主体不得贴边
3. **不描述具体人物长相** — 只用固定头像参考图指示模型融合上传的人像，不额外编造五官、年龄、发型等细节
4. **围绕文章类型选视觉风格** — A 工具神器型突出工具/产品展示感；B 教程实战型突出操作/过程感；C 系统改造型突出对比/顿悟感
5. **标题必须出现在图里** — 封面标题必须直接渲染在图片中，不能只生成无字背景图
6. **适合短视频缩略图** — 画面清晰、构图干净、有留白，手机小图也能看清主标题和人物脸
7. **禁止低质拼贴感** — 不要把真人照片作为一个矩形、圆角卡片、硬边抠图或单独图层贴在背景上；人物必须与场景透视、光源、阴影、桌面和环境氛围统一，像同一张照片/海报里真实拍出来的主体。
8. **身份漂移处理** — 如果首轮人物不像参考人，应保留首轮的构图、标题、背景、光效和商业封面质感，只针对人物身份做二次修正；不要退回到“原照片直接贴进画面”的方案。

### 平台裁切安全区

生成 Prompt 时必须加入安全区约束，避免上传到视频号、B 站后被裁切掉标题或人物：

- **16:9 横版封面**：核心主体、人物脸部、手势、标题、副标题、产品信息必须收进画面中央安全区；左右各保留约 10%-15% 可裁切背景。边缘区域只放氛围背景、虚化环境、光效或装饰元素，不放重要文字、人脸、手势、产品名和关键 UI。横版封面要兼容视频号首页推荐的 4:3 裁切，因此人物和内容都要略向中间收，不要贴左右边。
- **9:16 竖版封面**：核心主体、人物脸部、标题、副标题必须位于中部安全区；顶部和底部各保留约 10%-15% 可裁切背景。顶部不要顶标题，底部不要放关键文字、人脸、手势和产品信息，避免被平台按钮、标题栏、进度条或封面编辑 UI 遮挡。
- **不要简单缩小全部元素**：安全区的目标是把关键信息收进中间，把边缘留给背景；仍要保持标题足够大、人物脸部清晰、视觉冲击力强。

---

## 生图执行要求

调用生图能力时，应为横版和竖版分别生成，不要只生成一种比例再强行裁切。

横版生图提示词必须包含：

- 16:9，1920 x 1080
- 使用 `D:\data\images\头像\297.png` 作为真人头像参考图
- 标题文字直接出现在图中
- 人物、标题、核心道具和产品信息位于中央安全区
- 左右各 10%-15% 是可裁切背景，兼容 4:3 裁切

竖版生图提示词必须包含：

- 9:16，1080 x 1920
- 使用 `D:\data\images\头像\297.png` 作为真人头像参考图
- 标题文字直接出现在图中
- 人物脸部、标题和核心道具位于中部安全区
- 顶部和底部各 10%-15% 是可裁切背景，避开平台按钮、标题栏、进度条和封面编辑 UI

生成完成后：

- 保存横屏和竖屏两版到 `D:\data\images\Article-illustrations`
- 不上传图床
- 向用户返回本地文件路径，并简要说明两版分别适合哪个平台

---

## Prompt 参考格式

以下 Prompt 格式用于驱动生图，不是默认交付物。除非用户明确要求“只给 Prompt”，否则应该直接生成图片。

```
# 封面分析

文章类型：[A 工具神器型 / B 教程实战型 / C 系统改造型]

核心主题：[一句话概括]

推荐标题：[用户选择或确认的标题]

推荐副标题：[可选]


# 16:9 Prompt

Aspect Ratio: 16:9.
Resolution: 1920 x 1080.

Use the uploaded portrait reference image from D:\data\images\头像\297.png as the creator image. Preserve the creator's face identity from the reference photo, but adapt lighting, pose, clothing and scene to the cover concept.

Composition: [人物位置和画面布局的详细描述，明确哪一侧留白给标题文字。人物、标题、核心道具和产品信息都收进中央安全区，左右各保留约 10%-15% 可裁切背景，兼容 4:3 裁切]

Background: [背景描述，用户指定或模型根据选题决定]

Subject: [画面主体描述。如果是工具神器型：工具/产品/UI 作为视觉焦点；如果是教程实战型：操作/演示画面；如果是系统改造型：对比/变化/顿悟的画面]

Style: cinematic lighting, editorial cover design, high detail, premium magazine aesthetic, 8k detail

Text Rendering: Render the following text directly in the image, as part of the artwork:
- Title: "[封面标题]" — placed in the designated negative space, large size, bold, high contrast, clean sans-serif font
- Subtitle (if any): "[副标题]" — smaller size below the title
The text must be rendered natively, no misspellings, no overlay effect.

Safe Area: Keep all important text, the creator's face, hands, product names, icons and key UI elements inside the central safe area. Leave the left and right 10%-15% as non-essential background only.

Prohibit: No extra random words, no logos, no watermarks, no UI screenshots, no text at edges, no face or hands touching the edges


# 9:16 Prompt

Aspect Ratio: 9:16.
Resolution: 1080 x 1920.

Use the uploaded portrait reference image from D:\data\images\头像\297.png as the creator image. Preserve the creator's face identity from the reference photo, but adapt lighting, pose, clothing and scene to the cover concept.

Composition: [竖版布局。通常人物居中或中部偏下，标题在中部偏上或中部留白区；人物脸部、标题和核心道具全部进入中部安全区，顶部和底部各保留约 10%-15% 可裁切背景]

Background: [背景描述，适配竖版画面]

Subject: [画面主体描述，适配竖版比例]

Style: cinematic lighting, editorial cover design, high detail, premium magazine aesthetic, 8k detail

Text Rendering: Render the following text directly in the image, as part of the artwork:
- Title: "[封面标题]" — placed in the designated space, large size, bold, high contrast, clean sans-serif font
- Subtitle (if any): "[副标题]" — smaller size
The text must be rendered natively, no misspellings, no overlay effect.

Safe Area: Keep all important text, the creator's face, hands, product names, icons and key UI elements inside the middle safe area. Leave the top and bottom 10%-15% as non-essential background only.

Prohibit: No extra random words, no logos, no watermarks, no UI screenshots, no text at edges, no title touching the top edge, no key information near the bottom edge
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
4. 用户选择后 → 直接生成 16:9 和 9:16 两张封面图
5. 保存到 `D:\data\images\Article-illustrations`，不上传图床

如用户只给一句话或已明确标题，不需要停下来解释 Prompt，可直接生成两版封面。

---

## 修改请求

用户如果说"换个风格""标题不对""再出一版"，基于已有上下文只改指定的部分，重新生成横屏和竖屏封面图。只有用户明确要求“只给 Prompt”时，才重新输出两套 Prompt。

---

## 执行注意事项

1. **读取本 Skill 时必须优先使用 UTF-8**

   在 Windows PowerShell 中读取 `SKILL.md` 时，必须显式指定 UTF-8，避免中文说明显示成乱码：

   ```powershell
   Get-Content -LiteralPath 'C:\Users\Administrator\.agents\skills\cover-generator\SKILL.md' -Encoding UTF8
   ```

   如果首次读取出现乱码，不要据此判断文件内容损坏；先用 `-Encoding UTF8` 重新读取。

2. **读取用户提供的 `.md` / `.txt` 内容时也必须优先使用 UTF-8**

   视频脚本、文章素材和封面字段通常是 UTF-8 中文文件。读取本地素材时应显式指定 UTF-8，确保标题、封面主标题、副标题和正文不会乱码：

   ```powershell
   Get-Content -LiteralPath '<用户提供的文件路径>' -Raw -Encoding UTF8
   ```

   封面标题必须优先采用素材中已有字段，例如 `封面主标题`、`封面副标题`、`封面标题`；生成前要核对原文，避免把用户已有标题改写错。

3. **在 PowerShell 中不要使用 `$home` 作为临时变量名**

   PowerShell 里的 `$HOME` 是内置只读变量，变量名大小写不敏感，使用 `$home = ...` 可能报错。需要保存 Codex 目录或用户目录时，使用其他变量名，例如：

   ```powershell
   $codexHome = $env:CODEX_HOME
   if (-not $codexHome) {
     $codexHome = Join-Path $env:USERPROFILE '.codex'
   }
   ```

   如果生图工具已经提示了默认生成目录，应优先直接使用该目录定位图片，不要盲目递归扫描整个 `.codex` 目录。

4. **在 PowerShell 中不要使用 Bash here-doc 写法**

   Windows PowerShell 不支持 `python - <<'PY' ... PY` 这类 Bash 写法，会报：

   ```text
   Missing file specification after redirection operator.
   The '<' operator is reserved for future use.
   ```

   如果需要执行短 Python 检查，使用：

   ```powershell
   python -c "from PIL import Image; print('PIL ok')"
   ```

   如果需要执行多行 Python，优先把脚本写成 UTF-8 `.py` 文件后运行；或使用 PowerShell here-string 管道：

   ```powershell
   @'
   print("hello")
   '@ | python -
   ```

5. **中文路径传给 Python / 脚本时要特别处理**

   用户素材和头像路径经常包含中文，例如 `D:\data\images\头像\...`。在 PowerShell 管道、临时脚本或某些 Python stdin 场景里，中文路径可能被转成 `??`，导致 `OSError: [Errno 22] Invalid argument`。

   稳妥做法：

   - 文件操作优先使用 `-LiteralPath`，不要让 PowerShell 把特殊字符或中文路径错误解析。
   - 如果要交给 Python 图像处理，优先复制一份到 ASCII 临时路径，再处理副本；不要改动原图。
   - 复制命令示例：

   ```powershell
   Copy-Item -LiteralPath 'D:\data\images\头像\人物图.png' -Destination 'D:\zed-workspace\portrait_ref.png' -Force
   ```

   这只是在当前工作区创建一个处理副本，不删除、不移动用户原始素材。

6. **不要把“保证像本人”误解成“本地照片拼贴”**

   如果用户反馈“人物不像本人”，优先使用上一版效果好的 AI 封面作为风格/构图基础，继续做身份修正；不要默认改成本地脚本把原始照片矩形、圆角或硬边贴进背景。只有用户明确要求“保持原照片不变”“照片合成”“证件照风格”时，才走本地照片拼贴/合成路线。
