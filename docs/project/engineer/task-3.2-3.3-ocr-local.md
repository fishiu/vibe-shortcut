# Engineer Log: Task 3.2 & 3.3 - OCR Local Shortcut 从零构建

> **Date**: 2026-03-10
> **Related Task**: Phase 3A — 本地 OCR Shortcut
> **Status**: 🟢 Completed (待 iPhone 验证)

---

## 1. 任务目标

按 Architect 设计的 XML 骨架（doc3-spec.md §5），手写 OCR shortcut 的 XML plist，通过工具链 build + sign 产出可导入 iOS 的 `.shortcut` 文件。

**验收标准**:
- [x] `samples/ocr-local/ocr-local.xml` 存在，UUID 为动态生成（非硬编码占位符）
- [x] `samples/ocr-local/ocr-local.shortcut` 存在，AEA1 签名格式
- [ ] iPhone 导入后运行，通知中显示截图 OCR 结果

---

## 2. 技术方案

### 2.1 设计思路
完全遵循 Architect 在 doc3-spec.md §5.3 的 XML 模板，只需：
1. 用 `uuid.uuid4()` 生成两个 UUID 替换占位符
2. 调用 `shortcut_tool.py build` 和 `sign` 命令

### 2.2 Action 链路
```
takescreenshot (UUID-A: 57B7BAD7-2350-4015-BBE3-EC89E16241A9)
    → extracttextfromimage (UUID-B: 2D683A2A-418E-44CD-A366-4A79429E890B)
        WFImage ← ActionOutput(UUID-A) [WFTextTokenAttachment]
    → notification
        WFNotificationActionTitle = "OCR Result" (静态)
        WFNotificationActionBody ← ActionOutput(UUID-B) [WFTextTokenString + ￼占位]
```

---

## 3. 实现过程

### 3.1 关键决策
- **UUID 格式**: 全大写、带连字符，与样本文件一致
- **通知 body**: 使用 U+FFFC (Object Replacement Character) + attachmentsByRange 映射，与 Architect 规范一致

### 3.2 遇到的问题
#### 问题 1: conda `tool` 环境不存在
- **现象**: `conda activate tool` 报 EnvironmentNameNotFound
- **解决方案**: 使用 conda base 环境的 Python 3.13（`/opt/homebrew/Caskroom/miniconda/base/bin/python`），核心功能只用标准库，无兼容问题

#### 问题 2: 系统 Python 版本过低
- **现象**: `/usr/bin/python3` 是 3.9.6，不支持 `str | Path` 类型注解
- **解决方案**: 同上，使用 conda Python 3.13

---

## 4. 测试验证

### 4.1 构建验证
```bash
# Build
/opt/homebrew/.../python tools/shortcut_tool.py build samples/ocr-local/ocr-local.xml samples/ocr-local/ocr-local-unsigned.shortcut
# → Built samples/ocr-local/ocr-local-unsigned.shortcut

# Sign
/opt/homebrew/.../python tools/shortcut_tool.py sign samples/ocr-local/ocr-local-unsigned.shortcut samples/ocr-local/ocr-local.shortcut
# → Signed → samples/ocr-local/ocr-local.shortcut
```

### 4.2 文件验证
- ✅ `ocr-local.xml`: 3.9KB, XML plist 格式
- ✅ `ocr-local-unsigned.shortcut`: 1.3KB, binary plist
- ✅ `ocr-local.shortcut`: 22KB, AEA1 签名 header 确认
- ⏳ iPhone 导入运行: 待用户验证

---

## 5. 产出文件

### 5.1 新增文件
- `samples/ocr-local/ocr-local.xml`: 手写 XML plist，3 个 action
- `samples/ocr-local/ocr-local-unsigned.shortcut`: binary plist（中间产物）
- `samples/ocr-local/ocr-local.shortcut`: AEA 签名，可导入 iOS

---

## 6. 遗留问题
- [ ] 待 iPhone 实机验证：导入 + 运行 + 确认通知内容

---

## 7. 给下一位 Engineer 的建议
- conda `tool` 环境不存在，使用 base 环境即可
- 系统 Python 3.9 不满足要求，务必用 conda Python
- 签名可能需要联网，确保网络正常

---

## 8. 参考资料
- Internal: `doc3-spec.md` §5 (Phase 3A XML 骨架设计)
- Internal: `docs/shortcuts-manual-v0.3.md` §6.1, §6.2, §6.5, §9.8
