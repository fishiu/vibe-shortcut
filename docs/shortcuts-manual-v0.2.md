# iOS Shortcuts 编程手册 v0.2

> **版本**: 0.2 (基于 Sample A + Sample B 分析)
> **覆盖范围**: 24 种 action 类型 (系统 20 + 第三方 4)，控制流，变量传递，HTTP API 调用，JSON 解析
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

    <key>WFWorkflowImportQuestions</key>   <!-- 导入时的提问（见 1.3） -->
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

### 1.3 WFWorkflowImportQuestions — 导入时提问

可以在用户导入 shortcut 时弹窗要求配置参数（如 API Key）：

```xml
<key>WFWorkflowImportQuestions</key>
<array>
    <dict>
        <key>ActionIndex</key>
        <integer>0</integer>              <!-- 关联的 action 索引 -->
        <key>Category</key>
        <string>Parameter</string>
        <key>ParameterKey</key>
        <string>WFItems</string>          <!-- 要配置的参数名 -->
        <key>DefaultValue</key>
        <dict>...</dict>                  <!-- 默认值 -->
        <key>Text</key>
        <string>请配置你的 API Key</string>  <!-- 提示文本 -->
    </dict>
</array>
```

---

## 第 2 章：值传递机制

这是理解 Shortcuts 的**最关键概念**。Actions 之间通过序列化类型传递值。

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

**多变量示例**（来自 Sample B）：

```xml
<key>string</key>
<string>分析账单...分类:￼。账户:￼。账单:￼</string>
<key>attachmentsByRange</key>
<dict>
    <key>{74, 1}</key>    <!-- 第 1 个 ￼ 的位置 -->
    <dict>
        <key>Type</key><string>ActionOutput</string>
        <key>OutputUUID</key><string>{分类-UUID}</string>
        <key>OutputName</key><string>分类</string>
    </dict>
    <key>{79, 1}</key>    <!-- 第 2 个 ￼ 的位置 -->
    <dict>...</dict>
    <key>{84, 1}</key>    <!-- 第 3 个 ￼ 的位置 -->
    <dict>...</dict>
</dict>
```

### 2.3 WFDictionaryFieldValue — 词典字段值

用于 `dictionary` action 和 HTTP Headers，是第三种序列化类型：

```xml
<dict>
    <key>Value</key>
    <dict>
        <key>WFDictionaryFieldValueItems</key>
        <array>
            <dict>
                <key>WFItemType</key>
                <integer>0</integer>           <!-- 0 = Text 类型 -->
                <key>WFKey</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>string</key>
                        <string>api_key</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
                <key>WFValue</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>string</key>
                        <string>sk-xxx</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
            <!-- 更多键值对... -->
        </array>
    </dict>
    <key>WFSerializationType</key>
    <string>WFDictionaryFieldValue</string>
</dict>
```

**WFItemType 值**：`0` = Text（目前仅观察到此类型）

### 2.4 值来源类型一览

| Type 值 | 含义 | 必需字段 |
|---------|------|---------|
| `ActionOutput` | 引用某 action 的输出 | `OutputUUID`, `OutputName` |
| `Variable` | 引用命名变量 | `VariableName` |
| `CurrentDate` | 当前日期时间 | （无额外字段） |

### 2.5 特殊情况：conditional 的 WFInput

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
        <dict>...</dict>               <!-- 左操作数（见 2.5 节） -->
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
        <string>F422A1CF-...</string>
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
        <string>F422A1CF-...</string>
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
        <key>WFMenuPrompt</key>              <!-- 菜单标题（支持纯字符串或变量模板） -->
        <string>选择记账方式</string>
        <key>WFMenuItems</key>               <!-- 菜单选项列表 -->
        <array>
            <string>📷 截图识别</string>
            <string>✏️ 手动输入</string>
            <string>❌ 退出</string>
        </array>
    </dict>
</dict>
```

**注意**：`WFMenuPrompt` 既可以是纯 `<string>`，也可以是 WFTextTokenString dict（含变量模板）。

#### 菜单项 — 每个选项的执行体

```xml
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
        <string>📷 截图识别</string>        <!-- 对应 WFMenuItems 中的项 -->
    </dict>
