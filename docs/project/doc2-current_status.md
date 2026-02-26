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
  - 6 个单元测试全部通过 ✅

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
* **sign() 未集成**: `shortcuts sign` 尚未封装到 shortcut_tool.py 中（Engineer 建议的后续改进）
* **网络依赖**: `shortcuts sign` 可能需要联网访问 Apple 服务器

### Phase 1 收尾任务 (进入 Phase 2 前完成)

**Architect**:
- [ ] **Task 1.6**: 更新 `doc3-spec.md` — 补充 Phase 1 实际 API 签名、XML Plist 中间格式决策、AEA 相关约束

**Engineer**:
- [ ] **Task 1.7**: 给 `shortcut_tool.py` 补充三个函数：
  1. `dump_xml(data, path)` — Python dict → XML plist 文件
  2. `load_xml(path)` — XML plist 文件 → Python dict
  3. `sign(input, output)` — 封装 `shortcuts sign -m anyone`

---

## 下一阶段: Phase 2 - Cleaner & Schema Definition (待开始)
**目标**: 清洗原始 plist 数据，定义 AI 可读/可写的精简 XML Plist 格式。

### 已具备的前置能力
- ✅ 读取任意 .shortcut 文件（含 AEA 签名）
- ✅ 解析为 Python dict（完整数据结构）
- ✅ 导出为 XML Plist（无损、人/AI 可读）
- ✅ 生成可导入 iOS 的 .shortcut 文件

### 预期任务 (待 PM/Architect 细化)
- [ ] **Task 2.1**: 实现 `tools/cleaner.py` — 移除 UI 坐标、metadata 等冗余数据，输入输出均为 XML Plist
- [ ] **Task 2.2**: 分析多个不同类型 shortcuts 的数据结构，归纳共性
- [ ] **Task 2.3**: 定义精简 XML Plist Schema — 明确哪些字段必须保留、哪些可以丢弃、哪些需要 AI 生成
- [ ] **Task 2.4**: 验证 Schema：精简后的 XML Plist 能否重建出可工作的 shortcut

### Phase 2 后续预告
* Phase 3: Builder — 从精简 XML Plist 描述生成完整的 .shortcut 文件（项目核心价值）
