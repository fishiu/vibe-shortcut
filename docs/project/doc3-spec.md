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

手册版本历程：
- **v0.1**: 11 种 action (Sample A: OCR + 正则) ✅
- **v0.2**: 24 种 action (+ Sample B: API 调用) ✅
- **v0.3**: 46 种 action (+ Sample C: 完全体, 1914 行) ✅ **← 当前版本**

### 2.4 技术验证结论 (Phase 2 完成)
- ✅ `WFCondition` 运算符表完整: 0=等于, 1=不等于, 2=小于, 3=大于, 4=大于等于, 5=小于等于, 100=有任何值
- ✅ **conditional 分支方向**: BEGIN→ELSE = true 分支, ELSE→END = false 分支
- ✅ `WFCondition=4` 确认为 ≥ (Sample C 中出现 82 次)
- ✅ `WFItemType`: 0=Text, 1=Dictionary, 3=Number, 4=Boolean, 5=Array (无 2)
- ✅ 4 种序列化类型: WFTextTokenAttachment, WFTextTokenString, WFDictionaryFieldValue, WFContentPredicateTableTemplate
- ✅ 4 种控制流: conditional, choosefrommenu, repeat.count, repeat.each

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

---

## 5. Phase 3A — OCR Shortcut XML 骨架设计

### 5.1 功能描述
最简 OCR shortcut：截图 → 文字识别 → 通知显示结果。三个 action，零用户输入。

### 5.2 数据流与 UUID 引用链

```
Action 1: takescreenshot
  UUID = {{UUID-A}}
  输出 → 截图图片
         ↓ 引用 UUID-A
Action 2: extracttextfromimage
  UUID = {{UUID-B}}
  WFImage ← ActionOutput(UUID-A)   [WFTextTokenAttachment]
  输出 → 识别文字
         ↓ 引用 UUID-B
Action 3: notification
  无 UUID（终端 action，输出不被引用）
  WFNotificationActionTitle ← 静态字符串
  WFNotificationActionBody  ← ActionOutput(UUID-B)  [WFTextTokenString]
```

> **铁律提醒**: `{{UUID-A}}` 和 `{{UUID-B}}` 是占位符。Engineer 实现时**必须**用 `uuid.uuid4()` 动态生成，严禁硬编码。

### 5.3 完整 XML Plist 模板

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- ★ 核心: Action 列表 -->
    <key>WFWorkflowActions</key>
    <array>

        <!-- Action 1: 截图 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.takescreenshot</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-A}}</string>
            </dict>
        </dict>

        <!-- Action 2: OCR 文字识别 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.extracttextfromimage</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-B}}</string>
                <key>WFImage</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Screenshot</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-A}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 3: 通知显示 OCR 结果 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.notification</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>WFNotificationActionTitle</key>
                <string>OCR Result</string>
                <key>WFNotificationActionBody</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{0, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Text from Image</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-B}}</string>
                                <key>Type</key>
                                <string>ActionOutput</string>
                            </dict>
                        </dict>
                        <key>string</key>
                        <string>&#xFFFC;</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

    </array>

    <!-- 元数据 -->
    <key>WFWorkflowClientVersion</key>
    <string>3612.0.2.1</string>

    <key>WFWorkflowHasOutputFallback</key>
    <false/>

    <key>WFWorkflowHasShortcutInputVariables</key>
    <false/>

    <key>WFWorkflowIcon</key>
    <dict>
        <key>WFWorkflowIconGlyphNumber</key>
        <integer>59514</integer>
        <key>WFWorkflowIconStartColor</key>
        <integer>4274264319</integer>
    </dict>

    <key>WFWorkflowImportQuestions</key>
    <array/>

    <key>WFWorkflowInputContentItemClasses</key>
    <array>
        <string>WFImageContentItem</string>
    </array>

    <key>WFWorkflowMinimumClientVersion</key>
    <integer>900</integer>
    <key>WFWorkflowMinimumClientVersionString</key>
    <string>900</string>

    <key>WFWorkflowOutputContentItemClasses</key>
    <array/>

    <key>WFQuickActionSurfaces</key>
    <array/>

    <key>WFWorkflowTypes</key>
    <array>
        <string>WFWorkflowTypeShowInSearch</string>
    </array>
