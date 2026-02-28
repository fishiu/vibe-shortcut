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
│   ├── demo-notification.shortcut       # Phase 1 参考文件 (AEA 签名, 22KB)
│   └── money/                           # Phase 2 记账 shortcut 样本
│       ├── 1-reg.shortcut               # Sample A: OCR + 正则 (26 actions)
│       ├── 1-reg.xml                    # Sample A XML 导出
│       ├── 2-api.shortcut               # Sample B: OCR + DeepSeek API (46 actions)
│       └── 3-full.shortcut              # Sample C: 完全体 (1140 actions)
├── docs/
│   └── shortcuts-manual-v0.1.md         # Shortcuts 编程手册 (Phase 2 产出)
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

## 2. Intermediate Format: XML Plist

### 2.1 Design Decision
**中间格式选择 XML Plist，而非 JSON。**

| 维度 | JSON | XML Plist |
|------|------|-----------|
| datetime 类型 | ❌ 丢失（需自定义序列化） | ✅ 原生 `<date>` 标签 |
| binary 类型 | ❌ 丢失（需 Base64 workaround） | ✅ 原生 `<data>` 标签 |
| 与 .shortcut 的关系 | 需要额外转换层 | 同源格式，零损耗 |
| plistlib 支持 | 需额外 json.dumps | `FMT_XML` 一行切换 |
| 人类可读 | ✅ | ✅ |
| AI 可读/可写 | ✅ | ✅ |

### 2.2 Data Pipeline
```
[Input]  .shortcut (AEA signed, binary)
    ↓ decode()          — AEA 解包 + plist 反序列化
[Memory] Python dict     — 内存中的完整数据结构
    ↓ dump_xml()        — plistlib.dump(FMT_XML)
[Disk]   .xml            — 无损中间层，人/AI 可读写
    ↓ (编辑 / 清洗 / AI 生成)
    ↓ load_xml()        — plistlib.load()
[Memory] Python dict
    ↓ encode()          — plistlib.dump(FMT_BINARY)
[Disk]   .shortcut       — 未签名 binary plist
    ↓ sign()            — shortcuts sign -m anyone
[Output] .shortcut       — AEA 签名，可导入 iOS
```

### 2.3 Shortcuts 编程手册
Phase 2 的核心产出是 `docs/shortcuts-manual-v{version}.md`，记录了 Shortcuts XML Plist 的完整格式规范：
- 文件结构、值传递机制、控制流
- Action 参数参考（含完整 XML 代码示例）
- 可复用的编程模式

手册按 Round A/B/C 增量更新，版本号对应覆盖范围：
- **v0.1**: 11 种 action (Sample A: OCR + 正则) ✅
- **v0.2**: 24 种 action (+ Sample B: API 调用) ✅
- **v0.3**: 预计 ~44 种 action (+ Sample C: 完全体)

### 2.4 已验证项 (Architect Review 结论)
- ✅ `WFCondition=0` 确认为"等于" (Round B 交叉验证)
- ✅ **conditional 分支方向已确认**: BEGIN→ELSE 之间是 **true 分支**，ELSE→END 之间是 **false 分支**
- ⚠️ `WFCondition=4` (≥) 仍仅 Round A 一个样本，Round C 继续观察

### 2.5 Architect 指导: Round C 注意事项

> **以下内容是给 Round C Engineer 的指导，执行前请阅读。**

#### 2.5.1 Sample C 规模预警
Sample C 有 **1140 actions, 44 种 action 类型**，比 Sample B 多 ~20 种新 action。不要试图用单个分析文档覆盖全部 1140 actions 的执行顺序表——按业务模块分段分析即可。

#### 2.5.2 预期新增的 action 类型
根据"完全体记账工具"的功能推测，Round C 可能遇到：
- **循环**: `repeat` / `repeat.each` — WFControlFlowMode 的第三种应用场景，记录其与 conditional/menu 的结构差异
- **数学运算**: `math` — 关注 WFMathOperation 参数的可选值
- **日期处理**: `date`, `format.date`, `adjustdate`
- **文本操作**: `text.split`, `text.combine`, `gettype`
- **错误处理**: 如果存在 try/catch 机制，这是架构上的重要发现

#### 2.5.3 需要验证的遗留项
- `WFCondition=4` 的含义（Round A 标注为 ≥，但只有一个样本）— 如果 Sample C 中有使用 WFCondition=4 的场景，请用业务逻辑反推验证
- `WFItemType` 的其他值 — Round B 仅观察到 `0=Text`，Sample C 可能有更多类型

