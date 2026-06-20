# Detailed Workflow Procedures

## Step 1: Pre-check

### 1.0 Detect & Save Reference Images ⚠️ REQUIRED if images provided

Check if user provided reference images. Handle based on input type:

| Input Type | Action |
|------------|--------|
| Image file path provided | Copy to `references/` subdirectory → can use `--ref` |
| Image in conversation (no path) | **ASK user for file path** with AskUserQuestion |
| User can't provide path | Extract style/palette verbally → append to prompts (NO frontmatter references) |

**CRITICAL**: Only add `references` to prompt frontmatter if files are ACTUALLY SAVED to `references/` directory.

**If user provides file path**:
1. Copy to `references/NN-ref-{slug}.png`
2. Create description: `references/NN-ref-{slug}.md`
3. Verify files exist before proceeding

**If user can't provide path** (extracted verbally):
1. Analyze image visually, extract: colors, style, composition
2. Create `references/extracted-style.md` with extracted info
3. DO NOT add `references` to prompt frontmatter
4. Instead, append extracted style/colors directly to prompt text

**Description File Format** (only when file saved):
```yaml
---
ref_id: NN
filename: NN-ref-{slug}.png
---
[User's description or auto-generated description]
```

**Verification** (only for saved files):
```
Reference Images Saved:
- 01-ref-{slug}.png ✓ (can use --ref)
- 02-ref-{slug}.png ✓ (can use --ref)
```

**Or for extracted style**:
```
Reference Style Extracted (no file):
- Colors: #E8756D coral, #7ECFC0 mint...
- Style: minimal flat vector, clean lines...
→ Will append to prompt text (not --ref)
```

---

### 1.1 Determine Input Type

| Input | Output Directory | Next |
|-------|------------------|------|
| File path | Ask user (1.2) | → 1.2 |
| Pasted content | `illustrations/{topic-slug}/` | → 1.4 |

**Backup rule for pasted content**: If `source.md` exists in target directory, rename to `source-backup-YYYYMMDD-HHMMSS.md` before saving.

### 1.2-1.4 Configuration (file path input only)

Check preferences and existing state, then ask ALL needed questions in ONE AskUserQuestion call (max 4 questions).

**Questions to include** (skip if preference exists or not applicable):

| Question | When to Ask | Options |
|----------|-------------|---------|
| Output directory | No `default_output_dir` AND no `absolute_output_path` in EXTEND.md | `{article-dir}/`, `{article-dir}/imgs/` (Recommended), `{article-dir}/illustrations/`, `illustrations/{topic-slug}/` |
| Existing images | Target dir has `.png/.jpg/.webp` files | `supplement`, `overwrite`, `regenerate` |
| Article update | Always (file path input) | `update`, `copy` |

**Preference Values** (if configured, skip asking):

| Field | Path |
|-------|------|
| `absolute_output_path` | Uses absolute path directly (highest priority) |
| `default_output_dir` | See options below |

| `default_output_dir` | Path |
|----------------------|------|
| `same-dir` | `{article-dir}/` |
| `imgs-subdir` | `{article-dir}/imgs/` |
| `illustrations-subdir` | `{article-dir}/illustrations/` |
| `independent` | `illustrations/{topic-slug}/` |

### 1.5 Load Preferences (EXTEND.md) ⛔ BLOCKING

**CRITICAL**: If EXTEND.md not found, MUST complete first-time setup before ANY other questions or steps. Do NOT proceed to reference images, do NOT ask about content, do NOT ask about type/style — ONLY complete the preferences setup first.

```bash
test -f .claude/skills/baoyu-article-illustrator/EXTEND.md && echo "project"
test -f "$HOME/.claude/skills/baoyu-article-illustrator/EXTEND.md" && echo "user"
```

| Result | Action |
|--------|--------|
| Found | Read, parse, display summary → Continue |
| Not found | ⛔ **BLOCKING**: Run first-time setup ONLY ([config/first-time-setup.md](config/first-time-setup.md)) → Complete and save EXTEND.md → Then continue |

**Supports**: Watermark | Preferred type/style | Custom styles | Language | Output directory

---

## Step 2: Setup & Analyze

### 2.1 Analyze Content

