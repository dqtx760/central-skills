---
name: comment-topics
description: 当用户给出关键词，并要求做选题、短视频选题、文章选题，或要求抓取抖音/小红书/微博/B站/快手/贴吧/知乎等社交平台评论来提炼用户痛点时，必须使用此 Skill。该 Skill 会使用本机已安装的 MediaCrawler 抓取相关内容和评论，归纳多数用户痛点，并按固定模板生成 10 条短视频或文章选题脚本，写入 D:\project2026\fuwari\src\content\project\短视频脚本。
---

# Social Comment Topic Skill

这个 Skill 用于把“关键词 + 社交平台评论”转成可直接发布或二次打磨的短视频/文章选题脚本。

## 适用场景

当用户说类似下面的话时使用：

- “去抖音搜一下 XXX，抓评论做选题”
- “根据小红书评论，帮我找用户痛点”
- “给我一个关键词，抓平台评论，做 10 条短视频脚本”
- “用 MediaCrawler 抓评论，然后按刚才的模式写入短视频脚本目录”
- “围绕 XXX 做选题，要来自真实评论”

## 固定依赖

使用本机已经安装好的 MediaCrawler：

```powershell
D:\zed-workspace\MediaCrawler
```

固定输出目录：

```powershell
D:\project2026\fuwari\src\content\project\短视频脚本
```

## 工作原则

先明确假设，不要静默猜测。

如果用户只给关键词，默认平台为 `dy` 抖音，默认生成 10 条短视频脚本。

如果用户指定平台，按用户指定平台执行。

如果平台登录、扫码、CDP、验证码、风控导致抓取失败，要直接说明卡点，不要编造评论。

抓取规模保持克制，默认抓取 10-15 条内容，每条最多 20 条一级评论，避免大规模请求。

## 平台参数

MediaCrawler 常用平台参数：

| 平台 | 参数 |
| --- | --- |
| 抖音 | `dy` |
| 小红书 | `xhs` |
| 快手 | `ks` |
| B站 | `bili` |
| 微博 | `wb` |
| 贴吧 | `tieba` |
| 知乎 | `zhihu` |

## 执行流程

### 1. 明确任务

从用户输入中提取：

- 关键词
- 平台，缺省为抖音 `dy`
- 输出文件名，缺省用关键词生成
- 输出类型，缺省为短视频脚本
- 条数，缺省为 10 条

如果关键词不明确，先问用户。

### 2. 抓取评论

进入 MediaCrawler 目录：

```powershell
cd D:\zed-workspace\MediaCrawler
```

执行抓取，按需要替换平台和关键词：

```powershell
uv run main.py --platform dy --lt qrcode --type search --keywords "关键词" --crawler_max_notes_count 10 --get_comment true --max_comments_count_singlenotes 20 --save_data_option jsonl
```

如果 CDP 未开启，优先引导用户打开或重启 Chrome：

```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" "--remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=`"D:\zed-workspace\MediaCrawler\chrome_cdp_profile`""
```

验证 CDP：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/version" -TimeoutSec 5
```

如果需要扫码登录，让用户在弹出的浏览器中完成扫码后继续。

### 3. 找到本地数据

默认评论文件通常在：

```powershell
D:\zed-workspace\MediaCrawler\data\{platform}\jsonl\search_comments_yyyy-MM-dd.jsonl
```

内容文件通常在：

```powershell
D:\zed-workspace\MediaCrawler\data\{platform}\jsonl\search_contents_yyyy-MM-dd.jsonl
```

读取时使用 UTF-8，避免中文乱码。

优先分析：

- 高点赞评论
- 高回复评论
- 重复出现的问题
- 明确表达不会、贵、慢、卡、焦虑、选择困难、落地困难的评论
- 能代表多数人痛点的真实表达

### 4. 归纳痛点

先在内部归纳 5-10 个痛点，再转成选题。

常见痛点类型：

- 不知道为什么要学
- 不会安装或登录
- 工具太多，不知道选哪个
- token 成本高
- 看懂教程但不会上手
- 模型接入踩坑
- 运行慢、贵、跑偏
- 担心职业被替代
- 不知道普通人能用在哪些场景

### 5. 输出文件格式

在固定目录下创建 Markdown 文件：

```powershell
D:\project2026\fuwari\src\content\project\短视频脚本\{关键词}相关选题.md
```

如果文件已存在，优先询问用户是否覆盖；如果用户明确要求写入某个文件，则按用户指定路径写入。

每条短视频使用下面格式：

````markdown
### 1. 简短标题
```
发布标题
#标签 #标签 #标签
```

```
钩子段：用一句评论区洞察、反常识观点或高频问题抓住注意力。

痛点段：说明评论区反复出现的真实问题，不要泛泛而谈。

解决方案段：给出清晰、可执行、适合短视频表达的方法。

金句段：用一句有传播感的话收尾，便于用户记住和转发。
```
````

注意：正文四段之间各空一行，不要给正文段落加“钩子/痛点/解决方案/金句”等标题。

### 6. 质量检查

写完后检查：

- 是否有 10 条
- 每条是否有简短小节标题
- 每条是否有发布标题和标签
- 每条提词文案是否正好四段
- 四段之间是否空一行
- 是否写入了指定目录
- 是否基于抓取评论归纳，而不是凭空编造
- 是否适合发布到社交媒体，避免明显违规、限流、违禁词和平台敏感表达
- 是否避免绝对化承诺，例如“稳赚”“保证成功”“百分百有效”“必火”“吊打所有人”
- 是否避免高风险引导，例如诱导违规爬取、绕过平台风控、账号交易、接码灰产、盗号、刷量、薅羊毛等
- 是否避免过度贩卖焦虑、攻击特定群体、引战辱骂、低俗擦边、医疗金融法律等高风险断言
- 如果内容涉及 AI 工具、爬虫、平台数据或自动化，要强调合规、学习研究、低频使用和尊重平台规则
- 对可能限流的词做温和替换，例如用“成本高”替代“烧钱割韭菜”，用“效果不稳定”替代“垃圾/废物”，用“风控限制”替代“破解/绕过”

发布风险处理方式：

- 如果只是轻微风险，直接改写为更稳妥表达。
- 如果存在明显违规或高限流风险，先提示风险点，再给出合规改写版。
- 不要输出带有诱导违法、绕过风控、批量滥用平台、侵犯隐私或攻击他人的内容。

## 示例用户请求

用户：

```text
去抖音搜“code x”，抓一些评论，帮我做 10 条短视频选题，写到短视频脚本目录。
```

应该执行：

1. 用 MediaCrawler 抓抖音 `code x` 搜索结果和评论。
2. 从高赞、高回复、重复问题里提炼痛点。
3. 生成 10 条短视频脚本。
4. 写入：

```powershell
D:\project2026\fuwari\src\content\project\短视频脚本\Codex相关选题.md
```

5. 最后回复用户文件路径和简短验证结果。
