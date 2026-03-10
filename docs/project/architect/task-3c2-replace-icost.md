# Architect Design: Phase 3C-2 — 替换 3-full 的 icost.vip 请求

> **Status**: 📐 设计完成，待 Engineer 实现
> **产出**: `samples/money/3-full-deepseek.xml` + 对应 `.shortcut`

## 1. 功能描述

在 `3-full.xml`（1140 actions, ~39000 行）中**外科手术式替换** `icost.vip/wapi/v1/chat` 调用为 DeepSeek API，保持下游 1100+ actions 的逻辑不变。

**核心策略**: 新增本地 OCR → 构建 DeepSeek 请求 → 解析 DeepSeek 响应 → 输出与 icost.vip 兼容的 JSON 结构，下游 `getvalueforkey` 链路零改动。

## 2. 现状分析：icost.vip/wapi/v1/chat 接口

### 2.1 请求概览

- **URL**: `https://www.icost.vip/wapi/v1/chat`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Action 位置**: lines 2165–3601（单个 downloadurl action，~1436 行 XML）
- **Action UUID**: `86D23FE2-31E6-489C-86BE-1B351FE246C5`

### 2.1.1 请求字段完整清单

**WFFormValues `v` 字段**（JSON 字符串，7 个动态占位符）：

模板: `{"ECP":"￼","RCL":"￼","ECL":"￼","AL":"￼","TL":"￼","date":"￼","TOP":"￼"}`

| 字段 | 位置 | 来源 UUID | 来源 Action | 内容 |
|------|------|-----------|-------------|------|
| **ECP** | {8,1} | `6724C445` | ICSearchCategoryEntity (expense, first-level) .name | 支出一级分类名列表 |
| **RCL** | {18,1} | `7FEC0A01` | ICSearchCategoryEntity (income) .name | 收入分类名列表 |
| **ECL** | {28,1} | `1EDA8BA8` | ICSearchCategoryEntity (expense, second-level) .name | 支出二级分类名列表 |
| **AL** | {37,1} | `2493C32C` | ICSearchAssetEntity .name | 账户名列表 |
| **TL** | {46,1} | `E6362569` | ICSearchTagEntity .name | 标签名列表 |
| **date** | {57,1} | CurrentDate | 系统当前日期 (yyyy.MM.dd HH:mm:ss) | 当前日期时间 |
| **TOP** | {67,1} | `4856151E` | gettext (默认空, 用户可自定义) | 用户自定义识别规则 |

**WFFormValues 其他字段**：

| 字段 | 值 | 说明 |
|------|-----|------|
| **m** | "识别账单" (静态) | 请求类型标识 |

**WFJSONValues 字段**（WFHTTPBodyType=Form 时可能不生效，但存在于 XML 中）：

| 字段 | 内容 | 说明 |
|------|------|------|
| **v** (dict) | ECL/RCL/AL/TL/date (引用 dangling UUIDs) | 与 FormValues.v 重复 |
| **r** | mode 变量 (随机: 青龙/白虎/朱雀/玄武/麒麟) | 内部标识（A/B 测试或防重） |
| **f** (array) | 调整大小后的截图 (UUID `0B4F4A02`, 500px 宽) | **核心输入：服务端 OCR 的图片** |
| **m** | 空字符串 | — |

**Headers**：

| Header | 内容 | 说明 |
|--------|------|------|
| Authorization | `Bearer ￼` (UUID `D625BA13`, 密钥字段) | 身份认证 |
| Content-Type | multipart/form-data | 表单类型 |
| X-D | 屏幕宽度 (UUID `19BE56F4`) | 设备分析 |
| X-O | 设备名称 (UUID `DAF2DDF7`) | 设备分析 |

### 2.1.2 反推 icost.vip 的处理逻辑

通过对比「请求输入」与「响应输出 + 下游使用」，反推 icost.vip 的行为：

| 输入 | 推测用途 | 对应输出字段 | 证据 |
|------|----------|-------------|------|
| **f** (截图) | 服务端 OCR + 图像分析 → 提取商户名、金额、日期等 | `shop`, `amount`, `date` 等 | 3-full 无本地 OCR，所有文本信息必须来自图片 |
| **ECP** (支出一级分类) | 从中匹配最佳分类 | `CC` (当 type=支出) | 下游 `ICSearchCategoryEntity` 按 `name==CC` 精确匹配 |
| **ECL** (支出二级分类) | 更细粒度分类匹配 | `CC` (可能返回二级分类名) | 与 ECP 互补 |
| **RCL** (收入分类) | 收入场景的分类匹配 | `CC` (当 type=收入) | 独立的收入分类查询 |
| **AL** (账户列表) | 从中匹配支付方式 | `account` | 下游 `ICSearchAssetEntity` 按 `name==account` 精确匹配 |
| **TL** (标签列表) | 从中匹配标签 | `tag` | 下游有 tag 变量使用 |
| **date** (当前日期) | 无法识别日期时的 fallback | `date` | 防止 date 字段为空 |
| **TOP** (自定义规则) | 作为额外 prompt 指导识别行为 | 影响所有输出 | 注释说明: "识别到xxx则分类归为yyy" |
| **m** ("识别账单") | 路由到识别功能 | — | 区分不同 API 功能 |
| **r** (随机标识) | 内部 A/B 测试或请求去重 | — | 对识别结果无影响 |
| **X-D, X-O** | 设备分析/适配 | — | 对识别结果无影响 |

### 2.2 响应

icost.vip 返回的 JSON 顶层结构：

