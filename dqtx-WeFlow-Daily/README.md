# dqtx-WeFlow-Daily

基于 yao-meta-skill 封装的个人群日报技能，保留用户修复版模板。

解压后右键 scripts/Install.ps1，选择“使用 PowerShell 运行”。脚本创建桌面同名文件夹，并安装到用户 .agents/skills/dqtx-WeFlow-Daily；已有目录会停止，不覆盖。安装后重开 Codex，确保 WeFlow MCP 已连接。

调用示例：
- `$dqtx-WeFlow-Daily AI交流群`
- `给 AI交流群生成昨天的 HTML 日报`
- `AI交流群，2026-10-02，简化版日报`

默认上海当天完整版。技能是给 AI 的执行指南，并非双击即可独立生成日报的程序。依赖宿主连接 WeFlow MCP；不包含令牌。
