# Project Status: VibeShortcut

## 当前阶段: Phase 1 - The "Hello World" Round-Trip (✅ 已完成)
**目标**: 验证 Python 能否无损读取并重新打包 `.shortcut` 文件，确保能够导入 iOS。

### 任务清单 (Task List)
- [x] **Task 1.1**: 手动提取一个最简单的 `.shortcut` 文件 (Reference File)。
  - 产出: `samples/demo-notification.shortcut` (22KB, AEA 签名格式)
- [x] **Task 1.2**: 实现 `decode()` — 将 `.shortcut` 解包为 Python dict。
  - 产出: `tools/shortcut_tool.py` 中的 `decode()` 函数
  - 重要发现: iOS 15+ 的 .shortcut 使用 AEA (Apple Encrypted Archive) 签名包装，非纯 plist
  - 已实现自动检测 AEA/plist 两种格式
- [x] **Task 1.3**: 实现 `encode()` — 将 Python dict 重新打包为 `.shortcut` 文件。
  - 产出: `tools/shortcut_tool.py` 中的 `encode()` + `verify_roundtrip()`
  - 验证结果: plistlib 无损转换 ✅
- [x] **Task 1.4**: 验证 `output.shortcut` 在 iPhone 上是否可运行。
  - 关键发现: 未签名 plist 无法导入 iOS (系统强制要求 AEA 签名)
  - **解决方案**: 使用 macOS 自带 `/usr/bin/shortcuts sign -m anyone` 命令进行官方签名
  - 产出: `samples/official-signed.shortcut` — iPhone 导入成功并正常运行 ✅
- [x] **Task 1.5 (Milestone)**: 确认二进制读写闭环无误。
  - decode → encode → sign → import to iPhone: 全链路验证通过 ✅
  - `verify_roundtrip()` 数据一致性: 通过 ✅
  - 10 个单元测试全部通过 ✅

### 架构偏差说明
原计划: 分离的 `tools/dumper.py` + `tools/builder.py`
实际实现: 合并为 `tools/shortcut_tool.py`（含 decode/encode/verify_roundtrip 三个函数）
**原因**: 功能简单，拆分两个文件无实际意义，合并更清晰。

### 关键技术决策 (Phase 1 总结)

#### 决策 1: 持久化中间格式 — XML Plist
**结论**: 使用 **XML Plist** 作为无损持久化中间层。
**理由**: .shortcut 的核心数据本质就是 plist。XML plist 只是 binary plist 的人类可读写法，数据零损耗。`plistlib` 原生支持 `FMT_XML`，一行代码切换。JSON 不可行（丢失 datetime 和 binary 类型）。

#### 技术发现
1. **AEA 格式**: iOS 15+ 的 .shortcut 文件并非纯 plist，而是 AEA 签名容器。内部结构: AEA1 → LZFSE 压缩 → Apple Archive → Shortcut.wflow (plist)
2. **签名是强制的**: iOS 拒绝导入未签名文件，macOS 对自签名文件会闪退
3. **官方工具**: `shortcuts sign -m anyone` 是唯一可靠的签名方式（使用用户的 Apple ID 证书链）
4. **文件大小差异**: 未签名 plist ~1.3KB vs 签名后 AEA ~22KB（证书链占主要体积）
5. **macOS 依赖**: 当前工具链依赖 macOS 系统工具 (compression_tool, aa, shortcuts)

### 完整工具链
```
.shortcut (AEA签名)
  → decode() → Python dict → dump(FMT_XML) → .xml (人/AI可读，无损中间层)
  → 编辑/清洗/AI生成
  → load(.xml) → Python dict → encode(FMT_BINARY) → .shortcut (未签名)
  → shortcuts sign → .shortcut (AEA签名，可导入 iOS)
```

### 已知问题 (Known Issues)
* **macOS Only**: AEA 解包和签名功能仅在 macOS 上可用（依赖 compression_tool, aa, shortcuts 工具）
* **网络依赖**: `shortcuts sign` 可能需要联网访问 Apple 服务器

### Phase 1 收尾任务 (✅ 已完成)

**Architect**:
- [x] **Task 1.6**: 更新 `doc3-spec.md` — 补充实际项目结构、核心库、架构偏差说明

**Engineer**:
- [x] **Task 1.7**: 给 `shortcut_tool.py` 补充三个函数 + CLI 子命令：
  1. `dump_xml(data, path)` — Python dict → XML plist 文件
  2. `load_xml(path)` — XML plist 文件 → Python dict
  3. `sign(input, output)` — 封装 `shortcuts sign -m anyone`
  - 额外产出: CLI `pipeline` 命令（decode→xml→build→sign 一键完成）
  - 测试: 10/10 通过

