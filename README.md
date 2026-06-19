# 🧠 Central Skills 中央技能仓库

> 一次安装，所有 AI Agent 通用。
>
> 管理 Claude Code、Codex、Qwen、Gemini CLI、Reasonix、WorkBuddy 等 6 个 Agent 的共享技能库。

## 📦 快速开始

```bash
# 克隆本仓库到你的 Agent 中央仓库目录
git clone https://github.com/dqtx760/central-skills.git

# 然后在你每个 Agent 的 skills 目录创建 junction 链接
# 详情见下方「多 Agent 同步」章节
```

## 📂 目录结构

```
skills/
├── README.md                    ← 本文件
├── .gitignore
├── Title/                       ← 标题生成
├── article-cover-16x9/          ← 文章封面
├── ai-jian-koubo/               ← 口播剪辑
├── .../
└── install-to-central/          ← 自动安装技能（管理其他技能的技能）
```

## 🗂️ 技能分类

### ✍️ 写作与内容创作

| 技能 | 描述 | 用法 |
|------|------|------|
| **Title** | 咪蒙式爆款标题生成 | `/Title 帮我写10个标题` |
| **ljg-writes** | 深度观点文写作引擎 | `/ljg-writes` |
| **renwei-writing** | 人味儿写作打磨，降低AI味 | `/renwei-writing 润色这段` |
| **huashu-proofreading** | 三遍审校降低AI检测率 | `/huashu-proofreading 审校一下` |
| **huashu-topic-gen** | 快速生成选题方向 | `/huashu-topic-gen` |
| **content-topic-generator** | 多角度选题延伸 | `/content-topic-generator` |
| **xiaohongshu-converter** | 文章转小红书风格 | `/xiaohongshu-converter` |
| **khazix-writer** | 写作助手 | `/khazix-writer` |

### 🎨 封面与配图

| 技能 | 描述 | 用法 |
|------|------|------|
| **article-cover-16x9** | 文章16:9横版封面 | `/article-cover-16x9` |
| **oh-my-cover-design** | 小红书/公众号竖屏封面，10种风格 | `/oh-my-cover-design` |
| **png-xiaohongshu** | 小红书封面+配图生成 | `/png-xiaohongshu` |
| **ian-xiaohei-illustrations** | KATONG风格正文配图 | `/ian-xiaohei-illustrations 配图` |
| **baoyu-article-illustrator** | 文章配图策划与生成 | `/baoyu-article-illustrator` |
| **cover-generator** | 自动生成高点击率封面 Prompt，16:9和9:16双尺寸 | `/cover-generator` |
| **ljg-card** | 内容转PNG视觉卡片 | `/ljg-card` |

### 📊 演示与幻灯片

| 技能 | 描述 | 用法 |
|------|------|------|
| **frontend-slides** | HTML动画演示文稿 | `/frontend-slides` |
| **huashu-slides** | 内容→PPTX端到端制作 | `/huashu-slides` |
| **mindmap-ppt** | 思维导图→PPT | `/mindmap-ppt` |

### 🔍 AI 资讯与搜索

| 技能 | 描述 | 用法 |
|------|------|------|
| **aihot** | AI行业资讯日报 | `/aihot` 或「今天AI圈有什么」 |
| **agent-reach** | 社媒数据抓取脚手架 | `/agent-reach` |
| **web-access** | 网页内容访问 | `/web-access` |
| **find-skills** | 发现和安装新技能 | `/find-skills` |

### 🎬 音视频处理

| 技能 | 描述 | 用法 |
|------|------|------|
| **ai-jian-koubo** | 口播视频转录与口误识别 | `/ai-jian-koubo 剪口播` |
| **huashu-douyin-script** | 抖音脚本创作 | `/huashu-douyin-script` |
| **notebooklm** | NotebookLM自动化（播客/视频/测验） | `/notebooklm` |

### 🛠️ 开发工具

| 技能 | 描述 | 用法 |
|------|------|------|
| **hyperframes** | HyperFrames 动画框架 | `/hyperframes` |
| **gsap** | GSAP动画参考（HyperFrames） | `/gsap` |
| **impeccable** | 前端UI设计/重构/打磨 | `/impeccable` |
| **remotion-to-hyperframes** | Remotion项目迁移 | `/remotion-to-hyperframes` |

### 🤖 自动化与管理

| 技能 | 描述 | 用法 |
|------|------|------|
| **install-to-central** | ⭐ 从GitHub安装技能到中央仓库 | `/install-to-central <url>` |
| **skill-creator** | 创建和优化技能 | `/skill-creator` |
| **planning-with-files** | 复杂任务文件化规划 | `/planning-with-files` |
| **self-improving-agent** | 错误学习与持续改进 | `/self-improving-agent` |

### 🔗 平台集成

| 技能 | 描述 | 用法 |
|------|------|------|
| **x-post** | X/Twitter 发帖 | `/x-post` |
| **xiaohongshu-cli** | 小红书全操作CLI | `/xiaohongshu-cli` |
| **lark-im** | 飞书集成 | `/lark-im` |
| **Auto-Redbook-Skills** | 小红书笔记素材创作 | `/Auto-Redbook-Skills` |

## 🔗 多 Agent 同步

### 方案一：Junction 链接（推荐）

每个 Agent 的 skills 目录通过 Windows Junction 指向本仓库：

```cmd
# 以 Claude Code 为例
mklink /J "C:\Users\Administrator\.claude\skills\技能名" "C:\Users\Administrator\.agents\skills\技能名"
```

### 方案二：同步脚本

```powershell
# 运行一键同步脚本
.\sync-skills.ps1
```

### 支持的 Agent

| Agent | 路径 |
|-------|------|
| Claude Code | `C:\Users\Administrator\.claude\skills\` |
| Codex | `C:\Users\Administrator\.codex\skills\` |
| Qwen | `C:\Users\Administrator\.qwen\skills\` |
| Gemini CLI | `C:\Users\Administrator\.gemini\skills\` |
| Reasonix | `C:\Users\Administrator\.reasonix\skills\` |
| WorkBuddy | `C:\Users\Administrator\.workbuddy\skills\` |

## 📥 安装新技能

```bash
# 方式一：在任意 Agent 中输入
/install-to-central https://github.com/user/repo

# 方式二：子目录模式（一个仓库中有多个技能）
/install-to-central https://github.com/user/repo/path/to/skill

# 方式三：手动添加
# 1. 将技能文件夹复制到 skills/ 目录
# 2. 运行 sync-skills.ps1 同步到所有 Agent
```

## 📜 技能总数

**当前技能数量：41**

> 最后更新：2026-06-19
> 维护者：@dqtx760
