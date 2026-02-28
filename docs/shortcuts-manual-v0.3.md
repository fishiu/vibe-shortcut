# iOS Shortcuts 编程手册 v0.3

> **版本**: 0.3 (基于 Sample A + B + C 分析)
> **覆盖范围**: 46 种 action 类型 (系统 36 + 第三方 10)，循环，条件，菜单，变量传递，HTTP API，JSON 解析
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

**WFItemType 值**：

| 值 | 类型 | 示例 |
|:-:|------|------|
| 0 | Text (文本) | `api_key: "sk-xxx"` |
| 1 | Dictionary (词典) | 嵌套词典值 |
| 3 | Number (数字) | `版本号: 2.42` |
| 4 | Boolean (布尔) | `记录位置: False` |
| 5 | Array (数组) | 列表值 |

**注意**：没有 `2`（跳过了）

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
| 100 | 有任何值 (Has Any Value) |

**WFCondition=100** 用于检查变量是否非空。可配合 `WFConditionalActionString` (WFTextTokenString) 进一步检查是否包含指定文本。

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

### 3.3 repeat.count — 固定次数循环

同样使用 `GroupingIdentifier` + `WFControlFlowMode`，但**只有 BEGIN(0) 和 END(2)，没有 mode=1**。

#### BEGIN

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.repeat.count</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>{UUID}</string>
        <key>WFControlFlowMode</key>
        <integer>0</integer>
        <key>UUID</key>
        <string>{UUID}</string>
        <key>WFRepeatCount</key>
        <real>5</real>                      <!-- 循环次数（float 类型） -->
    </dict>
</dict>
```

#### END

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.repeat.count</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>{同上 UUID}</string>
        <key>WFControlFlowMode</key>
        <integer>2</integer>
        <key>UUID</key>
        <string>{UUID}</string>
    </dict>
</dict>
```

#### 执行顺序

```
[repeat.count BEGIN count=5]
    action_a                    ← 执行 5 次
    action_b
[repeat.count END]
```

### 3.4 repeat.each — 遍历列表循环

遍历列表中的每个元素。

#### BEGIN

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.repeat.each</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>GroupingIdentifier</key>
        <string>{UUID}</string>
        <key>WFControlFlowMode</key>
        <integer>0</integer>
        <key>UUID</key>
        <string>{UUID}</string>
        <key>WFInput</key>                  <!-- 要遍历的列表 -->
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key><string>ActionOutput</string>
                <key>OutputUUID</key><string>{list-UUID}</string>
                <key>OutputName</key><string>词典</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

#### END

与 repeat.count END 相同结构。

#### 执行顺序

```
[repeat.each BEGIN input=列表]
    action_a                    ← 对列表中每个元素执行
    action_b                    ← 通过 BEGIN 的 UUID 引用当前元素
[repeat.each END]
```

### 3.5 exit — 提前退出

无条件终止 shortcut 的执行。常与 conditional 配合做 guard 检查。

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.exit</string>
    <key>WFWorkflowActionParameters</key>
    <dict/>
</dict>
```

### 3.6 控制流结构对比

| 结构 | mode=0 | mode=1 | mode=2 |
|------|--------|--------|--------|
| conditional | BEGIN (条件) | ELSE | END |
| choosefrommenu | BEGIN (菜单定义) | ITEM (每个选项) | END |
| repeat.count | BEGIN (循环次数) | — | END |
| repeat.each | BEGIN (输入列表) | — | END |

所有控制流结构共用 `GroupingIdentifier` + `WFControlFlowMode` 模式。

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

### 4.9 number — 数字字面量

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.number` |
| **输入** | 无 |
| **输出** | 数字值 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFNumberActionNumber` | integer/real 或 WFTextTokenAttachment | 数字值（可为字面量或变量引用） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.number</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>A1B2C3D4-...</string>
        <key>WFNumberActionNumber</key>
        <integer>0</integer>
    </dict>
</dict>
```

**说明**：当值为变量引用时，`WFNumberActionNumber` 使用 WFTextTokenAttachment 包装。常用于为 conditional 提供比较值，或为 calculateexpression 提供操作数。