</dict>
</plist>
```

### 5.4 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 通知 body 格式 | WFTextTokenString | body 嵌入动态变量（OCR 结果），需用 ￼ (U+FFFC) 占位 + attachmentsByRange 映射 |
| OCR 输入格式 | WFTextTokenAttachment | WFImage 是单值参数，直接引用 ActionOutput |
| WFWorkflowInputContentItemClasses | 仅 WFImageContentItem | OCR shortcut 只处理图片 |
| WFWorkflowTypes | WFWorkflowTypeShowInSearch | 可在搜索中找到，无需 Watch 触发 |
| Action 3 无 UUID | 省略 | 终端 action，无下游引用 |

### 5.5 Engineer 实现指引

1. **创建** `samples/ocr-local/ocr-local.xml`，基于上述模板
2. **替换** `{{UUID-A}}` 和 `{{UUID-B}}` 为 `uuid.uuid4()` 生成的真实 UUID（全大写，带连字符）
3. **构建**: `python tools/shortcut_tool.py build samples/ocr-local/ocr-local.xml samples/ocr-local/ocr-local-unsigned.shortcut`
4. **签名**: `python tools/shortcut_tool.py sign samples/ocr-local/ocr-local-unsigned.shortcut samples/ocr-local/ocr-local.shortcut`
5. **验证**: 导入 iPhone，运行后应看到通知标题 "OCR Result"，body 为截图中识别出的文字

---

## 6. Phase 3B — DeepSeek API Shortcut XML 骨架设计

### 6.1 功能描述
用户输入问题 → 构建 JSON body → POST 到 DeepSeek API → 解析 response → 通知显示 AI 回答。8 个 action。

### 6.2 数据流与 UUID 引用链

```
Action 1: gettext (API Key)
  UUID = {{UUID-A}}
  输出 → API Key 字符串（明文占位符，Engineer 替换为真实 key）

Action 2: ask (用户输入)
  UUID = {{UUID-B}}
  输出 → 用户问题文本
         ↓ 引用 UUID-B
Action 3: gettext (构建 JSON Body)
  UUID = {{UUID-C}}
  WFTextActionText ← 嵌入 UUID-B 于 content 字段  [WFTextTokenString]
  输出 → '{"model":"deepseek-chat","messages":[{"role":"user","content":"..."}]}'
         ↓ 引用 UUID-A, UUID-C
Action 4: downloadurl (POST API 请求)
  UUID = {{UUID-D}}
  WFURL ← 静态 "https://api.deepseek.com/v1/chat/completions"
  WFHTTPHeaders.Authorization ← "Bearer " + UUID-A  [WFTextTokenString]
  WFHTTPHeaders.Content-Type ← 静态 "application/json"
  WFRequestVariable ← UUID-C  [WFTextTokenAttachment]
  输出 → JSON response (自动解析为 dict)
         ↓ 引用 UUID-D
Action 5: getvalueforkey (提取 choices)
  UUID = {{UUID-E}}
  WFDictionaryKey = "choices"
  WFInput ← UUID-D  [WFTextTokenAttachment]
  输出 → choices 数组
         ↓ 引用 UUID-E
Action 6: getitemfromlist (取第一项)
  UUID = {{UUID-F}}
  WFInput ← UUID-E  [WFTextTokenAttachment]
  WFItemIndex = 1  (Shortcuts 索引从 1 开始)
  输出 → choices[0] dict
         ↓ 引用 UUID-F
Action 7: getvalueforkey (提取 message.content)
  UUID = {{UUID-G}}
  WFDictionaryKey = "message.content"  (点号分隔的嵌套路径)
  WFInput ← UUID-F  [WFTextTokenAttachment]
  输出 → AI 回答文本
         ↓ 引用 UUID-G
Action 8: notification (显示结果)
  无 UUID（终端 action）
  WFNotificationActionTitle ← 静态 "DeepSeek"
  WFNotificationActionBody ← UUID-G  [WFTextTokenString]
