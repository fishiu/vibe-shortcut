# Engineer Log: Task 3C-5/3C-6/3C-7 — 计时通知 + API 配置外置 + 多平台配置

> **Date**: 2026-03-12
> **Related Task**: Phase 3C-5 ~ 3C-7
> **Status**: ✅ iPhone 验证通过

---

## 1. 任务目标

在 `modify_3full.py` 上逐步迭代，从简单的通知计时到完整的多平台 API 配置系统：

| 轮次 | 内容 | 验证 |
|------|------|------|
| 3C-5 | 隐藏收银员信息 + DeepSeek 前后通知 + max_tokens | ✅ |
| 3C-6 | API 配置外置（URL/模型/max_tokens 做成可配置项） | ⏭️ 被 3C-7 替代 |
| 3C-7 | 多平台配置 + 模型编号映射 + 调试开关 + reasoning_effort | ✅ |

**最终产出**: `samples/money/3-full-deepseek.shortcut`（AEA 签名，1172 actions）

---

## 2. 3C-5 实现（隐藏收银员 + 通知）

### 2.1 改动

- `显示记录详情` → `false`（action + ImportQuestions 双写，同 Fix 1b 模式）
- downloadurl 前后各插一个 notification（N1/N2）
- TEMPLATE 末尾加 `,"max_tokens":300,"temperature":0`
- N2 改为显示 DeepSeek 原始返回内容（`✅ {响应}`），方便调试

### 2.2 max_tokens 300→1000 教训

默认 300 导致 DeepSeek 返回被截断 → `detect.dictionary` 解析失败（"无法将文本转换为词典"）。用户手动改为 1000 后恢复正常。

**教训**: 记账 JSON 的 token 数比预期多，prompt + response 总共需要 ~800 tokens，300 不够。

---

## 3. 3C-7 实现（多平台配置 — 替代 3C-6）

### 3.1 架构概览

3C-6 的简单外置方案不够用，被 3C-7 完全替代。核心设计：

| 能力 | 实现方式 |
|------|----------|
| 平台选择（火山引擎/DeepSeek/其他） | 动态字典查找：`gettext "地址(￼)"` → `getvalueforkey` |
| 模型选择（编号 1-5） | 内置映射字典 + conditional 处理自定义模型 |
| 调试通知开关 | conditional 包裹 N1/N2（同显示随机文字模式） |
| reasoning_effort 配置 | TEMPLATE 占位符，运行时替换 |

### 3.2 密钥字典 29C441EE 改动（7 项）

```
密钥 → 密钥(火山引擎)     ← 重命名
+ 密钥(DeepSeek)          ← 空
+ 密钥(其他)              ← 空
+ 地址(火山引擎)          ← https://ark.cn-beijing.volces.com/api/v3/chat/completions
+ 地址(DeepSeek)          ← https://api.deepseek.com/v1/chat/completions
+ 地址(其他)              ← 空
+ 自定义模型              ← 空
```

### 3.3 配置字典 588A56AF 新增（5 项）

| Key | 类型 | 默认值 |
|-----|------|--------|
| 平台 | Text | 火山引擎 |
| 模型 | Number | 1 |
| max_tokens | Number | 300 |
| reasoning_effort | Text | minimal |
| 调试模式 | Boolean | false |

### 3.4 运行时 Action 链（30 actions，替换原 2 actions）

```
Phase 0 (5): S1-S5 从 588A56AF 读取配置
Phase 1 (4): T_URL→R_URL→T_KEY→R_KEY 动态字典查找 URL 和密钥
Phase 2 (7): MODEL_MAP→MODEL_LOOKUP→SV_MODEL_DEFAULT→MC_BEGIN→MC_CUSTOM→SV_MODEL_OVERRIDE→MC_END
Phase 3 (3): A1(OCR)→A2(gettext, 11占位符)→A3(text.replace)
Phase 4 (3): DB1_BEGIN→N1(⏳通知)→DB1_END  ← conditional 包裹
Phase 5 (1): B(downloadurl)
Phase 6 (3): DB2_BEGIN→N2(✅通知)→DB2_END  ← conditional 包裹
Phase 7 (4): C1→C2→C3→D(解析响应)
```

### 3.5 TEMPLATE（11 个占位符）

```
￼1  模型名         → Variable "model"（setvariable 共享）
￼2  当前日期       → CurrentDate (yyyy-MM-dd HH:mm)
￼3-7 iCost 实体    → 原有 5 个 entity ref
￼8  自定义规则     → UUID_CUSTOM_RULES
￼9  OCR 文本       → extracttextfromimage 输出
￼10 max_tokens     → S3 (cfg_maxtokens) 输出
￼11 reasoning_effort → S4 (cfg_reasoning) 输出
```

末尾硬编码 `,"thinking":{"type":"disabled"}`（关闭 GLM 推理模式，DeepSeek/火山引擎会忽略）。

### 3.6 模型编号映射表

| 编号 | 模型名 |
|------|--------|
| 1 | doubao-seed-2-0-mini-260215（默认） |
| 2 | deepseek-chat |
| 3 | doubao-seed-1-6-flash-250828 |
| 4 | deepseek-v3-2-251201 |
| 5 | 其他（读取密钥字典中的「自定义模型」） |