---

## Phase 2 - 读懂 Shortcuts，产出编程手册 (✅ 已完成)
**目标**: 逐步分析真实 shortcuts（从简单到复杂），理解其结构和 action 用法，沉淀为一份 AI/人类均可读的 Shortcuts 编程手册。

### 核心思路
- **纯分析，不改动** — 只读懂，不修改
- **手册是过程产物** — 边分析边记录，不是先设计格式再填内容
- **从具体到抽象** — 三个真实记账 shortcut 由简到难，逐步积累
- **手册格式**: Markdown + XML 代码块，人能检查、AI 能消费（未来可拆为 skills）

### 样本计划
| 样本 | 文件 | Actions | 独立类型 | 特点 | 状态 |
|------|------|---------|----------|------|------|
| Sample A | `samples/money/1-reg.shortcut` | 26 | ~8 种 | OCR + 正则匹配 | ✅ 分析完成 |
| Sample B | `samples/money/2-api.shortcut` | 46 | ~15 种 | OCR + DeepSeek API 解析 | ✅ 分析完成 |
| Sample C | `samples/money/3-full.shortcut` | 1140 | 44 种 | 完全体记账工具 | ✅ 分析完成 |

### 任务清单
**Round A — 简单样本 (OCR + 正则)**
- [x] **Task 2.1**: 用户提供 Sample A 文件
- [x] **Task 2.2**: decode → dump_xml，列出完整 action 列表和数据流
- [x] **Task 2.3**: 逐个标注 action 的作用、参数含义、输入输出关系
- [x] **Task 2.4**: 产出手册 v0.1 — 覆盖 11 种 action 类型 (869 行)

**Round B — 中等样本 (OCR + DeepSeek)**
- [x] **Task 2.5**: 用户提供 Sample B 文件
- [x] **Task 2.6**: 分析 7 种新增 action 类型（dictionary, downloadurl, detect.dictionary 等）
- [x] **Task 2.7**: 产出手册 v0.2 — 24 种 action，6 种常用模式 (1226 行)

**Round C — 复杂样本 (完全体)**
- [x] **Task 2.8**: 用户提供 Sample C 文件
- [x] **Task 2.9**: 分析 22 种新增 action（循环、数学运算、图片处理等）
- [x] **Task 2.10**: 产出手册 v0.3 — 46 种 action，9 种常用模式 (1914 行)

### Phase 2 Milestone ✅ 达成
**能用手册向一个不了解 shortcuts 内部格式的 AI 解释清楚这三个样本在做什么。**

### 手册迭代记录
| 版本 | 文件 | Action 类型 | 常用模式 | 行数 |
|------|------|:-----------:|:--------:|:----:|
| v0.1 | `docs/shortcuts-manual-v0.1.md` | 11 | 3 | 869 |
| v0.2 | `docs/shortcuts-manual-v0.2.md` | 24 | 6 | 1226 |
| **v0.3** | **`docs/shortcuts-manual-v0.3.md`** | **46** | **9** | **1914** |

### Phase 2 关键技术发现
1. **四种序列化类型**: WFTextTokenAttachment, WFTextTokenString, WFDictionaryFieldValue, WFContentPredicateTableTemplate
2. **四种控制流结构**: conditional, choosefrommenu, repeat.count, repeat.each — 共用 GroupingIdentifier + WFControlFlowMode 模式
3. **WFCondition=100**: "Has Any Value"，用于检查变量是否非空
4. **WFItemType 无 2**: 已知值为 0(Text), 1(Dict), 3(Number), 4(Bool), 5(Array)
5. **第三方 Action**: 通过 AppIntentDescriptor 声明 App 信息，参数名由 App 定义

---

---

## Phase 3 - 化整为零，逐步集成 (🔜 进行中)

**策略**: 不直接改 3-full，先从零搭三个独立小 shortcut，验证每个模块可独立运行，再考虑集成。

| 子任务 | 目标 | 状态 |
|--------|------|------|
| **3A** 本地 OCR | 截图 → OCR → 通知输出 | ✅ 完成 |
| **3B** DeepSeek 请求 | 文本输入 → API → 通知输出 | ✅ 完成 |
| **3C-1** OCR+DeepSeek 合体 | 截图 → OCR → DeepSeek JSON → 通知 | ✅ 完成 |
| **3C-2** 替换 icost.vip | 3-full 中 icost.vip → DeepSeek，保持下游不变 | ✅ 初步通过 |
| **3C-3** 精修：界面风格 + 时间精度 | 默认界面风格 3→1；CurrentDate 加时分 | 🔜 进行中 |

