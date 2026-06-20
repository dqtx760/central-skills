---
name: baoyu-article-illustrator
description: Analyzes article structure, identifies positions requiring visual aids, generates illustrations with Type × Style two-dimension approach. Use when user asks to "illustrate article", "add images", "generate images for article", or "为文章配�?.
---

# Article Illustrator

Analyze articles, identify illustration positions, generate images with Type × Style consistency.

## Two Dimensions

| Dimension | Controls | Examples |
|-----------|----------|----------|
| **Type** | Information structure | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | Visual aesthetics | notion, warm, minimal, blueprint, watercolor, elegant |

Combine freely: `--type infographic --style blueprint`

## Types

| Type | Best For |
|------|----------|
| `infographic` | Data, metrics, technical |
| `scene` | Narratives, emotional |
| `flowchart` | Processes, workflows |
| `comparison` | Side-by-side, options |
| `framework` | Models, architecture |
| `timeline` | History, evolution |

## Styles

See [references/styles.md](references/styles.md) for Core Styles, full gallery, and Type × Style compatibility.

## Workflow

```
- [ ] Step 1: Pre-check (EXTEND.md, references, config)
- [ ] Step 2: Analyze content
- [ ] Step 3: Confirm settings (AskUserQuestion)
- [ ] Step 4: Generate images
- [ ] Step 5: Finalize & Upload & Upload
```

### Step 1: Pre-check

**1.5 Load Preferences (EXTEND.md) �?BLOCKING**

```bash
test -f .claude/skills/baoyu-article-illustrator/EXTEND.md && echo "project"
test -f "$HOME/.claude/skills/baoyu-article-illustrator/EXTEND.md" && echo "user"
```

| Result | Action |
|--------|--------|
| Found | Read, parse, display summary |
| Not found | �?Run [first-time-setup](references/config/first-time-setup.md) |

Full procedures: [references/workflow.md](references/workflow.md#step-1-pre-check)

### Step 2: Analyze

| Analysis | Output |
|----------|--------|
| Content type | Technical / Tutorial / Methodology / Narrative |
| Purpose | information / visualization / imagination |
| Core arguments | 2-5 main points |
| Positions | Where illustrations add value |

**CRITICAL**: Metaphors �?visualize underlying concept, NOT literal image.

Full procedures: [references/workflow.md](references/workflow.md#step-2-setup--analyze)

### Step 3: Confirm Settings ⚠️

**ONE AskUserQuestion, max 4 Qs. Q1-Q3 REQUIRED.**

| Q | Options |
|---|---------|
| **Q1: Type** | [Recommended], infographic, scene, flowchart, comparison, framework, timeline, mixed |
| **Q2: Density** | minimal (1-2), balanced (3-5), per-section (Recommended), rich (6+) |
| **Q3: Style** | [Recommended], minimal-flat, sci-fi, hand-drawn, editorial, scene, Other |
| Q4: Language | When article language �?EXTEND.md setting |

Full procedures: [references/workflow.md](references/workflow.md#step-3-confirm-settings-)

### Step 4: Generate Images

1. Create prompts per [references/prompt-construction.md](references/prompt-construction.md)
2. **Detect available image generation method**:
   - **Method A (Claude Code)**: Use `/image` skill directly
   - **Method B (Other environments)**: Use Python script directly
3. Process references (`direct`/`style`/`palette`)
4. Apply watermark if EXTEND.md enabled
5. Generate sequentially
6. Retry once on failure

**Method A - Claude Code (with `/image` skill)**:
```bash
/image "<prompt>" -o illustrations/{topic}/01-{type}-{slug}.png
```

**Method B - Direct Python call (universal)**:
```bash
python "D:\data\images\Article-illustrations\gpt_image2_gen.py" \
  "<prompt>" "D:\data\images\Article-illustrations\NN-{type}-{slug}.png" \
  16:9 1k
```

**Method C - Batch generation**:
```bash
# 批量生成时，逐张调用
for i in 1 2 3 4 5; do
  python "D:\data\images\Article-illustrations\gpt_image2_gen.py" \
    "$prompt_$i" "D:\data\images\Article-illustrations\0$i-{type}-{slug}.png" \
    16:9 1k
done
```



Full procedures: [references/workflow.md](references/workflow.md#step-4-generate-images)

### Step 5: Finalize & Upload

图片生成后，自动通过 PicGo API 上传到图床，拿到外网 URL 再插入文章。

```
Article Illustration Complete!
Article: [path] | Type: [type] | Density: [level] | Style: [style]
Images: X generated, X uploaded to PicGo
```

**自动上传流程**:
1. 每张图片生成后，立即通过 PicGo API 上传
2. 拿到外网 URL 替换本地路径
3. 最终插入文章的图片地址为外网 URL

```bash
# PicGo 上传 API
curl -X POST "http://127.0.0.1:36677/upload" \
  -H "Content-Type: application/json" \
  -H "X-PicGo-Token: <TOKEN>" \
  -d '{"list": ["<图片绝对路径>"]}'
# 返回: {"success": true, "result": ["<外网URL>"]}
```

Full procedures: [references/workflow.md](references/workflow.md#step-5-finalize--upload)

## Output Directory

```
illustrations/{topic-slug}/
├── source-{slug}.{ext}
├── references/           # if provided
├── prompts/
└── NN-{type}-{slug}.png
```

**Slug**: 2-4 words, kebab-case. **Conflict**: append `-YYYYMMDD-HHMMSS`.

## Modification

| Action | Steps |
|--------|-------|
| Edit | Update prompt �?Regenerate �?Update reference |
| Add | Position �?Prompt �?Generate �?Insert |
| Delete | Delete files �?Remove reference |

## Local Environment Configuration

**Image Generation Backend**: `gpt_image2_gen.py` (GPT-Image-2 via Apimart API)

| Component | Path | Status |
|-----------|-------|--------|
| 生图脚本 | `D:\data\images\Article-illustrations\gpt_image2_gen.py` | ✅ 已配置 |
| API | Apimart (GPT-Image-2) | 内置 API Key |
| 输出目录 | `D:\data\images\Article-illustrations\` | 固定输出目录 |

**调用方式**:
```bash
python "D:\data\images\Article-illustrations\gpt_image2_gen.py" \
  "<prompt>" "D:\data\images\Article-illustrations\NN-{type}-{slug}.png" \
  16:9 1k
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| prompt | 图片描述提示词 | 必填 |
| output_path | 保存路径 | 必填 |
| size | 画面比例 | `16:9`（`1:1`, `4:3`, `16:9` 可选） |
| resolution | 分辨率 | `1k`（`2k`, `4k` 可选） |
### Environment-Specific Usage

| Environment | Method | Command |
|------------|----------|----------|
| **Claude Code** | `/image` skill | `/image "<prompt>" -o <path>` |
| **Claudian/Obsidian** | Python script | `python D:\zhishiku\.claude\skills\image\scripts\generate_image.py "<prompt>" -o <path>` |
| **Other** | Python script | `python <image-skill-path>/scripts/generate_image.py "<prompt>" -o <path>` |

**Note**: In non-Claude Code environments, always use the Python script directly instead of slash commands.

## References

| File | Content |
|------|---------|
| [references/workflow.md](references/workflow.md) | Detailed procedures |
| [references/usage.md](references/usage.md) | Command syntax |
| [references/styles.md](references/styles.md) | Style gallery |
| [references/prompt-construction.md](references/prompt-construction.md) | Prompt templates |
| [references/config/first-time-setup.md](references/config/first-time-setup.md) | First-time setup |