| Analysis | Description |
|----------|-------------|
| Content type | Technical / Tutorial / Methodology / Narrative |
| Illustration purpose | information / visualization / imagination |
| Core arguments | 2-5 main points to visualize |
| Visual opportunities | Positions where illustrations add value |
| Recommended type | Based on content signals and purpose |
| Recommended density | Based on length and complexity |

### 2.2 Extract Core Arguments

- Main thesis
- Key concepts reader needs
- Comparisons/contrasts
- Framework/model proposed

**CRITICAL**: If article uses metaphors (e.g., "电锯切西瓜"), do NOT illustrate literally. Visualize the **underlying concept**.

### 2.3 Identify Positions

**Illustrate**:
- Core arguments (REQUIRED)
- Abstract concepts
- Data comparisons
- Processes, workflows

**Do NOT Illustrate**:
- Metaphors literally
- Decorative scenes
- Generic illustrations

### 2.4 Analyze Reference Images (if provided in Step 1.0)

For each reference image:

| Analysis | Description |
|----------|-------------|
| Visual characteristics | Style, colors, composition |
| Content/subject | What the reference depicts |
| Suitable positions | Which sections match this reference |
| Style match | Which illustration types/styles align |
| Usage recommendation | `direct` / `style` / `palette` |

| Usage | When to Use |
|-------|-------------|
| `direct` | Reference matches desired output closely |
| `style` | Extract visual style characteristics only |
| `palette` | Extract color scheme only |

---

## Step 3: Confirm Settings ⚠️

**Do NOT skip.** Use ONE AskUserQuestion call with max 4 questions. **Q1, Q2, Q3 are ALL REQUIRED.**

### Q1: Illustration Type ⚠️ REQUIRED
- [Recommended based on analysis] (Recommended)
- infographic / scene / flowchart / comparison / framework / timeline / mixed

### Q2: Density ⚠️ REQUIRED - DO NOT SKIP
- minimal (1-2) - Core concepts only
- balanced (3-5) - Major sections
- per-section - At least 1 per section/chapter (Recommended)
- rich (6+) - Comprehensive coverage

### Q3: Style ⚠️ REQUIRED (ALWAYS ask, even with preferred_style in EXTEND.md)

If EXTEND.md has `preferred_style`:
- [Custom style name + brief description] (Recommended)
- [Top compatible core style 1]
- [Top compatible core style 2]
- Other (see full Style Gallery)

If no `preferred_style` (present Core Styles first):
- [Best compatible core style] (Recommended)
- [Other compatible core style 1]
- [Other compatible core style 2]
- Other (see full Style Gallery)

**Core Styles** (simplified selection):

| Core Style | Best For |
|------------|----------|
| `minimal-flat` | General, knowledge sharing, SaaS |
| `sci-fi` | AI, frontier tech, system design |
| `hand-drawn` | Relaxed, reflective, casual |
| `editorial` | Processes, data, journalism |
| `scene` | Narratives, emotional, lifestyle |

Style selection based on Type × Style compatibility matrix (styles.md).
Full specs: `styles/<style>.md`

### Q4: Image Text Language ⚠️ REQUIRED when article language ≠ EXTEND.md `language`

