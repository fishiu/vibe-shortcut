# Engineer Log: Task 1.7 - dump_xml / load_xml / sign

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-26
> **Related Task**: Phase 1 收尾 - Task 1.7
> **Status**: 🟢 Completed

---

## 1. 任务目标

给 `shortcut_tool.py` 补充三个函数，按 doc3-spec.md 规格实现。

**验收标准**:
- [x] `dump_xml(data, path)` — Python dict → XML plist 文件
- [x] `load_xml(path)` — XML plist 文件 → Python dict
- [x] `sign(input, output)` — 封装 `shortcuts sign -m anyone`
- [x] 全部测试通过
- [x] Pipeline 端到端验证通过

---

## 2. 实现

三个函数都很简单，直接调用标准库或系统工具：

```python
def dump_xml(data, output_path):
    plistlib.dump(data, f, fmt=plistlib.FMT_XML)

def load_xml(xml_path):
    return plistlib.load(f)

def sign(input_path, output_path, mode="anyone"):
    subprocess.run(['shortcuts', 'sign', '-m', mode, '-i', input, '-o', output])
```

额外添加了 `pipeline` CLI 命令，执行完整链路：
```
decode → dump_xml → load_xml → encode → sign
```

---

## 3. 遇到的问题

### 问题: Pipeline 数据不匹配

**现象**: `decode → xml → build → sign → decode` 后数据不一致

**原因**: `shortcuts sign` 会自动更新 `WFWorkflowClientVersion` 字段
- 签名前: `3612.0.2.3`
- 签名后: `3612.0.2.5`

**结论**: 这是系统工具的正常行为，非我们的 bug。Pipeline 验证中对此做了特殊处理。

---

## 4. 测试

```
tests/test_shortcut_tool.py::test_dump_xml_load_xml_roundtrip  PASSED  (含 bytes + datetime)
tests/test_shortcut_tool.py::test_load_xml_nonexistent_file    PASSED
tests/test_shortcut_tool.py::test_dump_xml_creates_parent_dirs PASSED
tests/test_shortcut_tool.py::test_sign_nonexistent_file        PASSED
```

**Pipeline 端到端**: `✓ Pipeline complete (sign tool updated WFWorkflowClientVersion)`

**全部测试**: 10/10 通过

---

## 5. 产出文件

### 修改
- `tools/shortcut_tool.py`: 新增 `dump_xml`, `load_xml`, `sign` + `pipeline` CLI 命令
- `tests/test_shortcut_tool.py`: 新增 4 个测试用例

---

## 6. XML 无损验证

测试 dump_xml → load_xml 对全部 plist 类型的支持：

| 类型 | 无损 |
|------|:----:|
| str | ✅ |
| int | ✅ |
| float | ✅ |
| bool | ✅ |
| list | ✅ |
| dict | ✅ |
| **bytes** | ✅ |
| **datetime** | ✅ |

**结论**: XML plist 作为中间格式，完全无损。验证了 Architect 的设计决策。
