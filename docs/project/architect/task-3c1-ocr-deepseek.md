# Architect Design: Phase 3C-1 — OCR + DeepSeek 合体 XML 骨架设计

> **Status**: ✅ 已验收
> **产出**: `samples/ocr-deepseek/ocr-deepseek.xml`, `samples/ocr-deepseek/ocr-deepseek.shortcut`

## 1. 功能描述
合并 3A（OCR）和 3B（DeepSeek API）为单一 shortcut：截图 → OCR → 拼接 prompt → 清洗控制字符 → DeepSeek API → 解析记账 JSON → 通知。10 个 action。

## 2. 数据流与 UUID 引用链

```
Action 1: gettext (API Key)
  UUID = {{UUID-A}}
  输出 → API Key 字符串

Action 2: takescreenshot
  UUID = {{UUID-B}}
  输出 → 截图图片
         ↓ 引用 UUID-B
Action 3: extracttextfromimage (OCR)
  UUID = {{UUID-C}}
  WFImage ← ActionOutput(UUID-B)  [WFTextTokenAttachment]
  输出 → OCR 识别文字
         ↓ 引用 UUID-C
Action 4: gettext (构建 JSON Body，含 system + user message)
  UUID = {{UUID-D}}
  WFTextActionText ← 嵌入 UUID-C 于 user.content 字段  [WFTextTokenString]
  输出 → 完整 JSON 请求体（可能含 OCR 带入的换行符）
         ↓ 引用 UUID-D
Action 5: text.replace (清洗控制字符：换行→空格)
  UUID = {{UUID-D2}}
  WFInput ← UUID-D  [⚠️ 必须用 WFTextTokenString，见 §8]
  WFReplaceTextFind = 真实换行符
  WFReplaceTextReplace = 空格
  输出 → 清洗后的 JSON 请求体
         ↓ 引用 UUID-A, UUID-D2
Action 6: downloadurl (POST DeepSeek API)
  UUID = {{UUID-E}}
  WFURL ← 静态 "https://api.deepseek.com/v1/chat/completions"
  WFHTTPHeaders.Authorization ← "Bearer " + UUID-A  [WFTextTokenString]
  WFHTTPHeaders.Content-Type ← 静态 "application/json"
  WFRequestVariable ← UUID-D2  [WFTextTokenAttachment]
  输出 → JSON response (自动解析为 dict)
         ↓ 引用 UUID-E
Action 7: getvalueforkey (提取 choices)
  UUID = {{UUID-F}}
  WFDictionaryKey = "choices"
  WFInput ← UUID-E  [WFTextTokenAttachment]
         ↓ 引用 UUID-F
Action 8: getitemfromlist (取第一项)
  UUID = {{UUID-G}}
  WFInput ← UUID-F  [WFTextTokenAttachment]
  WFItemIndex = 1
         ↓ 引用 UUID-G
Action 9: getvalueforkey (提取 message.content)
  UUID = {{UUID-H}}
  WFDictionaryKey = "message.content"
  WFInput ← UUID-G  [WFTextTokenAttachment]
         ↓ 引用 UUID-H
Action 10: notification (显示记账 JSON)
  无 UUID（终端 action）
  WFNotificationActionTitle ← 静态 "记账结果"
  WFNotificationActionBody ← UUID-H  [WFTextTokenString]
```

> **与 3B 的差异**: 去掉 `ask`，用 `takescreenshot + extracttextfromimage` 替代；JSON body 增加 system message；新增 `text.replace` 清洗 OCR 带入的换行符。

## 3. JSON 请求体设计

**System Prompt**（指导 DeepSeek 输出记账 JSON）:
```
你是记账助手。从以下文字中提取记账信息，只返回 JSON，不输出任何其他内容：
{"item": "商品名称", "amount": 金额数字}
如果有多笔，返回数组：[{"item": "...", "amount": ...}, ...]
无法识别时返回：{"item": "未知", "amount": 0}
```

