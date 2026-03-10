# Engineer Log: Task 3C-2 - 替换 3-full 的 icost.vip 请求

> **Date**: 2026-03-11
> **Related Task**: Phase 3C-2 — 替换 icost.vip
> **Status**: ✅ iPhone 初步验证通过，细节待打磨

---

## 1. 任务目标

按 Architect 设计（`architect/task-3c2-replace-icost.md`），在 `3-full.xml`（1140 actions）中外科手术式替换 `icost.vip/wapi/v1/chat` 调用为 DeepSeek API，保持下游 1100+ actions 零改动。

**验收标准**:
- [x] `samples/money/3-full-deepseek.xml` 存在，1146 actions（净增 6）
- [x] `samples/money/3-full-deepseek.shortcut` 存在，AEA1 签名格式
- [x] 8 个 ￼ 位置验证通过（Python 脚本自动计算）
- [x] UUID 引用链完整：downloadurl (86D23FE2) + detect.dictionary (CDA2A1C9) UUID 不变
- [x] 下游 getvalueforkey("detail") 仍引用 CDA2A1C9（零改动验证）
- [x] iCost 实体 Aggrandizement 含 data 块（3 个 CategoryEntity 已提取）
- [x] iPhone 导入并运行记账流程（初步通过，基础记账功能正常，细节待打磨）

---

## 2. 实现方案

### 2.1 工具选择

选择 Python 脚本 (`tools/modify_3full.py`) 操作 plist dict，而非手动编辑 XML。原因：
- 修改涉及 ~1436 行的精确替换
- plistlib 保证数据完整性
- 可自动提取现有 Aggrandizement data 块

### 2.2 修改区域

原 actions[66:68]（2 个 action）→ 新 actions[66:74]（8 个 action）：

```
[66] extracttextfromimage (OCR)     → UUID 157F6CD4  ← 引用 image.resize (0B4F4A02)
[67] gettext (JSON body)            → UUID 00EF1C9C  ← 8 个 ￼ 引用 iCost 实体 + OCR
[68] text.replace (清洗换行)        → UUID 62E85754  ← WFInput(WFTextTokenString) 引用 [67]
[69] downloadurl (POST DeepSeek)    → UUID 86D23FE2  ← 保留原 UUID，body 引用 [68]
[70] getvalueforkey (choices)       → UUID DFFB435A  ← 引用 [69]
[71] getitemfromlist (choices[0])    → UUID 8B128DC7  ← 引用 [70]
[72] getvalueforkey (msg.content)   → UUID CB1DCEEE  ← 引用 [71]
[73] detect.dictionary (修改输入)   → UUID CDA2A1C9  ← 保留原 UUID，输入改引 [72]
```

### 2.3 ￼ 位置计算结果

```
￼1 当前日期:    {497, 1}  → CurrentDate (yyyy-MM-dd)
￼2 支出分类:    {557, 1}  → 6724C445 .name (含 data 块)
￼3 支出子分类:  {566, 1}  → 1EDA8BA8 .name (含 data 块)
￼4 收入分类:    {574, 1}  → 7FEC0A01 .name (含 data 块)
￼5 账户:        {580, 1}  → 2493C32C .name (无 data 块)
￼6 标签:        {586, 1}  → E6362569 .name (无 data 块)
￼7 自定义规则:  {589, 1}  → 4856151E (gettext 输出)
￼8 OCR文本:     {626, 1}  → 157F6CD4 (OCR 输出)
```

### 2.4 Aggrandizement data 块提取

通过递归搜索原 downloadurl action 的 FormValues.v，成功提取了 5 个 iCost 实体引用的 Aggrandizement：
- **3 个含 data 块**：exp_first (6724C445), exp_second (1EDA8BA8), income (7FEC0A01) — 均为 ICSearchCategoryEntity
- **2 个无 data 块**：asset (2493C32C, ICSearchAssetEntity), tag (E6362569, ICSearchTagEntity) — 原 XML 中这两个实体的引用就没有 data 块

