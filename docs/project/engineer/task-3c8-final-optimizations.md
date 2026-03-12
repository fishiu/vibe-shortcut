# Engineer Log: Task 3C-8 — 最终优化三合一

> **Date**: 2026-03-12
> **Related Task**: Phase 3C-8a / 3C-8b / 3C-8c
> **Status**: ✅ 构建完成，待 iPhone 验证

---

## 1. 任务目标

Phase 3 收尾前的三个小优化 + 两个默认值调整，均在 `modify_3full.py` 上改动：

| 子任务 | 内容 | 状态 |
|--------|------|------|
| 3C-8a | 补充 prompt 默认值（自定义规则预填备注写法规则） | ✅ |
| 3C-8b | 恢复账本显示（撤销 Fix 1d，精简 gettext 只留入账账本） | ✅ |
| 3C-8c | 新增模型 5（doubao-seed-1-6-flash-250615），自定义改为 6 | ✅ |
| 额外 | 默认 max_tokens 300→1000，默认模型 1→5 | ✅ |

**最终产出**: `samples/money/3-full-deepseek.shortcut`（AEA 签名，1172 actions）

---

## 2. 3C-8a — 补充 prompt（自定义规则默认值）

### 2.1 改动

**三处修改**：

1. **gettext action `4856151E` 的 `WFTextActionText`**: 从空字符串改为备注写法规则
2. **ImportQuestions `DefaultValue`**: 同步改为备注写法规则（导入弹窗预填）
3. **ImportQuestions `Text`**: 更新描述，说明已预填默认规则
4. **comment action**: 更新自定义规则说明文本

### 2.2 默认规则文本

```
备注(remark)字段规则：简洁且表意完整，让人一眼能看明白这笔消费。网购写明平台、商家、商品（如 淘宝 xx旗舰店 数据线），信息不全只写已知部分；线下写明商户和内容（如 瑞幸 生椰拿铁）。不要捏造OCR中没有的信息。
```

### 2.3 教训

**仅改 ImportQuestions DefaultValue 不够**。ImportQuestions 只在首次导入时弹窗，action 本身的 `WFTextActionText` 必须同步写入，否则运行时读到的是空字符串。

---

## 3. 3C-8b — 恢复账本信息显示

### 3.1 改动

1. **删除 Fix 1d**: 移除 `显示记录详情` → false 的代码（action + ImportQuestions 双处）
2. **修改 gettext `5499E009`**:
   - 原文: `记录次数： ￼次 \n交易员： ￼\n入账账本： ￼ `（3 个 attachment）
   - 改为: `入账账本： ￼ `（1 个 attachment，仅保留 `{6,1}→ledger`）
3. **更新 comment**: `🗃️ 显示记录详情：是否显示操作员名称、记录次数等` → `🗃️ 显示记录详情：是否显示入账账本信息`

### 3.2 效果

- `显示记录详情` 保持原值 true → TRUE 分支执行 → 显示入账账本
- 交易员/收银员/记录次数信息已从 gettext 模板中移除
- 用户仍可通过设置 `显示记录详情=false` 来隐藏账本信息

---

## 4. 3C-8c — 新增模型选项

### 4.1 改动

1. **MODEL_MAP**: 新增第 5 条 `'5' → 'doubao-seed-1-6-flash-250615'`
2. **MC_BEGIN**: `WFNumberValue` 从 `'5'` 改为 `'6'`（编号 1-5 走内置映射，6+ 走自定义）
3. **文本更新**（三处）:
   - comment action 的 config_guide
   - ImportQuestions 的 Text（Fix 1f）
   - key_dict_guide 中的自定义模型说明

### 4.2 更新后的模型映射表

| 编号 | 模型名 |
|------|--------|
| 1 | doubao-seed-2-0-mini-260215 |
| 2 | deepseek-chat |
| 3 | doubao-seed-1-6-flash-250828 |
| 4 | deepseek-v3-2-251201 |
| 5 | doubao-seed-1-6-flash-250615（默认）|
| 6 | 其他（读取密钥字典「自定义模型」）|

---

## 5. 额外默认值调整

| 配置项 | 原默认值 | 新默认值 | 原因 |
|--------|----------|----------|------|
| max_tokens | 300 | 1000 | 300 导致响应截断，记账 JSON 需 ~800 tokens |
| 模型 | 1 | 5 | 用户偏好 doubao-seed-1-6-flash-250615 |

---

## 6. 经验教训

| 经验 | 说明 |
|------|------|
| gettext action 文本必须同步修改 | ImportQuestions DefaultValue 仅影响导入弹窗，action 本身的 WFTextActionText 才是运行时实际使用的值 |
| 精简 gettext 比改配置更灵活 | 隐藏收银员不需要把整个 conditional 块关掉，只需修改 TRUE 分支的 gettext 内容 |

---

## 7. 产出文件

| 文件 | 说明 |
|------|------|
| `tools/modify_3full.py` | 修改脚本（可重复执行，含全部 3C-2~3C-8 fix） |
| `samples/money/3-full-deepseek.xml` | 修改后 XML（1172 actions） |
| `samples/money/3-full-deepseek-unsigned.shortcut` | binary plist |
| `samples/money/3-full-deepseek.shortcut` | AEA 签名 |

---

## 8. 构建命令

```bash
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/modify_3full.py

/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py build \
    samples/money/3-full-deepseek.xml samples/money/3-full-deepseek-unsigned.shortcut
/opt/homebrew/Caskroom/miniconda/base/bin/python tools/shortcut_tool.py sign \
    samples/money/3-full-deepseek-unsigned.shortcut samples/money/3-full-deepseek.shortcut
```

---

## 9. iPhone 验证清单

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

### 额外
- [ ] max_tokens 默认 1000，响应不截断
- [ ] 默认模型为 5

---

## 10. 建议 Architect 更新

- **doc3-spec**: 补充 "修改 gettext action 内容时，ImportQuestions DefaultValue 和 action WFTextActionText 必须双写" 经验
- **doc2-current_status.md**: 3C-8 标记为 ✅ 完成
