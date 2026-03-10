# Architect Design: Phase 3B — DeepSeek API Shortcut XML 骨架设计

> **Status**: ✅ 已验收
> **产出**: `samples/deepseek-api/deepseek-api.xml`, `samples/deepseek-api/deepseek-api.shortcut`

## 1. 功能描述
用户输入问题 → 构建 JSON body → POST 到 DeepSeek API → 解析 response → 通知显示 AI 回答。8 个 action。

## 2. 数据流与 UUID 引用链

```
Action 1: gettext (API Key)
  UUID = {{UUID-A}}
  输出 → API Key 字符串（明文占位符，Engineer 替换为真实 key）

Action 2: ask (用户输入)
  UUID = {{UUID-B}}
  输出 → 用户问题文本
         ↓ 引用 UUID-B
Action 3: gettext (构建 JSON Body)
  UUID = {{UUID-C}}
  WFTextActionText ← 嵌入 UUID-B 于 content 字段  [WFTextTokenString]
  输出 → '{"model":"deepseek-chat","messages":[{"role":"user","content":"..."}]}'
         ↓ 引用 UUID-A, UUID-C
Action 4: downloadurl (POST API 请求)
  UUID = {{UUID-D}}
  WFURL ← 静态 "https://api.deepseek.com/v1/chat/completions"
  WFHTTPHeaders.Authorization ← "Bearer " + UUID-A  [WFTextTokenString]
  WFHTTPHeaders.Content-Type ← 静态 "application/json"
  WFRequestVariable ← UUID-C  [WFTextTokenAttachment]
  输出 → JSON response (自动解析为 dict)
         ↓ 引用 UUID-D
Action 5: getvalueforkey (提取 choices)
  UUID = {{UUID-E}}
  WFDictionaryKey = "choices"
  WFInput ← UUID-D  [WFTextTokenAttachment]
  输出 → choices 数组
         ↓ 引用 UUID-E
Action 6: getitemfromlist (取第一项)
  UUID = {{UUID-F}}
  WFInput ← UUID-E  [WFTextTokenAttachment]
  WFItemIndex = 1  (Shortcuts 索引从 1 开始)
  输出 → choices[0] dict
         ↓ 引用 UUID-F
Action 7: getvalueforkey (提取 message.content)
  UUID = {{UUID-G}}
  WFDictionaryKey = "message.content"  (点号分隔的嵌套路径)
  WFInput ← UUID-F  [WFTextTokenAttachment]
  输出 → AI 回答文本
         ↓ 引用 UUID-G
Action 8: notification (显示结果)
  无 UUID（终端 action）
  WFNotificationActionTitle ← 静态 "DeepSeek"
  WFNotificationActionBody ← UUID-G  [WFTextTokenString]
```

> **铁律提醒**: `{{UUID-A}}` ~ `{{UUID-G}}` 均为占位符，Engineer 必须用 `uuid.uuid4()` 动态生成。

