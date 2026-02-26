# Technical Specifications

> 注意：本文件由 Architect 角色维护。Engineer 在编写代码前必须阅读此文件。

## 0. Development Environment

### 0.1 Python Environment
- **Python Version**: 3.10+ (Current: 3.10.9)
- **Environment Manager**: Conda
- **Environment Name**: `tool`

### 0.2 Activation Command
```bash
# macOS/Linux
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate tool
```

### 0.3 Dependencies Installation
```bash
# Install development dependencies
pip install -r requirements.txt

# Or minimal install (core functionality only uses stdlib)
pip install pytest pytest-cov
```

### 0.4 Core Libraries (Standard Library - No Installation Required)
- `plistlib`: Binary/XML plist serialization/deserialization
- `struct`: 解析 AEA 容器中的二进制偏移量
- `subprocess`: 调用 macOS 系统工具 (compression_tool, aa, shortcuts)
- `tempfile`: AEA 解包过程中的临时文件管理
- `pathlib`: File path operations
- `uuid`: UUID generation (Phase 2+)

### 0.5 Philosophy: Minimal Dependencies
**Critical Constraint**: 核心功能 (dumper, builder, cleaner) 仅依赖 Python 标准库。
- ✅ 确保工具的可移植性和稳定性
- ✅ 避免依赖地狱（Dependency Hell）
- ⚠️ 仅在测试/开发工具中使用第三方库

---

## 1. File Structure

### 1.1 Project Layout
```
vibe-shortcut/
├── docs/
│   └── project/
│       ├── doc0-initial.md              # 项目愿景
│       ├── doc1-context.md              # 全局上下文（角色定义）
│       ├── doc2-current_status.md       # PM 维护的进度跟踪
│       ├── doc3-spec.md                 # Architect 维护的技术规范 (本文件)
│       └── engineer/                    # Engineer 工作日志目录
│           ├── template.md              # 标准模板
│           └── task-*.md                # 各任务实现日志
├── tools/
│   ├── shortcut_tool.py                 # 核心模块: decode/encode/verify_roundtrip
│   └── cleaner.py                       # 数据清洗 (Phase 2)
├── tests/
│   ├── test_shortcut_tool.py            # shortcut_tool 单元测试
│   └── test_aea_extraction.py           # AEA 解包测试
├── samples/
│   ├── demo-notification.shortcut       # 参考文件 (AEA 签名, 22KB)
│   └── official-signed.shortcut         # 工具链产出的签名文件
├── requirements.txt                     # Python 依赖
└── .gitignore
```

> **架构偏差说明**: 原计划 `dumper.py` + `builder.py` 合并为 `shortcut_tool.py`。
> 原因：功能简单，拆分两个文件无实际意义。

### 1.2 Engineer 文档规范
- **位置**: `docs/project/engineer/task-{编号}-{描述}.md`
- **模板**: 参考 `engineer/template.md`
- **强制要求**: 每个 Task 完成后必须创建对应日志
- **内容**: 实现思路、遇到的问题、解决方案、产出文件列表

---

(待定 - 将在 Phase 1 实现后补充)

## 2. JSON Schema (Intermediate Representation)
(待定)

## 3. API Signatures
(待定)