</dict>
<!-- 这里放该分支的 actions -->
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

### 3.3 exit — 提前退出

无条件终止 shortcut 的执行。常与 conditional 配合做 guard 检查。

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.exit</string>
    <key>WFWorkflowActionParameters</key>
    <dict/>
</dict>
```

---

## 第 4 章：Action 参考 — 数据处理

### 4.1 dictionary — 创建词典

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.dictionary` |
| **输入** | 无 |
| **输出** | 词典对象 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFItems` | WFDictionaryFieldValue | 键值对列表（见 2.3 节） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.dictionary</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>38703107-...</string>
        <key>WFItems</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>WFDictionaryFieldValueItems</key>
                <array>
                    <dict>
                        <key>WFItemType</key><integer>0</integer>
                        <key>WFKey</key>
                        <dict>
                            <key>Value</key><dict><key>string</key><string>api_key</string></dict>
                            <key>WFSerializationType</key><string>WFTextTokenString</string>
                        </dict>
                        <key>WFValue</key>
                        <dict>
                            <key>Value</key><dict><key>string</key><string>sk-xxx</string></dict>
                            <key>WFSerializationType</key><string>WFTextTokenString</string>
                        </dict>
                    </dict>
                </array>
            </dict>
            <key>WFSerializationType</key>
            <string>WFDictionaryFieldValue</string>
        </dict>
    </dict>
</dict>
```

### 4.2 getvalueforkey — 从词典取值

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.getvalueforkey` |
| **输入** | 词典 |
| **输出** | 对应 key 的值 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFDictionaryKey` | string | 要取的 key（支持嵌套路径如 `message.content`） |
| `WFInput` | WFTextTokenAttachment | 输入词典 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.getvalueforkey</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>3C0FFED2-...</string>
        <key>WFDictionaryKey</key>
        <string>api_key</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key><string>ActionOutput</string>
                <key>OutputUUID</key><string>38703107-...</string>
                <key>OutputName</key><string>词典</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

**嵌套路径**：`WFDictionaryKey` 支持点号分隔的嵌套路径，如 `message.content` 直接取 `dict["message"]["content"]`。

### 4.3 gettext — 构建文本

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.gettext` |
| **输入** | 无 |
| **输出** | 构建的文本 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFTextActionText` | WFTextTokenString | 文本模板（可嵌入变量） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.gettext</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>448B58A1-...</string>
        <key>WFTextActionText</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>attachmentsByRange</key>
                <dict>
                    <key>{10, 1}</key>
                    <dict>
                        <key>Type</key><string>ActionOutput</string>
                        <key>OutputUUID</key><string>{model-UUID}</string>
                        <key>OutputName</key><string>词典值</string>
                    </dict>
                    <key>{51, 1}</key>
                    <dict>
                        <key>Type</key><string>ActionOutput</string>
                        <key>OutputUUID</key><string>{prompt-UUID}</string>
                        <key>OutputName</key><string>更新后的文本</string>
                    </dict>
                </dict>
                <key>string</key>
                <string>{"model":"￼","messages":[{"role":"user","content":"￼"}]}</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenString</string>
        </dict>
    </dict>
</dict>
```

**用途**：构建任意文本，常用于拼接 API 请求 body、构建显示文本等。

### 4.4 text.replace — 文本替换

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.text.replace` |
| **输入** | 文本 |
| **输出** | 替换后的文本 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | WFTextTokenAttachment | 输入文本 |
| `WFReplaceTextFind` | string | 查找内容 |
| `WFReplaceTextReplace` | string | 替换内容 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.text.replace</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>4C618A1C-...</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key><string>ActionOutput</string>
                <key>OutputUUID</key><string>{text-UUID}</string>
                <key>OutputName</key><string>文本</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
        <key>WFReplaceTextFind</key>
        <string>"</string>
        <key>WFReplaceTextReplace</key>
        <string>'</string>
    </dict>
</dict>
```

### 4.5 text.match — 正则表达式匹配

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.text.match` |
| **输入** | 文本 |
| **输出** | 匹配结果列表 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | WFTextTokenString | 待匹配的文本 |
| `WFMatchTextPattern` | string | 正则表达式 |

