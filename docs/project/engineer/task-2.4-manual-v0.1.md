# Engineer Log: Task 2.4 - Shortcuts 编程手册 v0.1

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-28
> **Related Task**: Phase 2 - Task 2.4
> **Status**: 🟢 Completed

---

## 1. 任务目标

基于 Task 2.2（结构分析）和 Task 2.3（action 参数详解）的成果，产出一份 AI/人类均可读的 Shortcuts 编程手册 v0.1。

## 2. 手册设计思路

### 组织原则
- **从底层到应用**：先讲文件结构和值传递机制（底层概念），再讲控制流（中层），最后是 action 参考和常用模式（应用层）
- **每个 action 都有完整 XML 示例**：不是伪代码，是可以直接复制修改的真实 XML
- **模式归纳**：从 Sample A 中提炼出 3 种可复用的编程模式

### 章节结构
| 章 | 内容 | 目的 |
|---|------|------|
| 1 | 文件结构 | 理解顶层 plist 的所有 key |
| 2 | 值传递机制 | **核心概念**：WFTextTokenAttachment / WFTextTokenString |
| 3 | 控制流 | conditional + choosefrommenu 的完整结构 |
| 4 | Action 参考 | 11 种 action 的参数、输入输出、完整 XML |
| 5 | 常用模式 | 3 种可复用模式：线性管道、分支汇聚、菜单驱动 |
| 6 | 生成清单 | 从零生成 shortcut 的步骤 |
| 附录 | 字段参考 + 索引 | 快速查阅 |

### 关键决策
1. **值传递放在控制流之前**：因为控制流的参数（如 conditional 的 WFInput）依赖值传递知识
2. **conditional 的 WFInput 特殊结构单独标注**：外层多了一层 `{Type: Variable, Variable: ...}` 包装，容易踩坑
3. **第三方 action 单独成节**：AppIntentDescriptor 是区别于系统 action 的核心差异

## 3. 产出文件

- `docs/shortcuts-manual-v0.1.md` — Shortcuts 编程手册 v0.1

## 4. 手册覆盖范围

- 11 种 action 类型（9 种系统 + 2 种第三方）
- 3 种值传递类型（ActionOutput, Variable, CurrentDate）
- 2 种序列化类型（WFTextTokenAttachment, WFTextTokenString）
- 2 种控制流结构（conditional, choosefrommenu）
- 3 种编程模式（线性管道、条件分支汇聚、菜单驱动）
- 顶层文件结构全部 12 个字段

## 5. 后续扩展方向（Phase 2 Round B/C）

手册 v0.2 预计需要补充：
- API 调用相关 action（URL 请求、JSON 解析）
- 循环结构（repeat）
- 更多数据处理 action（文本替换、数学运算等）
- 错误处理机制