**完整 JSON Body**（gettext 中的字符串，￼ 代表 OCR 文本占位）:
```
{"model":"deepseek-chat","messages":[{"role":"system","content":"你是记账助手。从以下文字中提取记账信息，只返回 JSON，不输出任何其他内容：\n{\"item\": \"商品名称\", \"amount\": 金额数字}\n如果有多笔，返回数组：[{\"item\": \"...\", \"amount\": ...}, ...]\n无法识别时返回：{\"item\": \"未知\", \"amount\": 0}"},{"role":"user","content":"文字内容：\n￼"}]}
```

**￼ 位置**: `{279, 1}` — 第 279 个字符（0-indexed），引用 UUID-C（OCR 输出）。

验证脚本：
```python
s = '{"model":"deepseek-chat","messages":[{"role":"system","content":"你是记账助手。从以下文字中提取记账信息，只返回 JSON，不输出任何其他内容：\\n{\\"item\\": \\"商品名称\\", \\"amount\\": 金额数字}\\n如果有多笔，返回数组：[{\\"item\\": \\"...\\", \\"amount\\": ...}, ...]\\n无法识别时返回：{\\"item\\": \\"未知\\", \\"amount\\": 0}"},{"role":"user","content":"文字内容：\\n\ufffc"}]}'
assert s.index('\ufffc') == 279  # ← Engineer 用此验证
```

## 4. 完整 XML Plist 模板

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>WFWorkflowActions</key>
    <array>

        <!-- Action 1: API Key -->
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

        <!-- Action 2: 截图 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.takescreenshot</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-B}}</string>
            </dict>
        </dict>

        <!-- Action 3: OCR 文字识别 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.extracttextfromimage</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-C}}</string>
                <key>WFImage</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Screenshot</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-B}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 4: 构建 JSON 请求体（system + user message） -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.gettext</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-D}}</string>
                <key>WFTextActionText</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{279, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Text from Image</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-C}}</string>
                                <key>Type</key>
                                <string>ActionOutput</string>
                            </dict>
                        </dict>
                        <key>string</key>
                        <string>{"model":"deepseek-chat","messages":[{"role":"system","content":"你是记账助手。从以下文字中提取记账信息，只返回 JSON，不输出任何其他内容：\n{\"item\": \"商品名称\", \"amount\": 金额数字}\n如果有多笔，返回数组：[{\"item\": \"...\", \"amount\": ...}, ...]\n无法识别时返回：{\"item\": \"未知\", \"amount\": 0}"},{"role":"user","content":"文字内容：\n&#xFFFC;"}]}</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 5: 清洗控制字符（OCR 换行→空格） -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.text.replace</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-D2}}</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{0, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Text</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-D}}</string>
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
                <key>WFReplaceTextFind</key>
                <string>
</string>
                <key>WFReplaceTextReplace</key>
                <string> </string>
            </dict>
        </dict>

        <!-- Action 6: POST 到 DeepSeek API -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.downloadurl</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-E}}</string>
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
                        <string>{{UUID-D2}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 7: 提取 choices -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getvalueforkey</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-F}}</string>
                <key>WFDictionaryKey</key>
                <string>choices</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Contents of URL</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-E}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 8: 取第一项 choices[0] -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getitemfromlist</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-G}}</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Value for Key</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-F}}</string>
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

        <!-- Action 9: 提取 message.content -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getvalueforkey</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-H}}</string>
                <key>WFDictionaryKey</key>
                <string>message.content</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Item from List</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-G}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 10: 通知显示记账 JSON -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.notification</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>WFNotificationActionTitle</key>
                <string>记账结果</string>
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
                                <string>{{UUID-H}}</string>
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
        <integer>1001390335</integer>
    </dict>

    <key>WFWorkflowImportQuestions</key>
    <array/>

    <key>WFWorkflowInputContentItemClasses</key>
    <array>
        <string>WFImageContentItem</string>
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

