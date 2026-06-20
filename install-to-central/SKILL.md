---
name: install-to-central
description: 从 GitHub 安装技能到中央仓库，自动更新 README、Git 提交+推送、更新斜杠命令速查表，再同步到所有智能体。用法：/install-to-central <github-url>
---

# install-to-central

从 GitHub 安装技能到中央仓库 `C:\Users\Administrator\.agents\skills\`，完成后自动：
1. 更新 `README.md` 添加新技能记录
2. 更新 `AI skill命令速查.md` 添加斜杠命令条目
3. Git commit + push 到 GitHub
4. 同步到所有智能体目录

## 参数

提供一个 GitHub URL，支持两种格式：

- **整个仓库就是技能**: `https://github.com/user/repo`
- **仓库内的子目录**: `https://github.com/user/repo/path/to/skill`

技能名称会自动从 URL 最后一段提取。

## 执行步骤

### 1. 解析 URL

从 URL 提取 owner、repo 和子目录路径：

```
$url = '<用户提供的URL>'
$cleanUrl = $url -replace '\.git$',''
$parts = ($cleanUrl -replace 'https://github.com/','') -split '/'
$owner = $parts[0]
$repo = $parts[1]
```

- 如果 `$parts.Count -eq 2` → 整个仓库模式，技能名 = `$repo`
- 如果 `$parts.Count -gt 2` → 子目录模式，技能名 = 最后一段

### 2. 克隆到临时目录

```powershell
$tmpDir = Join-Path $env:TEMP "skill-install-$(Get-Random)"
git clone --depth 1 "https://github.com/${owner}/${repo}.git" $tmpDir
```

### 3. 定位技能源目录

- **仓库模式**：源目录 = `$tmpDir`
- **子目录模式**：源目录 = `Join-Path $tmpDir <子目录路径>`

验证源目录存在，否则报错终止。复制前移除源目录中的 `.git` 子目录，避免后续 gitlink 问题。

### 4. 复制到中央仓库

```powershell
$target = "C:\Users\Administrator\.agents\skills\<技能名>"
if (Test-Path $target) { throw "中央仓库已存在同名技能：<技能名>" }
Remove-Item -Recurse -Force "$sourceDir\.git" -ErrorAction SilentlyContinue
Copy-Item -Recurse $sourceDir $target
```

### 5. 从 SKILL.md 提取技能信息

读取刚安装的 `$target\SKILL.md`，提取 name 和 description：

```powershell
$nameLine = Select-String -Path "$target\SKILL.md" -Pattern "^name:" | ForEach-Object { $_ -replace "^name:\s*", "" }
$descLine = Select-String -Path "$target\SKILL.md" -Pattern "^description:" | ForEach-Object { $_ -replace "^description:\s*", ""; $_ -replace '^"', ''; $_ -replace '"$', '' }
$descShort = $descLine -replace '。.*$','' -replace '。',''  # 取第一句作为用途简述
```

### 6. 更新 README.md

在 `C:\Users\Administrator\.agents\skills\README.md` 的对应分类下插入新技能行。更新技能总数计数器。

```markdown
| **<技能名>** | <描述> | `/技能名` 或描述 |
```

**当前技能数量：N**

### 7. 更新 AI skill 命令速查文档

更新 `D:\project2026\fuwari\src\content\Xenia\AI skill命令速查.md`：

```powershell
$docPath = "D:\project2026\fuwari\src\content\Xenia\AI skill命令速查.md"
```

**7a. 确定分类**

根据技能 description 关键词匹配以下分类（优先匹配第一个命中的）：

| 关键词 | 分类 |
|--------|------|
| 标题、选题、写作、文案、内容创作、改写、发帖 | ✍️ 内容创作与写作 |
| 封面、配图、插图、图像、卡片、生图 | 🎨 封面与配图 |
| 幻灯片、演示、PPT、slides | 📊 演示与幻灯片 |
| 搜索、抓取、采集、爬虫、网页 | 🔍 搜索与数据采集 |
| 视频、音频、转录、口播、口误、播客 | 🎬 音视频处理 |
| 开发、编程、代码、前端、UI、动画 | 🛠️ 开发工具 |
| 自动化、规划、项目管理、skill | 📋 项目管理与自动化 |
| 小红书、飞书、平台、集成 | 🔗 平台集成 |
| AI资讯、日报、热点 | 📊 选题与分析 |

如果都不匹配，则归入 **📝 其他已安装技能**（该分类表格只有两列：`技能 | 说明`）。

**7b. 插入表格行**

在对应分类表格的最后一行前面插入新行：

```markdown
| <技能名> | /<技能名> | <用途简述（descShort）> |
```

如果归入「其他已安装技能」，表格格式为：

```markdown
| <技能名> | <用途简述> |
```

**7c. 更新页脚**

```markdown
> 最后更新：<当天日期 YYYY-MM-DD>
> 已安装技能：<当前计数+1>个
```

### 8. Git 提交并推送到 GitHub

```powershell
cd "C:\Users\Administrator\.agents\skills"
git add -A
git commit -m "✨ 新增技能: <技能名>

从 <GitHub URL> 安装"
git push
```

### 9. 运行同步脚本

```powershell
$syncScript = "C:\Users\Administrator\.agents\sync-skills.ps1"
if (Test-Path $syncScript) { & $syncScript }
```

### 10. 清理

```powershell
Remove-Item -Recurse -Force $tmpDir
```

### 11. 报告结果

输出安装摘要：
- 技能名、源 URL
- GitHub commit 链接
- 已同步的智能体列表
- AI skill命令速查已更新