---

### 3A — 本地 OCR Shortcut（从零构建）

**目标**: AI 根据手册手写 XML plist，工具链打包签名，iPhone 可运行。

**流程**: `takescreenshot → extracttextfromimage → notification`

**Done 定义**: 导入 iPhone，运行后截图识别结果出现在通知里。

**参考手册**: §6.1 takescreenshot、§6.2 extracttextfromimage、§6.5 notification、§9.8 模式 H

#### 任务清单

**Architect**:
- [x] **Task 3.1**: 设计 OCR shortcut 的完整 XML 骨架
  - 明确三个 action 的参数结构
  - 明确 UUID 引用关系（截图输出 → OCR 输入 → 通知输入）
  - 产出：`doc3-spec.md` §5，含完整 XML 模板 + 关键设计决策表 ✅

**Engineer**:
- [x] **Task 3.2**: 按 Architect 规范手写 XML plist
  - 产出：`samples/ocr-local/ocr-local.xml` ✅
- [x] **Task 3.3**: build → sign → iPhone 验证
  - 产出：`samples/ocr-local/ocr-local.shortcut`（AEA 签名，22KB）✅
  - 验证：iPhone 导入运行，通知显示 OCR 结果 ✅
  - 发现：conda `tool` 环境不存在，实际用 base Python 3.13，需 Architect 更新 doc3-spec.md §0.1

---

### 3B — DeepSeek 请求 Shortcut（从零构建）

**目标**: 独立验证 DeepSeek API 调用链路，不依赖 3A。

**流程**: `ask → text(构建请求体) → downloadurl → 解析 choices[0].message.content → notification`

**配置**: Import Questions（api_key + base_url，导入时由用户填写，不硬编码）

**Done 定义**: iPhone 上输入一句话，通知显示 DeepSeek 的回复。

**参考手册**: §5.1 downloadurl、§9.5 模式 E、§9.9 模式 I

#### 任务清单

**Architect**:
- [x] **Task 3.4**: 设计 DeepSeek shortcut 的完整 XML 骨架
  - 产出：`doc3-spec.md §6`，8 action 链路 + UUID 引用关系 + 字符位置计算 ✅

**Engineer**:
- [x] **Task 3.5**: 按规范手写 XML plist
  - 产出：`samples/deepseek-api/deepseek-api.xml`（13.5KB，8 action）✅
- [x] **Task 3.6**: build → sign → iPhone 验证
  - 产出：`samples/deepseek-api/deepseek-api.shortcut`（AEA 签名，23KB）✅
  - 验证：iPhone 输入文本，通知显示 DeepSeek 回复 ✅
  - 安全提醒：XML 含 API Key 占位符，替换真实 key 后勿 commit；`*.shortcut` 已在 `.gitignore`

---

---

### 3C-1 — OCR + DeepSeek 合体（截图记账 JSON）

**目标**: 将 3A、3B 合并为单一 shortcut，截图后自动 OCR 并调用 DeepSeek 输出记账 JSON，通知显示结果。

**流程**:
```
takescreenshot → extracttextfromimage → text(拼接 prompt + OCR 结果)
  → downloadurl(DeepSeek POST) → 解析 choices[0].message.content → notification
```

**与 3B 的关键差异**:
- 去掉 `ask` action，改用 OCR 输出作为 DeepSeek 输入
- 请求体中加入 system prompt，要求输出记账 JSON

**DeepSeek Prompt**:
```
你是记账助手。从以下文字中提取记账信息，只返回 JSON，不输出任何其他内容：
{"item": "商品名称", "amount": 金额数字}
如果有多笔，返回数组：[{"item": "...", "amount": ...}, ...]
无法识别时返回：{"item": "未知", "amount": 0}

文字内容：
```

**Done 定义**: iPhone 截图后，通知显示 `{"item": "xxx", "amount": 0.00}` 格式的 JSON。

**参考**: `doc3-spec.md §5`（OCR 链路）、`§6`（DeepSeek 链路）

#### 任务清单

**Architect**:
- [x] **Task 3.7**: 设计合体 shortcut 的 XML 骨架
  - 产出：`docs/project/architect/task-3c1-ocr-deepseek.md`

**Engineer**:
- [x] **Task 3.8**: 按规范手写 XML plist
  - 产出：`samples/ocr-deepseek/ocr-deepseek.xml`
