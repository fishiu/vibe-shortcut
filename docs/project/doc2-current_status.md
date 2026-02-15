# Project Status: VibeShortcut

## 当前阶段: Phase 1 - The "Hello World" Round-Trip (进行中)
**目标**: 验证 Python 能否无损读取并重新打包 `.shortcut` 文件，确保能够导入 iOS。

### 任务清单 (Task List)
- [ ] **Task 1.1**: 手动提取一个最简单的 `.shortcut` 文件 (Reference File)。
- [ ] **Task 1.2**: 编写 `tools/dumper.py`，将 `.shortcut` 解包为 `raw.json`。
- [ ] **Task 1.3**: 编写 `tools/builder.py`，将 `raw.json` 重新打包为 `output.shortcut`。
- [ ] **Task 1.4**: 验证 `output.shortcut` 在 iPhone 上是否可运行。
- [ ] **Task 1.5 (Milestone)**: 确认二进制读写闭环无误。

### 已知问题 (Known Issues)
* (暂无)

### 下一阶段预告
* Phase 2: Cleaner & Schema Definition (清洗数据，定义 AI 可读的中间格式)
