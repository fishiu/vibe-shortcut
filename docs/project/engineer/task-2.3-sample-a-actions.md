# Engineer Log: Task 2.3 - Sample A Action 参数详解

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-28
> **Related Task**: Phase 2 - Task 2.3
> **Status**: 🟢 Completed

---

## 概述

对 Sample A (`1-reg.shortcut`) 中的 11 种 action 类型，逐一标注参数含义和输入输出关系。

---

## 前置知识：值传递的两种序列化类型

在展开每个 action 之前，需要理解 Shortcuts 中值如何在 action 之间传递。

### WFTextTokenAttachment — 单值引用

引用**一个** action 的输出或一个命名变量。

```xml
<!-- 引用上游 action 输出 -->
<dict>
    <key>Value</key>
    <dict>
        <key>OutputUUID</key>
        <string>B109DAEA-...</string>    <!-- 产出该值的 action 的 UUID -->
        <key>Type</key>
        <string>ActionOutput</string>
        <key>OutputName</key>
        <string>截屏</string>            <!-- 显示名，不参与引用 -->
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenAttachment</string>
</dict>

<!-- 引用命名变量 -->
<dict>
    <key>Value</key>
    <dict>
        <key>VariableName</key>
        <string>金额</string>
        <key>Type</key>
        <string>Variable</string>
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenAttachment</string>
</dict>
```

### WFTextTokenString — 文本模板（含嵌入变量）

一段文本中嵌入变量引用。使用 `￼` (U+FFFC, Object Replacement Character) 作为占位符。

```xml
<dict>
    <key>Value</key>
    <dict>
        <key>string</key>
        <string>记账金额为￼元，它属于</string>    <!-- ￼ 是变量占位符 -->
        <key>attachmentsByRange</key>
        <dict>
            <key>{5, 1}</key>              <!-- 位置 5, 长度 1 (即第6个字符) -->
            <dict>
                <key>VariableName</key>
                <string>金额</string>
                <key>Type</key>
                <string>Variable</string>
            </dict>
        </dict>
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenString</string>
</dict>
```

**`attachmentsByRange` 的 key 格式**: `{offset, length}`
- offset: 在 string 中的字符位置
- length: 占位符长度（通常为 1）

### 引用类型一览

| Type 值 | 含义 | 需要的字段 |
|---------|------|-----------|
| `ActionOutput` | 引用某 action 的输出 | `OutputUUID`, `OutputName` |
| `Variable` | 引用命名变量 | `VariableName` |
| `CurrentDate` | 当前日期时间 | (无额外字段) |

---

## Action 详解

### 1. takescreenshot — 截取屏幕

```
[0] is.workflow.actions.takescreenshot
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `UUID` | `B109DAEA-...` | 本 action 的标识 |

- **输入**: 无
- **输出**: 截图图片 (OutputName: `截屏`)
- **备注**: 无任何配置参数，最简单的 action

---

### 2. extracttextfromimage — OCR 提取文字

```
[1] is.workflow.actions.extracttextfromimage
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `UUID` | string | `D4FCC320-...` | 本 action 的标识 |
| `WFImage` | WFTextTokenAttachment | → `截屏`(B109DAEA) | 输入图片 |

- **输入**: 图片 (来自 action[0] 的截图)
- **输出**: 识别到的文字 (OutputName: `图像中的文本`)

---

### 3. text.match — 正则表达式匹配

```
[2] is.workflow.actions.text.match
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `UUID` | string | `9C66AA21-...` | 本 action 的标识 |
| `text` | WFTextTokenString | 嵌入 `图像中的文本`(D4FCC320) | 待匹配的文本 |
| `WFMatchTextPattern` | string | `[¥]*\s*[0-9]\d*\.\d*\|-0\.\d*[0-9]\d*[元]` | 正则表达式 |

- **输入**: 文本 (来自 OCR 结果)
- **输出**: 匹配结果列表 (OutputName: `匹配`)
- **正则含义**: 匹配 `¥123.45` 或 `123.45元` 格式的金额

---

### 4. count — 计数

```
[3] is.workflow.actions.count
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `UUID` | string | `9DEB6023-...` | 本 action 的标识 |
| `Input` | WFTextTokenAttachment | → `匹配`(9C66AA21) | 要计数的列表 |