```json
{
  "detail": "错误信息（正常时为 null）",
  "social_account": "用户社交账号",
  "total_requests": 123,
  "cashier": "收银员名称",
  "user_id": "用户ID",
  "expire_time": "会员过期时间",
  "answer": [
    {
      "type": "支出",
      "amount": 25.5,
      "CC": "餐饮",
      "date": "2026-03-10",
      "shop": "肯德基",
      "remark": "",
      "tag": "",
      "currency": "CNY",
      "account": "",
      "from_account": "",
      "to_account": "",
      "fee": 0,
      "discount": 0
    }
  ]
}
```

### 2.3 下游消费（lines 3602–3895）

响应解析流程（所有 UUID 引用同一个 detect.dictionary 输出 `CDA2A1C9`）：

| 步骤 | Action | 提取 key | 存入变量 | 用途 |
|------|--------|----------|----------|------|
| 1 | detect.dictionary | — | CDA2A1C9 | 将响应转为词典 |
| 2 | getvalueforkey | `detail` | 263D6E12 | 错误检查：有值则通知+退出 |
| 3 | setvariable | `social_account` | → `social_account` | 账号信息（显示用） |
| 4 | setvariable | `total_requests` | → `requests` | 请求次数统计 |
| 5 | setvariable | `cashier` | → `cashier` | 收银员名 |
| 6 | setvariable | `user_id` | → `user_id` | 用户ID |
| 7 | setvariable | `expire_time` | → `ET` | 会员过期 |
| 8 | detect.dictionary | `answer` | F53D2915 | 解析 answer 数组 |
| 9 | count → conditional | — | — | answer 数量检查 |
| 10 | repeat.each | — | 4A899DA3 | 遍历每笔账单 |

**answer 数组中每项提取的 key**（在 repeat.each 循环内，lines 7160–38505）：

| key | 变量名 | 说明 |
|-----|--------|------|
| `type` | `type` | 支出/收入/转账 |
| `amount` | `amount` | 金额 |
| `CC` | — | 分类代码 |
| `account` | — | 账户 |
| `from_account` | — | 转出账户 |
| `to_account` | — | 转入账户 |
| `fee` | — | 手续费 |
| `date` | `date` | 日期 |
| `tag` | `tag` | 标签 |
| `currency` | `currency` | 币种 |
| `remark` | `remark` | 备注 |
| `shop` | `shop` | 商户 |
| `discount` | `discount` | 优惠金额 |

### 2.4 上游 iCost 查询（API 调用前，lines 780–1490）

3-full 在调用 icost.vip **之前**查询 iCost App 获取用户数据，作为 API 请求的上下文：

| 行 | Action | UUID | 查询内容 | 过滤条件 |
|----|--------|------|----------|----------|
| 780 | `ICSearchBookEntity` | 9A44FC98 | 账本列表 | 无 → 用户选择 → `ledger` 变量 |
| 1040 | `ICSearchCategoryEntity` | 1EDA8BA8 | 支出二级分类 | bookName=ledger, type=expense, level=second |
| 1180 | `ICSearchCategoryEntity` | 6724C445 | 支出一级分类 | bookName=ledger, type=expense, level=first |
| 1320 | `ICSearchCategoryEntity` | 7FEC0A01 | 收入分类 | type=income, bookName=ledger |
| 1425 | `ICSearchAssetEntity` | 2493C32C | 账户列表 | 无 |
| 1461 | `ICSearchTagEntity` | E6362569 | 标签列表 | 无 |

这些结果通过 `.name` 属性提取后，拼进发给 icost.vip 的 `v` 字段，让服务端从用户实际的分类/账户名中匹配。

### 2.5 下游 CC/account 匹配（repeat.each 循环内）

API 返回的 `CC` 和 `account` 字段被用于**按名称精确匹配** iCost 实体：

| 字段 | 下游 Action | 匹配方式 | 说明 |
|------|-------------|----------|------|
| `CC` → 变量 `CC` → 变量 `category` | `ICSearchCategoryEntity` (line 9487) | `name == CC` (Operator=4) | 必须与 iCost 分类名完全一致 |
| `account` → 变量 `account` | `ICSearchAssetEntity` (line 21420) | `name == account` (Operator=4) | 必须与 iCost 账户名完全一致 |

匹配到的**实体对象**（非字符串）传入 `ICMarkAShortcutOutcomeRecordIntent` 等记账 action。

**关键约束**: 如果 DeepSeek 返回的 CC/account 名称不在 iCost 中，匹配会失败 → 记账失败。因此**必须将 iCost 的分类和账户名列表传入 DeepSeek prompt**。

### 2.6 关键发现

1. **3-full 没有本地 OCR** — 无 `extracttextfromimage` action，依赖 icost.vip 服务端做图片分析
2. **API Key 存储** — 在首个 action（dictionary，ActionIndex=0）的 `密钥` 字段，通过 WFWorkflowImportQuestions 导入时设置
3. **Key 取用** — `getvalueforkey "密钥"` → UUID `D625BA13`，在 Authorization header 中引用为 `Bearer ￼`
4. **下游代码完全依赖响应 JSON 结构** — 所有 setvariable 和 getvalueforkey 都引用 detect.dictionary 的输出
5. **CC/account 必须精确匹配 iCost 名称** — 下游用 name==value 过滤，名称不匹配则记账失败

## 3. 替换方案设计

### 3.1 总体思路

