# Architect Design: Task 3C-8 — 最终优化三合一

> **Date**: 2026-03-12
> **Related Tasks**: 3C-8a (补充prompt), 3C-8b (恢复账本), 3C-8c (新增模型)
> **Status**: 📐 设计完成

---

## 1. 总览

三个独立小优化，均在 `modify_3full.py` 上改动，不涉及新架构：

| 子任务 | 改动范围 | 复杂度 |
|--------|----------|--------|
| 3C-8a 补充prompt | ImportQuestions DefaultValue + comment | 低 |
| 3C-8b 恢复账本 | 撤销 Fix 1d + 修改 gettext | 中 |
| 3C-8c 新增模型 | MODEL_MAP + MC_BEGIN 阈值 + 注释/IQ 文本 | 低 |

---

## 2. 3C-8a — 打通补充 prompt（自定义规则默认值）

### 2.1 背景

3-full 原版有一个「自定义规则」功能：
- comment action（说明）→ gettext action（UUID: `4856151E`，用户输入自定义规则）
- gettext 输出已接入 TEMPLATE 占位符 ￼8，作为 system prompt 的一部分发给 AI
- ImportQuestions（ActionIndex=6, ParameterKey=`WFTextActionText`）的 `DefaultValue` 为**空字符串**

功能已连通但默认值为空，等于没用。

### 2.2 改动

**A. 修改 ImportQuestions DefaultValue**

找到 `WFWorkflowImportQuestions` 中匹配条件的条目：
- `ActionIndex` = gettext UUID `4856151E` 在 actions 中的索引（原始 3-full.xml 中为 6）
- `ParameterKey` = `'WFTextActionText'`

将 `DefaultValue` 从 `''` 改为：

```
备注(remark)字段规则：简洁且表意完整，让人一眼能看明白这笔消费。网购写明平台、商家、商品（如 淘宝 xx旗舰店 数据线），信息不全只写已知部分；线下写明商户和内容（如 瑞幸 生椰拿铁）。不要捏造OCR中没有的信息。
```

> **注意**: 默认文本不含双引号 `"` 和反斜杠 `\`，避免破坏 JSON body。运行时文本中的换行符会被 A3（text.replace）替换为空格，因此保持单行即可。

**B. 更新 ImportQuestions Text 描述**

将该条目的 `Text` 改为：

```
🗣️ 自定义规则

如果有个性化需求，可在下方文本框输入自定义识别规则。
默认已填入备注写法规则，可根据需要修改或清空。
示例：识别到 xxx 则分类归为"xxx"，或标签为"xxx"
```

**C. 更新 comment action 文本**

找到含 `自定义规则` 的 comment action，将 `WFCommentActionText` 更新为同 B 的描述内容（保持 comment 和 ImportQuestions 一致）。

### 2.3 实现提示

- 用 ActionIndex 或 Text 内容匹配找 ImportQuestion 条目
- DefaultValue 是字符串类型，直接赋值即可
- 不需要动 TEMPLATE 或 action 链，仅改默认值和说明文字

---

## 3. 3C-8b — 恢复账本信息显示

### 3.1 背景

3C-5 的 Fix 1d 将 `显示记录详情` 设为 `false`，隐藏了「记录次数 + 交易员 + 入账账本」整个区块。用户只想隐藏收银员/交易员，但账本信息也被一起隐藏了。

原始 `显示记录详情` conditional 结构（GroupingIdentifier: `12D478E7`）：

```
getvalueforkey "显示记录详情" from 588A56AF → UUID D4FD621B
conditional BEGIN: if D4FD621B (coerce Bool) ≥ 1
  gettext UUID 5499E009: "记录次数： ￼次 \n交易员： ￼\n入账账本： ￼ "
    attachments: {6,1}→requests, {15,1}→cashier, {23,1}→ledger
conditional ELSE
  gettext UUID AB5D0DD4: (空文本)
conditional END
```

### 3.2 方案

**不改 `显示记录详情` 的值**（恢复为原始 true），而是**修改 TRUE 分支的 gettext 内容**，只保留账本：

**Step 1**: 删除 Fix 1d 代码

移除 `modify_3full.py` 中以下代码（及对应的 ImportQuestions 同步）：

```python
if key_str == '显示记录详情':
    item['WFValue']['Value'] = False
```

```python
if k == '显示记录详情':
    dv_item['WFValue']['Value'] = False
