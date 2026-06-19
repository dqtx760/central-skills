---
name: install-to-central
description: 从 GitHub 安装技能到中央仓库，自动更新 README、提交 Git 并推送到 GitHub，再同步到所有智能体。用法：/install-to-central <github-url>
---

# install-to-central

从 GitHub 安装技能到中央仓库 `C:\Users\Administrator\.agents\skills\`，完成后自动：
1. 更新 README.md 添加新技能记录
2. Git commit + push 到 GitHub
3. 同步到所有智能体目录

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

验证源目录存在，否则报错终止。

### 4. 复制到中央仓库

```powershell
$target = "C:\Users\Administrator\.agents\skills\<技能名>"
if (Test-Path $target) { throw "中央仓库已存在同名技能：<技能名>" }
Copy-Item -Recurse $sourceDir $target
```

### 5. 从 SKILL.md 提取技能信息

读取刚安装的 `$target\SKILL.md`，提取 name 和 description：

```powershell
$nameLine = Select-String -Path "$target\SKILL.md" -Pattern "^name:" | ForEach-Object { $_ -replace "^name:\s*", "" }
$descLine = Select-String -Path "$target\SKILL.md" -Pattern "^description:" | ForEach-Object { $_ -replace "^description:\s*", ""; $_ -replace '^"', ''; $_ -replace '"$', '' }
```

### 6. 更新 README.md

在 README.md 的「技能总数」标记上方插入新技能行，或者追加到对应分类下。

插入格式（在 `## 📥 安装新技能` 章节之前插入）：

```markdown
| **<技能名>** | <描述> | `/技能名` 或描述 |
```

更新技能总数计数器：

```markdown
**当前技能数量：N**
```

### 7. Git 提交并推送到 GitHub

```powershell
cd "C:\Users\Administrator\.agents\skills"
git add -A
git commit -m "✨ 新增技能: <技能名>

从 <GitHub URL> 安装"
git push
```

### 8. 运行同步脚本

```powershell
$syncScript = "C:\Users\Administrator\.agents\sync-skills.ps1"
if (Test-Path $syncScript) { & $syncScript }
```

### 9. 清理

```powershell
Remove-Item -Recurse -Force $tmpDir
```

### 10. 报告结果

输出安装摘要：
- 技能名、源 URL
- GitHub commit 链接
- 已同步的智能体列表
