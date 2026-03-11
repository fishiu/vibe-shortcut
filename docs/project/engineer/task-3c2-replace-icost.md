# Engineer Log: Task 3C-2/3C-3/3C-4 — 替换 icost.vip + 精修 + 随机文字开关

> **Date**: 2026-03-11
> **Related Task**: Phase 3C-2 ~ 3C-4
> **Status**: ✅ 阶段性完成，iPhone 验证通过

---

## 1. 任务目标

在 `3-full.xml`（1140 actions）中外科手术式替换 `icost.vip/wapi/v1/chat` 调用为 DeepSeek API，并做三轮精修：

| 轮次 | 内容 | 验证 |
|------|------|------|
| 3C-2 | 替换 icost.vip → DeepSeek（核心改动） | ✅ |
| 3C-3 | 界面风格 3→1、识别优惠默认关、时间精度 HH:mm | ✅ |
| 3C-4 | 新增「显示随机文字」开关，conditional 包裹金句块 | ✅ |

**最终产出**: `samples/money/3-full-deepseek.shortcut`（AEA 签名，1150 actions）

---

## 2. 实现方案

### 2.1 工具选择

Python 脚本 `tools/modify_3full.py`，读取原始 `3-full.xml` → 内存修改 plist dict → 输出 `3-full-deepseek.xml`，可重复执行。

### 2.2 全部修改清单

脚本按顺序执行以下修改（每次从原始 3-full.xml 开始）：

```
Fix 1a: 配置字典 588A56AF — 界面风格 "3" → "1"
Fix 1b: 配置字典 588A56AF — 识别优惠 True → False
Fix 1c: WFWorkflowImportQuestions — 同步 DefaultValue + 添加显示随机文字 + 更新 Text
Fix 2a: 配置字典 588A56AF — 添加「显示随机文字」= false
Fix 2b: Comment action — 追加 🎲 说明文字
Fix 2c: 用 conditional (BEGIN/ELSE/END) 包裹 10 个金句 action
主流程: 插入 OCR + gettext + text.replace → 替换 downloadurl → 插入 choices 解析链 → 修改 detect.dictionary 输入
```

### 2.3 Action 结构（最终）

```
[55] getvalueforkey 显示随机文字     ← 新增 (3C-4)
[56] conditional BEGIN (≥ 1)         ← 新增 (3C-4)
  [57-66] 原 10 个金句 action        ← 不变，被条件包裹
[67] conditional ELSE                ← 新增 (3C-4)
[68] conditional END                 ← 新增 (3C-4)
...
[70] extracttextfromimage (OCR)      ← 新增 (3C-2)
[71] gettext (JSON body, 8 个 ￼)    ← 新增 (3C-2), 时间格式 HH:mm (3C-3)
[72] text.replace (清洗换行)         ← 新增 (3C-2)
[73] downloadurl (POST DeepSeek)     ← 替换 (3C-2), UUID 86D23FE2 保留
[74] getvalueforkey (choices)        ← 新增 (3C-2)
[75] getitemfromlist (choices[0])     ← 新增 (3C-2)
[76] getvalueforkey (msg.content)    ← 新增 (3C-2)
[77] detect.dictionary               ← 修改输入引用 (3C-2), UUID CDA2A1C9 保留
```

### 2.4 ￼ 位置计算结果（3C-3 更新后）

```
￼1 当前日期:    {509, 1}  → CurrentDate (yyyy-MM-dd HH:mm)
￼2 支出分类:    {569, 1}  → 6724C445 .name
￼3 支出子分类:  {578, 1}  → 1EDA8BA8 .name
￼4 收入分类:    {586, 1}  → 7FEC0A01 .name
￼5 账户:        {592, 1}  → 2493C32C .name
￼6 标签:        {598, 1}  → E6362569 .name
￼7 自定义规则:  {601, 1}  → 4856151E
￼8 OCR文本:     {638, 1}  → OCR UUID
```

---

## 3. 经验教训（Shortcuts 开发铁律）

本轮开发踩了三个大坑，每个都导致了"代码写对了但 iPhone 上不工作"的情况。以下经验适用于所有未来 Shortcuts 开发。

### 铁律 1: WFCondition 数值运算符与文本运算符不同

**坑**: doc3-spec 记录的 `WFCondition` 运算符表 `0=等于, 1=不等于, 2=小于...` **仅适用于文本比较**。数值比较时，`WFCondition=0` 实际是"小于"（`<`），不是"等于"。

**现象**: 用 `WFCondition=0, WFNumberValue='1'` 检查布尔值，期望 `false(0) == 1 → 不执行`，iPhone 上实际显示为 `< 1`，导致 `false(0) < 1 → true → 执行`，逻辑完全反转。

**正确做法**: 数值条件优先使用 `WFCondition=4`（≥），这是原文件中已验证的运算符。判断布尔值用 `值 ≥ 1`：`true(1) ≥ 1 → 执行`，`false(0) ≥ 1 → 跳过`。

**数值 WFCondition 实测映射**（待补全）:

| WFCondition | 数值含义 | 文本含义 |
|:-----------:|----------|----------|
| 0 | < (小于) | 等于 |
| 4 | ≥ (大于等于) | ≥ (大于等于) |
| 其他 | 待验证 | 见 doc3-spec |