```

**Step 2**: 修改 gettext UUID `5499E009-3080-4D7C-BB04-55BA02F6AC53`

找到该 action，修改 `WFTextActionText`:

| 属性 | 原值 | 新值 |
|------|------|------|
| string | `记录次数： ￼次 \n交易员： ￼\n入账账本： ￼ ` | `入账账本： ￼ ` |
| attachmentsByRange | `{6,1}→requests`, `{15,1}→cashier`, `{23,1}→ledger` | `{6,1}→ledger` |

新 attachmentsByRange 结构：

```python
{
    '{6, 1}': {
        'Type': 'Variable',
        'VariableName': 'ledger'
    }
}
```

字符位置验证：`入(0)账(1)账(2)本(3)：(4) (5)￼(6) (7)` → ledger 变量在位置 6，正确。

**Step 3**: 更新 comment action 中 `显示记录详情` 的说明

原文：`🗃️ 显示记录详情：是否显示操作员名称、记录次数等`
改为：`🗃️ 显示记录详情：是否显示入账账本信息`

### 3.3 影响分析

- `显示记录详情` 在整个 shortcut 中仅被一个 `getvalueforkey`（UUID D4FD621B）读取，控制一个 conditional 块
- 恢复为 true + 精简 gettext 后：下游代码接收到 "入账账本： xxx" 文本，功能正常
- ELSE 分支（空 gettext）不受影响

---

## 4. 3C-8c — 新增模型选项

### 4.1 当前模型映射

MODEL_MAP（4 条内置 + 编号 5 为自定义）：

| 编号 | 模型名 |
|------|--------|
| 1 | doubao-seed-2-0-mini-260215（默认）|
| 2 | deepseek-chat |
| 3 | doubao-seed-1-6-flash-250828 |
| 4 | deepseek-v3-2-251201 |
| 5 | 其他（读取密钥字典「自定义模型」）|

MC_BEGIN 条件：`WFCondition=4, WFNumberValue='5'`（≥5 进入自定义分支）

### 4.2 改动

**A. MODEL_MAP 新增第 5 条**

```python
{
    'WFItemType': 0,
    'WFKey': {'Value': {'string': '5'}, 'WFSerializationType': 'WFTextTokenString'},
    'WFValue': {'Value': {'string': 'doubao-seed-1-6-flash-250615'}, 'WFSerializationType': 'WFTextTokenString'}
}
```

**B. MC_BEGIN 阈值 5→6**

```python
'WFNumberValue': '6'    # 原来是 '5'
```

编号 1-5 不满足 ≥6，走内置映射；编号 6+ 进入自定义分支。

**C. 更新所有模型编号文本**

需要更新三处文本（模型列表说明）：

1. **comment action**（Fix 2b 的 config_guide）
2. **ImportQuestions Text**（Fix 1f）
3. **密钥字典 comment 中的「自定义模型」说明**（Fix 2b 的 key_dict_guide）

更新内容：

```
🤖 模型：填写编号
  1 = doubao-seed-2-0-mini-260215（默认）
  2 = deepseek-chat
  3 = doubao-seed-1-6-flash-250828
  4 = deepseek-v3-2-251201
  5 = doubao-seed-1-6-flash-250615
  6 = 其他（需在密钥字典中填写「自定义模型」）
```

key_dict_guide 中 `• 自定义模型：当「模型」设为 5 时填写模型名` 改为 `• 自定义模型：当「模型」设为 6 时填写模型名`

---

## 5. 改动文件清单

| 文件 | 改动 |
|------|------|
| `tools/modify_3full.py` | 3C-8a: 找 IQ 改 DefaultValue + Text；找 comment 改文本 |
| | 3C-8b: 删 Fix 1d + 修改 gettext 5499E009 + 更新 comment |
| | 3C-8c: MODEL_MAP 加条目 + MC_BEGIN 阈值 + 更新文本 |

输出：重新生成 `samples/money/3-full-deepseek.xml` + build + sign

---

## 6. 验证清单

### 3C-8a
- [ ] 导入 shortcut 时，「自定义规则」文本框已预填备注规则文本
- [ ] 记账后，备注字段符合规则（网购有平台+商品信息）

### 3C-8b
- [ ] 记账结果页**不显示**交易员/收银员/记录次数
- [ ] 记账结果页**显示**入账账本信息
- [ ] 「显示记录详情」设为 false 时，账本信息也隐藏

### 3C-8c
- [ ] 模型设为 5，使用 doubao-seed-1-6-flash-250615 记账正常
- [ ] 模型设为 6 + 自定义模型已填，使用自定义模型记账正常
- [ ] 导入时配置说明显示新的 6 条模型映射