```
原链路:
  image.resize → downloadurl(icost.vip) → detect.dictionary → 下游
                  ↑ 发送图片+预处理字段        ↑ 直接解析 HTTP 响应

新链路:
  image.resize → extracttextfromimage(OCR) → gettext(构建JSON body)
    → text.replace(清洗换行) → downloadurl(DeepSeek) → getvalueforkey("choices")
    → getitemfromlist(1) → getvalueforkey("message.content")
    → detect.dictionary → 下游（零改动）
```

### 3.2 修改清单

#### A. 新增 4 个 action（插入在 downloadurl 之前）

| # | Action | 说明 | 新 UUID |
|---|--------|------|---------|
| A1 | `extracttextfromimage` | 对调整大小后的图像做本地 OCR | `{{UUID-OCR}}` |
| A2 | `gettext` | 构建 DeepSeek JSON 请求体（含分类/账户/标签/日期/自定义规则 + OCR 文本，8 个 ￼） | `{{UUID-BODY}}` |
| A3 | `text.replace` | 清洗 OCR 文本中的换行符（换行→空格） | `{{UUID-CLEAN}}` |
| A4 | `gettext` | API Key 文本（复用现有 D625BA13 即可，此步可省略） | — |

> 注意：A4 不需要单独 action。现有的 `getvalueforkey "密钥"` (UUID D625BA13) 已经提取了 API key，可直接在 downloadurl header 中引用。

#### B. 替换 1 个 action（downloadurl，lines 2165–3601）

将 ~1436 行的 icost.vip multipart POST 替换为 ~80 行的 DeepSeek JSON POST。

| 属性 | 原值 | 新值 |
|------|------|------|
| WFURL | `https://www.icost.vip/wapi/v1/chat` | `https://api.deepseek.com/v1/chat/completions` |
| WFHTTPMethod | POST | POST（不变） |
| WFHTTPBodyType | Form | File |
| WFFormValues/WFJSONValues | 复杂嵌套结构 | **删除** |
| WFRequestVariable | — | 引用 `{{UUID-CLEAN}}`（清洗后的 JSON body） |
| Headers.Authorization | `Bearer ￼`(D625BA13) | `Bearer ￼`(D625BA13)（**不变**） |
| Headers.Content-Type | multipart/form-data | application/json |
| Headers.X-D, X-O | 屏幕宽度/设备名 | **删除** |

#### C. 新增 3 个 action（插入在 downloadurl 与 detect.dictionary 之间）

| # | Action | 说明 | 新 UUID |
|---|--------|------|---------|
| C1 | `getvalueforkey` | 从 downloadurl 响应提取 `choices` | `{{UUID-CHOICES}}` |
| C2 | `getitemfromlist` | 取 `choices[0]`（WFItemIndex=1） | `{{UUID-FIRST}}` |
| C3 | `getvalueforkey` | 提取 `message.content` | `{{UUID-CONTENT}}` |

#### D. 修改 1 个 action（detect.dictionary，line 3602）

| 属性 | 原值 | 新值 |
|------|------|------|
| WFInput.OutputUUID | `86D23FE2`（downloadurl 输出） | `{{UUID-CONTENT}}`（message.content 输出） |
| WFInput.OutputName | `URL的内容` | `Value for Key` |

#### E. 下游零改动（lines 3625–39152）

所有 `getvalueforkey "detail"`、`setvariable "social_account"` 等都引用 `CDA2A1C9`（detect.dictionary 输出），不受影响。

### 3.3 UUID 引用链

```
[现有] image.resize
  UUID = 0B4F4A02
  输出 → 调整大小后的图像
         ↓ 引用 0B4F4A02
[新增 A1] extracttextfromimage (本地 OCR)
  UUID = {{UUID-OCR}}
  WFImage ← ActionOutput(0B4F4A02)  [WFTextTokenAttachment]
  输出 → OCR 识别文字
         ↓ 引用 {{UUID-OCR}}
[新增 A2] gettext (构建 DeepSeek JSON body)
  UUID = {{UUID-BODY}}
  WFTextActionText ← 8 个 ￼ 占位符 [WFTextTokenString]:
    ￼1 → CurrentDate (当前日期, yyyy-MM-dd)
    ￼2 → 6724C445 (支出一级分类.name)
    ￼3 → 1EDA8BA8 (支出二级分类.name)
    ￼4 → 7FEC0A01 (收入分类.name)
    ￼5 → 2493C32C (账户.name)
    ￼6 → E6362569 (标签.name)
    ￼7 → 4856151E (用户自定义规则)
    ￼8 → {{UUID-OCR}} (OCR 文本)
  输出 → 完整 JSON 请求体（可能含 OCR 换行符）
         ↓ 引用 {{UUID-BODY}}
[新增 A3] text.replace (清洗控制字符)
  UUID = {{UUID-CLEAN}}
  WFInput ← {{UUID-BODY}}  [⚠️ 必须用 WFTextTokenString，见 3C-1 §8]
  WFReplaceTextFind = 真实换行符
  WFReplaceTextReplace = 空格
  输出 → 清洗后的 JSON 请求体
         ↓ 引用 D625BA13 (密钥), {{UUID-CLEAN}}
[替换 B] downloadurl (POST DeepSeek API)
  UUID = 86D23FE2 ← 保留原 UUID，避免影响其他引用
  WFURL = "https://api.deepseek.com/v1/chat/completions"
  WFHTTPHeaders.Authorization ← "Bearer " + D625BA13 [WFTextTokenString]
  WFHTTPHeaders.Content-Type ← "application/json"
  WFRequestVariable ← {{UUID-CLEAN}} [WFTextTokenAttachment]
  输出 → DeepSeek JSON response
         ↓ 引用 86D23FE2
[新增 C1] getvalueforkey (提取 choices)
  UUID = {{UUID-CHOICES}}
  WFDictionaryKey = "choices"
  WFInput ← ActionOutput(86D23FE2) [WFTextTokenAttachment]
         ↓ 引用 {{UUID-CHOICES}}
[新增 C2] getitemfromlist (取第一项)
  UUID = {{UUID-FIRST}}
  WFInput ← {{UUID-CHOICES}} [WFTextTokenAttachment]
  WFItemIndex = 1
         ↓ 引用 {{UUID-FIRST}}
[新增 C3] getvalueforkey (提取 message.content)
  UUID = {{UUID-CONTENT}}
  WFDictionaryKey = "message.content"
  WFInput ← {{UUID-FIRST}} [WFTextTokenAttachment]
         ↓ 引用 {{UUID-CONTENT}}
[修改 D] detect.dictionary (原 CDA2A1C9)
  UUID = CDA2A1C9 ← 保留原 UUID
  WFInput ← {{UUID-CONTENT}}  ← 改为引用 message.content
  输出 → 词典（与 icost.vip 兼容的 JSON 结构）
         ↓ (后续全部不变)
[不变] getvalueforkey "detail" → conditional → ...
[不变] setvariable social_account / requests / cashier / user_id / ET
[不变] detect.dictionary "answer" → repeat.each → ...
```

