# Git 规范

## 分支与工作区

- 每个变更使用 `feature/<slug>`、`fix/<slug>`、`refactor/<slug>`、`docs/<slug>` 或 `chore/<slug>`。
- 禁止在 `main`、`master` 上实施或直接 push。
- 开始变更前要求干净工作区；不得自动 stash、reset、覆盖或删除用户改动。
- 同一仓库一次只实施一个变更。

## 提交

使用 `type(scope): 中文说明`：

- `docs(spec): 批准登录限流的规格与设计`
- `docs(plan): 批准登录限流的实施计划`
- `feat(auth): 增加登录限流`
- `fix(api): 修复空值导致的崩溃`

规格门禁、计划门禁、每个全绿任务和最终归档分别创建原子提交。先暂存准备提交的文件，再运行 `check commit`。不得提交密钥、依赖变更的未批准内容、迁移文件或无效验证。

## 远程操作

- 本地 commit 可在已批准计划内自动执行。
- push、创建 PR、merge、删除分支和 force push 都需要各自明确授权。
- 永不使用 force push；永不直接 push 受保护分支。
- PR 使用 Squash Merge，正文必须链接规格、列出需求—测试映射、验证证据、风险和遗留债务。