> **TODO for Architect**: 需要系统性验证数值条件的全部运算符映射（1/2/3/5），更新 doc3-spec §2.4 和手册。

### 铁律 2: 修改配置值必须同步 WFWorkflowImportQuestions

**坑**: 只修改了 dictionary action 中的 `WFItems` 值（如界面风格 `"3"` → `"1"`），但 `WFWorkflowImportQuestions` 有独立的 `DefaultValue` 副本。导入时 Shortcuts app 用的是 ImportQuestions 的 DefaultValue，不是 action 里的值。

**现象**: Python 验证脚本确认 action 中值已改，但 iPhone 导入后仍显示原默认值。

**正确做法**: 修改配置字典时，必须同时修改两处：

```python
# 1. 修改 action 中的字典值
cfg_items = actions[cfg_idx]['WFWorkflowActionParameters']['WFItems']['Value']['WFDictionaryFieldValueItems']

# 2. 同步修改 WFWorkflowImportQuestions 中对应条目的 DefaultValue
for iq in data['WFWorkflowImportQuestions']:
    if iq['ActionIndex'] == cfg_idx and iq['ParameterKey'] == 'WFItems':
        dv_items = iq['DefaultValue']['Value']['WFDictionaryFieldValueItems']
        # 同步修改 dv_items...
        # 新增配置项也要加到 dv_items 和 iq['Text']
```

### 额外经验（延续 3C-1）

| 经验 | 说明 |
|------|------|
| text.replace WFInput 必须用 WFTextTokenString | WFTextTokenAttachment 导致输入为空（3C-1 实战验证） |
| 大规模 XML 修改用 Python 脚本 | plistlib 操作 dict 保证数据完整性，可重复执行 |
| 替换 action 时保留原 UUID | 避免破坏不可见的下游引用链（如 86D23FE2, CDA2A1C9） |
| iCost 实体 Aggrandizement 含 data 块 | 从原 XML 提取复用最安全（递归搜索 + deepcopy） |
| ￼ 位置动态计算 | TEMPLATE 文本改动（如加 HH:mm）会移位，必须用脚本自动算，不能手动硬编码 |

---

## 4. 产出文件

| 文件 | 说明 |
|------|------|
| `tools/modify_3full.py` | 修改脚本（可重复执行，含全部 fix） |
| `samples/money/3-full-deepseek.xml` | 修改后 XML（1150 actions） |
| `samples/money/3-full-deepseek-unsigned.shortcut` | binary plist |
| `samples/money/3-full-deepseek.shortcut` | AEA 签名 |

---

## 5. 构建命令

```bash
# 生成修改后的 XML（从 3-full.xml 开始，可重复执行）
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/modify_3full.py

# 构建 + 签名
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py build \
    samples/money/3-full-deepseek.xml samples/money/3-full-deepseek-unsigned.shortcut
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py sign \
    samples/money/3-full-deepseek-unsigned.shortcut samples/money/3-full-deepseek.shortcut
```

---

## 6. iPhone 验证结果

### 3C-2 基础验证
- [x] 导入 shortcut，密钥改为 DeepSeek API Key
- [x] 选择账本 → 截图 → OCR + DeepSeek 识别 → 记账成功

### 3C-3 精修验证
- [x] 小票风格预览界面（含"不记录此条账单"选项、改类别入口）
- [x] 识别优惠默认关闭
- [x] 记录时间精确到分钟

### 3C-4 金句开关验证
- [x] 默认（显示随机文字=false）：截图后不弹金句，直接进入 OCR
- [x] 打开后（显示随机文字=true）：截图后弹出随机句子（原有行为）
- [x] 两种模式下记账主流程均正常

---

## 7. 已知风险

- **OCR 文本含双引号 `"`**: 可能破坏 JSON body，当前仅清洗换行符
- **DeepSeek 返回非 JSON**: detect.dictionary 解析失败时 answer 为空，触发"识别失败"菜单
- **收银员编辑等 icost.vip 功能**: 仅替换 /chat 接口，其他 icost.vip 调用暂不处理
- **数值 WFCondition 映射不完整**: 仅验证了 0(=<) 和 4(=≥)，其他值待验证

---

## 8. 建议 PM / Architect 更新

### 8.1 建议 PM 更新 `doc2-current_status.md`

- 3C-2: `✅ 初步通过` → `✅ 阶段性完成`
- 3C-3: `[ ] Task 3.12` → `[x]`，补充验证结果
- 3C-4: 新增任务条目，标记 `✅ 完成`

### 8.2 建议 Architect 更新 `doc3-spec.md`

- **§2.4 WFCondition**: 补充数值运算符与文本运算符的区别，标注 `WFCondition=0` 在数值模式下是"小于"
- **§5.1 跨任务技术经验**: 新增"修改配置必须同步 WFWorkflowImportQuestions"

### 8.3 建议更新手册

- `docs/shortcuts-manual-v0.3.md` 补充数值 WFCondition 映射表
- 新增"配置字典双写"模式（action WFItems + ImportQuestions DefaultValue）