### 4.6 count — 计数

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.count` |
| **输入** | 列表或文本 |
| **输出** | 数字 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `Input` | WFTextTokenAttachment | 要计数的对象 |
| `WFCountType` | string | 计数类型（可选） |

**WFCountType 可选值**：
- 省略（默认）：计数列表项数（Items）
- `Characters`：计数字符数

### 4.7 getitemfromlist — 从列表取指定项

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.getitemfromlist` |
| **输入** | 列表 |
| **输出** | 指定位置的项 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | WFTextTokenAttachment | 输入列表 |
| `WFItemIndex` | integer | 位置索引（从 1 开始） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.getitemfromlist</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>FFDBC555-...</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key><string>ActionOutput</string>
                <key>OutputUUID</key><string>{list-UUID}</string>
                <key>OutputName</key><string>词典值</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
        <key>WFItemIndex</key>
        <integer>1</integer>
    </dict>
</dict>
```

**注意**：`WFItemIndex` 从 **1** 开始（不是 0）。

### 4.8 detect.dictionary — 文本转词典（JSON 解析）

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.detect.dictionary` |
| **输入** | JSON 文本 |
| **输出** | 词典对象 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | WFTextTokenAttachment | 包含 JSON 的文本 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.detect.dictionary</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>2C33BCCB-...</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key><string>ActionOutput</string>
                <key>OutputUUID</key><string>{json-text-UUID}</string>
                <key>OutputName</key><string>词典值</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

**用途**：将 API 返回的 JSON 文本解析为词典，之后可用 `getvalueforkey` 提取字段。

---

## 第 5 章：Action 参考 — 网络

### 5.1 downloadurl — HTTP 请求

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.downloadurl` |
| **输入** | URL + 可选的 Body |
| **输出** | 响应内容（自动解析 JSON 为词典） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFURL` | WFTextTokenString | 请求 URL |
| `WFHTTPMethod` | string | HTTP 方法 |
| `WFHTTPBodyType` | string | Body 类型 |
| `WFHTTPHeaders` | WFDictionaryFieldValue | 自定义请求头 |
| `WFRequestVariable` | WFTextTokenAttachment | 请求体内容 |
| `ShowHeaders` | bool | 是否在 UI 中显示 Headers |

**WFHTTPMethod 可选值**：`GET`, `POST`, `PUT`, `PATCH`, `DELETE`

**WFHTTPBodyType 可选值**：`JSON`, `Form`, `File`

#### 完整示例：POST 请求 DeepSeek API

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.downloadurl</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>33EA887D-...</string>
        <key>ShowHeaders</key>
        <true/>
        <key>WFHTTPMethod</key>
        <string>POST</string>
        <key>WFHTTPBodyType</key>
        <string>File</string>

        <!-- URL -->
        <key>WFURL</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>attachmentsByRange</key>
                <dict>
                    <key>{0, 1}</key>
                    <dict>
                        <key>Type</key><string>ActionOutput</string>
                        <key>OutputUUID</key><string>{base-url-UUID}</string>
                        <key>OutputName</key><string>词典值</string>
                    </dict>
                </dict>
                <key>string</key>
                <string>￼</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenString</string>
        </dict>

        <!-- Headers -->
        <key>WFHTTPHeaders</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>WFDictionaryFieldValueItems</key>
                <array>
                    <dict>
                        <key>WFItemType</key><integer>0</integer>
                        <key>WFKey</key>
                        <dict>
                            <key>Value</key><dict><key>string</key><string>Authorization</string></dict>
                            <key>WFSerializationType</key><string>WFTextTokenString</string>
                        </dict>
                        <key>WFValue</key>
                        <dict>
                            <key>Value</key>
                            <dict>
                                <key>attachmentsByRange</key>
                                <dict>
                                    <key>{7, 1}</key>
                                    <dict>
                                        <key>Type</key><string>ActionOutput</string>
                                        <key>OutputUUID</key><string>{api-key-UUID}</string>
                                        <key>OutputName</key><string>词典值</string>
                                    </dict>
                                </dict>
                                <key>string</key>
                                <string>Bearer ￼</string>
                            </dict>
                            <key>WFSerializationType</key>
                            <string>WFTextTokenString</string>
                        </dict>
                    </dict>
                    <dict>
                        <key>WFItemType</key><integer>0</integer>
                        <key>WFKey</key>
                        <dict>
                            <key>Value</key><dict><key>string</key><string>Content-Type</string></dict>
                            <key>WFSerializationType</key><string>WFTextTokenString</string>
                        </dict>
                        <key>WFValue</key>
                        <dict>
                            <key>Value</key><dict><key>string</key><string>application/json</string></dict>
                            <key>WFSerializationType</key><string>WFTextTokenString</string>
                        </dict>
                    </dict>
                </array>
            </dict>
            <key>WFSerializationType</key>
            <string>WFDictionaryFieldValue</string>
        </dict>

        <!-- Body -->
        <key>WFRequestVariable</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key><string>ActionOutput</string>
                <key>OutputUUID</key><string>{body-text-UUID}</string>
                <key>OutputName</key><string>文本</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

