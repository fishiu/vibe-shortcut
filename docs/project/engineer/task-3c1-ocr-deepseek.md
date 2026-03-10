# Engineer Log: Task 3C-1 - OCR + DeepSeek 合体 Shortcut

> **Date**: 2026-03-10
> **Related Task**: Phase 3C-1 — OCR + DeepSeek 合体
> **Status**: 🟡 基本可用，待去除 debug 弹窗后做最终验证

---

## 1. 任务目标

按 Architect 设计的 XML 骨架（doc3-spec.md §7），合并 3A（OCR）和 3B（DeepSeek API）为单一 shortcut：截图 → OCR → 拼接 prompt → DeepSeek API → 解析记账 JSON → 通知。

**验收标准**:
- [x] `samples/ocr-deepseek/ocr-deepseek.xml` 存在，UUID 动态生成
- [x] `samples/ocr-deepseek/ocr-deepseek.shortcut` 存在，AEA1 签名格式
- [x] ￼ 位置验证: `{279, 1}` 通过 Python + binary plist 双重确认
- [x] OCR 文本成功嵌入 JSON body（DEBUG 2 确认）
- [x] DeepSeek API 调用成功（用户手动修复 text.replace 后全链路跑通）
- [ ] 去除 3 个 debug alert 后做最终验证

---

## 2. 当前 Action 链路（13 个 action，含 3 个 debug alert）

```
[0] gettext (API Key)              → UUID 2AFA2233
[1] takescreenshot                 → UUID 74BCFB69
[2] extracttextfromimage (OCR)     → UUID ACF72948  ← WFImage 引用 [1]
[3] alert (DEBUG 1: OCR 结果)
[4] gettext (JSON body)            → UUID 84A77FCE  ← attachmentsByRange {279,1} 引用 [2]
[5] text.replace (换行→空格)       → UUID 5E14B013  ← WFInput 引用 [4]
[6] alert (DEBUG 2: 发送内容)
[7] downloadurl (POST DeepSeek)    → UUID 96CF0D8A  ← body 引用 [5]
[8] alert (DEBUG 3: DS 返回)
[9] getvalueforkey (choices)       → UUID CCA697C3  ← 引用 [7]
[10] getitemfromlist ([0])          → UUID D9056D89  ← 引用 [9]
[11] getvalueforkey (msg.content)  → UUID E38AB855  ← 引用 [10]
[12] notification (记账结果)
```

**关键设计：text.replace 作用于拼好的整个 JSON body**（gettext 输出），而非单独的 OCR 文本。这样 OCR 文本先通过 gettext 的 attachmentsByRange 嵌入 JSON，再由 text.replace 清洗控制字符。

---

## 3. 调试历程与踩坑记录

### 3.1 Bug 1: JSON body 控制字符（已修复）

**现象**: DeepSeek 返回 `"Failed to parse the request body as JSON: control character (\u0000-\u001F) found"`

**根因**: OCR 文本含真实换行符（`\u000A`），直接嵌入 JSON body 后变成非法控制字符。

**修复**: 在 gettext（JSON body）之后、downloadurl 之前插入 `text.replace`，将真实换行替换为空格。

**教训**: 任何用户输入（OCR 文本、ask 输入等）嵌入 JSON body 前，必须清洗控制字符。Sample B (2-api.xml) 中也有同样的清洗步骤。

### 3.2 Bug 2: text.replace 输入为空（✅ 已修复）

**现象**: text.replace 的 WFInput 在 Shortcuts UI 中显示为空，action 没有接收到任何文本。用户手动在 UI 中设置输入后可正常工作。

**复现**: 所有通过工具链生成的 text.replace action 都有此问题，无论引用 OCR 输出还是 gettext 输出。

**曾错误假设**: OutputName 需要匹配系统语言（中文 vs 英文）。用户验证：**跟语言完全无关**。

**真正根因**: **text.replace 的 WFInput 不接受 `WFTextTokenAttachment`，必须用 `WFTextTokenString`**。

关键证据——对比用户手动修复的导出版本与我们的版本：

