# Wu5 Dev Flow

一个面向 Codex 与 Python 项目的个人开发流程 Skill，将可审计的 SDD、严格 TDD 和安全 Git 规范组合成可跨 Session 恢复的工程工作流。

## 核心能力

- 维护“当前有效规格 + 单次变更包”，避免需求只存在于聊天记录。
- 强制 RED–GREEN–REFACTOR，并使用 pytest、pyright 和可选 ruff 验证。
- 使用规格批准、计划批准、内容哈希和验证指纹阻止流程漂移。
- 支持完整、轻量和紧急修复三种变更模式。
- 区分空项目与老项目；老项目先建立结构、行为、测试、风险和债务基线。
- 规范短分支、中文 Conventional Commits、GitHub PR 和 Squash Merge。
- 禁止敏感信息、危险 Git 操作、数据迁移和不当 hardcode。
- 通过项目内 `AGENTS.md + spec/` 在新 Session 中恢复状态。

## 安装

克隆仓库：

```powershell
git clone https://github.com/WenOwen/wu5-dev-flow.git
```

将仓库中的 Skill 文件夹复制到 Codex 个人 Skills 目录：

```powershell
Copy-Item -Recurse .\wu5-dev-flow "$env:USERPROFILE\.codex\skills\wu5-dev-flow"
```

重新打开一个 Codex 任务，然后使用：

```text
使用 $wu5-dev-flow 初始化这个项目
```

也可以直接运行门禁脚本：

```powershell
python "$env:USERPROFILE\.codex\skills\wu5-dev-flow\scripts\wu5_flow.py" init
```

## 工作流

完整变更依次执行：

```text
规格草拟 → 明确批准规格 → 规格提交
→ 计划与测试计划 → 明确批准计划 → 计划提交
→ RED → GREEN → REFACTOR → 验证 → 双层审查
→ 更新当前规格 → 归档 → push → PR → Squash Merge
```

项目初始化后会创建：

```text
spec/
├── index.md
├── project.md
├── workflow.json
├── state.json
├── status.md
├── baseline/
├── features/
├── testing/
├── changes/
└── archive/
```

## 命令

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

## 设计边界

- 首版面向 Codex 和 Python 项目。
- pytest 与 pyright 是默认必需门禁；ruff 在项目已配置时启用。
- 不安装 Git Hooks；流程约束依靠 Skill、项目 `AGENTS.md` 和门禁脚本。
- 数据库结构及不可逆数据迁移不属于本 Skill 的实施范围。
- push、创建 PR、merge、删除分支和强制推送始终需要用户明确授权。

## 验证

运行标准库测试：

```powershell
python -B -m unittest discover -s .\wu5-dev-flow\scripts\tests -v
```

当前测试覆盖空项目初始化、老项目基线、跨 Session 恢复、批准哈希失效、TDD 验证指纹、依赖和迁移门禁、敏感输出脱敏、禁止 hardcode 审查以及完整归档流程。

## License

[MIT](LICENSE)
