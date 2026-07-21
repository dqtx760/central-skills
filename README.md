# 🧠 Central Skills 中央技能仓�?
> 一次安装，所�?AI Agent 通用�?>
> 管理 Claude Code、Codex、Qwen、Gemini CLI、Reasonix、WorkBuddy �?6 �?Agent 的共享技能库�?
## 📦 快速开�?
```bash
# 克隆本仓库到你的 Agent 中央仓库目录
git clone https://github.com/dqtx760/central-skills.git

# 然后在你每个 Agent �?skills 目录创建 junction 链接
# 详情见下方「多 Agent 同步」章�?```

## 📂 目录结构

```
skills/
├── README.md                    �?本文�?├── .gitignore
├── Title/                       �?标题生成
├── article-cover-16x9/          �?文章封面
├── ai-jian-koubo/               �?口播剪辑
├── .../
└── install-to-central/          �?自动安装技能（管理其他技能的技能）
```

## 🗂�?技能分�?
### ✍️ 写作与内容创�?
| 技�?| 描述 | 用法 |
|------|------|------|
| **Title** | 咪蒙式爆款标题生�?| `/Title 帮我�?0个标题` |
| **ljg-writes** | 深度观点文写作引�?| `/ljg-writes` |
| **renwei-writing** | 人味儿写作打磨，降低AI�?| `/renwei-writing 润色这段` |
| **huashu-proofreading** | 三遍审校降低AI检测率 | `/huashu-proofreading 审校一下` |
| **huashu-topic-gen** | 快速生成选题方向 | `/huashu-topic-gen` |
| **content-topic-generator** | 多角度选题延伸 | `/content-topic-generator` |
| **comment-topics** | 抓取社交平台评论并生成短视频/文章选题脚本 | `/comment-topics` |
| **xiaohongshu-converter** | 文章转小红书风格 | `/xiaohongshu-converter` |
| **demand-trigger-script** | 需求引爆点高转化短视频脚本 | /demand-trigger-script |
| **khazix-writer** | 写作助手 | `/khazix-writer` |

### 🎨 封面与配�?
| 技�?| 描述 | 用法 |
|------|------|------|
| **article-cover-16x9** | 文章16:9横版封面 | `/article-cover-16x9` |
| **oh-my-cover-design** | 小红�?公众号竖屏封面，10种风�?| `/oh-my-cover-design` |
| **png-xiaohongshu** | 小红书封�?配图生成 | `/png-xiaohongshu` |
| **ian-xiaohei-illustrations** | KATONG风格正文配图 | `/ian-xiaohei-illustrations 配图` |
| **baoyu-article-illustrator** | 文章配图策划与生�?| `/baoyu-article-illustrator` |
| **cover-generator** | 自动生成高点击率封面 Prompt�?6:9�?:16双尺�?| `/cover-generator` |
| **ljg-card** | 内容转PNG视觉卡片 | `/ljg-card` |

### 📊 演示与幻灯片

| 技�?| 描述 | 用法 |
|------|------|------|
| **frontend-slides** | HTML动画演示文稿 | `/frontend-slides` |
| **huashu-slides** | 内容→PPTX端到端制�?| `/huashu-slides` |
| **mindmap-ppt** | 思维导图→PPT | `/mindmap-ppt` |

### 🔍 AI 资讯与搜�?
| 技�?| 描述 | 用法 |
|------|------|------|
| **aihot** | AI行业资讯日报 | `/aihot` 或「今天AI圈有什么�?|
| **follow-builders** | AI builders digest，追踪 X 和 YouTube 播客上的 AI 建设者动态 | `/follow-builders` 或 `/ai` |
| **agent-reach** | 社媒数据抓取脚手�?| `/agent-reach` |
| **web-access** | 网页内容访问 | `/web-access` |
| **find-skills** | 发现和安装新技�?| `/find-skills` |

### 🎬 音视频处�?
| 技�?| 描述 | 用法 |
|------|------|------|
| **ai-jian-koubo** | 口播视频转录与口误识�?| `/ai-jian-koubo 剪口播` |
| **huashu-douyin-script** | 抖音脚本创作 | `/huashu-douyin-script` |
| **notebooklm** | NotebookLM自动化（播客/视频/测验�?| `/notebooklm` |