- **输入**: 列表 (来自正则匹配结果)
- **输出**: 数字 (OutputName: `计数`)

---

### 5. conditional — 条件判断 (if/else/endif)

一组 conditional 共享同一个 `GroupingIdentifier`，由 `WFControlFlowMode` 区分角色。

#### BEGIN (mode=0): 定义条件

```
[4] is.workflow.actions.conditional  (WFControlFlowMode: 0)
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `GroupingIdentifier` | string | `F422A1CF-...` | 标识一组 if/else/endif |
| `WFControlFlowMode` | int | `0` | BEGIN |
| `WFCondition` | int | `4` | 比较运算符 |
| `WFInput` | Variable → Attachment | → `计数`(9DEB6023) | 左操作数 |
| `WFNumberValue` | string | `"0"` | 右操作数 |

**WFCondition 运算符**:

| 值 | 含义 |
|---|------|
| 0 | 等于 (=) |
| 1 | 不等于 (≠) |
| 2 | 小于 (<) |
| 3 | 大于 (>) |
| 4 | 大于等于 (≥) |
| 5 | 小于等于 (≤) |

**注意**: `WFInput` 的结构比较特殊——外层是 `{Type: Variable, Variable: ...}`，内层才是实际的 attachment。

#### ELSE (mode=1)

```
[7] is.workflow.actions.conditional  (WFControlFlowMode: 1)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `GroupingIdentifier` | `F422A1CF-...` | 与 BEGIN 相同 |
| `WFControlFlowMode` | `1` | ELSE |

#### END (mode=2)

```
[14] is.workflow.actions.conditional  (WFControlFlowMode: 2)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `GroupingIdentifier` | `ADC40908-...` | 与 BEGIN 相同 |
| `WFControlFlowMode` | `2` | END |
| `UUID` | `E11E6F60-...` | END 节点的 UUID（可选） |

- **输出**: END 节点可以产出值 (如条件为 true 的分支结果)

---

### 6. ask — 请求用户输入

```
[5] is.workflow.actions.ask
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `UUID` | string | `88E326FA-...` | 本 action 的标识 |
| `WFAskActionPrompt` | string | `未检测到金额，请手动输入` | 弹窗提示文字 |
| `WFInputType` | string | `Number` | 输入类型限制 |

- **输入**: 无 (弹窗等待用户)
- **输出**: 用户输入的值 (OutputName: `请求输入`)

**WFInputType 可选值**: `Text`, `Number`, `URL`, `Date`, `Time`, `Date and Time`

---

### 7. setvariable — 设置命名变量

```
[6] is.workflow.actions.setvariable
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `WFVariableName` | string | `金额` | 变量名 |
| `WFInput` | WFTextTokenAttachment | → 某 action 输出或变量 | 要存储的值 |

- **输入**: 任意值 (通过 WFInput 引用)
- **输出**: 无 (副作用：设置命名变量)
- **用途**: 在控制流分支间共享数据。多个分支各自 setvariable 同一名称，下游统一用 Variable 引用。

**本样本中的 5 次使用**:

| # | WFInput 来源 | 场景 |
|---|-------------|------|
| [6] | `请求输入`(88E326FA) ActionOutput | 用户手动输入 → 金额 |
| [10] | `所选项目`(8694AE57) ActionOutput | 从列表选择 → 金额 |
| [13] | `匹配`(9C66AA21) ActionOutput | 直接使用匹配结果 → 金额 |
| [19] | Variable `金额` | 菜单"支出"分支内刷新 |
| [22] | Variable `金额` | 菜单"收入"分支内刷新 |

---

### 8. choosefromlist — 从列表中选择

```
[9] is.workflow.actions.choosefromlist
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `UUID` | string | `8694AE57-...` | 本 action 的标识 |
| `WFInput` | WFTextTokenAttachment | → `匹配`(9C66AA21) | 提供给用户的列表 |

- **输入**: 列表 (来自正则匹配结果)
- **输出**: 用户选中的项 (OutputName: `所选项目`)

---

### 9. choosefrommenu — 菜单选择

一组 choosefrommenu 共享同一个 `GroupingIdentifier`。

#### BEGIN (mode=0): 定义菜单

