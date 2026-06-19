# GPT-Image-2 Backend

High-quality image generation via apimart.ai's GPT-Image-2 API. No watermark, $0.005/image.

## Overview

| Property | Value |
|----------|-------|
| **Backend ID** | `gpt-image-2` |
| **Model** | gpt-image-2 (via apimart.ai) |
| **Cost** | ~$0.005/image ($1 = 200 images) |
| **Resolution** | 1K: 1536×864 / 1672×941 (16:9) |
| **Watermark** | None |
| **Format** | PNG (~2-2.4 MB output) |

## Prerequisites

- Python 3.x with `requests` and `urllib3` libraries
- API key for apimart.ai (get yours at https://apimart.ai/keys)
- Set environment variable: `APIMART_API_KEY=sk-xxx`
- Internet access (calls external API)

## Quick Setup

```bash
# Get your API key at https://apimart.ai/keys, then:
# Windows (CMD):
set APIMART_API_KEY=sk-your-key-here
# macOS / Linux:
export APIMART_API_KEY=sk-your-key-here
```

## Script Location

The skill auto-detects the script at these paths (first match wins):

1. `{output-dir}/gpt_image2_gen.py` — alongside generated images
2. `{skill-dir}/scripts/gpt_image2_gen.py` — bundled with the skill (recommended, zero config)
3. Any user-configured custom path

## Invocation

### Single Image Generation

```bash
python {script_path} "{prompt_content}" {output_path} [size] [resolution]
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `script_path` | auto-detected | Path to `gpt_image2_gen.py` (see Script Location above) |
| `prompt_content` | _(required)_ | The full image prompt text from the prompt file |
| `output_path` | _(required)_ | Absolute path to save the PNG file |
| `size` | `16:9` | Aspect ratio (`1:1`, `16:9`, `9:16`, `4:3`) |
| `resolution` | `1k` | Resolution tier (`1k`, `2k`) |

### Batch Generation (Recommended)

The script supports a `BATCH_JOBS` list for batch mode. When generating multiple images:

1. Write each prompt to its `prompts/NN-{type}-{slug}.md` file as usual
2. Call the script once per prompt file, or use parallel Bash calls (up to `generation_batch_size`)
3. Each call: read prompt file content → pass as arg1 → specify output path as arg2

**Parallel batch example** (batch_size=3):

```bash
# Read prompt content from files, then dispatch in parallel:
python gpt_image2_gen.py "$(cat prompts/01-scene-ai-as-mirror.md)" "output/01-scene-ai-as-mirror.png" "16:9" "1k" &
python gpt_image2_gen.py "$(cat prompts/02-scene-speed-trap.md)" "output/02-scene-speed-trap.png" "16:9" "1k" &
python gpt_image2_gen.py "$(cat prompts/03-scene-living-with-ai.md)" "output/03-scene-living-with-ai.png" "16:9" "1k" &
wait
```

### Workflow Integration

When baoyu-article-illustrator selects this backend:

1. **Read prompt file** — open `prompts/NN-{type}-{slug}.md`, extract the prompt body (skip YAML frontmatter)
2. **Determine output path** — `{output-dir}/NN-{type}-{slug}.png`
3. **Determine size** — map type to aspect ratio:
   - `infographic` / `comparison` / `framework` / `timeline` → `16:9`
   - `scene` → `16:9`
   - `flowchart` → `16:9`
   - Or use `aspect_ratio` from prompt frontmatter if set
4. **Call script** via Bash tool with prompt content and output path
5. **Verify** output file exists and size > 0
6. **Retry once** on failure

## Async Flow

The API uses async generation (submit → poll → download):

```
POST /v1/images/generations  →  task_id (immediate)
GET  /v1/tasks/{task_id}     →  poll every 5s, max 5 min
                             →  completed → download URL
```

Typical generation time: 15-45 seconds per image.

## Post-Processing Notes

Generated PNGs are large (~2+ MB). For WeChat/public account use:

- Compress to 900px width JPEG (quality 85) → reduces to ~80-120 KB
- This is handled separately (not part of backend invocation)

## Error Handling

| Error | Action |
|-------|--------|
| Submit fails (non-200) | Log error, retry once, then skip |
| Poll timeout (5 min) | Log error, mark as failed |
| Download fails | Log error, retry once |
| API key invalid | Tell user to check key at apimart.ai/keys |
| Script not found | Fall through to next backend in priority list |
