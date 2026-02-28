# iOS Shortcuts 编程手册 v0.1

> **版本**: 0.1 (基于 Sample A 分析)
> **覆盖范围**: 11 种 action 类型，基础控制流，变量传递
> **目标读者**: 需要通过 XML Plist 生成 `.shortcut` 文件的 AI 或开发者

---

## 第 1 章：文件结构

### 1.1 顶层结构

一个 `.shortcut` 文件的核心是一个 plist dict，包含以下 key：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>WFWorkflowActions</key>           <!-- ★ 核心：action 列表 -->
    <array>...</array>

    <key>WFWorkflowClientVersion</key>     <!-- 客户端版本号 -->
    <string>3612.0.2.1</string>

    <key>WFWorkflowIcon</key>              <!-- 图标配置 -->
    <dict>
        <key>WFWorkflowIconGlyphNumber</key>
        <integer>59514</integer>
        <key>WFWorkflowIconStartColor</key>
        <integer>4274264319</integer>
    </dict>

    <key>WFWorkflowInputContentItemClasses</key>  <!-- 可接受的输入类型 -->
    <array>
        <string>WFStringContentItem</string>
        <string>WFImageContentItem</string>
        <!-- ... 更多类型 ... -->
    </array>

    <key>WFWorkflowOutputContentItemClasses</key>  <!-- 输出类型（可为空） -->
    <array/>

    <key>WFWorkflowTypes</key>             <!-- 触发方式 -->
    <array>
        <string>Watch</string>
        <string>WFWorkflowTypeShowInSearch</string>
    </array>

    <key>WFWorkflowImportQuestions</key>   <!-- 导入时的提问（可为空） -->
    <array/>

    <key>WFWorkflowHasOutputFallback</key>
    <false/>

    <key>WFWorkflowHasShortcutInputVariables</key>
    <false/>

    <key>WFWorkflowMinimumClientVersion</key>
    <integer>900</integer>
    <key>WFWorkflowMinimumClientVersionString</key>
    <string>900</string>

    <key>WFQuickActionSurfaces</key>
    <array/>
</dict>
</plist>
```

### 1.2 Action 基本结构

`WFWorkflowActions` 是一个有序数组，每个元素是一个 action dict：

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.xxx</string>   <!-- action 类型 ID -->

    <key>WFWorkflowActionParameters</key>
    <dict>                                      <!-- action 的参数 -->
        <key>UUID</key>
        <string>XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX</string>
        <!-- ... 其他参数 ... -->
    </dict>
</dict>
```

**重要规则**：
- Actions 按数组顺序依次执行（除非被控制流改变）
- `UUID` 必须动态生成，严禁硬编码
- `UUID` 是可选的——只有需要被下游引用输出的 action 才需要

---

## 第 2 章：值传递机制

这是理解 Shortcuts 的**最关键概念**。Actions 之间通过两种序列化类型传递值。

### 2.1 WFTextTokenAttachment — 单值引用

引用**一个**值：某个 action 的输出、一个命名变量、或内置变量。

#### 引用 Action 输出

```xml
<dict>
    <key>Value</key>
    <dict>
        <key>Type</key>
        <string>ActionOutput</string>
        <key>OutputUUID</key>
        <string>B109DAEA-0357-448C-B179-83BB781E2ED3</string>
        <key>OutputName</key>
        <string>截屏</string>          <!-- 仅用于显示，不影响引用 -->
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenAttachment</string>
</dict>
```

#### 引用命名变量

```xml
<dict>
    <key>Value</key>
    <dict>
        <key>Type</key>
        <string>Variable</string>
        <key>VariableName</key>
        <string>金额</string>
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenAttachment</string>
</dict>
```

### 2.2 WFTextTokenString — 文本模板

一段文本中嵌入一个或多个变量。使用 `￼` (U+FFFC, Object Replacement Character) 作为占位符。

```xml
<dict>
    <key>Value</key>
    <dict>
        <key>string</key>
        <string>记账金额为￼元，它属于</string>
        <key>attachmentsByRange</key>
        <dict>
            <key>{5, 1}</key>                <!-- 字符位置 5，长度 1 -->
            <dict>
                <key>Type</key>
                <string>Variable</string>
                <key>VariableName</key>
                <string>金额</string>
            </dict>
        </dict>
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenString</string>
</dict>
```