## 3. 完整 XML Plist 模板

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>WFWorkflowActions</key>
    <array>

        <!-- Action 1: API Key（明文存储，Engineer 替换为真实 key） -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.gettext</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-A}}</string>
                <key>WFTextActionText</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>string</key>
                        <string>sk-REPLACE-WITH-REAL-KEY</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 2: 用户输入 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.ask</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-B}}</string>
                <key>WFAskActionPrompt</key>
                <string>Ask DeepSeek:</string>
                <key>WFInputType</key>
                <string>Text</string>
            </dict>
        </dict>

        <!-- Action 3: 构建 JSON 请求体 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.gettext</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-C}}</string>
                <key>WFTextActionText</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{63, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Provided Input</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-B}}</string>
                                <key>Type</key>
                                <string>ActionOutput</string>
                            </dict>
                        </dict>
                        <key>string</key>
                        <string>{"model":"deepseek-chat","messages":[{"role":"user","content":"&#xFFFC;"}]}</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 4: POST 到 DeepSeek API -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.downloadurl</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-D}}</string>
                <key>ShowHeaders</key>
                <true/>
                <key>WFHTTPMethod</key>
                <string>POST</string>
                <key>WFHTTPBodyType</key>
                <string>File</string>
                <key>WFURL</key>
                <string>https://api.deepseek.com/v1/chat/completions</string>
                <key>WFHTTPHeaders</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>WFDictionaryFieldValueItems</key>
                        <array>
                            <!-- Authorization: Bearer {API_KEY} -->
                            <dict>
                                <key>WFItemType</key>
                                <integer>0</integer>
                                <key>WFKey</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>string</key>
                                        <string>Authorization</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                                <key>WFValue</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>attachmentsByRange</key>
                                        <dict>
                                            <key>{7, 1}</key>
                                            <dict>
                                                <key>OutputName</key>
                                                <string>Text</string>
                                                <key>OutputUUID</key>
                                                <string>{{UUID-A}}</string>
                                                <key>Type</key>
                                                <string>ActionOutput</string>
                                            </dict>
                                        </dict>
                                        <key>string</key>
                                        <string>Bearer &#xFFFC;</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                            </dict>
                            <!-- Content-Type: application/json -->
                            <dict>
                                <key>WFItemType</key>
                                <integer>0</integer>
                                <key>WFKey</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>string</key>
                                        <string>Content-Type</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                                <key>WFValue</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>string</key>
                                        <string>application/json</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                            </dict>
                        </array>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFDictionaryFieldValue</string>
                </dict>
                <key>WFRequestVariable</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Text</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-C}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 5: 提取 choices 数组 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getvalueforkey</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-E}}</string>
                <key>WFDictionaryKey</key>
                <string>choices</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Contents of URL</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-D}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 6: 取第一项 choices[0] -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getitemfromlist</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-F}}</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Value for Key</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-E}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
                <key>WFItemIndex</key>
                <integer>1</integer>
            </dict>
        </dict>

        <!-- Action 7: 提取 message.content -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getvalueforkey</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-G}}</string>
                <key>WFDictionaryKey</key>
                <string>message.content</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Item from List</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-F}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 8: 通知显示 AI 回答 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.notification</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>WFNotificationActionTitle</key>
                <string>DeepSeek</string>
                <key>WFNotificationActionBody</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{0, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Value for Key</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-G}}</string>
                                <key>Type</key>
                                <string>ActionOutput</string>
                            </dict>
                        </dict>
                        <key>string</key>
                        <string>&#xFFFC;</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

    </array>

    <!-- 元数据 -->
    <key>WFWorkflowClientVersion</key>
    <string>3612.0.2.1</string>

    <key>WFWorkflowHasOutputFallback</key>
    <false/>

    <key>WFWorkflowHasShortcutInputVariables</key>
    <false/>

    <key>WFWorkflowIcon</key>
    <dict>
        <key>WFWorkflowIconGlyphNumber</key>
        <integer>59514</integer>
        <key>WFWorkflowIconStartColor</key>
        <integer>431817727</integer>
    </dict>

    <key>WFWorkflowImportQuestions</key>
    <array/>

    <key>WFWorkflowInputContentItemClasses</key>
    <array>
        <string>WFStringContentItem</string>
    </array>

    <key>WFWorkflowMinimumClientVersion</key>
    <integer>900</integer>
    <key>WFWorkflowMinimumClientVersionString</key>
    <string>900</string>

    <key>WFWorkflowOutputContentItemClasses</key>
    <array/>

    <key>WFQuickActionSurfaces</key>
    <array/>

    <key>WFWorkflowTypes</key>
    <array>
        <string>WFWorkflowTypeShowInSearch</string>
    </array>
</dict>
</plist>
```

## 4. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| API Key 存储 | gettext 明文 | 3B 是验证性 shortcut，简单优先。生产环境应用 WFWorkflowImportQuestions |
| WFURL 格式 | 静态 `<string>` | URL 不含变量，无需 WFTextTokenString 包装 |
| HTTP Body 类型 | `File` (非 `JSON`) | 与 Sample B 一致，body 由 gettext 预构建为 JSON 字符串 |
| JSON body 构建 | gettext + WFTextTokenString | 在模板字符串中用 ￼ 占位插入用户输入，位置 {63, 1} |
| Response 解析 | downloadurl 自动解析 | downloadurl 收到 JSON response 自动转 dict，无需 detect.dictionary |
| 嵌套取值 | `message.content` 点号路径 | getvalueforkey 原生支持点号分隔的嵌套路径 |
| 数组索引 | WFItemIndex=1 | Shortcuts 索引从 1 开始，非 0 |
| 图标颜色 | 431817727 (深蓝) | 区分于 3A 的紫色 |

## 5. 字符位置计算备注

Action 3 的 JSON body 模板中 ￼ 的位置：
```
{"model":"deepseek-chat","messages":[{"role":"user","content":"￼"}]}
0         1         2         3         4         5         6
0123456789012345678901234567890123456789012345678901234567890123
                                                               ^
                                                            pos 63
```
`{63, 1}` — 第 63 个字符处，长度 1（占位符 ￼）。

## 6. Engineer 实现指引

1. **创建** `samples/deepseek-api/deepseek-api.xml`，基于上述模板
2. **替换** `{{UUID-A}}` ~ `{{UUID-G}}` 为 `uuid.uuid4()` 生成的真实 UUID（全大写，带连字符）
3. **替换** `sk-REPLACE-WITH-REAL-KEY` 为真实 DeepSeek API Key
4. **构建**: `python tools/shortcut_tool.py build samples/deepseek-api/deepseek-api.xml samples/deepseek-api/deepseek-api-unsigned.shortcut`
5. **签名**: `python tools/shortcut_tool.py sign samples/deepseek-api/deepseek-api-unsigned.shortcut samples/deepseek-api/deepseek-api.shortcut`
6. **验证**: 导入 iPhone → 输入任意问题 → 通知标题 "DeepSeek"，body 为 AI 回答
7. **安全提醒**: `.shortcut` 文件包含明文 API Key，**不要** commit 到 git。在 `.gitignore` 中排除或提交前清除 key