### 🛠�?开发工�?
| 技�?| 描述 | 用法 |
|------|------|------|
| **hyperframes** | HyperFrames 动画框架 | `/hyperframes` |
| **gsap** | GSAP动画参考（HyperFrames�?| `/gsap` |
| **impeccable** | 前端UI设计/重构/打磨 | `/impeccable` |
| **remotion-to-hyperframes** | Remotion项目迁移 | `/remotion-to-hyperframes` |
| **archimate** | Create ArchiMate enterprise architecture diagrams using PlantUML stdlib macros | `/archimate` |
| **architecture** | Create layered system architecture diagrams using HTML/CSS templates with color-coded tiers and grid layouts | `/architecture` |
| **bpmn** | Create business process diagrams using PlantUML syntax with BPMN, EIP, and Lean Mapping stencil icons | `/bpmn` |
| **canvas** | Create spatial diagrams with free-positioned nodes using JSON format | `/canvas` |
| **cloud** | Create cloud provider architecture diagrams using PlantUML syntax with official AWS, Azure, GCP, and Alibaba Cloud service icons | `/cloud` |
| **data-analytics** | Create data pipeline and analytics architecture diagrams using PlantUML syntax with database/analytics stencil icons | `/data-analytics` |
| **graphviz** | Create directed/undirected graphs using DOT language with automatic layout | `/graphviz` |
| **infocard** | Create editorial-style information cards using HTML/CSS in Markdown | `/infocard` |
| **infographic** | Create template-based infographics with space-separated key-value syntax (NOT YAML) | `/infographic` |
| **iot** | Create IoT architecture diagrams using PlantUML syntax with device and sensor stencil icons | `/iot` |
| **mindmap** | Create hierarchical mind maps using PlantUML @startmindmap syntax | `/mindmap` |
| **network** | Create network topology diagrams using PlantUML syntax with mxgraph device icons (Cisco, Citrix, etc.) | `/network` |
| **security** | Create security architecture diagrams using PlantUML syntax with identity, encryption, firewall, and compliance stencil icons | `/security` |
| **uml** | Create UML diagrams using PlantUML syntax | `/uml` |
| **vega** | Create data-driven charts with Vega-Lite (declarative) and Vega (programmatic) | `/vega` |

### 🤖 自动化与管理

| 技�?| 描述 | 用法 |
|------|------|------|
| **install-to-central** | �?从GitHub安装技能，自动更新文档+Git推�?同步 | `/install-to-central <url>` |
| **skill-creator** | 创建和优化技�?| `/skill-creator` |
| **planning-with-files** | 复杂任务文件化规�?| `/planning-with-files` |
| **self-improving-agent** | 错误学习与持续改�?| `/self-improving-agent` |

### 🔗 平台集成

| 技�?| 描述 | 用法 |
|------|------|------|
| **x-post** | X/Twitter 发帖 | `/x-post` |
| **xiaohongshu-cli** | 小红书全操作CLI | `/xiaohongshu-cli` |
| **lark-im** | 飞书集成 | `/lark-im` |
| **zsxq-group** | 知识星球管理：列出星球、浏览主题、查询标签、搜索成员 | `/zsxq-group` |
| **zsxq-topic** | 知识星球主题管理：搜索、查看、发布、编辑、评论和回答主题 | `/zsxq-topic` |
| **zsxq-note** | 知识星球公开笔记管理：创建、编辑、查看和删除笔记 | `/zsxq-note` |
| **zsxq-user** | 知识星球用户信息：查看个人资料和发帖足迹 | `/zsxq-user` |
| **zsxq-shared** | 知识星球认证、诊断、通用 API 和安全规则 | `/zsxq-shared` |
| **wechat-sender** | 自动发送微信文本、图片、文件和语音消息 | `/wechat-sender` |
| **yichen-wecom-local-vault** | 企业微信本地数据库解析与导出 | `/yichen-wecom-local-vault` |


