# 来源、适配与许可

这是材料溯源文件，只有核对来源、更新内容或审计许可时读取；日常工作按 SKILL.md 的阶段索引加载。

## 核对过的原始材料

核对日期：2026-10-13。网站：[vibeprompt.tech](https://vibeprompt.tech/)。流程页正在跳转到新站，因此通过网站链接的官方仓库核对旧版十阶段内容，未混入新版移动应用专用教程。

源码快照：[dotsystemsdevs/pineflow，vibeprompt-site 分支，8d2dbbc](https://github.com/dotsystemsdevs/pineflow/tree/8d2dbbc2a5b3061d102c6beb2e9070c4c4f05e3d)。以下路径均属于这个快照：

- `src/lib/workflow-data.ts`：十阶段正文、目标、交接、FAQ、任务与误区。
- `src/lib/workflow-related.ts`：阶段关联文章与故障案例。
- `src/lib/list-problems.ts`：代码、上线、分发、收入与持续投入的故障建议。
- `content/articles/what-an-mvp-actually-is.md`：MVP 的实验目标、陌生人使用与停止条件。
- `content/articles/vibe-debugging.md`：先理解与复现，再定位和最小修复。
- `content/articles/keep-your-agent-on-current-docs.md`：实际依赖版本与 API 文档。
- `content/articles/vibe-coding-mistakes.md`：上下文、任务大小、规划、恢复点与差异审查。
- `prompt-library/Research Validate/kill-criteria-generator.md`：提前定义停止投入的条件。
- `prompt-library/Architecture Stack/api-contract-first.md`：接口输入、输出、失败与副作用。
- `prompt-library/Agent Setup/session-kickoff-protocol.md`、`context-reset-after-drift.md`、`context-window-compaction.md`：接手、偏航与交接。
- `prompt-library/Testing Quality/debug-persistent-bug.md`：重复修复失败时用假设与最小实验定位。
- `prompt-library/Ops Maintenance/dependency-update-safety-check.md`：升级影响与恢复方式。

## 本技能的取舍

阶段参考用中文重述网站的实用见解，分别标明读取场景、行动与交接。参考指导可以比项目文档长；生成的 PRD、TechDesign 等仍各自不超过 500 字。

保留先需求后选型、轻量上下文、纵向切片、真实用户路径、可观察发布和有基线的迭代。项目样例是示例，不是已执行结果。

适配点：不用固定功能数、文件数、测试数、人数或期限作为通用门禁；不强制 Next.js、特定 Agent、MCP、追踪产品或每任务新聊天；不复制每阶段重复审批。已有授权继续有效，危险与外部动作仍按授权执行。

修正点：`git log --grep` 不能扫描历史源码；泄露秘密要撤销或轮换。平台规则、工具 API、价格和统计需在实际任务中查官方资料。未核验的营销数据、模型榜单、法律及平台结论未纳入操作要求。

PRD 与 TechDesign 分开，面向不同读者；任务清单、临时状态和验证摘要合到 memory，不照搬网站的多层 memory-bank。参考更新时重新核对来源与适用条件，不把经验口号变成永久规则。

## 原始材料许可

上述改编材料来自 MIT 许可项目，保留原版权与许可全文：

```text
MIT License

Copyright (c) 2026 Dot Systems Devs

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
