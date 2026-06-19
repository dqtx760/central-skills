---
name: ian-xiaohei-illustrations
description: 生成 KATONG 风格的中文正文配图。用于用户要求为中文文章、帖子、博客、Notion 文档、工作流文档、方法论、流程、结构、状态、隐喻或观点生成“创业者”“KATONG”“企业插画”“正文配图”“文章插图”“配图建议”“shot list”“去标题/改图”等任务；默认使用 KATONG IP（亚洲男性创业者）、极简扁平矢量、皇家蓝主色、白底留白、少量中文标注的干净企业插画风格。
---

# KATONG 创业者正文配图

## 核心定位

为中文文章设计和生成 16:9 横版正文配图。目标不是做 PPT 信息图、可爱卡通或复杂架构图，而是把文章里的关键判断、流程、结构、状态或隐喻，变成一张干净、专业、现代、可读但不说明书的极简扁平矢量插画。

默认视觉 IP 是“KATONG”：亚洲男性创业者，短黑寸头、浓眉细眼、黑hoodie、皇家蓝裤子、胸前白色 34 号徽章。KATONG 必须参与画面的核心动作，不能只是站在旁边当装饰。

## 先读这些参考

按任务需要读取，不要一次塞满上下文：

- `references/style-dna.md`：风格 DNA、颜色、文字、禁忌。
- `references/xiaohei-ip.md`：KATONG IP 的形象、性格、动作库和禁忌（文件名沿用，内容已是 KATONG）。
- `references/composition-patterns.md`：结构类型、原创隐喻方法和反复刻规则。
- `references/prompt-template.md`：单张生图提示词模板。
- `references/qa-checklist.md`：生成后检查和迭代规则。
- `assets/examples/`：只作低频视觉校准，不进入默认生成路径。不要照抄这些案例的构图、物件或标注。

## 工作流

### 1. 消化正文

先读用户给的正文、链接、Notion 页面、Markdown 文件或截图内容。提炼：

- 核心观点是什么
- 哪些段落承担认知转折
- 哪些内容适合用图解释
- 哪些地方只适合文字，不需要图

不要平均配图。优先选择“认知锚点”，例如：核心判断、两个断点、输入输出闭环、分流、前后对比、一鱼多吃、承接路径、常见坑、角色状态变化。

### 2. 先出配图策略

如果用户只是说“分析怎么配图 / 思考哪些地方需要配图”，先给 shot list。每张图写清楚：

- 放在哪个段落后
- 图的主题
- 核心意思
- 结构类型
- KATONG 在图里做什么
- 建议元素
- 建议中文标注词

默认 4-8 张。文章很短时 1-3 张；长文也不要轻易超过 9 张。够用就好，避免把正文做成画册。

### 3. 单张生成

如果用户明确要求“生成 / 输出 / 做图 / 帮我生成”，不要停下来等确认；用 `scripts/gemini_image_gen.py` 本地生图后端，每张单独生成。不要把多张图拼在一张里。

生图后端调用方式（把整个提示词写进一个临时文件再用 `@` 传入，提示词通常很长）：

```bash
# 先把这张图的提示词按 prompt-template.md 写好，存成 prompt_01.txt
python scripts/gemini_image_gen.py gen @prompt_01.txt -o assets/<article-slug>-illustrations --name 01-topic-name
```

- 提示词必须按 `references/prompt-template.md` 填满所有变量后调用，不要留 `{}` 占位符。
- 一次只生成一张。多张就多次调用，文件名按 `01- / 02-` 递增。
- 局部编辑（去标题、修正角色一致性）用 `edit` 子命令：`python scripts/gemini_image_gen.py edit "去掉左上角标题XXX" -i assets/.../01-xxx.png`。
- 首次使用见文末「生图后端配置」一节。

每张图只讲一个核心结构。提示词必须包含：

- 16:9 横版中文正文配图
- 纯白背景
- 极简扁平矢量风格、干净轮廓线
- KATONG 的完整特征（短黑寸头 / 浓眉细眼 / 黑hoodie / 皇家蓝裤子 #4A78F0 / 胸前白色 34 号徽章）
- 少量红色/蓝色中文无衬线标注
- 大量留白
- KATONG 作为核心动作主体
- 禁止 anime / 3D / 写实 / PPT / 幼稚可爱 / 复杂架构 / 左上角类型标题

不要复刻过往案例。案例只提供风格密度和 KATONG 参与方式，不能直接复用已有构图，除非用户明确要求复刻某张图。每次都要从当前文章重新发明一个成立的隐喻。

### 4. 检查与迭代

生成后检查 `references/qa-checklist.md`。如果出现以下问题，优先重生成或局部编辑：

- KATONG 只是装饰，没参与核心动作
- 角色特征漂移（丢了徽章 34、换了发色、画风变 anime/3D）
- 画面太满
- 太像流程图/PPT
- 中文太多或错字严重
- 左上角出现“常见坑/流程图/系统架构图”等标题
- 背景不是干净白底

### 5. 保存交付

如果用户在 workspace 内工作，把最终图复制到：

```text
assets/<article-slug>-illustrations/
```

按顺序命名：

```text
01-topic-name.png
02-topic-name.png
```

保留原始生成文件，不要覆盖已有资产，除非用户明确要求替换。

## 输出口径

生成前的策略输出要短而准。生成后的交付要包含：

- 生成了几张
- 每张图的用途
- 保存路径
- 哪些图最稳，哪些图是可选

不要长篇解释风格理论；让图自己说话。

## 生图后端配置（仅首次使用）

本 skill 的生图能力由 `scripts/gemini_image_gen.py` 提供，它通过逆向 `gemini.google.com` 网页接口调用 Gemini Pro（Nano Banana）生图，生成后下载到本地。首次使用需配置一次鉴权 cookie：

1. 安装依赖（一次性）：

   ```bash
   pip install -U gemini_webapi python-dotenv
   ```

2. 复制 `.env.example` 为 `.env`，填入两个 cookie：

   - 用浏览器（建议无痕窗口）登录 https://gemini.google.com
   - F12 → Application → Cookies → 复制 `__Secure-1PSID` 和 `__Secure-1PSIDTS` 的值
   - 粘到 `.env` 的 `GEMINI_1PSID` 和 `GEMINI_1PSIDTS`

3. 验证可用性（可选）：

   ```bash
   python scripts/gemini_image_gen.py gen "Generate one image. Minimalist flat vector, an Asian male entrepreneur with short black buzz cut, black hoodie, royal blue pants, white chest badge number 34, pushing a heavy box on a clean white background."
   ```

   若在默认输出目录（`D:\data\images\Article-illustrations` 或 `.env` 里配的 `IMAGE_OUTPUT_DIR`）下看到生成的 png，说明后端通了。

注意：

- 登录账号需 ≥18 岁，且账号所在地区/语言支持 Gemini 生图（Nano Banana）。
- `__Secure-1PSIDTS` 有效期短，脚本运行期间会自动刷新；长期不用重新取即可。
- 这两个 cookie 等同于登录态，已在 `.gitignore` 默认排除，切勿提交或外泄。
- 若环境无内置生图工具，本脚本是唯一生图路径；若环境已有 `image_gen` 工具，两者可并存，按可用性择一。