- [x] **Task 3.9**: build → sign → iPhone 验证
  - 产出：`samples/ocr-deepseek/ocr-deepseek.shortcut`
  - 日志：`docs/project/engineer/task-3c1-ocr-deepseek.md`
  - 验证：截图后通知显示记账 JSON ✅

---

---

### 3C-2 — 替换 3-full 的 icost.vip 请求

**目标**: 在 `3-full.xml` 中外科手术式替换 `icost.vip/wapi/v1/chat` 调用为 DeepSeek，保持下游逻辑不变。

**核心策略**: prompt 让 DeepSeek 返回与 icost.vip `detail` 字段完全相同的 JSON 结构，下游 `getvalueforkey` 链路无需改动。

**Done 定义**: 修改后的 3-full 导入 iPhone，记账流程正常运行。

#### 任务清单

**Architect**:
- [x] **Task 3.10**: 分析 `3-full.xml` 中 icost.vip/chat 的接口
  - 完整逆向工程 icost.vip 请求/响应结构（7 个 v-field 附件、detail JSON 结构）
  - 设计 DeepSeek 替换方案：8 个 prompt 占位符（日期/分类/账户/标签/自定义规则/OCR文本）
  - 产出：`docs/project/architect/task-3c2-replace-icost.md`（1065 行）

**Engineer**:
- [x] **Task 3.11**: 在 `3-full.xml` 中做外科替换，build → sign → iPhone 验证
  - 实现：`tools/modify_3full.py`（Python 脚本操作 plist dict，可重复执行）
  - 产出：`samples/money/3-full-deepseek.xml`（1146 actions，净增 6）+ `.shortcut`（AEA 签名，101.9 KB）
  - 日志：`docs/project/engineer/task-3c2-replace-icost.md`
  - 验证：iPhone 基础记账功能正常，细节待打磨

---

### 3C-3 — 精修：界面风格 + 时间精度

**背景**: 3C-2 初步通过后发现两个问题，均为 `modify_3full.py` 的参数配置问题，不涉及架构变更。

#### 问题 1：界面风格默认简易风格（缺少"不记录"和"改类别"功能）

**根因**: `3-full.xml` 配置 dict（UUID `588A56AF`）的 `界面风格` 默认值为 `3`（简易风格）。简易风格不支持跳过单笔记录和直接改类别，而用户的 3-full 手机版已手动改为风格 1（小票风格）。`modify_3full.py` 未修改该配置，导致 3-full-deepseek 沿用默认值 3。

**修复**: 在 `modify_3full.py` 中增加一步，将 `界面风格` 从 `3` 改为 `1`（小票风格，功能最全）。

#### 问题 2：时间精度不够（只有日期，没有时分）

**根因**: `modify_3full.py` 中 CurrentDate 的 aggrandizement 使用 `yyyy-MM-dd` 格式且 `WFISO8601IncludeTime: False`，导致传给 DeepSeek 的日期无时间信息，DeepSeek 返回的 `date` 字段也只有日期，iCost 记录时无时分。

**修复**: 将格式改为 `yyyy-MM-dd HH:mm`，启用 `WFISO8601IncludeTime: True`，同时更新 TEMPLATE 中的 date 格式说明。

#### 任务清单

**Engineer**:
- [ ] **Task 3.12**: 修改 `modify_3full.py`，rebuild → sign → iPhone 验证
  - Fix 1: 找到 UUID `588A56AF` 对应的 dictionary action，将 `界面风格` 值从 `"3"` 改为 `"1"`
  - Fix 2: 将 A2 的 CurrentDate aggrandizement `WFDateFormat` 改为 `"yyyy-MM-dd HH:mm"`，`WFISO8601IncludeTime` 改为 `True`；更新 TEMPLATE 中 `date` 字段格式说明为 `"YYYY-MM-DD HH:mm"`
  - 重新运行 `modify_3full.py` → build → sign → iPhone 验证
  - 验证要点：① 运行后出现小票风格预览界面 ② 预览界面含"不记录此条账单"选项 ③ 含改类别入口 ④ 记录后 iCost 时间精确到分钟

**Done 定义**: 导入 iPhone，记账流程与用户原 3-full（风格 1）体验一致；记录时间精确到分钟。

---

### Phase 4 - AI 生成 Shortcuts（待规划）
**目标**: AI 根据手册从零生成可工作的 shortcut。
- 手册拆为 skills，按需加载
- 端到端：自然语言 → AI 生成 XML plist → 工具链 → 可导入 iOS