#### 2.5.4 手册结构建议
v0.3 预计 2000+ 行。Round C 期间保持单文件 `shortcuts-manual-v0.3.md`。如果最终超过 2500 行，Architect 会在 Phase 3 开始前将其拆分为：
```
docs/
├── shortcuts-manual.md              # 核心概念 (文件结构、值传递、控制流、模式、生成清单)
└── shortcuts-actions/               # Action 参考（按类别拆分）
    ├── data-processing.md
    ├── network.md
    ├── interaction.md
    ├── control-flow.md
    └── third-party.md
```
**Round C Engineer 不需要做拆分**，正常写 v0.3 单文件即可。

---

## 3. API Signatures

### 3.1 Module: `tools/shortcut_tool.py`

#### 已实现 (Phase 1)

```python
def decode(shortcut_path: str | Path) -> Dict[str, Any]
```
- 将 `.shortcut` 文件解码为 Python dict
- 自动检测 AEA 签名 / 纯 plist 两种格式
- **Raises**: `FileNotFoundError`, `plistlib.InvalidFileException`, `ValueError`

```python
def encode(data: Dict[str, Any], output_path: str | Path) -> None
```
- 将 Python dict 编码为 binary plist (`.shortcut`)
- 自动创建父目录
- **输出格式**: `plistlib.FMT_BINARY`

```python
def verify_roundtrip(input_path: str | Path, output_path: str | Path) -> bool
```
- 验证 decode → encode 无损性
- 返回 `True` 表示数据一致

#### 内部函数

```python
def _extract_from_aea(aea_data: bytes) -> bytes
```
- 从 AEA 签名容器中提取 plist 数据
- 依赖 macOS 工具: `compression_tool` (LZFSE 解压), `aa` (Apple Archive 解包)

#### Task 1.7 新增

```python
def dump_xml(data: Dict[str, Any], output_path: str | Path) -> None
```
- Python dict → XML plist 文件
- **输出格式**: `plistlib.FMT_XML`
- 自动创建父目录

```python
def load_xml(xml_path: str | Path) -> Dict[str, Any]
```
- XML plist 文件 → Python dict
- **Raises**: `FileNotFoundError`, `plistlib.InvalidFileException`

```python
def sign(input_path: str | Path, output_path: str | Path, mode: str = "anyone") -> None
```
- 封装 `shortcuts sign -m <mode> -i <input> -o <output>`
- `mode`: `"anyone"` (默认) 或 `"people-who-know-me"`
- **Raises**: `FileNotFoundError`, `RuntimeError`
- **约束**: 仅 macOS 可用，可能需要联网

#### CLI 命令 (`python shortcut_tool.py <command>`)

| 命令 | 用法 | 说明 |
|------|------|------|
| `decode` | `decode <input.shortcut>` | 显示顶层 keys |
| `dump-xml` | `dump-xml <input.shortcut> <output.xml>` | 导出 XML plist |
| `build` | `build <input.xml> <output.shortcut>` | 从 XML 构建 |
| `sign` | `sign <input> <output>` | Apple 签名 |
| `verify` | `verify <input> <output>` | 验证无损 |
| `pipeline` | `pipeline <input> <output>` | 全链路: decode→xml→build→sign |

---

## 4. Platform Constraints

### 4.1 AEA (Apple Encrypted Archive)
- iOS 15+ 的 `.shortcut` 文件使用 AEA 签名容器
- 内部结构: `AEA1 header → LZFSE 压缩 → Apple Archive → Shortcut.wflow (plist)`
- 文件大小: 未签名 ~1.3KB vs 签名后 ~22KB（证书链占主要体积）

### 4.2 macOS 系统工具依赖
| 工具 | 用途 | 路径 |
|------|------|------|
| `compression_tool` | LZFSE 解压缩 | 系统自带 |
| `aa` | Apple Archive 解包 | 系统自带 |
| `shortcuts` | 官方签名工具 | `/usr/bin/shortcuts` |

### 4.3 签名约束
- iOS **强制要求** AEA 签名，未签名文件无法导入
- macOS 对自签名文件会闪退
- `shortcuts sign -m anyone` 使用用户的 Apple ID 证书链
- 签名过程**可能需要联网**访问 Apple 服务器
