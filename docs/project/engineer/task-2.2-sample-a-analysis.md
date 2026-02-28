# Engineer Log: Task 2.2 - Sample A 结构分析

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-28
> **Related Task**: Phase 2 - Task 2.2 (decode → dump_xml, 列出 action 列表和数据流)
> **Status**: 🟢 Completed

---

## 1. 样本信息

- **文件**: `samples/money/1-reg.shortcut` (24KB, AEA 签名)
- **功能**: OCR 截屏识别金额 + 正则匹配 + 记账 App 写入
- **Actions 数量**: 26
- **独立 Action 类型**: 11 种
- **导出 XML**: `samples/money/1-reg.xml`

---

## 2. Action 列表 (执行顺序)

| # | Action | 说明 |
|---|--------|------|
| 0 | `takescreenshot` | 截取当前屏幕 |
| 1 | `extracttextfromimage` | OCR：从截图中提取文字 |
| 2 | `text.match` | 正则匹配金额：`[¥]*\s*[0-9]\d*\.\d*\|-0\.\d*[0-9]\d*[元]` |
| 3 | `count` | 统计匹配结果数量 |
| 4 | `conditional` | **IF** 匹配数 > 0 |
| 5 | `ask` | 未检测到金额，用户手动输入 (Number) |
| 6 | `setvariable` | 设置变量 `金额` ← 用户输入 |
| 7 | `conditional` | **ELSE** |
| 8 | `conditional` | **IF** 匹配数 = 1（嵌套） |
| 9 | `choosefromlist` | 匹配到多个，让用户选择 |
| 10 | `setvariable` | 设置变量 `金额` ← 用户选择 |
| 11 | `conditional` | **ELSE** |
| 12 | `conditional` | **IF** 匹配数 > 1（嵌套） |
| 13 | `setvariable` | 设置变量 `金额` ← 匹配结果 |
| 14 | `conditional` | **ENDIF** (内层) |
| 15 | `conditional` | **ENDIF** (中层) |
| 16 | `conditional` | **ENDIF** (外层) |
| 17 | `choosefrommenu` | 菜单: "记账金额为X元，它属于" → [支出/收入/取消] |
| 18 | `choosefrommenu` | **菜单项: 支出** |
| 19 | `setvariable` | 设置变量 `金额` ← 当前金额 |
| 20 | `ICMarkAShortcutOutcomeRecordIntent` | 调用记账 App: 写入**支出**记录 |
| 21 | `choosefrommenu` | **菜单项: 收入** |
| 22 | `setvariable` | 设置变量 `金额` ← 当前金额 |
| 23 | `ICMarkAShortcutIncomeRecordIntent` | 调用记账 App: 写入**收入**记录 |
| 24 | `choosefrommenu` | **菜单项: (空 = 取消)** |
| 25 | `choosefrommenu` | **ENDMENU** |

---

## 3. 数据流

```
[0] takescreenshot ─────────── UUID:B109DAEA ──→ "截屏"
     │
     ↓ (图片)
[1] extracttextfromimage ───── UUID:D4FCC320 ──→ "图像中的文本"
     │                         ← reads "截屏"(B109DAEA)
     ↓ (文字)
[2] text.match ────────────── UUID:9C66AA21 ──→ "匹配"
     │                         ← reads "图像中的文本"(D4FCC320)
     │                         pattern: 金额正则
     ↓ (匹配列表)
[3] count ─────────────────── UUID:9DEB6023 ──→ "计数"
     │                         ← reads "匹配"(9C66AA21)
     ↓ (数字)
┌────────────────────────────────────────────────┐
│ [4] IF 计数 > 0                                 │
│   [5] ask "请手动输入" ─── UUID:88E326FA        │
│   [6] setvariable "金额" ← "请求输入"(88E326FA) │
│ [7] ELSE                                        │
│   ┌──────────────────────────────────────┐      │
│   │ [8] IF 计数 = 1                      │      │
│   │   [9] choosefromlist ─ UUID:8694AE57 │      │
│   │       ← reads "匹配"(9C66AA21)      │      │
│   │   [10] setvariable "金额" ← 选中项  │      │
│   │ [11] ELSE                            │      │
│   │   [12] IF 计数 > 1                   │      │
│   │     [13] setvariable "金额" ← 匹配  │      │
│   │   [14] ENDIF                         │      │
│   │ [15] ENDIF                           │      │
│   └──────────────────────────────────────┘      │
│ [16] ENDIF                                      │
└────────────────────────────────────────────────┘
     │
     ↓ 变量 "金额" 已确定
┌────────────────────────────────────────────────┐
│ [17] choosefrommenu "记账金额为{金额}元，它属于" │
│                                                 │
│ ┌─ 支出 ──────────────────────────────────────┐ │
│ │ [19] setvariable "金额"                      │ │
│ │ [20] 记账App.支出(amount=金额, time=当前日期) │ │
│ └──────────────────────────────────────────────┘ │
│ ┌─ 收入 ──────────────────────────────────────┐ │
│ │ [22] setvariable "金额"                      │ │
│ │ [23] 记账App.收入()                          │ │
│ └──────────────────────────────────────────────┘ │
│ ┌─ 取消 ──────────────────────────────────────┐ │
│ │ (空，什么都不做)                              │ │
│ └──────────────────────────────────────────────┘ │
│ [25] ENDMENU                                    │
└────────────────────────────────────────────────┘
```

