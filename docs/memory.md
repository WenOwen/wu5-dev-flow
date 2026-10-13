# 当前进度

## 本轮
用户要求把技能装进常用 Skills 库。目标改用共享枢纽 `~/.agents/skills`（用户技能根 rank 500，本机 DSH 实际加载源），不再用 README 里的 `.codex\skills`。分支 codex/validate-install。

## 已落实
安装 `wu5-dev-flow\` 到 `~/.agents/skills/wu5-dev-flow`：22 项文件与源 SHA256 全同，根层有 SKILL.md、agents/openai.yaml、完整 references，无嵌套。重装按 README 拒绝；备份移出再移回后文件集不变。技能目录已在本会话被发现，`skill wu5-dev-flow` 加载成功。

## 未解决
README「使用」与「从旧版切换」仍写 `.codex\skills`，与本机共享枢纽不一致；待用户决定是否改为可选技能目录并示例 `.agents\skills`。

## 下一步
改 README 安装路径说明并提交；再用真实项目请求复测按需加载五阶段参考与文档字数限制。已有版本标签不动，未推送。