```
[17] is.workflow.actions.choosefrommenu  (WFControlFlowMode: 0)
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `GroupingIdentifier` | string | `C9E0DA54-...` | 标识一组菜单 |
| `WFControlFlowMode` | int | `0` | BEGIN |
| `WFMenuPrompt` | WFTextTokenString | `记账金额为￼元，它属于` | 菜单标题（含变量） |
| `WFMenuItems` | list[string] | `["支出", "收入", ""]` | 菜单选项列表 |

#### 菜单项 (mode=1): 每个选项的执行体

```
[18] is.workflow.actions.choosefrommenu  (WFControlFlowMode: 1)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `GroupingIdentifier` | `C9E0DA54-...` | 与 BEGIN 相同 |
| `WFControlFlowMode` | `1` | 菜单项分支 |
| `WFMenuItemTitle` | `支出` | 对应 WFMenuItems 中的哪一项 |

**结构**: BEGIN 后面紧跟 N 个 mode=1 分支（顺序对应 WFMenuItems），每个分支后面是该分支要执行的 actions。

#### END (mode=2)

```
[25] is.workflow.actions.choosefrommenu  (WFControlFlowMode: 2)
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `GroupingIdentifier` | `C9E0DA54-...` | 与 BEGIN 相同 |
| `WFControlFlowMode` | `2` | END |
| `UUID` | `740968E2-...` | END 节点的 UUID |

---

### 10. ICMarkAShortcutOutcomeRecordIntent — 记账 App: 支出

```
[20] com.gostraight.smallAccountBook.ICMarkAShortcutOutcomeRecordIntent
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `UUID` | string | `BB2C4E67-...` | 本 action 的标识 |
| `AppIntentDescriptor` | dict | (见下) | App 声明 |
| `amount` | WFTextTokenAttachment | → Variable `金额` | 金额参数 |
| `time` | WFTextTokenString | 嵌入 `CurrentDate` | 时间参数 |

**AppIntentDescriptor**:
| 字段 | 值 | 说明 |
|------|-----|------|
| `TeamIdentifier` | `PAG33UNQ5Q` | Apple 开发者团队 ID |
| `BundleIdentifier` | `com.gostraight.smallAccountBook` | App Bundle ID |
| `Name` | `iCost` | App 显示名 |
| `AppIntentIdentifier` | `ICMarkAShortcutOutcomeRecordIntent` | Intent 标识 |

- **输入**: `amount` (金额), `time` (当前日期)
- **输出**: 记账结果

---

### 11. ICMarkAShortcutIncomeRecordIntent — 记账 App: 收入

```
[23] com.gostraight.smallAccountBook.ICMarkAShortcutIncomeRecordIntent
```

| 参数 | 类型 | 值 | 说明 |
|------|------|-----|------|
| `UUID` | string | `701F35EC-...` | 本 action 的标识 |
| `AppIntentDescriptor` | dict | (同上，仅 Intent 不同) | App 声明 |

- **输入**: 无显式参数 (可能使用默认值或隐式传入)
- **输出**: 记账结果
- **备注**: 与 OutcomeRecord 不同，这里没有 `amount` 和 `time` 参数，可能是样本中的省略或 App 端有默认行为

---

## 参数模式总结

### 通用参数（几乎每个 action 都有）

| 参数 | 说明 | 必须? |
|------|------|:-----:|
| `UUID` | action 唯一标识，供下游引用 | 仅产出值的 action |

### 控制流参数（conditional / choosefrommenu 共用）

| 参数 | 说明 |
|------|------|
| `GroupingIdentifier` | 将一组 BEGIN/ELSE/END 关联起来 |
| `WFControlFlowMode` | 0=BEGIN, 1=ELSE/ITEM, 2=END |

### 值引用参数（action 间传值）

| 模式 | WFSerializationType | 用途 |
|------|---------------------|------|
| 单值引用 | `WFTextTokenAttachment` | 直接引用一个 action 输出或变量 |
| 文本模板 | `WFTextTokenString` | 文本中嵌入多个变量 |

### 值来源类型

| Type | 引用方式 | 示例 |
|------|---------|------|
| `ActionOutput` | UUID | `{OutputUUID: "xxx", OutputName: "截屏"}` |
| `Variable` | 变量名 | `{VariableName: "金额"}` |
| `CurrentDate` | 内置 | `{Type: "CurrentDate"}` |
