# Engineer Log: Task 2.6 - Sample B 分析（新增 action 类型）

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-28
> **Related Task**: Phase 2 - Task 2.6
> **Status**: 🟢 Completed

---

## 1. 样本信息

- **文件**: `samples/money/2-api.shortcut` (AEA 签名)
- **功能**: OCR 截屏 + DeepSeek API 解析账单 + 记账 App 写入；备选手动输入
- **Actions 数量**: 46
- **独立 Action 类型**: 15 种（其中 8 种为 Sample A 已覆盖，7 种新增）
- **导出 XML**: `samples/money/2-api.xml`

---

## 2. Action 列表 (执行顺序)

| # | Action | 说明 |
|---|--------|------|
| 0 | `dictionary` | **[新]** 创建配置词典 {api_key, base_url, model} |
| 1 | `comment` | **[新]** 注释：配置说明 |
| 2 | `getvalueforkey` | **[新]** 取出 api_key |
| 3 | `count` | 计数 api_key 的字符数（WFCountType: Characters） |
| 4 | `conditional` | IF 字符数 = 0（api_key 为空） |
| 5 | `alert` | **[新]** 弹窗警告"请先配置 API Key" |
| 6 | `exit` | **[新]** 退出 shortcut |
| 7 | `conditional` | ELSE |
| 8 | `conditional` | ENDIF |
| 9 | `getvalueforkey` | 取出 base_url |
| 10 | `getvalueforkey` | 取出 model |
| 11 | `choosefrommenu` | 菜单：截图识别 / 手动输入 / 退出 |
| 12 | `choosefrommenu` | ITEM "📷 截图识别" |
| 13 | `takescreenshot` | 截屏 |
| 14 | `extracttextfromimage` | OCR |
| 15 | `ICSearchCategoryEntity` | **[新]** 第三方：获取记账 App 分类列表 |
| 16 | `ICSearchAssetEntity` | **[新]** 第三方：获取记账 App 账户列表 |
| 17 | `gettext` | **[新]** 构建 AI prompt（嵌入分类、账户、OCR文本） |
| 18 | `text.replace` | **[新]** 替换换行为空格 |
| 19 | `text.replace` | 替换双引号为单引号 |
| 20 | `gettext` | 构建 API 请求 JSON body |
| 21 | `downloadurl` | **[新]** POST 请求 DeepSeek API |
| 22 | `getvalueforkey` | 取 response.choices |
| 23 | `getitemfromlist` | **[新]** 取 choices[0] |
| 24 | `getvalueforkey` | 取 message.content |
| 25 | `detect.dictionary` | **[新]** 文本转词典（JSON 解析） |
| 26 | `getvalueforkey` | 取 type |
| 27 | `getvalueforkey` | 取 amount |
| 28 | `getvalueforkey` | 取 category |
| 29 | `getvalueforkey` | 取 account |
| 30 | `getvalueforkey` | 取 remark |
| 31 | `gettext` | 构建确认摘要文本 |
| 32 | `alert` | 弹窗确认记账 |
| 33 | `ICMarkAShortcutOutcomeRecordIntent` | 记账 App：支出（含 account, category, remark 参数） |
| 34 | `notification` | **[新]** 推送通知"✅ 记账成功" |
| 35 | `choosefrommenu` | ITEM "✏️ 手动输入" |
| 36 | `ask` | 输入金额 |
| 37 | `ICSearchCategoryEntity` | 获取分类列表 |
| 38 | `choosefromlist` | 选择分类 |
| 39 | `ICSearchAssetEntity` | 获取账户列表 |
| 40 | `choosefromlist` | 选择账户 |
| 41 | `ask` | 输入备注（可选） |
| 42 | `ICMarkAShortcutOutcomeRecordIntent` | 记账 App：支出 |
| 43 | `notification` | 通知"✅ 记账成功" |
| 44 | `choosefrommenu` | ITEM "❌ 退出" |
| 45 | `choosefrommenu` | ENDMENU |

---

## 3. 数据流（截图识别分支）

```
[0] dictionary ─── {api_key, base_url, model}
     │
     ├─→ [2] getvalueforkey "api_key" ──→ [3] count(Characters) ──→ [4] IF = 0
     │                                                                  ├─ [5] alert + [6] exit
     │                                                                  └─ ELSE: 继续
     ├─→ [9] getvalueforkey "base_url"
     └─→ [10] getvalueforkey "model"
          │
[11] choosefrommenu ── "📷 截图识别" 分支:
          │
   [13] takescreenshot ──→ [14] OCR
   [15] ICSearchCategoryEntity ──→ 分类列表
   [16] ICSearchAssetEntity ──→ 账户列表
          │
   [17] gettext ── prompt = "分析账单...分类:{分类}。账户:{账户}。账单:{OCR文本}"
          │
   [18] text.replace (换行→空格)
   [19] text.replace ("→')
          │
   [20] gettext ── body = {"model":"{model}","messages":[{"role":"user","content":"{prompt}"}]}
          │
   [21] downloadurl ── POST {base_url}
        Headers: Authorization: Bearer {api_key}, Content-Type: application/json
        Body: {body} (File mode)
          │
   [22] getvalueforkey "choices"
   [23] getitemfromlist [1]
   [24] getvalueforkey "message.content"
          │
   [25] detect.dictionary ── JSON 文本 → 词典
          │
   ├─→ [26] getvalueforkey "type"
   ├─→ [27] getvalueforkey "amount"
   ├─→ [28] getvalueforkey "category"
   ├─→ [29] getvalueforkey "account"
   └─→ [30] getvalueforkey "remark"
          │
   [31] gettext ── 构建确认文本
   [32] alert ── "确认记账"
          │
   [33] ICMarkAShortcutOutcomeRecordIntent
        (amount, category, account, remark)
          │
   [34] notification ── "✅ 记账成功"
```

