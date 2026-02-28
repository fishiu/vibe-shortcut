# Engineer Log: Task 2.7 - Shortcuts 编程手册 v0.2

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-28
> **Related Task**: Phase 2 - Task 2.6 + 2.7
> **Status**: 🟢 Completed

---

## 1. 任务目标

分析 Sample B（OCR + DeepSeek API 记账），标注新增 action 类型，更新手册到 v0.2。

## 2. Sample B 分析摘要

- **文件**: `samples/money/2-api.shortcut`，46 个 action，15 种独立类型
- **核心差异**：相比 Sample A 新增了 HTTP API 调用和 JSON 解析整套流程
- **新增系统 action**: 10 种（dictionary, getvalueforkey, gettext, text.replace, alert, exit, downloadurl, getitemfromlist, detect.dictionary, notification）
- **新增第三方 action**: 2 种（ICSearchCategoryEntity, ICSearchAssetEntity）
- **详细分析**: 见 `task-2.6-sample-b-analysis.md`

## 3. 手册 v0.2 变更摘要

### 新增内容
| 项目 | 说明 |
|------|------|
| 1.3 WFWorkflowImportQuestions | 导入时提问机制 |
| 2.3 WFDictionaryFieldValue | 第三种序列化类型（词典字段值） |
| 第 4 章 数据处理 | 8 个 action：dictionary, getvalueforkey, gettext, text.replace, text.match, count, getitemfromlist, detect.dictionary |
| 第 5 章 网络 | downloadurl 完整 HTTP 请求参考 |
| 第 6 章 交互与 UI | alert, notification, comment |
| 3.3 exit | 提前退出机制 |
| 模式 D | Guard 检查（前置验证 + 提前退出） |
| 模式 E | API 调用 + JSON 解析管道 |
| 模式 F | 配置存储（词典 + Import Questions） |

### 结构重组
- v0.1 的第 4 章（Action 参考）拆分为 4 个章节（数据处理 / 网络 / 交互 / 变量与控制流）
- 第三方 action 独立成第 8 章，补充了 4 种 iCost action
- action 总数：11 种 → 24 种（系统 20 + 第三方 4）
- 模式总数：3 种 → 6 种

### 已有 action 的参数补充
- `count`: 新增 `WFCountType` 参数（Characters 模式）
- `ask`: 新增 `WFAskActionDefaultAnswer` 参数
- `choosefromlist`: 新增 `WFChooseFromListActionPrompt` 参数
- `choosefrommenu`: `WFMenuPrompt` 可以是纯 string 或 WFTextTokenString
- 第三方 AppIntentDescriptor: 新增 `ActionRequiresAppInstallation` 字段

## 4. 产出文件

- `samples/money/2-api.xml` — Sample B XML plist 无损导出
- `docs/project/engineer/task-2.6-sample-b-analysis.md` — Sample B 分析文档
- `docs/shortcuts-manual-v0.2.md` — 手册 v0.2
- `docs/project/engineer/task-2.7-manual-v0.2.md` — 本工作日志