**`attachmentsByRange` key 格式**：`{offset, length}`
- `offset`：`￼` 在 string 中的字符位置（从 0 开始）
- `length`：占位符长度（通常为 1）
- 当整个字符串就是一个变量时：`string` = `"￼"`，key = `{0, 1}`

### 2.3 值来源类型一览

| Type 值 | 含义 | 必需字段 |
|---------|------|---------|
| `ActionOutput` | 引用某 action 的输出 | `OutputUUID`, `OutputName` |
| `Variable` | 引用命名变量 | `VariableName` |
| `CurrentDate` | 当前日期时间 | （无额外字段） |

### 2.4 特殊情况：conditional 的 WFInput

`conditional` action 的 `WFInput` 参数有一层额外包装：

```xml
<key>WFInput</key>
<dict>
    <key>Type</key>
    <string>Variable</string>
    <key>Variable</key>                    <!-- 注意：多了 Variable 包装层 -->
    <dict>
        <key>Value</key>
        <dict>
            <key>Type</key>
            <string>ActionOutput</string>
            <key>OutputUUID</key>
            <string>9DEB6023-...</string>
            <key>OutputName</key>
            <string>计数</string>
        </dict>
        <key>WFSerializationType</key>
        <string>WFTextTokenAttachment</string>
    </dict>
</dict>
```

结构是 `WFInput → { Type: Variable, Variable: { WFTextTokenAttachment } }`，外层不是标准的 WFTextTokenAttachment。

---

## 第 3 章：控制流

### 3.1 conditional — 条件分支 (if / else / endif)

一组 conditional 通过相同的 `GroupingIdentifier` 关联。由 `WFControlFlowMode` 区分角色：

| WFControlFlowMode | 角色 | 说明 |
|:-:|------|------|
| 0 | BEGIN | 定义条件，包含比较表达式 |
| 1 | ELSE | else 分支（可选） |
| 2 | END | 结束标记 |

#### BEGIN — 定义条件

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.conditional</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>F422A1CF-0DE4-4C04-9191-FD72841891C6</string>
        <key>WFControlFlowMode</key>
        <integer>0</integer>
        <key>WFCondition</key>
        <integer>4</integer>           <!-- 比较运算符 -->
        <key>WFInput</key>
        <dict>...</dict>               <!-- 左操作数（见 2.4 节） -->
        <key>WFNumberValue</key>
        <string>0</string>             <!-- 右操作数 -->
    </dict>
</dict>
```

**WFCondition 运算符**：

| 值 | 含义 |
|:-:|------|
| 0 | 等于 (=) |
| 1 | 不等于 (≠) |
| 2 | 小于 (<) |
| 3 | 大于 (>) |
| 4 | 大于等于 (≥) |
| 5 | 小于等于 (≤) |

#### ELSE

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.conditional</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>F422A1CF-0DE4-4C04-9191-FD72841891C6</string>
        <key>WFControlFlowMode</key>
        <integer>1</integer>
    </dict>
</dict>
```

#### END

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.conditional</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>F422A1CF-0DE4-4C04-9191-FD72841891C6</string>
        <key>WFControlFlowMode</key>
        <integer>2</integer>
        <key>UUID</key>
        <string>73124FE6-...</string>  <!-- END 可以有 UUID，供下游引用分支结果 -->
    </dict>
</dict>
```

#### 执行顺序

```
[conditional BEGIN]     ← 条件判断
    action_a            ← 条件为 true 时执行
    action_b
[conditional ELSE]      ← 否则
    action_c            ← 条件为 false 时执行
[conditional END]       ← 结束

下一个 action...        ← 无论哪个分支都会继续
```

**嵌套**：在一个分支内部放置新的 conditional（不同 GroupingIdentifier）即可实现嵌套。

### 3.2 choosefrommenu — 菜单选择

用户从菜单中选择一项，根据选择执行不同分支。同样通过 `GroupingIdentifier` + `WFControlFlowMode` 组织。

#### BEGIN — 定义菜单

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.choosefrommenu</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>C9E0DA54-...</string>
        <key>WFControlFlowMode</key>
        <integer>0</integer>
        <key>WFMenuPrompt</key>              <!-- 菜单标题（支持变量模板） -->
        <dict>
            <!-- WFTextTokenString，见第 2 章 -->
        </dict>
        <key>WFMenuItems</key>               <!-- 菜单选项列表 -->
        <array>
            <string>支出</string>
            <string>收入</string>
            <string></string>                <!-- 空字符串 = 取消/无标题 -->
        </array>
    </dict>
</dict>
```