---

## 4. 新增 Action 类型（7 种系统 + 2 种第三方）

### 与 Sample A 对比

| 状态 | Action ID | 说明 |
|:----:|-----------|------|
| 已有 | `takescreenshot` | 截屏 |
| 已有 | `extracttextfromimage` | OCR |
| 已有 | `count` | 计数（新增 WFCountType 参数） |
| 已有 | `conditional` | 条件判断 |
| 已有 | `choosefrommenu` | 菜单选择 |
| 已有 | `ask` | 用户输入（新增 WFAskActionDefaultAnswer 参数） |
| 已有 | `choosefromlist` | 列表选择（新增 WFChooseFromListActionPrompt 参数） |
| 已有 | `ICMarkAShortcutOutcomeRecordIntent` | 记账支出（新增 category, account, remark 参数） |
| **新增** | `dictionary` | 创建词典 |
| **新增** | `comment` | 注释（无执行效果） |
| **新增** | `getvalueforkey` | 从词典取值 |
| **新增** | `alert` | 弹窗提示 |
| **新增** | `exit` | 退出 shortcut |
| **新增** | `gettext` | 构建文本（文本模板） |
| **新增** | `text.replace` | 文本替换 |
| **新增** | `downloadurl` | HTTP 请求 |
| **新增** | `getitemfromlist` | 从列表取指定位置项 |
| **新增** | `detect.dictionary` | 文本转词典（JSON 解析） |
| **新增** | `notification` | 推送通知 |
| **新增** | `ICSearchCategoryEntity` | 第三方：查询分类 |
| **新增** | `ICSearchAssetEntity` | 第三方：查询账户 |

### 新增系统 Action 共 10 种，新增第三方 Action 共 2 种

---

## 5. 关键技术发现

### 5.1 dictionary — 词典创建的序列化类型

词典使用独有的序列化类型 `WFDictionaryFieldValue`，内部是 `WFDictionaryFieldValueItems` 数组：
- 每项包含 `WFKey`（键名）和 `WFValue`（值），均为 WFTextTokenString
- `WFItemType`: 0 = Text 类型

### 5.2 downloadurl — HTTP 请求的完整结构

这是 Shortcuts 中做 API 调用的核心 action：
- `WFURL`: 请求地址（WFTextTokenString）
- `WFHTTPMethod`: `GET` / `POST` / `PUT` / `DELETE` 等
- `WFHTTPBodyType`: `JSON` / `Form` / `File`
- `WFHTTPHeaders`: 自定义请求头（WFDictionaryFieldValue）
- `WFRequestVariable`: 请求体内容（WFTextTokenAttachment）
- `ShowHeaders`: boolean，是否显示 Headers UI

### 5.3 detect.dictionary — JSON 解析

将文本转为词典对象（本质是 JSON 解析）。之后可以用 `getvalueforkey` 逐字段提取。

### 5.4 getvalueforkey 支持嵌套路径

`WFDictionaryKey` 支持点号路径：`message.content` 可以直接取嵌套字段。

### 5.5 count 的 WFCountType 参数

Sample A 中 count 没有 WFCountType（默认计数列表项数），Sample B 新增 `WFCountType: Characters` 用于计数字符数。

### 5.6 ask 的新增参数

- `WFAskActionDefaultAnswer`: 默认值（空字符串表示无默认值）
- Sample A 中没有 WFInputType 时默认为 Text

### 5.7 choosefromlist 的新增参数

- `WFChooseFromListActionPrompt`: 自定义提示文本（如"选择分类"）

### 5.8 WFWorkflowImportQuestions — 导入时提问

Sample B 使用了 `WFWorkflowImportQuestions`，可以在用户导入 shortcut 时弹窗要求配置参数：
- `ActionIndex`: 关联的 action 索引
- `Category`: `Parameter`
- `ParameterKey`: 要配置的参数名
- `DefaultValue`: 默认值
- `Text`: 提示文本

### 5.9 第三方 App 的 ActionRequiresAppInstallation

Sample B 的第三方 action 新增了 `ActionRequiresAppInstallation: true`，标记该 action 需要安装对应 App。

---

## 6. Shortcut 业务逻辑（自然语言）

```
1. 创建配置词典（api_key, base_url, model）
2. 检查 api_key 是否为空
   - 为空: 弹窗提示配置，退出
   - 不为空: 继续
3. 弹出菜单: 截图识别 / 手动输入 / 退出

--- 截图识别分支 ---
4. 截屏 → OCR 提取文字
5. 获取记账 App 的分类和账户列表
6. 构建 AI prompt: "分析账单,返回JSON...分类:{分类列表}。账户:{账户列表}。账单:{OCR文本}"
7. 文本清洗（去换行、替换引号）
8. 构建 API 请求 JSON body
9. POST 请求 DeepSeek API
10. 解析 API 返回的 JSON: choices[0].message.content → 词典
11. 提取 type, amount, category, account, remark
12. 弹窗确认
13. 调用记账 App 写入支出记录
14. 推送通知"记账成功"

--- 手动输入分支 ---
15. 用户输入金额
16. 用户选择分类（从 App 分类列表）
17. 用户选择账户（从 App 账户列表）
18. 用户输入备注
19. 调用记账 App 写入支出记录
20. 推送通知"记账成功"

--- 退出分支 ---
21. 什么都不做
```

---

## 7. 产出文件

- `samples/money/2-api.xml` — XML plist 无损导出
- `docs/project/engineer/task-2.6-sample-b-analysis.md` — 本分析文档