### 3.7 关键设计决策

**动态字典查找**: 利用 `WFDictionaryKey` 支持 `WFTextTokenString` 的能力（3-full.xml line 1666 已验证），用 4 个 action 替代 16+ 个嵌套 conditional。`gettext "地址(￼)"` 运行时拼出 `"地址(火山引擎)"`，再做 `getvalueforkey`。

**命名变量共享**: 模型调度有"其他"分支需要 conditional。用 `setvariable "model"` 在分支间共享结果，A2 的 attachment 用 `{Type: "Variable", VariableName: "model"}` 引用。

**注释友好化**: 在 shortcut 开头的 comment action 中添加了完整的密钥字典说明和模型编号映射表，不仅在导入弹窗时提示，编辑时也能随时查看。

---

## 4. 经验教训

### 铁律 1（再次验证）: WFCondition=0 在数值模式下是"小于"

3C-7 的 MC_BEGIN（模型编号判断是否等于 5）最初按 Architect 设计用 `WFCondition=0` + `WFConditionalActionString='5'` + `CoercionItemClass: WFStringContentItem` 做文本等于比较。

**iPhone 上的表现**: 显示为"如果 词典值 小于"，后面的比较值丢失（因为数值模式期望 `WFNumberValue`，不认 `WFConditionalActionString`）。

**原因**: 即使指定了 `WFStringContentItem` 强制转文本，iPhone 仍按数值模式解析 `WFCondition=0`。文本模式的切换机制不可靠。

**修复**: 改为 `WFCondition=4`（≥5），用已验证的数值比较。编号 1-4 不满足 ≥5 跳过，编号 5 满足进入自定义模型分支。

**结论**: **永远不要用 `WFCondition=0` 做任何判断**。数值比较只用 `WFCondition=4`（≥），文本比较的可靠方式待验证。这是第三次踩同一个坑（3C-4、3C-7 Architect 设计、3C-7 实现）。

### 新增经验

| 经验 | 说明 |
|------|------|
| max_tokens 不能太小 | 300 导致响应截断，记账 JSON 需要 ~800 tokens |
| 动态 WFDictionaryKey 可用 | gettext 拼接 key 名 + WFTextTokenString 做动态查找，4 action 替代 16+ |
| setvariable 跨分支共享 | conditional 内外用命名变量传值，A2 用 `{Type: "Variable"}` 引用 |
| notification body 可嵌变量 | WFTextTokenString + attachmentsByRange 在通知中显示动态内容 |
| comment action 是最佳注释位置 | 导入弹窗只显示一次，comment action 编辑时随时可见 |

---

## 5. 产出文件

| 文件 | 说明 |
|------|------|
| `tools/modify_3full.py` | 修改脚本（可重复执行，含全部 3C-2~3C-7 fix） |
| `samples/money/3-full-deepseek.xml` | 修改后 XML（1172 actions） |
| `samples/money/3-full-deepseek-unsigned.shortcut` | binary plist |
| `samples/money/3-full-deepseek.shortcut` | AEA 签名 |

---

## 6. 构建命令

```bash
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/modify_3full.py

/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py build \
    samples/money/3-full-deepseek.xml samples/money/3-full-deepseek-unsigned.shortcut
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py sign \
    samples/money/3-full-deepseek-unsigned.shortcut samples/money/3-full-deepseek.shortcut
```

---

## 7. iPhone 验证结果

### 3C-5
- [x] 记账结果页无收银员/操作员信息
- [x] DeepSeek 调用前后各弹通知（调试模式下）
- [x] max_tokens=1000 时响应完整，记账正常

### 3C-7 默认配置（火山引擎 + 模型 1）
- [x] 导入成功，配置页显示所有新字段
- [x] 记账功能正常
- [x] 调试模式默认关闭，不弹通知

### 3C-7 切换平台
- [x] 动态字典查找能正确按平台名取值
- [ ] 切换到 DeepSeek 验证（待用户测试）
- [ ] 切换到"其他"验证（待用户测试）

### 3C-7 注释
- [x] shortcut 开头 comment action 包含密钥字典说明和模型映射表

---

## 8. 已知风险

- **动态 WFDictionaryKey 回退**: 若某些 iOS 版本不支持动态 key，需回退到嵌套 conditional 方案（~18 actions 替代 Phase 1 的 4 actions）
- **max_tokens 默认 300**: 默认值偏小，复杂小票可能截断。用户已知需手动调大
- **reasoning_effort 参数**: DeepSeek/火山引擎是否忽略此参数待验证，可能返回 400 错误
- **OCR 文本含双引号**: 可能破坏 JSON body，当前仅清洗换行符

---

## 9. 建议 Architect 更新

- **doc3-spec §2.4**: 标注 `WFCondition=0` 即使指定 `WFStringContentItem` 仍会按数值模式解析，文本等于比较不可靠
- **doc3-spec §5.1**: 新增"动态 WFDictionaryKey"模式、"setvariable 跨分支共享"模式
- **手册 v0.4**: 新增 `setvariable`/`getvariable` action 参考、Variable 引用类型
