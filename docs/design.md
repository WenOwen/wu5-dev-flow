# 技术设计：Wu5 Dev Flow

## 载体与运行环境
采用 Agent Skill：Markdown 指令与 YAML 元数据，由 Codex 读取并执行。技能包无运行时依赖，保持三个文件。

## 交互
使用自然语言对话；SKILL.md 判断阶段并指导行动，references 提供按需读取的短文档样例，agents/openai.yaml 提供展示信息。

## 数据与上下文
项目 Markdown 文件保存需求、技术选择与当前进度；AGENTS.md 保存稳定约定，Git 保存历史。沿用文件系统，不引入数据库或账号系统。

## 分发与安装
通过 GitHub 仓库、版本标签和 Release 分发技能目录。Windows 使用 README 中的 PowerShell 命令安装，升级先备份。开发资料 docs/ 留在仓库，不进入技能包。

## 验证
检查技能格式、文档字数和安装升级；用真实任务检验阶段选择与会话接手。具体结果记录在 memory.md。
