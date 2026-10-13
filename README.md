# Wu5 Dev Flow

给 AI 开发的一条短流程：明确问题 → 写小范围需求 → 选简单方案 → 测试、实现、验证、提交 → 发布 → 根据反馈迭代。

一个入口，适配现有技术栈。新项目从想法开始，老项目直接进入当前任务。每份新建项目文档不超过 500 字，按非空白字符计。

## 版本

| 版本 | 内容 |
| --- | --- |
| `1.0.0` | 当前精简版：短文档、按需阶段、最小验证循环。 |
| [`0.1.0`](https://github.com/WenOwen/wu5-dev-flow/tree/dc2d220b804f3825f3343565e02331fb1c84201f) | 重构前的完整流程：审批门禁、状态机、脚本与变更包。 |

Git 标签使用 `v1.0.0`、`v0.1.0`，固定对应版本内容，不随 `main` 更新。`1.0.0` 不兼容旧 CLI，升级方法见下文。

标签发布到 GitHub 后，可指定版本下载旧版：

```powershell
git clone --branch v0.1.0 --depth 1 https://github.com/WenOwen/wu5-dev-flow.git wu5-dev-flow-0.1.0
```

## 使用

将仓库中的 `wu5-dev-flow` 文件夹复制到个人 Skills 目录，重新打开任务后调用：

```powershell
Copy-Item -Recurse .\wu5-dev-flow "$env:USERPROFILE\.codex\skills\wu5-dev-flow"
```

```text
使用 $wu5-dev-flow 帮我把这个想法收敛成 MVP，先不写代码。
使用 $wu5-dev-flow 继续这个项目，完成下一个可验证的小任务。
使用 $wu5-dev-flow 修复这个问题，先复现再改。
使用 $wu5-dev-flow 准备发布，列清验证和恢复步骤。
```

## 项目里留下什么

按需创建，沿用已有等价文件；小修改不要求补齐文档。

```text
AGENTS.md          稳定约定、真实命令、文档入口
docs/
  research.md      调研依据与未知项，需要时写
  prd.md           用户、目标、MVP、非目标、成功标准
  design.md        实现边界、重要取舍、测试与交付方式
  memory.md        当前任务、关键决定、最新验证、下一步
  release.md       当前候选版本、发布与恢复、实际结果
```

先写能复现行为的测试，再写实现；验证通过、审查差异后创建本地小提交。质量检查使用项目现有工具。远程操作按已有授权执行。

## 从旧版切换

新版移除了 `wu5_flow.py`、审批口令、JSON 状态、变更包和归档机制，旧命令不再支持。升级已安装副本时，先确认安装目录内没有个人修改，再用这三个文件替换整个旧技能目录，避免残留脚本与规则。

已有项目接入时，读取旧 `spec/` 的相关规格和未完成任务，提炼到对应 `docs/*.md`；保留旧材料供查阅，核实源码与测试后再记录当前进度。只替换 `AGENTS.md` 中旧技能管理的说明块，保留其他规则。旧材料的删除由用户决定。

技能本身只有 [入口](wu5-dev-flow/SKILL.md)、[文档样例](wu5-dev-flow/references/documents.md) 和 UI 元数据，无运行时依赖。

流程组织参考 [The Vibe Coding Cookbook](https://vibeprompt.tech/workflow)。

## License

[MIT](LICENSE)
