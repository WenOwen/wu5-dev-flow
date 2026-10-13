# 当前进度

## 本轮
用户要求把技能装进常用 Skills 库，并去掉 README 里特定智能体的路径。安装到共享枢纽 `~/.agents/skills`（用户技能根 rank 500，本机 DSH 实际加载源）。分支 codex/validate-install。

## 已落实
安装 `wu5-dev-flow\` 到 `~/.agents/skills/wu5-dev-flow`，13 个文件与源 SHA256 全同，无嵌套。README「使用」与「从旧版切换」改用用户自定的 `$skillsRoot`；TechDesign 去掉 Codex 限定。临时仓库副本重跑：安装、拒绝重装、备份与恢复均通过。

## 下一步
用真实项目请求复测按需加载十份阶段参考与单份文档字数限制。已有版本标签不动，未推送。