#### 菜单项 — 每个选项的执行体

```xml
<!-- 菜单项 1: "支出" -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.choosefrommenu</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>C9E0DA54-...</string>
        <key>WFControlFlowMode</key>
        <integer>1</integer>
        <key>WFMenuItemTitle</key>
        <string>支出</string>               <!-- 对应 WFMenuItems 中的项 -->
    </dict>
</dict>
<!-- 这里放"支出"分支的 actions -->

<!-- 菜单项 2: "收入" -->
<dict>
    ...
    <key>WFMenuItemTitle</key>
    <string>收入</string>
    ...
</dict>
<!-- 这里放"收入"分支的 actions -->
```

#### END

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.choosefrommenu</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>C9E0DA54-...</string>
        <key>WFControlFlowMode</key>
        <integer>2</integer>
        <key>UUID</key>
        <string>740968E2-...</string>
    </dict>
</dict>
```

#### 执行顺序

```
[choosefrommenu BEGIN]        ← 弹出菜单，用户选择
[choosefrommenu ITEM "支出"]  ← 选项标记
    action_a                  ← 选了"支出"时执行
    action_b
[choosefrommenu ITEM "收入"]  ← 选项标记
    action_c                  ← 选了"收入"时执行
[choosefrommenu ITEM ""]      ← 选项标记（取消）
    （空，不执行任何操作）
[choosefrommenu END]          ← 结束
```

---

## 第 4 章：Action 参考

### 4.1 takescreenshot — 截取屏幕

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.takescreenshot` |
| **输入** | 无 |
| **输出** | 截图图片 |
| **参数** | 无（仅 UUID） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.takescreenshot</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>B109DAEA-0357-448C-B179-83BB781E2ED3</string>
    </dict>
</dict>
```

### 4.2 extracttextfromimage — OCR 提取文字

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.extracttextfromimage` |
| **输入** | 图片 |
| **输出** | 识别到的文字 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFImage` | WFTextTokenAttachment | 输入图片的引用 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.extracttextfromimage</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>D4FCC320-E42B-4315-8F6B-712A504B9941</string>
        <key>WFImage</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key>
                <string>ActionOutput</string>
                <key>OutputUUID</key>
                <string>B109DAEA-0357-448C-B179-83BB781E2ED3</string>
                <key>OutputName</key>
                <string>截屏</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

### 4.3 text.match — 正则表达式匹配

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.text.match` |
| **输入** | 文本 |
| **输出** | 匹配结果列表 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | WFTextTokenString | 待匹配的文本 |
| `WFMatchTextPattern` | string | 正则表达式 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.text.match</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>9C66AA21-E39D-48F6-B2B5-75C871AFB457</string>
        <key>WFMatchTextPattern</key>
        <string>[¥]*\s*[0-9]\d*\.\d*|-0\.\d*[0-9]\d*[元]</string>
        <key>text</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>attachmentsByRange</key>
                <dict>
                    <key>{0, 1}</key>
                    <dict>
                        <key>Type</key>
                        <string>ActionOutput</string>
                        <key>OutputUUID</key>
                        <string>D4FCC320-E42B-4315-8F6B-712A504B9941</string>
                        <key>OutputName</key>
                        <string>图像中的文本</string>
                    </dict>
                </dict>
                <key>string</key>
                <string>￼</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenString</string>
        </dict>
    </dict>
</dict>
```

### 4.4 count — 计数

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.count` |
| **输入** | 列表 |
| **输出** | 数字（列表长度） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `Input` | WFTextTokenAttachment | 要计数的列表 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.count</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>9DEB6023-A94D-43C0-8D8C-E31A7F976B0C</string>
        <key>Input</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key>
                <string>ActionOutput</string>
                <key>OutputUUID</key>
                <string>9C66AA21-E39D-48F6-B2B5-75C871AFB457</string>
                <key>OutputName</key>
                <string>匹配</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

### 4.5 ask — 请求用户输入

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.ask` |
| **输入** | 无（弹窗等待用户） |
| **输出** | 用户输入的值 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFAskActionPrompt` | string | 弹窗提示文字 |
| `WFInputType` | string | 输入类型限制 |

**WFInputType 可选值**：`Text`, `Number`, `URL`, `Date`, `Time`, `Date and Time`

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.ask</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>88E326FA-4E8C-45C0-B0ED-3A5B9F5F665C</string>
        <key>WFAskActionPrompt</key>
        <string>未检测到金额，请手动输入</string>
        <key>WFInputType</key>
        <string>Number</string>
    </dict>