### 4.10 calculateexpression — 计算表达式

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.calculateexpression` |
| **输入** | 无 |
| **输出** | 计算结果（数字） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `Input` | WFTextTokenString | 数学表达式（可嵌入变量） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.calculateexpression</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>E5F6A7B8-...</string>
        <key>Input</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>attachmentsByRange</key>
                <dict>
                    <key>{0, 1}</key>
                    <dict>
                        <key>Type</key><string>ActionOutput</string>
                        <key>OutputUUID</key><string>{num1-UUID}</string>
                        <key>OutputName</key><string>数字</string>
                    </dict>
                    <key>{2, 1}</key>
                    <dict>
                        <key>Type</key><string>ActionOutput</string>
                        <key>OutputUUID</key><string>{num2-UUID}</string>
                        <key>OutputName</key><string>数字</string>
                    </dict>
                </dict>
                <key>string</key>
                <string>￼+￼</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenString</string>
        </dict>
    </dict>
</dict>
```

**说明**：表达式作为 WFTextTokenString 传入，数学运算符（`+`, `-`, `*`, `/`）直接写在 string 中，变量用 `￼` 占位。

### 4.11 number.random — 随机数

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.number.random` |
| **输入** | 无 |
| **输出** | 随机整数 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFRandomNumberMinimum` | integer | 最小值 |
| `WFRandomNumberMaximum` | integer | 最大值 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.number.random</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>C9D0E1F2-...</string>
        <key>WFRandomNumberMinimum</key>
        <integer>1</integer>
        <key>WFRandomNumberMaximum</key>
        <integer>5</integer>
    </dict>
</dict>
```

### 4.12 text.split — 文本分割

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.text.split` |
| **输入** | 文本 |
| **输出** | 文本列表 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | WFTextTokenAttachment | 要分割的文本 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.text.split</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>A3B4C5D6-...</string>
        <key>text</key>
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
    </dict>
</dict>
```

**说明**：默认按换行符分割。分割符可通过其他参数自定义（如 `WFTextSeparator`）。

### 4.13 filter.files — 过滤/查询

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.filter.files` |
| **输入** | 列表 |
| **输出** | 符合条件的项 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFContentItemInputParameter` | WFTextTokenAttachment | 输入列表 |
| `WFContentItemFilter` | WFContentPredicateTableTemplate | 过滤条件 |
| `WFContentItemLimitEnabled` | bool | 是否限制结果数量 |
| `WFContentItemLimitNumber` | real | 最大结果数量 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.filter.files</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>D7E8F9A0-...</string>
        <key>WFContentItemInputParameter</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>Type</key><string>ActionOutput</string>
                <key>OutputUUID</key><string>{list-UUID}</string>
                <key>OutputName</key><string>iCost</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
        <key>WFContentItemFilter</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>WFActionParameterFilterPrefix</key>
                <integer>1</integer>
                <key>WFContentPredicateBoundedDate</key>
                <false/>
                <key>WFActionParameterFilterTemplates</key>
                <array>
                    <dict>
                        <key>Operator</key>
                        <integer>4</integer>
                        <key>Property</key>
                        <string>Name</string>
                        <key>Removable</key>
                        <true/>
                        <key>Values</key>
                        <dict>
                            <key>String</key>
                            <dict>
                                <key>Value</key>
                                <dict>
                                    <key>string</key><string>￼</string>
                                    <key>attachmentsByRange</key>
                                    <dict>
                                        <key>{0, 1}</key>
                                        <dict>
                                            <key>Type</key><string>Variable</string>
                                            <key>VariableName</key><string>from_account</string>
                                        </dict>
                                    </dict>
                                </dict>
                                <key>WFSerializationType</key>
                                <string>WFTextTokenString</string>
                            </dict>
                            <key>Unit</key>
                            <integer>4</integer>
                        </dict>
                    </dict>
                </array>
            </dict>
            <key>WFSerializationType</key>
            <string>WFContentPredicateTableTemplate</string>
        </dict>
        <key>WFContentItemLimitEnabled</key>
        <true/>
        <key>WFContentItemLimitNumber</key>
        <real>1</real>
    </dict>
</dict>
```

**说明**：`WFContentPredicateTableTemplate` 是第四种序列化类型，用于描述过滤查询条件。`Operator` 使用与 WFCondition 相同的运算符编号。`Property` 指定要比较的属性名。常用于对第三方 App 返回的实体列表进行筛选。

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

### 5.2 openurl — 打开 URL

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.openurl` |
| **输入** | URL |
| **输出** | 无 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | string 或 WFTextTokenAttachment | 要打开的 URL |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.openurl</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>WFInput</key>
        <string>https://example.com</string>
    </dict>
</dict>
```