---

## 第 6 章：Action 参考 — 交互与 UI

### 6.1 takescreenshot — 截取屏幕

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.takescreenshot` |
| **参数** | 无（仅 UUID） |
| **输出** | 截图图片 |

### 6.2 extracttextfromimage — OCR 提取文字

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.extracttextfromimage` |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFImage` | WFTextTokenAttachment | 输入图片 |

### 6.3 ask — 请求用户输入

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.ask` |
| **输出** | 用户输入的值 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFAskActionPrompt` | string | 弹窗提示文字 |
| `WFInputType` | string | 输入类型限制（可选，默认 Text） |
| `WFAskActionDefaultAnswer` | string | 默认值（可选） |

**WFInputType 可选值**：`Text`, `Number`, `URL`, `Date`, `Time`, `Date and Time`

### 6.4 alert — 弹窗提示

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.alert` |
| **输出** | 无（用户点击按钮后继续） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFAlertActionTitle` | string | 弹窗标题 |
| `WFAlertActionMessage` | string 或 WFTextTokenString | 弹窗内容（支持变量） |
| `WFAlertActionCancelButtonShown` | bool | 是否显示取消按钮 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.alert</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>WFAlertActionTitle</key>
        <string>⚠️ 请先配置 API Key</string>
        <key>WFAlertActionMessage</key>
        <string>请编辑此快捷指令，填入你的 API Key。</string>
        <key>WFAlertActionCancelButtonShown</key>
        <false/>
    </dict>
</dict>
```

**注意**：`WFAlertActionCancelButtonShown` 为 `true` 时，用户可以取消（取消会中断执行）；为 `false` 时只有确定按钮。

### 6.5 notification — 推送通知

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.notification` |
| **输出** | 无 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFNotificationActionTitle` | string | 通知标题 |
| `WFNotificationActionBody` | string 或 WFTextTokenString | 通知内容（支持变量） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.notification</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>WFNotificationActionTitle</key>
        <string>✅ 记账成功</string>
        <key>WFNotificationActionBody</key>
        <string>手动记账完成</string>
    </dict>
</dict>
```

### 6.6 choosefromlist — 从列表中选择

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.choosefromlist` |
| **输出** | 用户选中的项 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | WFTextTokenAttachment | 提供给用户的列表 |
| `WFChooseFromListActionPrompt` | string | 自定义提示文本（可选） |

### 6.7 comment — 注释

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.comment` |
| **输出** | 无（不执行任何操作） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFCommentActionText` | string | 注释文字 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.comment</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>WFCommentActionText</key>
        <string>🔧 配置说明：在下方词典中填入 API Key</string>
    </dict>
</dict>
```

---

## 第 7 章：Action 参考 — 变量与控制流

### 7.1 setvariable — 设置命名变量

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFVariableName` | string | 变量名 |
| `WFInput` | WFTextTokenAttachment | 要存储的值 |

**用途**：在控制流分支之间共享数据。多个分支各自 setvariable 同一名称，下游统一用 `{Type: Variable, VariableName: "xxx"}` 引用。

### 7.2 conditional — 条件判断

