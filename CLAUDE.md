# VibeShortcut

Python 工具链，用于程序化读写 Apple Shortcuts（`.shortcut` 文件），最终目标是 AI 根据自然语言生成可用的 Shortcut。

## 开始对话前

**第一步：确认角色。** 用户会指定 PM / Architect / Engineer，对应不同职责和文档。若未指定，请主动询问。

角色定义与铁律详见：`docs/project/doc1-context.md`（必读）

**第二步：按角色读对应文档：**
- PM → `docs/project/doc2-current_status.md`（进度与任务）
- Architect → `docs/project/doc3-spec.md`（技术规范）
- Engineer → 先读 `doc3-spec.md`，再读对应 Task 描述

## 当前阶段

- **Phase 1** ✅ 读写闭环 — decode/encode/sign 全链路验证通过
- **Phase 2** ✅ 读懂格式 — 分析三个真实 shortcut，产出编程手册 v0.3（46 种 action）
- **Phase 3** 🔜 改动 Shortcuts — 基于手册修改现有 shortcut，验证手册实用性
- **Phase 4** 🔜 AI 生成 Shortcuts — 自然语言 → XML plist → 工具链 → 可导入 iOS

## 开发环境

**macOS only** — 核心功能依赖 macOS 系统工具，无法在其他平台运行。

```bash
conda activate tool   # Python 3.10.9
```

运行测试：
```bash
cd /Users/leverest/repos/tools/apple/shortcut/vibe-shortcut
conda run -n tool pytest tests/ -v
```

## 关键技术约束（非显而易见）

1. **iOS 强制要求 AEA 签名** — 未签名文件无法导入，macOS 对自签名会闪退
2. **唯一可靠签名方式** — `/usr/bin/shortcuts sign -m anyone`（使用 Apple ID 证书链，可能需联网）
3. **中间格式是 XML Plist，不是 JSON** — JSON 会丢失 `datetime` 和 `binary` 类型
4. **AEA 内部结构** — `AEA1 header → LZFSE 压缩 → Apple Archive → Shortcut.wflow (plist)`

## 核心工具链

```
.shortcut (AEA 签名)
  → decode()     →  Python dict
  → dump_xml()   →  .xml（无损中间层，可编辑/AI 生成）
  → load_xml()   →  Python dict
  → encode()     →  .shortcut（未签名）
  → sign()       →  .shortcut（AEA 签名，可导入 iOS）
```

一键运行：
```bash
python tools/shortcut_tool.py pipeline <input.shortcut> <output.shortcut>
```

主模块：`tools/shortcut_tool.py`（decode / encode / dump_xml / load_xml / sign / verify_roundtrip）

技术规范：`docs/project/doc3-spec.md`

## Shortcuts 编程手册

`docs/shortcuts-manual-v0.3.md` — 46 种 action、9 种常用模式、1914 行

分析样本（`samples/money/`）：
- `1-reg.xml / shortcut` — 26 actions，OCR + 正则
- `2-api.shortcut` — 46 actions，OCR + DeepSeek API
- `3-full.shortcut` — 1140 actions，完全体记账工具

## 文件结构

```
tools/shortcut_tool.py       核心模块
samples/money/               三个分析样本 + XML 导出
docs/shortcuts-manual-v0.3.md  Shortcuts 编程手册（当前版本）
docs/project/                项目文档（进度/规范/日志）
tests/                       pytest 单元测试
```
