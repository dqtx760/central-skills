# Subtitle Optimizer

Subtitle Optimizer 是一个 Agent skill，用来在保留 SRT 序号和时间戳的前提下优化字幕文本。它会生成候选修正版和可视化 HTML 审查台，让你逐条接受、拒绝或手动修正。

## 核心特性

- **保留时间戳**：只修改字幕文本，不改 SRT 序号和时间码。
- **词汇规则修正**：内置 `assets/corrections.json`，可自动处理常见产品名、命令名和 ASR 错词。
- **上下文审阅**：Agent 会继续检查词汇表覆盖不到的错别字、近音字、断句和术语不一致。
- **可视化校对**：在 HTML 审查台中逐条接受、拒绝或手动修正。
- **直接导出最终字幕**：确认后从页面下载 `{文件名}_fixed.srt`。

---

## 安装

### 方法 1：使用 npx（推荐）

```bash
npx skills add rancho-7/subtitle-optimizer
```

### 方法 2：手动安装到 Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/rancho-7/subtitle-optimizer.git ~/.claude/skills/subtitle-optimizer
```

### 方法 3：让 Agent 安装
给你的Agent发送以下内容：
```text
安装这个 skill：https://github.com/rancho-7/subtitle-optimizer
```

---

## 如何使用

装好之后，在 Agent 里引用 SRT 文件并说明要优化字幕：

```text
优化一下这个视频字幕 @video.srt
```

### 工作流

1. **Agent 分析原始 SRT**：读取字幕和 `assets/corrections.json`，先识别词汇表能确定的修正。
2. **准备审查文件**：在原始字幕同目录生成 `{文件名}_candidate.srt` 和 `{文件名}_diff_preview.html`。候选文件保留原始序号和时间戳，只修改字幕文本。
3. **执行上下文审阅**：Agent 继续检查词汇表覆盖不到的 ASR 错字、近音字、断句问题和语义偏差。长字幕文件会分段处理并覆盖完整字幕。
4. **补充高置信度修正**：如果 Agent 发现上下文级修正，会写入候选 SRT 并刷新审查台；如果没有，会明确说明没有可安全加入的 AI 建议。
5. **用户可视化校对**：用浏览器打开 HTML 页面，对每条修改接受、拒绝或手动修正。
6. **导出结果**：确认无误后，点击网页上的导出按钮，下载最终的 `{文件名}_fixed.srt`。

### 输出文件

处理完成后，原始字幕同目录通常会出现：

- `{文件名}_candidate.srt`：候选修正版，用于审查，不是最终文件。
- `{文件名}_diff_preview.html`：可视化审查台，用浏览器打开。
- `{文件名}_fixed.srt`：你在审查台中点击导出后得到的最终字幕。

### 维护词汇规则

审查台里的“追加词汇规则”不会直接修改 `assets/corrections.json`。如果你在页面中添加了可复用规则，可以在页面中导出 `new_corrections.json`，然后把它交给 Agent：

```text
请把这个 new_corrections.json 合并到 subtitle-optimizer 的词汇规则里
```

Agent 会把新增规则合并进 `assets/corrections.json`。合并后的规则会在下次处理字幕时继续使用。

---

## 运行要求

- **Node.js**：18.0 或更高版本
- **依赖**：当前脚本只使用 Node.js 内置模块，不需要额外安装运行时依赖