Detect article language from content. If different from EXTEND.md `language` setting, MUST ask:
- Article language (match article content) (Recommended)
- EXTEND.md language (user's general preference)

**Skip only if**: Article language matches EXTEND.md `language`, or EXTEND.md has no `language` setting.

### Display Reference Usage (if references detected in Step 1.0)

When presenting outline preview to user, show reference assignments:

```
Reference Images:
| Ref | Filename | Recommended Usage |
|-----|----------|-------------------|
| 01 | 01-ref-diagram.png | direct → Illustration 1, 3 |
| 02 | 02-ref-chart.png | palette → Illustration 2 |
```

---

## Step 4: Generate Outline

Save as `outline.md`:

```yaml
---
type: infographic
density: balanced
style: blueprint
image_count: 4
references:                    # Only if references provided
  - ref_id: 01
    filename: 01-ref-diagram.png
    description: "Technical diagram showing system architecture"
  - ref_id: 02
    filename: 02-ref-chart.png
    description: "Color chart with brand palette"
---

## Illustration 1

**Position**: [section] / [paragraph]
**Purpose**: [why this helps]
**Visual Content**: [what to show]
**Type Application**: [how type applies]
**References**: [01]                    # Optional: list ref_ids used
**Reference Usage**: direct             # direct | style | palette
**Filename**: 01-infographic-concept-name.png

## Illustration 2
...
```

**Requirements**:
- Each position justified by content needs
- Type applied consistently
- Style reflected in descriptions
- Count matches density
- References assigned based on Step 2.4 analysis

---

## Step 5: Generate Images

### 5.1 Create Prompts

Follow [prompt-construction.md](prompt-construction.md). Save to `prompts/illustration-{slug}.md`.
- **Backup rule**: If prompt file exists, rename to `prompts/illustration-{slug}-backup-YYYYMMDD-HHMMSS.md`

**CRITICAL - References in Frontmatter**:
- Only add `references` field if files ACTUALLY EXIST in `references/` directory
- If style/palette was extracted verbally (no file), append info to prompt BODY instead
- Before writing frontmatter, verify: `test -f references/NN-ref-{slug}.png`

### 5.2 Select Generation Method

**固定使用 GPT-Image-2 后端**（通过 `gpt_image2_gen.py` 脚本调用）：

```bash
python "D:\data\images\Article-illustrations\gpt_image2_gen.py" \
  "<prompt>" "D:\data\images\Article-illustrations\NN-{type}-{slug}.png" \
  16:9 1k
```

**参数说明**:

| 参数 | 说明 | 默认值 |
|------|------|--------|
| prompt | 图片描述提示词（必填） | — |
| output_path | 输出文件路径（必填） | — |
| size | 画面比例 | `16:9`（也可用 `1:1`, `4:3`） |
| resolution | 分辨率 | `1k`（也可用 `2k`, `4k`） |

**注意**: 所有图片输出到固定目录 `D:\data\images\Article-illustrations\`，便于后续 PicGo 自动上传。


### 5.3 Process References ⚠️ REQUIRED if references saved in Step 1.0

**DO NOT SKIP if user provided reference images.** For each illustration with references:

1. **VERIFY files exist first**:
   ```bash
   test -f references/NN-ref-{slug}.png && echo "exists" || echo "MISSING"
   ```
   - If file MISSING but in frontmatter → ERROR, fix frontmatter or remove references field
   - If file exists → proceed with processing

2. Read prompt frontmatter for reference info
3. Process based on usage type:

| Usage | Action | Example |
|-------|--------|---------|
| `direct` | Add reference path to `--ref` parameter | `--ref references/01-ref-brand.png` |
| `style` | Analyze reference, append style traits to prompt | "Style: clean lines, gradient backgrounds..." |
| `palette` | Extract colors from reference, append to prompt | "Colors: #E8756D coral, #7ECFC0 mint..." |

4. Check image generation skill capability:

| Skill Supports `--ref` | Action |
|------------------------|--------|
| Yes (e.g., baoyu-image-gen with Google) | Pass reference images via `--ref` |
| No | Convert to text description, append to prompt |

**Verification**: Before generating, confirm reference processing:
```
Reference Processing:
- Illustration 1: using 01-ref-brand.png (direct) ✓
- Illustration 2: extracted palette from 02-ref-style.png ✓
```

### 5.4 Apply Watermark (if enabled)

Add: `Include a subtle watermark "[content]" at [position].`

### 5.5 Generate

**使用 GPT-Image-2 统一生成**（不区分环境，所有环境都用同一个脚本）：

```bash
# 生成单张图片
python "D:\data\images\Article-illustrations\gpt_image2_gen.py" \
  "<prompt>" "D:\data\images\Article-illustrations\NN-{type}-{slug}.png" \
  16:9 1k
```

**Generation Steps**:
1. For each illustration:
   - **Backup rule**: If image file exists, rename to `NN-{type}-{slug}-backup-YYYYMMDD-HHMMSS.png`
   - If references with `direct` usage: include reference info in prompt
   - Generate image using the GPT-Image-2 script
   - **输出到固定目录**: `D:\data\images\Article-illustrations\`
2. After each: `Generated X/N - 已保存到 D:\data\images\Article-illustrations\`
3. On failure: retry once, then log and continue

**16:9 尺寸建议**: 脚本默认 `16:9` + `1k` 分辨率，适合文章配图。如需更高分辨率用 `2k`。


### 6.1 Update Article (with PicGo URLs)

插入图片时，使用 PicGo 上传后的外网 URL 替换本地路径。

```markdown
![description](https://图床URL/NN-{type}-{slug}.png)
```

**URL 替换规则**：
1. 从 Step 5.6 的上传映射表中查找每张图片的外网 URL
2. 如果上传成功 → 使用外网 URL
3. 如果上传失败（重试后仍失败）→ 使用本地路径作为 fallback，并在报告中标记

Alt text: concise description in article's language.

### 6.2 Output Summary

```
Article Illustration Complete!

Article: [path]
Type: [type] | Density: [level] | Style: [style]
Location: [directory]
Images: X/N generated

Positions:
- 01-xxx.png → After "[Section]"
- 02-yyy.png → After "[Section]"

[If failures]
Failed:
- NN-zzz.png: [reason]
```


### 5.6 Upload to PicGo (自动上传图床)

每张图片生成后，立即通过 PicGo API 上传到图床，拿到外网 URL。

**PicGo API 调用**:

```bash
# 上传单张图片到图床
PICGO_SERVER="http://127.0.0.1:36677"
PICGO_TOKEN=""  # 如果 PicGo 设置了 token，在这里填写

# 调用上传 API
curl -X POST "${PICGO_SERVER}/upload" \
  -H "Content-Type: application/json" \
  ${PICGO_TOKEN:+-H "X-PicGo-Token: $PICGO_TOKEN"} \
  -d "{"list": ["$IMAGE_PATH"]}"

# 成功返回: {"success": true, "result": ["https://图床URL/图片.png"]}
```

**上传流程**:

1. 每张图片生成后，记录其**绝对路径**（如 `D:\data\images\Article-illustrations-infographic-concept.png`）
2. 调用 PicGo API 上传该路径
3. 解析返回结果，提取外网 URL：
   ```bash
   # 从响应中提取 URL
   response=$(curl -s -X POST "${PICGO_SERVER}/upload" ...)
   url=$(echo $response | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0])")
   ```
4. 保存 `本地路径 → 外网URL` 的映射表，供 Step 6 使用
5. 如果上传失败，重试一次；仍失败则保留本地路径，在最终报告中标记

**配置来源**（优先级从高到低）：
1. EXTEND.md 中的 `picgo_server` 和 `picgo_token` 字段
2. 默认值：`http://127.0.0.1:36677`，无 Token

**上传映射表示例**：
```
Upload Mapping:
  01-infographic-concept.png → https://img.example.com/01-infographic-concept.png  ✓
  02-scene-atmosphere.png    → https://img.example.com/02-scene-atmosphere.png     ✓
```

---


---

## Step 7: PicGo 配置检测

### 7.1 检查 PicGo 服务状态

在生成图片前，检查 PicGo 服务是否可用：

```bash
# 检查 PicGo 服务是否在监听
curl -s --connect-timeout 3 "http://127.0.0.1:36677/" > /dev/null 2>&1 && \
  echo "PICGO_AVAILABLE=true" || echo "PICGO_AVAILABLE=false"
```

| 结果 | 行为 |
|------|------|
| 可用 | 自动上传所有生成的图片 |
| 不可用 | 跳过上传，使用本地路径，报告末尾提示启动 PicGo |

### 7.2 EXTEND.md 配置模板

```yaml
---
picgo_server: "http://127.0.0.1:36677"
picgo_token: ""         # 如果 PicGo 设置了 token，填在这里
---
```

### 7.3 故障处理

| 问题 | 处理 |
|------|------|
| 上传失败（网络） | 重试 1 次，仍失败则 fallback 到本地路径 |
| 上传失败（鉴权） | 检查 `picgo_token` 是否与 PicGo 设置一致 |
| 返回 `success: false` | 输出 PicGo 错误信息，保留本地路径 |
| PicGo 未运行 | 提示用户启动 PicGo，继续生图（不上传） |