```

> **铁律提醒**: `{{UUID-A}}` ~ `{{UUID-G}}` 均为占位符，Engineer 必须用 `uuid.uuid4()` 动态生成。

### 6.3 完整 XML Plist 模板

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>WFWorkflowActions</key>
    <array>

        <!-- Action 1: API Key（明文存储，Engineer 替换为真实 key） -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.gettext</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-A}}</string>
                <key>WFTextActionText</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>string</key>
                        <string>sk-REPLACE-WITH-REAL-KEY</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 2: 用户输入 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.ask</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-B}}</string>
                <key>WFAskActionPrompt</key>
                <string>Ask DeepSeek:</string>
                <key>WFInputType</key>
                <string>Text</string>
            </dict>
        </dict>

        <!-- Action 3: 构建 JSON 请求体 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.gettext</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-C}}</string>
                <key>WFTextActionText</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{63, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Provided Input</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-B}}</string>
                                <key>Type</key>
                                <string>ActionOutput</string>
                            </dict>
                        </dict>
                        <key>string</key>
                        <string>{"model":"deepseek-chat","messages":[{"role":"user","content":"&#xFFFC;"}]}</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 4: POST 到 DeepSeek API -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.downloadurl</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-D}}</string>
                <key>ShowHeaders</key>
                <true/>
                <key>WFHTTPMethod</key>
                <string>POST</string>
                <key>WFHTTPBodyType</key>
                <string>File</string>
                <key>WFURL</key>
                <string>https://api.deepseek.com/v1/chat/completions</string>
                <key>WFHTTPHeaders</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>WFDictionaryFieldValueItems</key>
                        <array>
                            <!-- Authorization: Bearer {API_KEY} -->
                            <dict>
                                <key>WFItemType</key>
                                <integer>0</integer>
                                <key>WFKey</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>string</key>
                                        <string>Authorization</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                                <key>WFValue</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>attachmentsByRange</key>
                                        <dict>
                                            <key>{7, 1}</key>
                                            <dict>
                                                <key>OutputName</key>
                                                <string>Text</string>
                                                <key>OutputUUID</key>
                                                <string>{{UUID-A}}</string>
                                                <key>Type</key>
                                                <string>ActionOutput</string>
                                            </dict>
                                        </dict>
                                        <key>string</key>
                                        <string>Bearer &#xFFFC;</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                            </dict>
                            <!-- Content-Type: application/json -->
                            <dict>
                                <key>WFItemType</key>
                                <integer>0</integer>
                                <key>WFKey</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>string</key>
                                        <string>Content-Type</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                                <key>WFValue</key>
                                <dict>
                                    <key>Value</key>
                                    <dict>
                                        <key>string</key>
                                        <string>application/json</string>
                                    </dict>
                                    <key>WFSerializationType</key>
                                    <string>WFTextTokenString</string>
                                </dict>
                            </dict>
                        </array>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFDictionaryFieldValue</string>
                </dict>
                <key>WFRequestVariable</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Text</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-C}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 5: 提取 choices 数组 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getvalueforkey</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-E}}</string>
                <key>WFDictionaryKey</key>
                <string>choices</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Contents of URL</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-D}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 6: 取第一项 choices[0] -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getitemfromlist</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-F}}</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Value for Key</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-E}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
                <key>WFItemIndex</key>
                <integer>1</integer>
            </dict>
        </dict>

        <!-- Action 7: 提取 message.content -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.getvalueforkey</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>UUID</key>
                <string>{{UUID-G}}</string>
                <key>WFDictionaryKey</key>
                <string>message.content</string>
                <key>WFInput</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>OutputName</key>
                        <string>Item from List</string>
                        <key>OutputUUID</key>
                        <string>{{UUID-F}}</string>
                        <key>Type</key>
                        <string>ActionOutput</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenAttachment</string>
                </dict>
            </dict>
        </dict>

        <!-- Action 8: 通知显示 AI 回答 -->
        <dict>
            <key>WFWorkflowActionIdentifier</key>
            <string>is.workflow.actions.notification</string>
            <key>WFWorkflowActionParameters</key>
            <dict>
                <key>WFNotificationActionTitle</key>
                <string>DeepSeek</string>
                <key>WFNotificationActionBody</key>
                <dict>
                    <key>Value</key>
                    <dict>
                        <key>attachmentsByRange</key>
                        <dict>
                            <key>{0, 1}</key>
                            <dict>
                                <key>OutputName</key>
                                <string>Value for Key</string>
                                <key>OutputUUID</key>
                                <string>{{UUID-G}}</string>
                                <key>Type</key>
                                <string>ActionOutput</string>
                            </dict>
                        </dict>
                        <key>string</key>
                        <string>&#xFFFC;</string>
                    </dict>
                    <key>WFSerializationType</key>
                    <string>WFTextTokenString</string>
                </dict>
            </dict>
        </dict>

    </array>

    <!-- 元数据 -->
    <key>WFWorkflowClientVersion</key>
    <string>3612.0.2.1</string>

    <key>WFWorkflowHasOutputFallback</key>
    <false/>

    <key>WFWorkflowHasShortcutInputVariables</key>
    <false/>

    <key>WFWorkflowIcon</key>
    <dict>
        <key>WFWorkflowIconGlyphNumber</key>
        <integer>59514</integer>
        <key>WFWorkflowIconStartColor</key>
        <integer>431817727</integer>
    </dict>

    <key>WFWorkflowImportQuestions</key>
    <array/>

    <key>WFWorkflowInputContentItemClasses</key>
    <array>
        <string>WFStringContentItem</string>
    </array>

    <key>WFWorkflowMinimumClientVersion</key>
    <integer>900</integer>
    <key>WFWorkflowMinimumClientVersionString</key>
    <string>900</string>

    <key>WFWorkflowOutputContentItemClasses</key>
    <array/>

    <key>WFQuickActionSurfaces</key>
    <array/>

    <key>WFWorkflowTypes</key>
    <array>
        <string>WFWorkflowTypeShowInSearch</string>
    </array>
</dict>
</plist>
```