## 4. DeepSeek Prompt 设计

### 4.1 设计思路

Prompt 需要包含三类信息：
1. **任务指令** — 格式要求、字段说明（system message）
2. **约束列表** — 用户 iCost 中的实际分类名和账户名（system message 尾部）
3. **OCR 文本** — 截图识别出的文字（user message）

分类和账户名来自上游 iCost 查询（§2.4），在 gettext 模板中通过 ￼ 占位符嵌入。

### 4.2 System Prompt

```
你是记账识别助手。分析用户提供的OCR文字，提取账单信息。只返回JSON，不要输出任何其他内容。

返回格式：
{"answer":[{"type":"支出","amount":0,"CC":"分类名","date":"YYYY-MM-DD","shop":"商户名","remark":"备注","tag":"标签","currency":"CNY","account":"账户名","from_account":"","to_account":"","fee":0,"discount":0}]}

字段规则：
- type: 支出/收入/转账
- CC: 必须从下方分类列表中选择，不要自创
- account: 必须从下方账户列表中选择，不要自创
- tag: 如匹配下方标签列表则填写，否则留空
- date: 格式YYYY-MM-DD，无法识别则用今天: ￼
- amount: 金额数字
- 多笔交易返回多个对象，无法识别返回{"answer":[]}

支出分类：￼
支出子分类：￼
收入分类：￼
账户：￼
标签：￼
￼
```

> **7 个 ￼ 占位符**，按出现顺序：
>
> | # | 内容 | 来源 UUID | 说明 |
> |---|------|-----------|------|
> | 1 | 当前日期 | CurrentDate (yyyy-MM-dd) | date 字段的 fallback |
> | 2 | 支出一级分类名 | `6724C445` .name | CC 必须从此列表选 |
> | 3 | 支出二级分类名 | `1EDA8BA8` .name | 可用于更精确的 CC 匹配 |
> | 4 | 收入分类名 | `7FEC0A01` .name | 收入时 CC 从此列表选 |
> | 5 | 账户名 | `2493C32C` .name | account 必须从此列表选 |
> | 6 | 标签名 | `E6362569` .name | tag 可从此列表选 |
> | 7 | 用户自定义规则 | `4856151E` (gettext, 默认空) | 个性化指令，如 "识别到xxx则归为yyy" |
>
> Shortcuts 运行时将实体列表的 `.name` 展开为换行分隔文本。
> 用户自定义规则（TOP）默认为空字符串，prompt 中会显示为空行，不影响行为。

### 4.3 User Message

```
文字内容：
￼
```

> ￼ 占位符引用 OCR 输出 → UUID `{{UUID-OCR}}`

### 4.4 完整 JSON Body（gettext 模板）

```
{"model":"deepseek-chat","messages":[{"role":"system","content":"你是记账识别助手。分析用户提供的OCR文字，提取账单信息。只返回JSON，不要输出任何其他内容。\n\n返回格式：\n{\"answer\":[{\"type\":\"支出\",\"amount\":0,\"CC\":\"分类名\",\"date\":\"YYYY-MM-DD\",\"shop\":\"商户名\",\"remark\":\"备注\",\"tag\":\"标签\",\"currency\":\"CNY\",\"account\":\"账户名\",\"from_account\":\"\",\"to_account\":\"\",\"fee\":0,\"discount\":0}]}\n\n字段规则：\n- type: 支出/收入/转账\n- CC: 必须从下方分类列表中选择\n- account: 必须从下方账户列表中选择\n- tag: 如匹配下方标签列表则填写，否则留空\n- date: 格式YYYY-MM-DD，无法识别则用今天: ￼\n- amount: 金额数字\n- 多笔返回多个对象，无法识别返回{\"answer\":[]}\n\n支出分类：￼\n支出子分类：￼\n收入分类：￼\n账户：￼\n标签：￼\n￼"},{"role":"user","content":"文字内容：\n￼"}]}
```