</dict>
```

### 4.6 setvariable — 设置命名变量

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.setvariable` |
| **输入** | 任意值 |
| **输出** | 无（副作用：设置命名变量） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFVariableName` | string | 变量名 |
| `WFInput` | WFTextTokenAttachment | 要存储的值 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.setvariable</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>WFVariableName</key>
        <string>金额</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key>
                <string>ActionOutput</string>
                <key>OutputUUID</key>
                <string>88E326FA-4E8C-45C0-B0ED-3A5B9F5F665C</string>
                <key>OutputName</key>
                <string>请求输入</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

**用途**：在控制流分支之间共享数据。多个分支各自 setvariable 同一名称，下游统一用 `{Type: Variable, VariableName: "xxx"}` 引用。

### 4.7 choosefromlist — 从列表中选择

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.choosefromlist` |
| **输入** | 列表 |
| **输出** | 用户选中的项 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | WFTextTokenAttachment | 提供给用户的列表 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.choosefromlist</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>8694AE57-2F1E-4D4C-A6EC-80FF2C2C7833</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key>
                <string>ActionOutput</string>
                <key>OutputUUID</key>
                <string>9C66AA21-E39D-48F6-B2B5-75C871AFB457</string>
                <key>OutputName</key>
                <string>匹配</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

### 4.8 conditional — 条件判断