| | 我们的版本（不工作） | 用户手动修复版（工作） |
|---|---|---|
| WFSerializationType | `WFTextTokenAttachment` | `WFTextTokenString` |
| Value 结构 | 直接 OutputName/OutputUUID/Type | `attachmentsByRange` + `{0,1}` + ￼ 占位符 |

**修复**: 将 text.replace 的 WFInput 从 WFTextTokenAttachment 改为 WFTextTokenString + attachmentsByRange：

```xml
<key>WFInput</key>
<dict>
    <key>Value</key>
    <dict>
        <key>attachmentsByRange</key>
        <dict>
            <key>{0, 1}</key>
            <dict>
                <key>OutputName</key>
                <string>文本</string>
                <key>OutputUUID</key>
                <string>84A77FCE-...</string>
                <key>Type</key>
                <string>ActionOutput</string>
            </dict>
        </dict>
        <key>string</key>
        <string>￼</string>
    </dict>
    <key>WFSerializationType</key>
    <string>WFTextTokenString</string>
</dict>
```

**注意**: Sample B（2-api.shortcut）的 text.replace WFInput 也是 WFTextTokenAttachment 格式，经用户实测**同样无法正常运行**。即 Sample B 本身的 text.replace 就是坏的（已知问题，待后续修复）。结论：**text.replace 的 WFInput 必须用 WFTextTokenString，与来源无关。**

### 3.3 误判：attachmentsByRange 位置偏移

**曾怀疑**: gettext 模板中的 `\n` 和 `\"` 被 Shortcuts 解释为转义字符，导致 ￼ 位置偏移。

**实际**: 位置 {279, 1} 正确。OCR 文本成功嵌入 JSON body（DEBUG 2 确认）。gettext 不会对 `\n` `\"` 做转义处理，它们是字面量两字符。

### 3.4 误判：text.replace 作用于 OCR 文本

**最初方案**: OCR → text.replace（清洗）→ gettext（嵌入 JSON body）

**问题**: text.replace 的输出无法被 gettext 的 attachmentsByRange 正确引用（输入为空 bug + 引用链断裂）。

**最终方案**: OCR → gettext（直接嵌入 JSON body）→ text.replace（清洗整个 JSON body）→ downloadurl

这样 text.replace 的输入是 gettext 的完整输出（一个长字符串），引用更可靠。

---

## 4. 产出文件

- `samples/ocr-deepseek/ocr-deepseek.xml` — 当前版本含 3 个 debug alert
- `samples/ocr-deepseek/ocr-deepseek-unsigned.shortcut` — binary plist
- `samples/ocr-deepseek/ocr-deepseek.shortcut` — AEA 签名

---

## 5. 遗留问题

- [ ] 验证 OutputName `"文本"` 修复是否生效（用户测试中）
- [ ] 验证通过后去除 3 个 debug alert，rebuild + sign 做最终版
- [ ] API Key 需替换为真实 key（`sk-REPLACE-WITH-REAL-KEY`）
- [ ] `.shortcut` 含明文 API Key，不应 commit

---

## 6. 给下一位 Engineer 的建议

### 6.1 text.replace 的正确用法
清洗用户输入（OCR 文本等）时，**不要**对原始文本做 replace 后再嵌入 JSON body。而是：
1. 先用 gettext + attachmentsByRange 将原始文本嵌入 JSON body
2. 再对整个 JSON body 做 text.replace

这样避免了 text.replace 输出被下游 attachmentsByRange 引用时的 bug。

### 6.2 已知问题：Sample B (2-api.shortcut) 的 text.replace 是坏的
Sample B 中的 text.replace action 使用 WFTextTokenAttachment 格式引用输入，经实测无法正常运行。这是样本自身的问题，待后续修复。**不要以 Sample B 的 text.replace 为参考。**

### 6.3 调试技巧
- 用 `alert` action（不是 `notification`）做 debug，可显示更多文字且阻塞执行
- 插入位置：OCR 后、发送前、API 返回后
- 验证 binary plist 内容：`plistlib.load()` → 遍历 action → 检查 UUID 引用链和字符位置

### 6.4 环境
```bash
# 构建命令
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py build <input.xml> <output.shortcut>
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py sign <input> <output>
```
conda `tool` 环境不存在，使用 base Python 3.13。
