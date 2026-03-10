# Engineer Log: Task 3B - DeepSeek API Shortcut 从零构建

> **Date**: 2026-03-10
> **Related Task**: Phase 3B — DeepSeek API Shortcut
> **Status**: 🟢 Completed (待 iPhone 验证)

---

## 1. 任务目标

按 Architect 设计的 XML 骨架（doc3-spec.md §6），手写 DeepSeek API shortcut 的 XML plist，通过工具链 build + sign 产出可导入 iOS 的 `.shortcut` 文件。

**验收标准**:
- [x] `samples/deepseek-api/deepseek-api.xml` 存在，7 个 UUID 为动态生成
- [x] `samples/deepseek-api/deepseek-api.shortcut` 存在，AEA1 签名格式
- [ ] iPhone 导入后运行，通知标题 "DeepSeek"，body 为 AI 回答
- [ ] 用户需替换 `sk-REPLACE-WITH-REAL-KEY` 为真实 API Key

---

## 2. 技术方案

### 2.1 设计思路
完全遵循 Architect 在 doc3-spec.md §6.3 的 XML 模板，8 个 action 的完整数据流。

### 2.2 Action 链路 (8 个 action, 7 个 UUID)
```
A: gettext (API Key)        → 779A5B1A-29A9-42FF-BADA-70143092EA91
B: ask (用户输入)            → 3BF2C20A-2929-412C-8729-259A3392815F
C: gettext (JSON body)       → B4A11CAB-48B0-4D7E-B8D9-51FD11CF1B94
   ← 引用 UUID-B (用户输入嵌入 content 字段, 位置 {63,1})
D: downloadurl (POST API)   → E9F4CFA7-63BA-4E63-ADBC-769C27116766
   ← 引用 UUID-A (Bearer token, 位置 {7,1}), UUID-C (body)
E: getvalueforkey (choices)  → 00736E38-0762-4F41-8A0C-CA3D8B95A8D0
   ← 引用 UUID-D
F: getitemfromlist ([0])     → 8B809760-33C7-4CF9-A426-A8DD683A52D8
   ← 引用 UUID-E
G: getvalueforkey (message.content) → 517A3557-0C2C-4CC8-BC32-44A9D4511E86
   ← 引用 UUID-F
H: notification              → 无 UUID (终端 action)
   ← 引用 UUID-G
```

---

## 3. 实现过程

### 3.1 关键点
- **API Key 占位符**: `sk-REPLACE-WITH-REAL-KEY`，用户导入后需手动编辑替换
- **JSON body 位置计算**: `{63, 1}` — Architect 已在 §6.5 验证
- **Authorization header**: `Bearer ￼` 中 ￼ 在位置 `{7, 1}`
- **HTTP Body 类型**: `File`（非 `JSON`），body 由 gettext 预构建为 JSON 字符串

### 3.2 环境
- 使用 conda base Python 3.13（`/opt/homebrew/Caskroom/miniconda/base/bin/python`）

---

## 4. 测试验证

### 4.1 构建验证
```bash
# Build → 2.5KB unsigned binary plist
# Sign  → 23KB AEA 签名
# AEA1 header 确认 ✅
```

---

## 5. 产出文件

- `samples/deepseek-api/deepseek-api.xml`: 手写 XML plist，8 个 action (13.5KB)
- `samples/deepseek-api/deepseek-api-unsigned.shortcut`: binary plist 中间产物 (2.5KB)
- `samples/deepseek-api/deepseek-api.shortcut`: AEA 签名，可导入 iOS (23KB)

---

## 6. 遗留问题
- [ ] 待 iPhone 实机验证
- [ ] API Key 需替换为真实 key
- [ ] `.shortcut` 文件含明文 API Key，不应 commit 到 git

---

## 7. 安全提醒
Architect §6.6 明确：`.shortcut` 文件包含明文 API Key，**不要** commit 到 git。建议在 `.gitignore` 中排除 `samples/deepseek-api/*.shortcut`，或提交前清除 key。