> 模板中有 **8 个 ￼ 占位符**，按出现顺序：
>
> | # | 内容 | 来源 | Aggrandizement |
> |---|------|------|----------------|
> | 1 | 当前日期 | CurrentDate | WFDateFormatVariableAggrandizement, format "yyyy-MM-dd" |
> | 2 | 支出一级分类 | UUID `6724C445` | WFPropertyVariableAggrandizement, name |
> | 3 | 支出二级分类 | UUID `1EDA8BA8` | WFPropertyVariableAggrandizement, name |
> | 4 | 收入分类 | UUID `7FEC0A01` | WFPropertyVariableAggrandizement, name |
> | 5 | 账户 | UUID `2493C32C` | WFPropertyVariableAggrandizement, name |
> | 6 | 标签 | UUID `E6362569` | WFPropertyVariableAggrandizement, name |
> | 7 | 自定义规则 | UUID `4856151E` | 无（直接引用 gettext 输出） |
> | 8 | OCR 文本 | UUID `{{UUID-OCR}}` | 无（直接引用 extracttextfromimage 输出） |

### 4.5 ￼ 位置计算

Engineer 需要用以下 Python 脚本验证所有占位符位置：

```python
PLACEHOLDER = '\ufffc'

s = ('{"model":"deepseek-chat","messages":[{"role":"system","content":"'
     '你是记账识别助手。分析用户提供的OCR文字，提取账单信息。只返回JSON，不要输出任何其他内容。'
     '\\n\\n返回格式：\\n'
     '{\\"answer\\":[{\\"type\\":\\"支出\\",\\"amount\\":0,\\"CC\\":\\"分类名\\",'
     '\\"date\\":\\"YYYY-MM-DD\\",\\"shop\\":\\"商户名\\",\\"remark\\":\\"备注\\",'
     '\\"tag\\":\\"标签\\",\\"currency\\":\\"CNY\\",\\"account\\":\\"账户名\\",'
     '\\"from_account\\":\\"\\",\\"to_account\\":\\"\\",\\"fee\\":0,\\"discount\\":0}]}'
     '\\n\\n字段规则：\\n'
     '- type: 支出/收入/转账\\n'
     '- CC: 必须从下方分类列表中选择\\n'
     '- account: 必须从下方账户列表中选择\\n'
     '- tag: 如匹配下方标签列表则填写，否则留空\\n'
     '- date: 格式YYYY-MM-DD，无法识别则用今天: ' + PLACEHOLDER +   # ￼1: 当前日期
     '\\n- amount: 金额数字\\n'
     '- 多笔返回多个对象，无法识别返回{\\"answer\\":[]}\\n\\n'
     '支出分类：' + PLACEHOLDER +     # ￼2: 支出一级分类
     '\\n支出子分类：' + PLACEHOLDER + # ￼3: 支出二级分类
     '\\n收入分类：' + PLACEHOLDER +   # ￼4: 收入分类
     '\\n账户：' + PLACEHOLDER +       # ￼5: 账户
     '\\n标签：' + PLACEHOLDER +       # ￼6: 标签
     '\\n' + PLACEHOLDER +             # ￼7: 自定义规则
     '"},{"role":"user","content":"文字内容：\\n'
     + PLACEHOLDER +                   # ￼8: OCR 文本
     '"}]}')

positions = []
idx = 0
while True:
    pos = s.find(PLACEHOLDER, idx)
    if pos == -1:
        break
    positions.append(pos)
    idx = pos + 1

labels = ['当前日期', '支出分类', '支出子分类', '收入分类', '账户', '标签', '自定义规则', 'OCR文本']
for i, pos in enumerate(positions):
    print(f"  ￼{i+1} {labels[i]}: position {pos} → key: {{{pos}, 1}}")

assert len(positions) == 8, f"Expected 8 placeholders, got {len(positions)}"
```

### 4.6 Aggrandizement 格式（引用 iCost 实体的 .name 属性）

分类和账户的 ￼ 占位符需要使用 `WFPropertyVariableAggrandizement` 提取 `.name`：

```xml
<key>{POS_支出分类, 1}</key>
<dict>
    <key>Aggrandizements</key>
    <array>
        <dict>
            <key>PropertyName</key>
            <string>name</string>
            <key>PropertyUserInfo</key>
            <dict>
                <key>WFLinkEntityContentPropertyUserInfoPropertyIdentifier</key>
                <string>name</string>
            </dict>
            <key>Type</key>
            <string>WFPropertyVariableAggrandizement</string>
        </dict>
    </array>
    <key>OutputName</key>
    <string>分类</string>
    <key>OutputUUID</key>
    <string>6724C445-3E84-42FA-AD33-1CD9AEA79FF3</string>
    <key>Type</key>
    <string>ActionOutput</string>
</dict>
```

> 收入分类（UUID `7FEC0A01`）和账户（UUID `2493C32C`，OutputName `账户`）结构相同，只需替换 OutputUUID 和 OutputName。
>
> ⚠️ **PropertyUserInfo 中的 data 字段**: 上游代码（line 2232-2403）中 Aggrandizement 包含一个大段 base64 `<data>` 块（`WFLinkEntityContentPropertyUserInfoEnumMetadata`），这是 iCost entity 的类型元数据。Engineer 需要从原 XML 中对应的 ICSearchCategoryEntity/ICSearchAssetEntity action 的 Aggrandizement 中复制此 data 块。如果不含此 data 块，Shortcuts 运行时可能无法正确提取 `.name` 属性。

## 5. 兼容性分析：下游字段缺失处理

DeepSeek 只返回 `answer` 数组，不返回 icost.vip 的账号元数据。下游代码的处理：

