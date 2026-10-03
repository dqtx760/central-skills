# 封装记录
模式：Scaffold，个人重复使用。身份：dqtx-WeFlow-Daily；目标：当前工作区同名目录。原 yao-meta-skill 只读。
参考：yao-meta-skill 方法及资源边界、用户修复版 TXT、用户预览 HTML、WeFlow 官方 README。
风险：错群、漏页、时区边界、幻觉统计、词云回归、二维码弹窗回归。对应防护见两个 references 文件及校验脚本。
模板是 file-backed fixture；input_files 为用户提供 TXT 与 HTML。output contract 为 UTF-8 固定模板日报。
rollback boundary：仅删除新建技能包，不改变 MCP 配置、聊天数据或原技能。
missing evidence：当前无可调用 WeFlow MCP，未执行真实群端到端生成；未做浏览器交互验证。触发场景人工审查：今天完整版、昨天简化版、同名群需选择；私聊/朋友圈/配置请求不触发。

2026-10-03 布局更新：用户授权恢复椭圆词云和手机居中弹窗；本次变更与验证限制见 layout-fix.md。