详见 [第 3.1 节](#31-conditional--条件分支-if--else--endif)。

### 7.3 choosefrommenu — 菜单选择

详见 [第 3.2 节](#32-choosefrommenu--菜单选择)。

### 7.4 exit — 退出

详见 [第 3.3 节](#33-exit--提前退出)。

---

## 第 8 章：第三方 App Action

第三方 App 通过 SiriKit / App Intents 框架暴露 action。与系统 action 的区别：
- `WFWorkflowActionIdentifier` 使用 App 的 Bundle ID 前缀（而非 `is.workflow.actions.`）
- 必须包含 `AppIntentDescriptor` 声明 App 信息
- 参数名由 App 定义（如 `amount`, `time`），不遵循 `WF` 前缀命名

### AppIntentDescriptor 字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `AppIntentIdentifier` | Intent 标识符 | `ICMarkAShortcutOutcomeRecordIntent` |
| `BundleIdentifier` | App Bundle ID | `com.gostraight.smallAccountBook` |
| `Name` | App 显示名 | `iCost` |
| `TeamIdentifier` | Apple 开发者团队 ID | `PAG33UNQ5Q` |
| `ActionRequiresAppInstallation` | 是否要求安装 App | `true`（可选字段） |

### 已知第三方 Action（iCost 记账 App）

| Action ID | 说明 | 参数 |
|-----------|------|------|
| `*.ICMarkAShortcutOutcomeRecordIntent` | 记录支出 | `amount`, `time`, `category`, `account`, `remark` |
| `*.ICMarkAShortcutIncomeRecordIntent` | 记录收入 | (同上) |
| `*.ICSearchCategoryEntity` | 查询分类列表 | 无参数，输出分类列表 |
| `*.ICSearchAssetEntity` | 查询账户列表 | 无参数，输出账户列表 |

---

## 第 9 章：常用模式

### 9.1 模式 A：线性管道

```
action_1 → action_2 → action_3
```

前一个 action 的输出通过 `ActionOutput` + UUID 传给下一个。

**示例**：截屏 → OCR → 正则匹配

### 9.2 模式 B：条件分支汇聚（通过命名变量）

多个分支各自设置同名变量，下游统一引用。

```
       ┌─ 分支 A → setvariable "结果" ← 值1
条件 ──┤
       └─ 分支 B → setvariable "结果" ← 值2

下游 action ← Variable "结果"    (无论哪个分支执行，都能拿到值)
```

这是 Shortcuts 中**跨分支传值的唯一方式**。

### 9.3 模式 C：菜单驱动的分支逻辑

```
choosefrommenu BEGIN ("选择操作")
├─ ITEM "选项1" → actions...
├─ ITEM "选项2" → actions...
└─ ITEM "退出"  → (空，不做操作)
choosefrommenu END
```

菜单项的顺序必须与 `WFMenuItems` 数组一致。

### 9.4 模式 D：Guard 检查（前置验证 + 提前退出）

在执行核心逻辑之前验证前置条件，不满足则提示用户并退出。

```
dictionary → getvalueforkey "api_key" → count(Characters) → IF = 0
    alert "请先配置"
    exit                               ← 不满足条件，提前退出
ELSE
ENDIF
... 继续正常逻辑 ...
```

### 9.5 模式 E：API 调用 + JSON 解析管道

Shortcuts 中调用外部 API 并解析返回数据的标准流程：

```
1. gettext         ← 构建请求 body (JSON 字符串)
2. text.replace    ← 清洗文本（可选，去换行/转义引号）
3. downloadurl     ← POST 请求，自动解析 JSON 响应为词典
4. getvalueforkey  ← 提取 response.choices
5. getitemfromlist  ← 取 choices[0]
6. getvalueforkey  ← 取 message.content
7. detect.dictionary ← JSON 文本 → 词典
8. getvalueforkey  ← 逐字段提取 (type, amount, ...)
```

### 9.6 模式 F：配置存储（词典 + Import Questions）

将配置参数存在词典 action 中，用 `WFWorkflowImportQuestions` 让用户在导入时配置。

```
[action 0] dictionary {api_key: "", base_url: "...", model: "..."}
    ↑ WFWorkflowImportQuestions 指向 ActionIndex=0, ParameterKey="WFItems"

运行时: getvalueforkey 逐项读取配置
```

---

## 第 10 章：生成 Shortcut 的清单

当你要从零生成一个 `.shortcut` 文件时，按以下步骤：

1. **规划 action 列表**：确定执行顺序和数据流
2. **为需要被引用的 action 生成 UUID**：使用 `uuid.uuid4()`，严禁复制示例中的 UUID
3. **为控制流生成 GroupingIdentifier**：每组 if/else/endif 或 menu 共用一个 UUID
4. **编写 XML plist**：按本手册的格式组装
5. **填充顶层字段**：
   - `WFWorkflowActions`：action 数组
   - `WFWorkflowClientVersion`：`"3612.0.2.1"`
   - `WFWorkflowIcon`：可使用默认值
   - `WFWorkflowInputContentItemClasses`：根据需要填充（可为空数组）
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
| `WFWorkflowImportQuestions` | array | ✅ | 导入提问（可为空数组，见 1.3） |
| `WFWorkflowHasOutputFallback` | bool | ✅ | 输出回退 |
| `WFWorkflowHasShortcutInputVariables` | bool | ✅ | 是否有 shortcut 输入变量 |
| `WFWorkflowMinimumClientVersion` | int | ✅ | 最低客户端版本 |
| `WFWorkflowMinimumClientVersionString` | string | ✅ | 最低版本字符串 |
| `WFQuickActionSurfaces` | array | ✅ | Quick Action 配置（可为空数组） |

## 附录 B：已知 Action 类型索引

### 系统 Action（19 种）

| # | Action Identifier | 简称 | 类别 | 章节 |
|:-:|-------------------|------|------|:----:|
| 1 | `is.workflow.actions.dictionary` | 创建词典 | 数据 | 4.1 |
| 2 | `is.workflow.actions.getvalueforkey` | 词典取值 | 数据 | 4.2 |
| 3 | `is.workflow.actions.gettext` | 构建文本 | 数据 | 4.3 |
| 4 | `is.workflow.actions.text.replace` | 文本替换 | 数据 | 4.4 |
| 5 | `is.workflow.actions.text.match` | 正则匹配 | 数据 | 4.5 |
| 6 | `is.workflow.actions.count` | 计数 | 数据 | 4.6 |
| 7 | `is.workflow.actions.getitemfromlist` | 列表取项 | 数据 | 4.7 |
| 8 | `is.workflow.actions.detect.dictionary` | JSON 解析 | 数据 | 4.8 |
| 9 | `is.workflow.actions.downloadurl` | HTTP 请求 | 网络 | 5.1 |
| 10 | `is.workflow.actions.takescreenshot` | 截屏 | 交互 | 6.1 |
| 11 | `is.workflow.actions.extracttextfromimage` | OCR | 交互 | 6.2 |
| 12 | `is.workflow.actions.ask` | 用户输入 | 交互 | 6.3 |
| 13 | `is.workflow.actions.alert` | 弹窗 | 交互 | 6.4 |
| 14 | `is.workflow.actions.notification` | 通知 | 交互 | 6.5 |
| 15 | `is.workflow.actions.choosefromlist` | 列表选择 | 交互 | 6.6 |
| 16 | `is.workflow.actions.comment` | 注释 | 其他 | 6.7 |
| 17 | `is.workflow.actions.setvariable` | 设置变量 | 变量 | 7.1 |
| 18 | `is.workflow.actions.conditional` | 条件判断 | 控制流 | 7.2 / 3.1 |
| 19 | `is.workflow.actions.choosefrommenu` | 菜单选择 | 控制流 | 7.3 / 3.2 |
| 20 | `is.workflow.actions.exit` | 退出 | 控制流 | 7.4 / 3.3 |

### 第三方 Action — iCost 记账 App（4 种）

| # | Action Identifier | 简称 | 章节 |
|:-:|-------------------|------|:----:|
| 21 | `*.ICMarkAShortcutOutcomeRecordIntent` | 记账(支出) | 8 |
| 22 | `*.ICMarkAShortcutIncomeRecordIntent` | 记账(收入) | 8 |
| 23 | `*.ICSearchCategoryEntity` | 查询分类 | 8 |
| 24 | `*.ICSearchAssetEntity` | 查询账户 | 8 |
