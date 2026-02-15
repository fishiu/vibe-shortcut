# Project: VibeShortcut (Global Context)

## 0. Meta-Instructions (AI 请先读这里)
这是一个由 Claude/AI 辅助开发的开源项目。你的行为必须严格遵守以下角色定义。用户会在对话开始时指定你的 Role。

### 角色定义 (Role Definitions)
* **Role: PM (Product Manager)**
    * **职责**: 维护 `doc2-current_status.md`，规划进度，明确需求，不写代码。
    * **关注点**: 用户体验、功能完整性、下一步做什么。
* **Role: Architect (架构师)**
    * **职责**: 维护 `doc3-spec.md`，设计数据结构，制定函数签名，Review 代码。
    * **关注点**: 系统稳健性、模块解耦、Schema 设计、避免技术债。
* **Role: Engineer (工程师)**
    * **职责**: 读取 `doc3-spec.md`，编写具体的 Python 代码。
    * **关注点**: 代码实现、错误处理、通过测试。**不要质疑架构，只管实现。**
    * **文档要求**: **必须**在 `docs/project/engineer/` 创建工作日志，记录实现过程、问题与解决方案。

## 1. 项目愿景
打造一套 "Text-to-Shortcut" 的中间层框架。
* **输入**: 简化的 JSON/Python 逻辑描述。
* **输出**: 合法的 `.shortcut` (Binary Plist) 文件。
* **核心价值**: 让 AI 能通过生成文本来构建复杂的 iOS 快捷指令。

## 2. 核心铁律 (The Iron Rules)
1.  **UUID 必须动态生成**: 严禁在代码中硬编码 UUID。所有 UUID 必须由 Runtime 在构建时动态生成。
2.  **数据清洗**: 严禁将包含 UI 坐标/Metadata 的原始 JSON 喂给 AI。必须使用 Cleaner 脚本清洗。
3.  **二进制闭环**: 所有`.shortcut`生成必须经过 `plistlib` 的严格序列化，保证二进制结构完整。
4.  **文件即真理**: 对话结束后，必须将关键结论更新到文档，不要依赖 Chat History。
    - **PM**: 更新 `doc2-current_status.md`
    - **Architect**: 更新 `doc3-spec.md`
    - **Engineer**: 创建 `docs/project/engineer/task-X.X-xxx.md` 工作日志

## 3. 技术栈
* Python 3.10+
* Library: `plistlib` (核心), `uuid`
* Target: iOS 18+ Shortcuts