**说明**：`WFInput` 可以是纯字符串（静态 URL），也可以是 WFTextTokenAttachment（动态引用）。支持 `http(s)://` 和自定义 scheme（如 `icost://`）。

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

### 6.7 showresult — 显示结果

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.showresult` |
| **输出** | 无（在屏幕上显示内容） |

| 参数 | 类型 | 说明 |
|------|------|------|
| `Text` | WFTextTokenString | 要显示的内容（支持变量） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.showresult</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>Text</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>attachmentsByRange</key>
                <dict>
                    <key>{0, 1}</key>
                    <dict>
                        <key>Type</key><string>ActionOutput</string>
                        <key>OutputUUID</key><string>{result-UUID}</string>
                        <key>OutputName</key><string>文本</string>
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

**说明**：与 `alert` 类似但更轻量，在 Shortcut 执行界面直接显示内容，用户无需点击按钮。

### 6.8 comment — 注释

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

### 6.9 delay — 延迟

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.delay` |
| **输出** | 无 |

| 参数 | 类型 | 说明 |
|------|------|------|
| （无必需参数） | | 默认延迟 1 秒 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.delay</string>
    <key>WFWorkflowActionParameters</key>
    <dict/>
</dict>
```

**说明**：暂停执行。参数为空时默认 1 秒。可通过 `WFDelayTime` 自定义秒数。

### 6.10 getdevicedetails — 获取设备信息

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.getdevicedetails` |
| **输出** | 设备信息值 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFDeviceDetail` | string | 要获取的信息类型 |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.getdevicedetails</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>B1C2D3E4-...</string>
        <key>WFDeviceDetail</key>
        <string>Screen Width</string>
    </dict>
</dict>
```

**WFDeviceDetail 已知值**：`System Version`, `Screen Width`, `Device Name`, `Device Model` 等。省略时默认取设备名称。

### 6.11 openapp — 打开 App

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.openapp` |
| **输出** | 无 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFAppIdentifier` | string | App 的 Bundle ID |
| `WFSelectedApp` | dict | App 信息（BundleIdentifier, Name, TeamIdentifier） |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.openapp</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>WFAppIdentifier</key>
        <string>com.apple.shortcuts</string>
        <key>WFSelectedApp</key>
        <dict>
            <key>BundleIdentifier</key>
            <string>com.apple.shortcuts</string>
            <key>Name</key>
            <string>快捷指令</string>
            <key>TeamIdentifier</key>
            <string>0000000000</string>
        </dict>
    </dict>
</dict>
```

### 6.12 setclipboard — 设置剪贴板

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.setclipboard` |
| **输出** | 无 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | WFTextTokenAttachment | 要复制到剪贴板的内容 |

