# 当前进度

## 本轮
用户选择完成真实任务并提交。任务：修复 README 重复安装产生嵌套目录、旧版升级残留 CLI；分支 codex/validate-install。

## 已完成
写 PRD、验收方案与稳定入口；首次安装增加已有目录检查，升级先备份旧目录。

## 实际验证
2026-10-13：先观察到 6 文件及旧 CLI 残留。
`pwsh -NoProfile -File C:/Users/Administrator/AppData/Local/Temp/wu5-dev-flow-validation-5a46d24dbbb94550a023b0922d5e5bbc/verify-readme.ps1`：退出 0。
首装、重复安装保护、备份、升级、恢复 5 项通过；按 SHA256 核对文件。

## 边界与下一步
本轮任务完成，提交见本分支最新提交。已有 v0.1.0/v1.0.0 标签不动；未推送、未改全局安装。下一步由用户阅读短文档并反馈，再验证新会话接手。
