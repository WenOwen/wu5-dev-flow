# Wu5 Dev Flow

给 AI 开发的一条短流程：明确问题 → 写小范围需求 → 选简单方案 → 测试、实现、验证、提交 → 发布 → 根据反馈迭代。

一个入口，适配现有技术栈。新项目从想法开始，老项目直接进入当前任务。每份新建项目文档不超过 500 字，按非空白字符计。

## 版本

| 版本 | 内容 |
| --- | --- |
| 开发中 | 当前分支：十阶段按需参考、短文档与最小验证循环；尚未发布。 |
| `1.0.0` | 首个精简版：短文档、按需阶段、最小验证循环。 |
| [`0.1.0`](https://github.com/WenOwen/wu5-dev-flow/tree/dc2d220b804f3825f3343565e02331fb1c84201f) | 重构前的完整流程：审批门禁、状态机、脚本与变更包。 |

Git 标签使用 `v1.0.0`、`v0.1.0`，固定对应版本内容，不随 `main` 更新。`1.0.0` 不兼容旧 CLI，升级方法见下文。

标签发布到 GitHub 后，可指定版本下载旧版：

```powershell
git clone --branch v0.1.0 --depth 1 https://github.com/WenOwen/wu5-dev-flow.git wu5-dev-flow-0.1.0
```

## 使用

技能是通用的 Agent Skill：只要你的智能体能读取本地技能目录，就能使用，不限定某个产品。

先在仓库根目录取得技能目录，再复制到你自己的技能目录：

```powershell
$skillSource = (Resolve-Path -LiteralPath .\wu5-dev-flow -ErrorAction Stop).Path
$skillsRoot = Join-Path $env:USERPROFILE '.agents\skills'   # 换成你的智能体读取的技能目录
$skillTarget = Join-Path $skillsRoot 'wu5-dev-flow'
if (Test-Path -LiteralPath $skillTarget) {
    throw '已安装 Wu5 Dev Flow，请先按下文备份旧目录，再安装。'
}
New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
Copy-Item -Recurse -LiteralPath $skillSource -Destination $skillTarget -ErrorAction Stop
```

`$skillsRoot` 是技能根，`$skillTarget` 是它下面的技能名目录；两者不同，复制目标必须是带技能名的完整路径。你的智能体若提供了专门的安装命令，优先使用。

重新打开任务后调用：

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
  PRD.md           面向需求读者：用户、目标、范围、验收
  TechDesign.md    面向技术读者：技术选型、数据模型、交付方案
  memory.md        当前任务、关键决定、最新验证、下一步
  release.md       当前候选版本、发布与恢复、实际结果
```

先写能复现行为的测试，再写实现；验证通过、审查差异后创建本地小提交。质量检查使用项目现有工具。远程操作按已有授权执行。

## 从旧版切换

新版移除了 `wu5_flow.py`、审批口令、JSON 状态、变更包和归档机制，旧命令不再支持。先备份整个旧目录，备份放在技能目录之外，避免同时发现两个版本，再安装新版：

```powershell
$skillsRoot = Join-Path $env:USERPROFILE '.agents\skills'   # 与安装时同一个技能根
$skillTarget = Join-Path $skillsRoot 'wu5-dev-flow'
$backupRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('wu5-dev-flow-backup-' + [guid]::NewGuid().ToString('N'))
Move-Item -LiteralPath $skillTarget -Destination $backupRoot -ErrorAction Stop
Write-Output "旧目录已备份到：$backupRoot"
```

然后在本仓库根目录运行上面的安装命令。成功后，目标包含 `SKILL.md`、`agents/openai.yaml` 和完整 `references/`，没有嵌套目录或旧脚本。核对备份中的个人修改，按需迁回；安装失败可先将新目录移走，再把备份移回原位置。重新打开任务后使用新版。

已有项目接入时，读取旧 `spec/` 的相关规格和未完成任务，提炼到对应 `docs/*.md`；保留旧材料供查阅，核实源码与测试后再记录当前进度。只替换 `AGENTS.md` 中旧技能管理的说明块，保留其他规则。旧材料的删除由用户决定。

## 阶段参考

[入口](wu5-dev-flow/SKILL.md) 按任务索引环境、调研、PRD、TechDesign、上下文、开发、质量、技术发布、用户交付与迭代十份参考。默认只加载当前阶段，跨阶段问题再补相关参考；文档样例随阶段放置。

材料提炼自网站的阶段正文、文章、提示词和故障案例，保留来源与适配说明，见 [SOURCES.md](wu5-dev-flow/references/SOURCES.md)。技能无运行时依赖。

流程组织参考 [The Vibe Coding Cookbook](https://vibeprompt.tech/workflow)。

## License

[MIT](LICENSE)