### 6.13 vibrate — 震动

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.vibrate` |
| **输出** | 无 |

无参数。触发设备震动反馈。

### 6.14 image.crop — 裁剪图片

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.image.crop` |
| **输入** | 图片 |
| **输出** | 裁剪后的图片 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFInput` | WFTextTokenAttachment | 输入图片 |
| `WFImageCropPosition` | string | 裁剪方式（`Custom` 等） |
| `WFImageCropX` | string/integer | X 坐标 |
| `WFImageCropY` | string/integer | Y 坐标 |
| `WFImageCropWidth` | integer 或 WFTextTokenAttachment | 宽度 |
| `WFImageCropHeight` | integer 或 WFTextTokenAttachment | 高度 |

**说明**：`WFImageCropPosition` 为 `Custom` 时使用 X/Y/Width/Height 参数。宽高支持变量引用（如引用 `getdevicedetails` 获取的屏幕宽度）。

### 6.15 image.resize — 调整图片大小

| 项目 | 值 |
|------|-----|
| **Identifier** | `is.workflow.actions.image.resize` |
| **输入** | 图片 |
| **输出** | 调整后的图片 |

| 参数 | 类型 | 说明 |
|------|------|------|
| `WFImage` | WFTextTokenAttachment | 输入图片 |
| `WFImageResizeWidth` | integer | 目标宽度（高度自动按比例缩放） |

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

### 7.4 repeat.count — 固定次数循环

详见 [第 3.3 节](#33-repeatcount--固定次数循环)。

### 7.5 repeat.each — 遍历列表循环

详见 [第 3.4 节](#34-repeateach--遍历列表循环)。

### 7.6 exit — 退出

详见 [第 3.5 节](#35-exit--提前退出)。

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

### 已知第三方 Action — iCost 记账 App（9 种）

| Action ID | 说明 | 参数 |
|-----------|------|------|
| `*.ICMarkAShortcutOutcomeRecordIntent` | 记录支出 | `amount`, `time`, `category`, `account`, `remark` |
| `*.ICMarkAShortcutIncomeRecordIntent` | 记录收入 | (同上) |
| `*.ICMarkAShortcutTransferRecordIntent` | 记录转账 | `amount`, `book`, `from_account`, `to_account` |
| `*.ICSearchCategoryEntity` | 查询分类列表 | 无参数（可带 `WFContentItemFilter`），输出分类列表 |
| `*.ICSearchAssetEntity` | 查询账户列表 | 无参数（可带 `WFContentItemFilter`），输出账户列表 |
| `*.ICSearchBookEntity` | 查询账本列表 | 无参数（可带 `WFContentItemFilter`），输出账本列表 |
| `*.ICSearchCurrencyEntity` | 查询货币列表 | 无参数（可带 `WFContentItemFilter`），输出货币列表 |
| `*.ICSearchTagEntity` | 查询标签列表 | 无参数（可带 `WFContentItemFilter`），输出标签列表 |
| `*.ICRouterShortcut` | 路由/导航 | `url`（dict: 含 value/title/subtitle） |

**注**：`*` = `com.gostraight.smallAccountBook`

#### ICRouterShortcut — App 内路由

```xml
<key>url</key>
<dict>
    <key>value</key>
    <string>icost://book_main</string>
    <key>title</key>
    <dict><key>key</key><string>账本首页</string></dict>
    <key>subtitle</key>
    <dict><key>key</key><string>账本首页</string></dict>
</dict>
```

**说明**：通过自定义 scheme 导航到 App 内特定页面。`url.value` 是实际的路由地址。

#### ICSearch*Entity 的过滤查询

查询类 action（ICSearchBookEntity、ICSearchCurrencyEntity、ICSearchTagEntity）可以通过 `WFContentItemFilter`（WFContentPredicateTableTemplate）进行条件筛选，语法与 `filter.files` 相同（见 4.13 节）。

### 已知第三方 Action — Apple 系统（1 种）

| Action ID | 说明 | 参数 |
|-----------|------|------|
| `com.apple.ShortcutsActions.ShowControlCenterAction` | 控制中心 | `operation` (string) |

```xml
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>com.apple.ShortcutsActions.ShowControlCenterAction</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>AppIntentDescriptor</key>
        <dict>
            <key>AppIntentIdentifier</key>
            <string>ShowControlCenterAction</string>
            <key>BundleIdentifier</key>
            <string>com.apple.ShortcutsActions</string>
            <key>Name</key>
            <string>ShortcutsActions</string>
            <key>TeamIdentifier</key>
            <string>0000000000</string>
        </dict>
        <key>operation</key>
        <string>hide</string>
    </dict>
</dict>
```

**operation 已知值**：`hide`（隐藏控制中心）。

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

### 9.6 模式 F：遍历列表 + 条件筛选

```
[list] → repeat.each BEGIN
    getvalueforkey "type"         ← 取当前元素的属性
    conditional BEGIN (=1)        ← 条件筛选
        setvariable "result"      ← 保存符合条件的项
    conditional END
repeat.each END
```

遍历列表中的每个元素，对每个元素进行条件判断并处理。循环体内通过 BEGIN 的 UUID 引用当前元素。

### 9.7 模式 G：数学运算管道

```
number(0) → setvariable "total"
repeat.each BEGIN input=列表
    getvalueforkey "amount"
    calculateexpression "￼+￼"    ← total + 当前值
    setvariable "total"           ← 更新累计值