| 原 key | 原值类型 | DeepSeek 返回 | 下游 getvalueforkey | setvariable 结果 | 影响评估 |
|--------|----------|---------------|---------------------|------------------|----------|
| `detail` | string/null | 不存在 | 返回空 | — | ✅ conditional "has any value" 为 false，不触发错误退出 |
| `social_account` | string | 不存在 | 返回空 | `social_account` = 空 | ✅ 仅用于显示，空值无害 |
| `total_requests` | number | 不存在 | 返回空 | `requests` = 空 | ✅ 仅用于显示，空值无害 |
| `cashier` | string | 不存在 | 返回空 | `cashier` = 空 | ⚠️ 收银员编辑功能不可用，可接受 |
| `user_id` | string | 不存在 | 返回空 | `user_id` = 空 | ✅ 仅用于 icost.vip 交互 |
| `expire_time` | string | 不存在 | 返回空 | `ET` = 空 | ⚠️ 会员过期检查不触发，可接受 |
| `answer` | array | ✅ 存在 | 正常提取 | — | ✅ 核心功能完全兼容 |

**answer 各字段兼容性**:

| 字段 | DeepSeek 能力 | 约束方式 | 风险 |
|------|-------------|----------|------|
| `CC` | ✅ 从分类列表选择 | prompt 包含 ECP+ECL 列表 | 低：列表明确 |
| `account` | ✅ 从账户列表选择 | prompt 包含 AL 列表 | 低：列表明确 |
| `tag` | ✅ 从标签列表选择 | prompt 包含 TL 列表 | 低：可留空 |
| `type` | ✅ 三选一 | prompt 明确约束 | 极低 |
| `amount` | ✅ 数字提取 | OCR 文本含金额 | 低 |
| `date` | ✅ 日期识别 | 有 CurrentDate fallback | 极低 |
| `shop` | ✅ 文本提取 | 自由文本 | 低 |
| `remark` | ✅ 文本生成 | 自由文本 | 低 |
| `currency` | ✅ 默认 CNY | prompt 格式示例 | 极低 |
| `discount` | ⚠️ 难以准确识别 | 默认 0 | 可接受：非核心字段 |

**结论**: 所有缺失字段都是 icost.vip 特有的账号管理功能，对记账核心流程无影响。

## 6. API Key 处理

**复用现有机制**，零改动：

1. 首个 action（dictionary，ActionIndex=0）有 `密钥` 字段
2. WFWorkflowImportQuestions 在导入时提示用户填写密钥
3. `getvalueforkey "密钥"` → UUID `D625BA13`
4. downloadurl 的 Authorization header 引用 `D625BA13`

**用户只需**: 导入时将 `密钥` 字段从 icost.vip token 改为 DeepSeek API Key（`sk-xxx`）。

## 7. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 新增本地 OCR | extracttextfromimage | 3-full 原本无本地 OCR（依赖 icost.vip 服务端），DeepSeek 文本 API 无法处理图片 |
| 保留 downloadurl UUID | 86D23FE2 不变 | 避免影响其他可能引用此 UUID 的代码 |
| DeepSeek 只返回 answer | 不返回 detail/social_account 等 | 这些是 icost.vip 账号元数据，DeepSeek 无法提供有意义的值；缺失字段在 Shortcuts 中 getvalueforkey 返回空，下游 setvariable 设为空值，无害 |
| text.replace 清洗 | 换行→空格 | 3C-1 验证的成熟方案，OCR 文本含真实换行符会破坏 JSON |
| text.replace 用 WFTextTokenString | 而非 WFTextTokenAttachment | 3C-1 §8 实战经验：WFTextTokenAttachment 导致输入为空 |
| System prompt 精简版 | 去掉非核心字段说明 | 减少 token 消耗，保留格式骨架和关键规则即可 |
| Body type 用 File | 而非 Form/JSON | 3B/3C-1 验证的成熟方案：gettext 构建 JSON 字符串 + text.replace 清洗 + File body 发送 |
| 全量传递 iCost 上下文 | 分类+账户+标签+日期+自定义规则全部嵌入 prompt | 还原 icost.vip 能获得的全部信息，最大化识别准确率 |
| 引用已有实体查询 UUID | 6724C445/1EDA8BA8/7FEC0A01/2493C32C/E6362569/4856151E | 复用 3-full 已有的 iCost 查询和用户配置，不新增 action |
| 丢弃的字段 | m/r/X-D/X-O/f | m=路由标识、r=随机防重、X-D/X-O=设备分析，对识别结果无影响；f(图片)由本地 OCR 替代 |

## 8. XML 修改定位指南（Engineer 用）

### 8.1 需要操作的行范围

| 操作 | 位置 | 行范围 | 说明 |
|------|------|--------|------|
| 插入 A1–A3 | image.resize 之后 | line 2164 之后 | 新增 3 个 action |
| 替换 B | downloadurl | lines 2165–3601 | 删除原 ~1436 行，替换为 ~80 行 |
| 插入 C1–C3 | downloadurl 之后 | line 3601 之后（新位置） | 新增 3 个 action |
| 修改 D | detect.dictionary | lines 3602–3623（新位置偏移后） | 改 WFInput 引用 |

### 8.2 建议实现顺序

1. 复制 `samples/money/3-full.xml` → `samples/money/3-full-deepseek.xml`
2. 生成 6 个新 UUID（UUID-OCR, UUID-BODY, UUID-CLEAN, UUID-CHOICES, UUID-FIRST, UUID-CONTENT）
3. 在 line 2164 后插入 A1–A3 的 XML
4. 删除 lines 2165–3601（原 downloadurl），替换为新 downloadurl
5. 在新 downloadurl 之后插入 C1–C3
6. 修改 detect.dictionary 的 WFInput
7. 运行 `python tools/shortcut_tool.py build` + `sign`
8. iPhone 验证

