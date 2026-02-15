# Project: Vibe Coding for Apple Shortcuts (Project "VibeShortcut")

## 1. 愿景与目标 (Vision)
**核心目标**：打造一套 "Text-to-Shortcut" 的开发框架/中间层，解决 Apple 快捷指令（Shortcuts）无法高效进行 AI 辅助编程（Vibe Coding）的问题。

**痛点分析**：
1.  **黑盒与低代码**：目前的 `.shortcut` 文件是二进制 plist，且开发依赖 UI 拖拽，无法进行文本化版本控制或 AI 生成。
2.  **语料缺失**：缺乏公开的文本化语料，LLM 无法理解 Shortcut 的内部逻辑结构。
3.  **调试困难**：无法在电脑端完成“代码 -> 运行”的闭环。

**最终形态**：
用户（或 AI）编写/生成简化的逻辑描述（JSON/Python），通过本框架编译为合法的 `.shortcut` 文件，直接导入 iOS/macOS 运行。

## 2. 技术路线 (Technical Architecture)

我们**不**重新发明一种 DSL（领域特定语言），而是采用 **"Reverse Engineering & Recompilation"**（逆向与重编译）策略。

### 核心流程：
1.  **Decompile (逆向)**：`.shortcut` (Binary Plist) -> `Raw Dict` -> **`Clean JSON`** (去除 UI/Metadata 噪音)。
2.  **Vibe (生成)**：AI 根据用户需求，基于 `Clean JSON` 的 Schema 生成逻辑片段。
3.  **Compile (编译)**：`Clean JSON` -> **`Builder (Python)`** -> 注入 UUID/控制流 -> `Binary Plist` -> `.shortcut`。

### 关键组件：
* **Cleaner**: 清洗脚本。从原始 Plist 中剥离 `WFWorkflowIcon`、`is.workflow.actions.document` 等非逻辑数据，提取纯粹的 Action ID 和 Parameters。
* **Action Registry**: 通过分析大量 Shortcut 文件构建的“动作字典”（即 MCP 的 Tool Definition），让 AI 知道有哪些动作可用。
* **Graph Builder**: 处理 Shortcut 最复杂的 UUID 引用关系（DAG 图结构），确保变量传递正确。

## 3. 核心风险与工程陷阱 (Critical Pitfalls)

**Claude 请注意，以下是前序分析中识别出的“必死”陷阱，开发时必须极度小心：**

1.  **Context 污染**：原始 Shortcut JSON 包含 90% 的 UI 布局噪音。直接喂给 LLM 会导致幻觉。**必须严格清洗数据。**
2.  **UUID 地狱**：Shortcut 的变量传递依赖 UUID（`WFSerializationRecord`）。这是图结构而非树结构。**绝对不能让 LLM 手写 UUID**，必须由 Python Runtime 动态生成并管理连接。
3.  **二进制兼容性**：`.shortcut` 本质是 `bplist`。必须使用 Python 的 `plistlib` 严格处理二进制转换，且需注意 iOS 的导入签名限制（虽然本地导入通常只需要结构合法）。

## 4. 执行计划：曳光弹策略 (Tracer Bullet)

我们需要遵循 **Fail Fast** 原则，先验证最小闭环。

**Phase 1: The "Hello World" Round-Trip (当前阶段)**
* **目标**：不涉及 AI 生成，仅验证 Python 脚本能否无损（或逻辑无损）地处理 `.shortcut` 文件。
* **任务**：
    1.  读取一个最简单的 `.shortcut` (例如只有“震动”一个动作)。
    2.  解包为 JSON。
    3.  重新打包为 `.shortcut`。
    4.  验证重新打包的文件能否在设备上打开。

**Phase 2: Schema & Registry**
* 定义 `Clean JSON` 的结构。
* 批量扫描 Shortcut 文件，建立 Action 数据库。

**Phase 3: The Builder**
* 编写 Python 类，实现 `add_action()`, `link_variable()` 等方法。

---
*Created via initial brainstorming session. This document serves as the Source of Truth for the project context.*