---

## 3. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| text.replace WFInput | WFTextTokenString | 3C-1 实战教训：WFTextTokenAttachment 导致输入为空 |
| Aggrandizement data 块 | 从原 XML 提取 | 保持与原文件完全一致，避免运行时 .name 提取失败 |
| downloadurl body type | File | 3B/3C-1 验证的成熟方案 |
| 保留原 UUID | 86D23FE2 + CDA2A1C9 | 避免破坏下游引用链 |
| 无 debug alert | 直接发布版 | 基于 3C-1 成熟模式，风险可控 |

---

## 4. 产出文件

- `tools/modify_3full.py` — 修改脚本（可重复执行）
- `samples/money/3-full-deepseek.xml` — 修改后 XML（1146 actions）
- `samples/money/3-full-deepseek-unsigned.shortcut` — binary plist
- `samples/money/3-full-deepseek.shortcut` — AEA 签名（101.9 KB）

---

## 5. 构建命令

```bash
# 生成修改后的 XML
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/modify_3full.py

# 构建 + 签名
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py build samples/money/3-full-deepseek.xml samples/money/3-full-deepseek-unsigned.shortcut
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py sign samples/money/3-full-deepseek-unsigned.shortcut samples/money/3-full-deepseek.shortcut
```

---

## 6. 已知风险

- **OCR 文本含双引号 `"`**：可能破坏 JSON。当前仅清洗换行符，实测后决定是否需要额外 text.replace
- **asset/tag 无 data 块**：原 XML 中这两个实体引用就没有 data 块，可能影响 .name 提取
- **DeepSeek 返回非 JSON**：detect.dictionary 解析失败时 answer 为空，触发"识别失败"菜单
- **收银员编辑等 icost.vip 功能**：仅替换 /chat 接口，其他 icost.vip 调用暂不处理

---

## 7. iPhone 验证结果

1. [x] 导入 `3-full-deepseek.shortcut` 到 iPhone
2. [x] 修改密钥为 DeepSeek API Key (`sk-xxx`)
3. [x] 选择账本 → 截图 → 验证 OCR + DeepSeek 识别结果
4. [x] 基础记账流程正常执行（分类匹配、账户匹配等）

**结论**: 初步通过，基础记账功能可用，部分细节待打磨。

---

## 8. 建议 PM / Architect 更新的内容

以下内容供 PM 和 Architect 参考，Engineer 不直接修改他们的文档。

### 8.1 建议 PM 更新 `doc2-current_status.md`

- 3C-1 状态：`🔜 进行中` → `✅ 完成`
- 3C-2 状态：`⏳ 待开始` → `✅ 初步通过`
- Task 3.10 (Architect)：勾选完成，补充产出 `architect/task-3c2-replace-icost.md`
- Task 3.11 (Engineer)：勾选完成，补充：
  - 实现：`tools/modify_3full.py`
  - 产出：`samples/money/3-full-deepseek.xml`（1146 actions）+ `.shortcut`（AEA 签名，101.9 KB）
  - 日志：`docs/project/engineer/task-3c2-replace-icost.md`
  - 验证：iPhone 基础记账功能正常，细节待打磨

### 8.2 建议 Architect 更新 `doc3-spec.md`

- §5 设计文档索引表：3C-2 行更新状态 `📐 设计完成` → `✅ 初步通过`，补充 Engineer 日志链接
- §5.1 跨任务技术经验，建议新增：
  - **大规模 XML 修改用 Python 脚本**，不要手动编辑（`plistlib` 操作 dict，自动保持数据完整性）
  - **iCost 实体 Aggrandizement 含 data 块**，从原 XML 提取复用最安全（`find_attachment_for_uuid` 递归搜索 + `copy.deepcopy`）
  - **替换 action 时保留原 UUID**，避免破坏不可见的下游引用链
