# Architect Design: Phase 3A — OCR Shortcut XML 骨架设计

> **Status**: ✅ 已验收
> **产出**: `samples/ocr-local/ocr-local.xml`, `samples/ocr-local/ocr-local.shortcut`

## 1. 功能描述
最简 OCR shortcut：截图 → 文字识别 → 通知显示结果。三个 action，零用户输入。

## 2. 数据流与 UUID 引用链

```
Action 1: takescreenshot
  UUID = {{UUID-A}}
  输出 → 截图图片
         ↓ 引用 UUID-A
Action 2: extracttextfromimage
  UUID = {{UUID-B}}
  WFImage ← ActionOutput(UUID-A)   [WFTextTokenAttachment]
  输出 → 识别文字
         ↓ 引用 UUID-B
Action 3: notification
  无 UUID（终端 action，输出不被引用）
  WFNotificationActionTitle ← 静态字符串
  WFNotificationActionBody  ← ActionOutput(UUID-B)  [WFTextTokenString]
```

> **铁律提醒**: `{{UUID-A}}` 和 `{{UUID-B}}` 是占位符。Engineer 实现时**必须**用 `uuid.uuid4()` 动态生成，严禁硬编码。

## 3. 完整 XML Plist 模板

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- ★ 核心: Action 列表 -->
    <key>WFWorkflowActions</key>
    <array>

        <!-- Action 1: 截图 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.takescreenshot</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-A}}</string>
            </dict>
        </dict>

        <!-- Action 2: OCR 文字识别 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.extracttextfromimage</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-B}}</string>
                <key>WFImage</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Screenshot</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-A}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 3: 通知显示 OCR 结果 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.notification</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>WFNotificationActionTitle</key>
                <string>OCR Result</string>
                <key>WFNotificationActionBody</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{0, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Text from Image</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-B}}</string>
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
        <integer>4274264319</integer>
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

## 4. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 通知 body 格式 | WFTextTokenString | body 嵌入动态变量（OCR 结果），需用 ￼ (U+FFFC) 占位 + attachmentsByRange 映射 |
| OCR 输入格式 | WFTextTokenAttachment | WFImage 是单值参数，直接引用 ActionOutput |
| WFWorkflowInputContentItemClasses | 仅 WFImageContentItem | OCR shortcut 只处理图片 |
| WFWorkflowTypes | WFWorkflowTypeShowInSearch | 可在搜索中找到，无需 Watch 触发 |
| Action 3 无 UUID | 省略 | 终端 action，无下游引用 |

## 5. Engineer 实现指引

1. **创建** `samples/ocr-local/ocr-local.xml`，基于上述模板
2. **替换** `{{UUID-A}}` 和 `{{UUID-B}}` 为 `uuid.uuid4()` 生成的真实 UUID（全大写，带连字符）
3. **构建**: `python tools/shortcut_tool.py build samples/ocr-local/ocr-local.xml samples/ocr-local/ocr-local-unsigned.shortcut`
4. **签名**: `python tools/shortcut_tool.py sign samples/ocr-local/ocr-local-unsigned.shortcut samples/ocr-local/ocr-local.shortcut`
5. **验证**: 导入 iPhone，运行后应看到通知标题 "OCR Result"，body 为截图中识别出的文字