---

## 4. 独立 Action 类型汇总 (11 种)

### 系统 Action (9 种)

| Action ID | 简称 | 出现次数 | 类别 |
|-----------|------|:--------:|------|
| `is.workflow.actions.takescreenshot` | 截屏 | 1 | 输入 |
| `is.workflow.actions.extracttextfromimage` | OCR | 1 | 数据处理 |
| `is.workflow.actions.text.match` | 正则匹配 | 1 | 数据处理 |
| `is.workflow.actions.count` | 计数 | 1 | 数据处理 |
| `is.workflow.actions.conditional` | 条件判断 | 8 | 控制流 |
| `is.workflow.actions.ask` | 用户输入 | 1 | 交互 |
| `is.workflow.actions.setvariable` | 设置变量 | 5 | 变量 |
| `is.workflow.actions.choosefromlist` | 列表选择 | 1 | 交互 |
| `is.workflow.actions.choosefrommenu` | 菜单选择 | 5 | 控制流/交互 |

### 第三方 Action (2 种)

| Action ID | 说明 | App |
|-----------|------|-----|
| `com.gostraight.smallAccountBook.ICMarkAShortcutOutcomeRecordIntent` | 记录支出 | iCost 记账 |
| `com.gostraight.smallAccountBook.ICMarkAShortcutIncomeRecordIntent` | 记录收入 | iCost 记账 |

---

## 5. 关键技术发现

### 5.1 变量传递机制

Shortcuts 有**两种**变量引用方式:

**方式 1: ActionOutput (隐式变量)**
- 每个 action 自动产出一个值，通过 UUID 引用
- 格式: `{Type: ActionOutput, OutputUUID: "xxx", OutputName: "截屏"}`
- OutputName 是显示名称，OutputUUID 是真正的引用 ID

**方式 2: Named Variable (显式变量)**
- 通过 `setvariable` 设置命名变量
- 引用格式: `{Type: Variable, VariableName: "金额"}`
- 用途: 在控制流分支之间共享数据

### 5.2 控制流结构

**conditional (if/else/endif)**:
- 同一个 `GroupingIdentifier` 标识一组
- `WFControlFlowMode`: 0=BEGIN, 1=ELSE, 2=END
- 可嵌套（本样本有 3 层嵌套）

**choosefrommenu (菜单选择)**:
- 同样使用 `GroupingIdentifier` 分组
- Mode 0=菜单定义, 1=各菜单项, 2=END
- 每个菜单项通过 `WFMenuItemTitle` 标识

### 5.3 WFSerializationType

值的传递使用序列化类型标记:
- `WFTextTokenAttachment`: 单个变量引用
- `WFTextTokenString`: 文本模板中嵌入变量（使用 `￼` (U+FFFC) 作为占位符）

### 5.4 第三方 App Action

- 通过 `AppIntentDescriptor` 声明 App 信息
- `BundleIdentifier`: App 标识 (`com.gostraight.smallAccountBook`)
- `TeamIdentifier`: 开发者标识 (`PAG33UNQ5Q`)
- `AppIntentIdentifier`: 具体 Intent 名称

---

## 6. Shortcut 业务逻辑（自然语言）

```
1. 截取当前屏幕
2. OCR 识别截图中的文字
3. 用正则提取金额数字（支持 ¥ 和 元）
4. 根据匹配到的金额数量:
   - 0 个: 弹窗让用户手动输入金额
   - 1 个: 弹窗让用户从匹配结果中选择（确认）
   - 多个: 直接使用匹配结果
5. 弹出菜单 "记账金额为X元，它属于":
   - 选"支出": 调用记账 App 写入支出记录
   - 选"收入": 调用记账 App 写入收入记录
   - 选"取消": 不做任何操作
```

---

## 7. 产出文件

- `samples/money/1-reg.xml` — XML plist 无损导出
- `docs/project/engineer/task-2.2-sample-a-analysis.md` — 本分析文档