## 5. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 替代 ask 的方式 | takescreenshot + extracttextfromimage | 3A 已验证可行，OCR 输出直接作为 user message |
| JSON body 中 system prompt | 内联在 gettext 模板中 | 避免额外 action，单个 gettext 构建完整请求体 |
| ￼ 位置 | {279, 1} | Python 验证：`s.index('\ufffc') == 279` |
| system prompt 格式 | JSON 转义（`\n` `\"` 等） | gettext 输出的是字面量字符串，作为 HTTP body 发给 API，JSON 解析器处理转义 |
| 图标颜色 | 1001390335 (绿色) | 区分于 3A(紫)、3B(蓝) |
| text.replace 清洗 | 换行→空格，作用于整个 JSON body | OCR 文本含真实换行符 `\u000A`，直接嵌入会破坏 JSON 格式 |
| text.replace 先于 downloadurl | gettext → text.replace → downloadurl | 先嵌入再清洗，避免 text.replace 输出被 attachmentsByRange 引用时的问题 |

## 6. 与 3A/3B 的复用关系

| 模块 | 来源 | 变化 |
|------|------|------|
| Action 1 (API Key) | 3B Action 1 | 无变化 |
| Action 2-3 (截图+OCR) | 3A Action 1-2 | 无变化 |
| Action 4 (JSON body) | 3B Action 3 | body 增加 system message，￼ 位置从 {63,1} 变为 {279,1}，引用 OCR 输出而非 ask |
| **Action 5 (text.replace)** | **新增** | **清洗 OCR 带入的换行符，3A/3B 中不存在** |
| Action 6-9 (API+解析) | 3B Action 4-7 | body 引用从 UUID-D 改为 UUID-D2（text.replace 输出） |
| Action 10 (通知) | 3B Action 8 | 标题改为 "记账结果" |

## 7. Engineer 实现指引

1. **创建** `samples/ocr-deepseek/ocr-deepseek.xml`，基于上述模板
2. **替换** `{{UUID-A}}` ~ `{{UUID-H}}` 和 `{{UUID-D2}}` 为 `uuid.uuid4()` 生成的真实 UUID（全大写，带连字符）
3. **替换** `sk-REPLACE-WITH-REAL-KEY` 为真实 DeepSeek API Key
4. **验证 ￼ 位置**: 运行 §3 中的 Python 验证脚本确认 `assert s.index('\ufffc') == 279`
5. **构建**: `python tools/shortcut_tool.py build samples/ocr-deepseek/ocr-deepseek.xml samples/ocr-deepseek/ocr-deepseek-unsigned.shortcut`
6. **签名**: `python tools/shortcut_tool.py sign samples/ocr-deepseek/ocr-deepseek-unsigned.shortcut samples/ocr-deepseek/ocr-deepseek.shortcut`
7. **验证**: 在含价格信息的页面截图 → 通知标题 "记账结果"，body 为 `{"item": "xxx", "amount": 0.00}` 格式
8. **安全提醒**: 同 3B，API Key 不要 commit

## 8. 实战发现：text.replace 的 WFInput 必须用 WFTextTokenString

**问题**: `text.replace` 的 WFInput 使用 `WFTextTokenAttachment` 格式时，导入 iPhone 后输入显示为空，action 无效。

**解决**: 改用 `WFTextTokenString` + `attachmentsByRange` + ￼ 占位符格式（见 Action 5 模板）。

**与 OutputName 语言无关** — 实测确认这纯粹是序列化类型问题，与中英文无关。

## 9. 已知问题：Sample B (2-api.shortcut) 的 text.replace 是坏的

Sample B 中的 `text.replace` action 也使用了 `WFTextTokenAttachment` 格式引用输入，经实测**同样无法正常运行**。这是样本自身的缺陷，不是"原生创建 vs 外部导入"的区别。

**影响**: Sample B 的 text.replace 不能作为参考模板。后续有时间需修复 Sample B 或在手册中标注此问题。