### 8.3 推荐使用 Python 脚本修改

由于修改涉及 ~1400 行的精确替换，建议 Engineer **编写 Python 脚本**（如 `tools/modify_3full.py`）来操作 XML，而非手动编辑：

```python
# 伪代码
import plistlib
data = plistlib.loads(open('3-full.xml', 'rb').read())
actions = data['WFWorkflowActions']

# 找到 downloadurl action (UUID=86D23FE2)
idx = find_action_by_uuid(actions, '86D23FE2-31E6-489C-86BE-1B351FE246C5')

# 在 idx 前插入 OCR + gettext + text.replace
# 替换 actions[idx] 为新的 downloadurl
# 在 idx+1 插入 choices 解析链
# 修改 detect.dictionary 的输入引用
```

## 9. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| OCR 文本含双引号 `"` 破坏 JSON | DeepSeek 收到格式错误的请求 | 可增加 text.replace 将 `"` → `\"` ；实测再决定是否需要 |
| DeepSeek 返回非 JSON 文本 | detect.dictionary 解析失败 | System prompt 强调"只返回 JSON"；失败时 answer 为空，触发"识别失败"菜单 |
| 下游代码引用 social_account 等空变量 | 运行时某些 UI 显示为空 | 可接受，这些是 icost.vip 特有功能，不影响记账核心流程 |
| 收银员编辑（PUT /wapi/v1/name）仍指向 icost.vip | 功能失效 | 3C-2 scope 仅替换 /chat 接口，其他 icost.vip 调用（name, text, update）暂不处理 |

## 10. 完整 XML 模板（新增/替换部分）

### A1: extracttextfromimage

```xml
<!-- A1: 本地 OCR 文字识别 -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.extracttextfromimage</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{{UUID-OCR}}</string>
        <key>WFImage</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>OutputName</key>
                <string>调整大小后的图像</string>
                <key>OutputUUID</key>
                <string>0B4F4A02-1E9A-4B90-9391-CE8950343539</string>
                <key>Type</key>
                <string>ActionOutput</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

### A2: gettext (构建 JSON body)

```xml
<!-- A2: 构建 DeepSeek JSON 请求体（含分类/账户/标签/日期/自定义规则 + OCR 文本） -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.gettext</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{{UUID-BODY}}</string>
        <key>WFTextActionText</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>attachmentsByRange</key>
                <dict>
                    <!-- ￼1: 当前日期 (date fallback) -->
                    <key>{POS_1, 1}</key>
                    <dict>
                        <key>Aggrandizements</key>
                        <array>
                            <dict>
                                <key>WFDateFormatStyle</key>
                                <string>Custom</string>
                                <key>WFDateFormat</key>
                                <string>yyyy-MM-dd</string>
                                <key>WFISO8601IncludeTime</key>
                                <false/>
                                <key>Type</key>
                                <string>WFDateFormatVariableAggrandizement</string>
                            </dict>
                        </array>
                        <key>Type</key>
                        <string>CurrentDate</string>
                    </dict>
                    <!-- ￼2: 支出一级分类名列表 -->
                    <key>{POS_2, 1}</key>
                    <dict>
                        <key>Aggrandizements</key>
                        <array>
                            <dict>
                                <key>PropertyName</key>
                                <string>name</string>
                                <key>PropertyUserInfo</key>
                                <dict>
                                    <key>WFLinkEntityContentPropertyUserInfoPropertyIdentifier</key>
                                    <string>name</string>
                                </dict>
                                <key>Type</key>
                                <string>WFPropertyVariableAggrandizement</string>
                            </dict>
                        </array>
                        <key>OutputName</key>
                        <string>分类</string>
                        <key>OutputUUID</key>
                        <string>6724C445-3E84-42FA-AD33-1CD9AEA79FF3</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <!-- ￼3: 支出二级分类名列表 -->
                    <key>{POS_3, 1}</key>
                    <dict>
                        <key>Aggrandizements</key>
                        <array>
                            <dict>
                                <key>PropertyName</key>
                                <string>name</string>
                                <key>PropertyUserInfo</key>
                                <dict>
                                    <key>WFLinkEntityContentPropertyUserInfoPropertyIdentifier</key>
                                    <string>name</string>
                                </dict>
                                <key>Type</key>
                                <string>WFPropertyVariableAggrandizement</string>
                            </dict>
                        </array>
                        <key>OutputName</key>
                        <string>分类</string>
                        <key>OutputUUID</key>
                        <string>1EDA8BA8-63C6-49BC-A435-B06E25F90FC2</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <!-- ￼4: 收入分类名列表 -->
                    <key>{POS_4, 1}</key>
                    <dict>
                        <key>Aggrandizements</key>
                        <array>
                            <dict>
                                <key>PropertyName</key>
                                <string>name</string>
                                <key>PropertyUserInfo</key>
                                <dict>
                                    <key>WFLinkEntityContentPropertyUserInfoPropertyIdentifier</key>
                                    <string>name</string>
                                </dict>
                                <key>Type</key>
                                <string>WFPropertyVariableAggrandizement</string>
                            </dict>
                        </array>
                        <key>OutputName</key>
                        <string>分类</string>
                        <key>OutputUUID</key>
                        <string>7FEC0A01-66F2-42BA-8663-E5A3755B7C43</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <!-- ￼5: 账户名列表 -->
                    <key>{POS_5, 1}</key>
                    <dict>
                        <key>Aggrandizements</key>
                        <array>
                            <dict>
                                <key>PropertyName</key>
                                <string>name</string>
                                <key>PropertyUserInfo</key>
                                <dict>
                                    <key>WFLinkEntityContentPropertyUserInfoPropertyIdentifier</key>
                                    <string>name</string>
                                </dict>
                                <key>Type</key>
                                <string>WFPropertyVariableAggrandizement</string>
                            </dict>
                        </array>
                        <key>OutputName</key>
                        <string>账户</string>
                        <key>OutputUUID</key>
                        <string>2493C32C-EF78-4A09-88B7-B7AA729FCED7</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <!-- ￼6: 标签名列表 -->
                    <key>{POS_6, 1}</key>
                    <dict>
                        <key>Aggrandizements</key>
                        <array>
                            <dict>
                                <key>PropertyName</key>
                                <string>name</string>
                                <key>PropertyUserInfo</key>
                                <dict>
                                    <key>WFLinkEntityContentPropertyUserInfoPropertyIdentifier</key>
                                    <string>name</string>
                                </dict>
                                <key>Type</key>
                                <string>WFPropertyVariableAggrandizement</string>
                            </dict>
                        </array>
                        <key>OutputName</key>
                        <string>标签</string>
                        <key>OutputUUID</key>
                        <string>E6362569-6744-4835-BBAA-12428853205C</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <!-- ￼7: 用户自定义规则 -->
                    <key>{POS_7, 1}</key>
                    <dict>
                        <key>OutputName</key>
                        <string>文本</string>
                        <key>OutputUUID</key>
                        <string>4856151E-17D0-45C6-B4F0-DC03CE6B5E6D</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <!-- ￼8: OCR 识别文字 -->
                    <key>{POS_8, 1}</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Text from Image</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-OCR}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                </dict>
                <key>string</key>
                <string>JSON_BODY_WITH_8_PLACEHOLDERS</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenString</string>
        </dict>
    </dict>