### 6.4 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| API Key 存储 | gettext 明文 | 3B 是验证性 shortcut，简单优先。生产环境应用 WFWorkflowImportQuestions |
| WFURL 格式 | 静态 `<string>` | URL 不含变量，无需 WFTextTokenString 包装 |
| HTTP Body 类型 | `File` (非 `JSON`) | 与 Sample B 一致，body 由 gettext 预构建为 JSON 字符串 |
| JSON body 构建 | gettext + WFTextTokenString | 在模板字符串中用 ￼ 占位插入用户输入，位置 {63, 1} |
| Response 解析 | downloadurl 自动解析 | downloadurl 收到 JSON response 自动转 dict，无需 detect.dictionary |
| 嵌套取值 | `message.content` 点号路径 | getvalueforkey 原生支持点号分隔的嵌套路径 |
| 数组索引 | WFItemIndex=1 | Shortcuts 索引从 1 开始，非 0 |
| 图标颜色 | 431817727 (深蓝) | 区分于 3A 的紫色 |

### 6.5 字符位置计算备注

Action 3 的 JSON body 模板中 ￼ 的位置：
```
{"model":"deepseek-chat","messages":[{"role":"user","content":"￼"}]}
0         1         2         3         4         5         6
0123456789012345678901234567890123456789012345678901234567890123
                                                               ^
                                                            pos 63
```
`{63, 1}` — 第 63 个字符处，长度 1（占位符 ￼）。

### 6.6 Engineer 实现指引

1. **创建** `samples/deepseek-api/deepseek-api.xml`，基于上述模板
2. **替换** `{{UUID-A}}` ~ `{{UUID-G}}` 为 `uuid.uuid4()` 生成的真实 UUID（全大写，带连字符）
3. **替换** `sk-REPLACE-WITH-REAL-KEY` 为真实 DeepSeek API Key
4. **构建**: `python tools/shortcut_tool.py build samples/deepseek-api/deepseek-api.xml samples/deepseek-api/deepseek-api-unsigned.shortcut`
5. **签名**: `python tools/shortcut_tool.py sign samples/deepseek-api/deepseek-api-unsigned.shortcut samples/deepseek-api/deepseek-api.shortcut`
6. **验证**: 导入 iPhone → 输入任意问题 → 通知标题 "DeepSeek"，body 为 AI 回答
7. **安全提醒**: `.shortcut` 文件包含明文 API Key，**不要** commit 到 git。在 `.gitignore` 中排除或提交前清除 key