### 🧩 dbskill 商业工具箱
| 技能 | 描述 | 用法 |
|------|------|------|
| **dbs** | dontbesilent 商业工具箱主入口，自动路由当前任务 | `/dbs` |
| **dbs-diagnosis** | 商业模式、产品、定价和客户诊断 | `/dbs-diagnosis` |
| **dbs-benchmark** | 寻找和分析值得研究的对标 | `/dbs-benchmark` |
| **dbs-content** | 内容方向与创作做法诊断 | `/dbs-content` |
| **dbs-hook** | 短视频开头优化 | `/dbs-hook` |
| **dbs-xhs-title** | 小红书标题公式 | `/dbs-xhs-title` |
| **dbs-resonate** | 文稿共鸣诊断 | `/dbs-resonate` |
| **dbs-script-flow** | 逐字稿结构与表达检查 | `/dbs-script-flow` |
| **dbs-ai-check** | AI 写作特征识别 | `/dbs-ai-check` |
| **dbs-wechat-html** | 微信公众号 HTML 生成 | `/dbs-wechat-html` |
| **dbs-spread** | 传播心理与内容扩散分析 | `/dbs-spread` |
| **dbs-content-system** | 把大量素材搭成内容资产工程 | `/dbs-content-system` |
| **dbs-deconstruct** | 概念拆解与问题澄清 | `/dbs-deconstruct` |
| **dbs-goal** | 目标清晰化 | `/dbs-goal` |
| **dbs-good-question** | 好问题生成器 | `/dbs-good-question` |
| **dbs-action** | 行动受阻与执行力诊断 | `/dbs-action` |
| **dbs-slowisfast** | 找长期更快的慢方法 | `/dbs-slowisfast` |
| **dbs-decision** | 决策记录与回填系统 | `/dbs-decision` |
| **dbs-save** | 保存当前诊断状态 | `/dbs-save` |
| **dbs-restore** | 恢复上次诊断状态 | `/dbs-restore` |
| **dbs-report** | 汇总多次存档生成报告 | `/dbs-report` |
| **dbs-learning** | 交互式学习与反馈迭代 | `/dbs-learning` |
| **dbs-chatroom** | 多角色定向聊天室 | `/dbs-chatroom` |
| **dbs-chatroom-austrian** | 奥派经济学聊天室 | `/dbs-chatroom-austrian` |
| **dbs-agent-migration** | 多端 Agent 工作台迁移 | `/dbs-agent-migration` |
| **dbs-bridge** | Skill 或 skills 目录多端桥接 | `/dbs-bridge` |
| **dbs-skill-cleaner** | 本地 skill 风险扫描与隔离建议 | `/dbs-skill-cleaner` |
| **dbs-update** | 更新 dbskill 官方技能 | `/dbs-update` |

## 🔗 �?Agent 同步

### 方案一：Junction 链接（推荐）

每个 Agent �?skills 目录通过 Windows Junction 指向本仓库：

```cmd
# �?Claude Code 为例
mklink /J "C:\Users\Administrator\.claude\skills\技能名" "C:\Users\Administrator\.agents\skills\技能名"
```

### 方案二：同步脚本

```powershell
# 运行一键同步脚�?.\sync-skills.ps1
```

### 支持�?Agent

| Agent | 路径 |
|-------|------|
| Claude Code | `C:\Users\Administrator\.claude\skills\` |
| Codex | `C:\Users\Administrator\.codex\skills\` |
| Qwen | `C:\Users\Administrator\.qwen\skills\` |
| Gemini CLI | `C:\Users\Administrator\.gemini\skills\` |
| Reasonix | `C:\Users\Administrator\.reasonix\skills\` |
| WorkBuddy | `C:\Users\Administrator\.workbuddy\skills\` |

## 📥 安装新技�?
```bash
# 方式一：在任意 Agent 中输�?/install-to-central https://github.com/user/repo

# 方式二：子目录模式（一个仓库中有多个技能）
/install-to-central https://github.com/user/repo/path/to/skill

# 方式三：手动添加
# 1. 将技能文件夹复制�?skills/ 目录
# 2. 运行 sync-skills.ps1 同步到所�?Agent
```

## 📜 技能总数

**当前技能数量：93**

> 最后更新：2026-07-21
> 维护者：@dqtx760