</dict>
```

> **Engineer 实现指引**:
> 1. 用 §4.5 的 Python 脚本计算 8 个 ￼ 的精确位置
> 2. `{POS_1, 1}` ~ `{POS_8, 1}` 替换为实际位置
> 3. `JSON_BODY_WITH_8_PLACEHOLDERS` 替换为 §4.4 中的完整 JSON body 字符串（含 8 个 &#xFFFC;）
> 4. ⚠️ 分类/账户/标签的 Aggrandizement 可能需要从原 XML 复制 `WFLinkEntityContentPropertyUserInfoEnumMetadata` data 块（见 §4.6）— 如果不含此 data 块，先尝试不带的版本，导入 iPhone 测试是否能正确提取 .name

### A3: text.replace

```xml
<!-- A3: 清洗 OCR 换行符 -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.text.replace</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{{UUID-CLEAN}}</string>
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
                        <string>{{UUID-BODY}}</string>
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
```

### B: downloadurl (替换版)

```xml
<!-- B: POST 到 DeepSeek API -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.downloadurl</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>86D23FE2-31E6-489C-86BE-1B351FE246C5</string>
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
                                        <string>词典值</string>
                                        <key>OutputUUID</key>
                                        <string>D625BA13-A5F8-4D69-955E-29681DF71DD6</string>
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
                <string>Updated Text</string>
                <key>OutputUUID</key>
                <string>{{UUID-CLEAN}}</string>
                <key>Type</key>
                <string>ActionOutput</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

### C1–C3: DeepSeek 响应解析链

```xml
<!-- C1: 提取 choices -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.getvalueforkey</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{{UUID-CHOICES}}</string>
        <key>WFDictionaryKey</key>
        <string>choices</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>OutputName</key>
                <string>Contents of URL</string>
                <key>OutputUUID</key>
                <string>86D23FE2-31E6-489C-86BE-1B351FE246C5</string>
                <key>Type</key>
                <string>ActionOutput</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>

<!-- C2: 取第一项 choices[0] -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.getitemfromlist</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{{UUID-FIRST}}</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>OutputName</key>
                <string>Value for Key</string>
                <key>OutputUUID</key>
                <string>{{UUID-CHOICES}}</string>
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

<!-- C3: 提取 message.content -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.getvalueforkey</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>{{UUID-CONTENT}}</string>
        <key>WFDictionaryKey</key>
        <string>message.content</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>OutputName</key>
                <string>Item from List</string>
                <key>OutputUUID</key>
                <string>{{UUID-FIRST}}</string>
                <key>Type</key>
                <string>ActionOutput</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```

### D: detect.dictionary (修改后)

```xml
<!-- D: 解析 DeepSeek 返回的 JSON 文本为词典 -->
<dict>
    <key>WFWorkflowActionIdentifier</key>
    <string>is.workflow.actions.detect.dictionary</string>
    <key>WFWorkflowActionParameters</key>
    <dict>
        <key>UUID</key>
        <string>CDA2A1C9-17AB-4840-AF03-C0701246A682</string>
        <key>WFInput</key>
        <dict>
            <key>Value</key>
            <dict>
                <key>OutputName</key>
                <string>Value for Key</string>
                <key>OutputUUID</key>
                <string>{{UUID-CONTENT}}</string>
                <key>Type</key>
                <string>ActionOutput</string>
            </dict>
            <key>WFSerializationType</key>
            <string>WFTextTokenAttachment</string>
        </dict>
    </dict>
</dict>
```
