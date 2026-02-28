# Engineer Log: Task 2.10 - 编程手册 v0.3

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-28
> **Related Task**: Phase 2 - Task 2.10
> **Status**: 🟢 Completed

---

## 1. 任务目标

基于 Task 2.9 的 Sample C 分析结果，将 22 种新增 action 类型和新发现的技术细节整合到编程手册 v0.3。

## 2. v0.2 → v0.3 变更摘要

### 新增/更新的章节

| 章节 | 变更 |
|------|------|
| 2.3 WFItemType | 扩展为 5 种值（新增 1/3/4/5），标注"无 2" |
| 2.4 (新增说明) | 提及 WFContentPredicateTableTemplate 为第四种序列化类型 |
| 3.1 WFCondition | 新增 100=Has Any Value |
| 3.3 repeat.count | 新增：固定次数循环 |
| 3.4 repeat.each | 新增：遍历列表循环 |
| 3.5 exit | 移至新编号 |
| 3.6 控制流对比 | 新增：四种控制流结构对比表 |
| 4.9 number | 新增：数字字面量 |
| 4.10 calculateexpression | 新增：计算表达式（WFTextTokenString 嵌入变量） |
| 4.11 number.random | 新增：随机数 |
| 4.12 text.split | 新增：文本分割 |
| 4.13 filter.files | 新增：过滤/查询（WFContentPredicateTableTemplate） |
| 5.2 openurl | 新增：打开 URL |
| 6.7 showresult | 新增：显示结果 |
| 6.8 comment | 编号调整（原 6.7） |
| 6.9 delay | 新增：延迟 |
| 6.10 getdevicedetails | 新增：获取设备信息 |
| 6.11 openapp | 新增：打开 App |
| 6.12 setclipboard | 新增：设置剪贴板 |
| 6.13 vibrate | 新增：震动 |
| 6.14 image.crop | 新增：裁剪图片 |
| 6.15 image.resize | 新增：调整图片大小 |
| 7.4 repeat.count | 新增交叉引用 |
| 7.5 repeat.each | 新增交叉引用 |
| 7.6 exit | 编号调整（原 7.4） |
| 8 第三方 Action | 扩展为 iCost 9 种 + Apple 1 种 |
| 9.6 模式 F | 新增：遍历列表 + 条件筛选 |
| 9.7 模式 G | 新增：数学运算管道 |
| 9.8 模式 H | 新增：截屏 + 裁剪 + OCR |
| 9.9 模式 I | 编号调整（原 9.6） |
| 附录 B | 更新为 46 种（系统 36 + 第三方 10） |

### 统计

| 指标 | v0.2 | v0.3 |
|------|:----:|:----:|
| Action 类型 | 24 | 46 |
| 系统 Action | 20 | 36 |
| 第三方 Action | 4 | 10 |
| 常用模式 | 6 | 9 |
| 文件行数 | 1227 | 1914 |

## 3. 技术重点

1. **WFContentPredicateTableTemplate** — 第四种序列化类型，用于 filter.files 和第三方实体查询的过滤条件
2. **calculateexpression** — 数学运算通过 WFTextTokenString 嵌入变量，运算符写在 string 中
3. **repeat 循环** — 与 conditional/choosefrommenu 共用 GroupingIdentifier + WFControlFlowMode，但只有 mode 0 和 2（无 mode 1）
4. **ICRouterShortcut** — 第三方 App 路由使用 dict 结构（value/title/subtitle），value 为自定义 scheme URL

## 4. 产出文件

- `docs/shortcuts-manual-v0.3.md` — 编程手册 v0.3（1914 行）
- `docs/project/engineer/task-2.10-manual-v0.3.md` — 本工作日志