详见 [第 3.1 节](#31-conditional--条件分支-if--else--endif)。

### 4.9 choosefrommenu — 菜单选择

详见 [第 3.2 节](#32-choosefrommenu--菜单选择)。

### 4.10 第三方 App Action

第三方 App 通过 SiriKit / App Intents 框架暴露 action。与系统 action 的区别：
- `WFWorkflowActionIdentifier` 使用 App 的 Bundle ID 前缀（而非 `is.workflow.actions.`）
- 必须包含 `AppIntentDescriptor` 声明 App 信息
- 参数名由 App 定义（如 `amount`, `time`），不遵循 `WF` 前缀命名

#### 完整示例：记账 App 支出

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>com.gostraight.smallAccountBook.ICMarkAShortcutOutcomeRecordIntent</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>BB2C4E67-E81A-48C8-A192-56C5F5BD13E9</string>

        <!-- App 声明（必须） -->
        <key>AppIntentDescriptor</key>
        <dict>
            <key>AppIntentIdentifier</key>
            <string>ICMarkAShortcutOutcomeRecordIntent</string>
            <key>BundleIdentifier</key>
            <string>com.gostraight.smallAccountBook</string>
            <key>Name</key>
            <string>iCost</string>
            <key>TeamIdentifier</key>
            <string>PAG33UNQ5Q</string>
        </dict>

        <!-- App 自定义参数 -->
        <key>amount</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key>
                <string>Variable</string>
                <key>VariableName</key>
                <string>金额</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>

        <key>time</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>attachmentsByRange</key>
                <dict>
                    <key>{0, 1}</key>
                    <dict>
                        <key>Type</key>
                        <string>CurrentDate</string>
                    </dict>
                </dict>
                <key>string</key>
                <string>￼</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenString</string>
        </dict>
    </dict>
</dict>
```

**AppIntentDescriptor 字段**：

| 字段 | 说明 | 示例 |
|------|------|------|
| `AppIntentIdentifier` | Intent 标识符 | `ICMarkAShortcutOutcomeRecordIntent` |
| `BundleIdentifier` | App Bundle ID | `com.gostraight.smallAccountBook` |
| `Name` | App 显示名 | `iCost` |
| `TeamIdentifier` | Apple 开发者团队 ID | `PAG33UNQ5Q` |

---

## 第 5 章：常用模式

### 5.1 模式 A：线性管道

```
action_1 → action_2 → action_3
```

前一个 action 的输出通过 `ActionOutput` + UUID 传给下一个。

**示例**：截屏 → OCR → 正则匹配

```xml
<!-- 1. 截屏 -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.takescreenshot</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{UUID-A}</string>
    </dict>
</dict>

<!-- 2. OCR，输入引用截屏的输出 -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.extracttextfromimage</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{UUID-B}</string>
        <key>WFImage</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key>
                <string>ActionOutput</string>
                <key>OutputUUID</key>
                <string>{UUID-A}</string>      <!-- 引用截屏 -->
                <key>OutputName</key>
                <string>截屏</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

### 5.2 模式 B：条件分支汇聚（通过命名变量）

多个分支各自设置同名变量，下游统一引用。

```
       ┌─ 分支 A → setvariable "结果" ← 值1
条件 ──┤
       └─ 分支 B → setvariable "结果" ← 值2

下游 action ← Variable "结果"    (无论哪个分支执行，都能拿到值)
```

这是 Shortcuts 中**跨分支传值的唯一方式**。

### 5.3 模式 C：菜单驱动的分支逻辑

```
choosefrommenu BEGIN ("选择操作")
├─ ITEM "选项1" → actions...
├─ ITEM "选项2" → actions...
└─ ITEM ""      → (空，不做操作)
choosefrommenu END
```

菜单项的顺序必须与 `WFMenuItems` 数组一致。

---

## 第 6 章：生成 Shortcut 的清单

当你要从零生成一个 `.shortcut` 文件时，按以下步骤：

1. **规划 action 列表**：确定执行顺序和数据流
2. **为需要被引用的 action 生成 UUID**：使用 `uuid.uuid4()`，严禁复制示例中的 UUID
3. **为控制流生成 GroupingIdentifier**：每组 if/else/endif 或 menu 共用一个 UUID
4. **编写 XML plist**：按本手册的格式组装
5. **填充顶层字段**：
   - `WFWorkflowActions`：action 数组
   - `WFWorkflowClientVersion`：`"3612.0.2.1"`
   - `WFWorkflowIcon`：可使用默认值
   - `WFWorkflowInputContentItemClasses`：根据需要填充
   - 其他字段可参考第 1 章的模板
6. **构建并签名**：
   ```bash
   python tools/shortcut_tool.py build input.xml output.shortcut
   python tools/shortcut_tool.py sign output.shortcut signed.shortcut
   ```

---

## 附录 A：顶层字段参考

| Key | 类型 | 必须 | 说明 |
|-----|------|:----:|------|
| `WFWorkflowActions` | array | ✅ | Action 列表（核心） |
| `WFWorkflowClientVersion` | string | ✅ | 客户端版本号 |
| `WFWorkflowIcon` | dict | ✅ | 图标（GlyphNumber + StartColor） |
| `WFWorkflowInputContentItemClasses` | array | ✅ | 可接受的输入类型列表 |
| `WFWorkflowOutputContentItemClasses` | array | ✅ | 输出类型列表（可为空数组） |
| `WFWorkflowTypes` | array | ✅ | 触发方式 |
| `WFWorkflowImportQuestions` | array | ✅ | 导入提问（可为空数组） |
| `WFWorkflowHasOutputFallback` | bool | ✅ | 输出回退 |
| `WFWorkflowHasShortcutInputVariables` | bool | ✅ | 是否有 shortcut 输入变量 |
| `WFWorkflowMinimumClientVersion` | int | ✅ | 最低客户端版本 |
| `WFWorkflowMinimumClientVersionString` | string | ✅ | 最低版本字符串 |
| `WFQuickActionSurfaces` | array | ✅ | Quick Action 配置（可为空数组） |

## 附录 B：已知 Action 类型索引

| # | Action Identifier | 简称 | 类别 | 章节 |
|:-:|-------------------|------|------|:----:|
| 1 | `is.workflow.actions.takescreenshot` | 截屏 | 输入 | 4.1 |
| 2 | `is.workflow.actions.extracttextfromimage` | OCR | 数据处理 | 4.2 |
| 3 | `is.workflow.actions.text.match` | 正则匹配 | 数据处理 | 4.3 |
| 4 | `is.workflow.actions.count` | 计数 | 数据处理 | 4.4 |
| 5 | `is.workflow.actions.ask` | 用户输入 | 交互 | 4.5 |
| 6 | `is.workflow.actions.setvariable` | 设置变量 | 变量 | 4.6 |
| 7 | `is.workflow.actions.choosefromlist` | 列表选择 | 交互 | 4.7 |
| 8 | `is.workflow.actions.conditional` | 条件判断 | 控制流 | 4.8 / 3.1 |
| 9 | `is.workflow.actions.choosefrommenu` | 菜单选择 | 控制流 | 4.9 / 3.2 |
| 10 | `*.ICMarkAShortcutOutcomeRecordIntent` | 记账(支出) | 第三方 | 4.10 |
| 11 | `*.ICMarkAShortcutIncomeRecordIntent` | 记账(收入) | 第三方 | 4.10 |
