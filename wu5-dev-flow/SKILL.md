---
name: wu5-dev-flow
description: 使用可审计的 SDD、严格 RED-GREEN-REFACTOR TDD 与安全 Git 门禁初始化、开发、修复、重构和交付 Python 项目。用于任何会修改项目源码、测试、规格、依赖或 Git 历史的任务，也用于继续跨 Session 的现有 spec/ 变更、审查代码、验证完成状态、创建提交或准备 GitHub PR。
---

# Wu5 Dev Flow

## 开始工作

1. 从项目根目录运行 `python <本 Skill 目录>/scripts/wu5_flow.py status`。
2. 如果尚未初始化，运行 `init`；初始化后先阅读 `spec/index.md`、`spec/status.md` 与相关规格。
3. 遵守 `spec/state.json` 的当前阶段。不得依赖聊天记忆代替项目状态。
4. 在任何写操作前读取 [SDD 工作流](references/sdd-workflow.md)。涉及 Python 代码时再读取 [Python TDD](references/python-tdd.md) 与 [禁止 Hardcode](references/hardcode-policy.md)；涉及提交、push 或 PR 时读取 [Git 规范](references/git-policy.md)；进入审查时读取 [审查规范](references/review-policy.md)。

## 核心约束

- 先对齐规格，再批准计划，最后实施。只有用户明确说“批准基线”“批准规格”“批准计划”“批准依赖”或“批准紧急修复”时才能记录对应批准。
- 完整变更严格执行两次人工门禁；轻量变更仅限无行为变化的低风险文档、注释、格式与配置调整；范围扩大时立即升级。
- 对可测试代码执行 RED-GREEN-REFACTOR。未观察到预期失败，不得编写业务实现；没有新鲜验证证据，不得提交或宣称完成。
- 同一仓库只允许一个实施中的变更。检测到脏工作区时只分析，不自动 stash、reset、覆盖或删除。
- 数据库结构或不可逆数据迁移不在本 Skill 的实施范围内；发现后暂停并向用户说明。
- 不读取、记录或提交 `.env`、密钥、令牌、凭据和真实敏感数据。
- 禁止不当 hardcode。不得把密钥、环境差异、路径、URL、业务阈值或可变策略直接写死在实现中；按 Hardcode 规范改用配置、命名常量或依赖注入。
- 可自动创建已授权的本地原子提交。push、创建 PR、merge、删除分支和任何强制推送必须分别获得明确授权。

## 状态机

按以下顺序推进：

`uninitialized → baseline-review|ready → drafting-spec → drafting-plan → implementing → verifying → ready-to-archive → ready-to-push`

- 老项目必须在 `baseline-review` 获得“批准基线”。
- `approve spec` 对 `proposal.md`、`spec.md`、`design.md` 建立内容哈希。
- `approve plan` 对 `plan.md`、`test-plan.md` 建立内容哈希。
- 获批文件变化时，使该批准及下游批准失效并停止实施。
- 把任务进度写入 `state.json/status.md`，不要修改已获批的计划文档。

## 使用门禁脚本

```text
wu5_flow.py init
wu5_flow.py new <slug> --type <type> --mode <full|light|hotfix>
wu5_flow.py status
wu5_flow.py approve <baseline|spec|plan|dependency|hotfix>
wu5_flow.py check <implement|commit|push|archive>
wu5_flow.py verify <targeted|affected|full>
wu5_flow.py archive <slug>
wu5_flow.py doctor
```

先暂存准备提交的文件，再运行 `check commit`。脚本只创建模板、维护公开状态、执行项目配置的质量命令并验证门禁；规格、设计、测试和审查结论必须由人和 AI 共同维护。

## 完成标准

- 当前需求均映射到测试，pytest 与 pyright 通过；项目已启用 ruff 时也必须通过。
- 完整变更完成规格符合性与代码质量两轮审查；高风险变更按审查规范调用独立代理。
- 已审查并确认没有引入不当 hardcode；合理的协议固有常量已命名、说明并测试。
- `verification.md` 包含命令、退出码、时间、内容指纹、两轮审查和遗留债务。
- `features/` 已更新为当前有效行为，变更已归档，最终文档提交已创建。
- PR 摘要链接规格、列出需求—测试映射、验证证据、风险与债务。