repeat.each END
```

利用 `calculateexpression` 在循环中累加值。表达式中的变量通过 WFTextTokenString 嵌入。

### 9.8 模式 H：截屏 + 裁剪 + OCR

```
getdevicedetails "Screen Width"  ← 获取屏幕宽度
takescreenshot                   ← 截取屏幕
image.crop (Custom, x=0, y=120, w=屏幕宽, h=计算值)
image.resize (width=500)         ← 缩小以加速 OCR
extracttextfromimage             ← OCR 识别
```

动态获取设备信息来计算裁剪区域，常用于截屏识别场景。

### 9.9 模式 I：配置存储（词典 + Import Questions）

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

### 系统 Action（36 种）

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
| 9 | `is.workflow.actions.number` | 数字字面量 | 数据 | 4.9 |
| 10 | `is.workflow.actions.calculateexpression` | 计算表达式 | 数据 | 4.10 |
| 11 | `is.workflow.actions.number.random` | 随机数 | 数据 | 4.11 |
| 12 | `is.workflow.actions.text.split` | 文本分割 | 数据 | 4.12 |
| 13 | `is.workflow.actions.filter.files` | 过滤/查询 | 数据 | 4.13 |
| 14 | `is.workflow.actions.downloadurl` | HTTP 请求 | 网络 | 5.1 |
| 15 | `is.workflow.actions.openurl` | 打开 URL | 网络 | 5.2 |
| 16 | `is.workflow.actions.takescreenshot` | 截屏 | 交互 | 6.1 |
| 17 | `is.workflow.actions.extracttextfromimage` | OCR | 交互 | 6.2 |
| 18 | `is.workflow.actions.ask` | 用户输入 | 交互 | 6.3 |
| 19 | `is.workflow.actions.alert` | 弹窗 | 交互 | 6.4 |
| 20 | `is.workflow.actions.notification` | 通知 | 交互 | 6.5 |
| 21 | `is.workflow.actions.choosefromlist` | 列表选择 | 交互 | 6.6 |
| 22 | `is.workflow.actions.showresult` | 显示结果 | 交互 | 6.7 |
| 23 | `is.workflow.actions.comment` | 注释 | 其他 | 6.8 |
| 24 | `is.workflow.actions.delay` | 延迟 | 系统 | 6.9 |
| 25 | `is.workflow.actions.getdevicedetails` | 设备信息 | 系统 | 6.10 |
| 26 | `is.workflow.actions.openapp` | 打开 App | 系统 | 6.11 |
| 27 | `is.workflow.actions.setclipboard` | 设置剪贴板 | 系统 | 6.12 |
| 28 | `is.workflow.actions.vibrate` | 震动 | 系统 | 6.13 |
| 29 | `is.workflow.actions.image.crop` | 裁剪图片 | 图片 | 6.14 |
| 30 | `is.workflow.actions.image.resize` | 调整图片 | 图片 | 6.15 |
| 31 | `is.workflow.actions.setvariable` | 设置变量 | 变量 | 7.1 |
| 32 | `is.workflow.actions.conditional` | 条件判断 | 控制流 | 7.2 / 3.1 |
| 33 | `is.workflow.actions.choosefrommenu` | 菜单选择 | 控制流 | 7.3 / 3.2 |
| 34 | `is.workflow.actions.repeat.count` | 固定循环 | 控制流 | 7.4 / 3.3 |
| 35 | `is.workflow.actions.repeat.each` | 遍历循环 | 控制流 | 7.5 / 3.4 |
| 36 | `is.workflow.actions.exit` | 退出 | 控制流 | 7.6 / 3.5 |

### 第三方 Action — iCost 记账 App（9 种）

| # | Action Identifier | 简称 | 章节 |
|:-:|-------------------|------|:----:|
| 37 | `*.ICMarkAShortcutOutcomeRecordIntent` | 记账(支出) | 8 |
| 38 | `*.ICMarkAShortcutIncomeRecordIntent` | 记账(收入) | 8 |
| 39 | `*.ICMarkAShortcutTransferRecordIntent` | 记账(转账) | 8 |
| 40 | `*.ICSearchCategoryEntity` | 查询分类 | 8 |
| 41 | `*.ICSearchAssetEntity` | 查询账户 | 8 |
| 42 | `*.ICSearchBookEntity` | 查询账本 | 8 |
| 43 | `*.ICSearchCurrencyEntity` | 查询货币 | 8 |
| 44 | `*.ICSearchTagEntity` | 查询标签 | 8 |
| 45 | `*.ICRouterShortcut` | 路由/导航 | 8 |

### 第三方 Action — Apple 系统（1 种）

| # | Action Identifier | 简称 | 章节 |
|:-:|-------------------|------|:----:|
| 46 | `com.apple.ShortcutsActions.ShowControlCenterAction` | 控制中心 | 8 |
