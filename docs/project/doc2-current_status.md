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

## 下一阶段: Phase 2 - 读懂 Shortcuts，产出编程手册 (待开始)
**目标**: 逐步分析真实 shortcuts（从简单到复杂），理解其结构和 action 用法，沉淀为一份 AI/人类均可读的 Shortcuts 编程手册。

### 核心思路
- **纯分析，不改动** — 只读懂，不修改
- **手册是过程产物** — 边分析边记录，不是先设计格式再填内容
- **从具体到抽象** — 三个真实记账 shortcut 由简到难，逐步积累
- **手册格式**: Markdown + XML 代码块，人能检查、AI 能消费（未来可拆为 skills）

### 样本计划
| 样本 | 文件 | Actions | 独立类型 | 特点 | 状态 |
|------|------|---------|----------|------|------|
| Sample A | `samples/money/1-reg.shortcut` | 26 | ~8 种 | OCR + 正则匹配 | ✅ 已到位 |
| Sample B | `samples/money/2-api.shortcut` | 46 | ~15 种 | OCR + DeepSeek API 解析 | ✅ 已到位 |
| Sample C | `samples/money/3-full.shortcut` | 1140 | 44 种 | 完全体记账工具 | ✅ 已到位 |

**备注**: 三个样本均包含第三方 action `com.gostraight.smallAccountBook.*`（记账 App 的 SiriKit Intent）。

### 任务清单
**Round A — 简单样本 (OCR + 正则)**
- [x] **Task 2.1**: 用户提供 Sample A 文件
- [ ] **Task 2.2**: decode → dump_xml，列出完整 action 列表和数据流
- [ ] **Task 2.3**: 逐个标注 action 的作用、参数含义、输入输出关系
- [ ] **Task 2.4**: 产出手册 v0.1 — 覆盖 Sample A 涉及的 action 类型

**Round B — 中等样本 (OCR + DeepSeek)**
- [x] **Task 2.5**: 用户提供 Sample B 文件
- [ ] **Task 2.6**: 分析新增的 action 类型（API 调用、JSON 解析等）
- [ ] **Task 2.7**: 更新手册 v0.2 — 补充新 action，归纳共性模式

**Round C — 复杂样本 (完全体)**
- [x] **Task 2.8**: 用户提供 Sample C 文件
- [ ] **Task 2.9**: 分析复杂控制流（条件、循环、变量传递、错误处理等）
- [ ] **Task 2.10**: 更新手册 v0.3 — 补充高级模式，形成较完整的参考手册

### Phase 2 Milestone
**能用手册向一个不了解 shortcuts 内部格式的 AI 解释清楚这三个样本在做什么。**

---

## 后续阶段预告

### Phase 3 - 改动 Shortcuts
**目标**: 基于 Phase 2 的理解，实际修改现有 shortcut（如去掉 OCR 云服务依赖）。
- 验证手册的实用性：AI 能否根据手册指导完成改动
- encode → sign → iPhone 验证改动后可运行

### Phase 4 - AI 生成 Shortcuts
**目标**: AI 根据手册从零生成可工作的 shortcut。
- 手册拆为 skills，按需加载
- 端到端：自然语言 → AI 生成 XML plist → 工具链 → 可导入 iOS
