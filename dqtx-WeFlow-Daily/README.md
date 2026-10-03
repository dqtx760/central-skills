<div align="center">

# dqtx-WeFlow-Daily

### 一个群名，一份 HTML 群聊日报。

通过本机 **WeFlow MCP** 读取微信群消息，把当天讨论整理成可浏览、可截图分享的日报。

[在线模板预览](https://me.dqtx.cc/dqtx-WeFlow-Daily/assets/reference-preview.html) · [开始安装](#开始安装) · [配置 MCP](#配置-mcp) · [使用示例](#使用示例) · [关于作者](#关于作者)

</div>

```text
$dqtx-WeFlow-Daily AI交流群
```

默认生成 **上海时区当天 · 完整版**，也支持指定日期和简化版。

> **使用前必须先安装 WeFlow，并配置好 WeFlow MCP。**
> 本仓库是 AI 技能包，需要在支持技能的 AI 客户端中调用。仅下载本仓库无法独立生成日报。

## 从群名到日报

![生成流程：指定群名，通过 WeFlow MCP 读取消息，整理成 HTML 日报](./assets/readme/workflow.svg)

先匹配正确的群，再按日期分页读取、去重和归纳，最后生成固定模板 HTML。支持目录导航、深浅色切换、云朵式词云和居中的二维码弹窗。

## 可以整理哪些内容

| 完整版 | 简化版 |
| --- | --- |
| 热门词云、讨论热点、资源分享、答疑建议 | 热门词云、最多 3 个讨论热点 |
| 消息汇总、精彩金句、数据看板 | 消息汇总、前 3 名话唠榜 |

生成时会匹配群名、按指定日期读取消息、分页去重，再填入固定模板。模板保留目录导航、深浅色切换、云朵式词云和居中的二维码弹窗。

## 开始安装

### 1. 安装并启动 WeFlow

**[下载 WeFlow 安装包（迅雷网盘）](https://pan.xunlei.com/s/VP1LIQZGCXCfvEMV53Ut48uWA1?pwd=cs4s)** · 提取码：`cs4s`

打开 WeFlow，连接自己的微信数据库，在设置中启用 **API 服务**，并复制自己的 **Access Token**。下载链接由作者提供。

### 2. 安装技能

1. [下载技能 ZIP](https://github.com/dqtx760/dqtx-WeFlow-Daily/archive/refs/heads/main.zip)，完整解压。
2. 打开 `scripts` 文件夹，右键 `Install.ps1` → **使用 PowerShell 运行**。
3. 脚本创建桌面 `dqtx-WeFlow-Daily` 文件夹，并安装到 `%USERPROFILE%\.agents\skills\dqtx-WeFlow-Daily`。

已有同名目录时脚本会停止并保留原内容；请先自行重命名。也可手动复制整个技能目录到客户端的技能目录，确保其中包含 `SKILL.md`。

### 3. 配置 MCP 并重启客户端

完成下方 MCP 配置后重开 Codex，确认 WeFlow 正在运行，且客户端能调用 WeFlow 工具，再开始生成日报。

## 配置 MCP

本机需要 **Node.js/npm**。每位使用者连接自己的 WeFlow 和微信数据，填写自己的令牌。

在 Codex 的 `config.toml` 中加入以下配置；已有 `weflow` 配置时修改对应项：

```toml
[mcp_servers.weflow]
command = "npx"
args = ["-y", "weflow-mcp"]

[mcp_servers.weflow.env]
WEFLOW_BASE_URL = "http://127.0.0.1:5031"
WEFLOW_ACCESS_TOKEN = "填写你自己的 Access Token"
```

<details>
<summary>其他 MCP 客户端：JSON 配置示例</summary>

```json
{
  "mcpServers": {
    "weflow": {
      "command": "npx",
      "args": ["-y", "weflow-mcp"],
      "env": {
        "WEFLOW_BASE_URL": "http://127.0.0.1:5031",
        "WEFLOW_ACCESS_TOKEN": "填写你自己的 Access Token"
      }
    }
  }
}
```

同时需要将技能安装到该客户端支持的技能目录。不同客户端的配置文件位置可能不同，见 [WeFlow MCP 官方说明](https://github.com/L-Chris/weflow-mcp)。

</details>

## 使用示例

安装和连接完成后，在 AI 客户端中输入：

| 想生成什么 | 怎么说 |
| --- | --- |
| 今天的完整版 | `$dqtx-WeFlow-Daily AI交流群` |
| 昨天的日报 | `使用 dqtx-WeFlow-Daily，给 AI交流群生成昨天的 HTML 日报。` |
| 指定日期的简化版 | `使用 dqtx-WeFlow-Daily，AI交流群，2026-10-02，简化版。` |

完成后得到一份 UTF-8 HTML 文件，可用浏览器打开，再截图分享。

## 手机预览

先用手机浏览器打开 [在线模板预览](https://me.dqtx.cc/dqtx-WeFlow-Daily/assets/reference-preview.html)，查看词云并测试“微信公众号”和“赞赏支持”。在线页只有模板占位内容及演示关键词，不含真实群聊天记录。

微信文件预览可能报告整份长文档的高度，导致遮罩出现而卡片落在可见区域外。模板已加入针对这种情况的定位兼容逻辑与无脚本回退，但各预览器的表现仍需在目标手机上确认；正常浏览器是主要验证入口。

## 常见情况

- **搜到多个同名群**：先选择正确的群，再读取消息。
- **连接失败或令牌失效**：先修复 WeFlow/MCP 连接，不生成虚构日报。
- **读取中断或分页未确认完整**：页面注明“部分记录”。
- **日期内没有消息**：生成标明无消息的空日报。
- **二维码显示不出来**：原模板的二维码依赖网络加载。

技能只读取指定群并生成文件，不自动发送日报。本仓库不包含真实群聊天记录或 Access Token。页尾的公众号、赞赏入口和二维码来自原始模板，当前原样保留。

<details>
<summary>文件说明与验证状态</summary>

| 文件 | 用途 |
| --- | --- |
| `SKILL.md` | AI 执行入口 |
| `assets/daily-template.html` | 固定日报模板 |
| `assets/reference-preview.html` | 带占位符的视觉参考 |
| `references/` | 消息读取与内容规则 |
| `scripts/Install.ps1` | Windows 安装脚本 |
| `scripts/check_report.py` | 检查样式、脚本、二维码、锚点与占位符 |

```powershell
python scripts/check_report.py "你的日报.html"
```

技能按 yao-meta-skill 方法封装，模板来自用户提供的修复版文件。已通过结构、资源边界、安装脚本语法和五项模板校验；尚未完成真实 WeFlow 群数据的端到端测试。流程图说明执行步骤，不代表真实群数据或已完成端到端测试。统计与总结需基于真实消息核对。

</details>

---

## 关于作者

**大强同学 · 把 AI 工具用起来，把想法做成作品。**

如果这个技能对你有帮助，欢迎给仓库点个 ⭐，也欢迎来看看我的其他作品、文章和资源。

| 去哪里逛逛 | 入口 |
| --- | --- |
| 大强同学主页 | [dqtx.cc](https://www.dqtx.cc/) |
| 大强同学作品集 | [os.dqtx.cc](https://os.dqtx.cc/) |
| 大强同学博客 | [blog.dqtx.cc](https://blog.dqtx.cc/) |
| 大强同学 GitHub | [dqtx760](https://github.com/dqtx760) |
| 大强同学 OpenList | [dqtx.fly.dev](https://dqtx.fly.dev/) |

**喜欢折腾 AI、寻找实用工具？从 [大强同学主页](https://www.dqtx.cc/) 开始逛逛。**
