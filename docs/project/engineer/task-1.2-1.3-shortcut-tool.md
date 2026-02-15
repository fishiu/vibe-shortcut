# Engineer Log: Task 1.2 & 1.3 - Shortcut Tool Implementation

> **Author**: Claude Sonnet 4.5 (Engineer Role)
> **Date**: 2026-02-16
> **Related Task**: Phase 1 - Task 1.2 (dumper) & Task 1.3 (builder)
> **Status**: 🟢 Completed

---

## 1. 任务目标

实现 `tools/shortcut_tool.py`，包含：
- `decode()` - 解码 .shortcut 文件为 Python dict
- `encode()` - 编码 Python dict 为 .shortcut 文件
- `verify_roundtrip()` - 验证 plistlib 无损转换

**核心要求**：
- 验证 plistlib 的无损转换能力
- 不需要清洗数据，越简单越好
- 遵守核心铁律：二进制闭环，使用 plistlib 严格序列化

---

## 2. 实现过程

### 2.1 初始实现（纯 plist 版本）

**文件**: `tools/shortcut_tool.py`

最初实现了基础的三个函数：

```python
def decode(shortcut_path: str | Path) -> Dict[str, Any]:
    """直接使用 plistlib.load() 读取 .shortcut 文件"""

def encode(data: Dict[str, Any], output_path: str | Path) -> None:
    """使用 plistlib.dump() 写入二进制 plist"""

def verify_roundtrip(input_path: str | Path, output_path: str | Path) -> bool:
    """验证 decode -> encode -> decode 数据一致性"""
```

**测试结果**: ✅ 4/4 测试通过

---

### 2.2 实际文件格式发现

**问题**: 用户提供的真实 .shortcut 文件无法被 plistlib 解析

**调查过程**:

1. **文件分析**:
   ```bash
   file samples/demo-notification.shortcut
   # 输出: data (不是 plist)

   xxd samples/demo-notification.shortcut | head -20
   # 发现: 文件以 "AEA1" 开头，不是 "bplist00"
   ```

2. **格式识别**:
   - 文件魔数: `AEA1` (Apple Encrypted Archive)
   - iOS 15+ 的 .shortcut 文件使用 AEA 签名包装
   - Profile 0: 签名但不加密

3. **Web 搜索**:
   - 找到 [Apple Encrypted Archive 文档](https://theapplewiki.com/wiki/Apple_Encrypted_Archive)
   - 找到 [提取方法 gist](https://gist.github.com/0xilis/776d873475a5626aa612804fa9821199)

---

### 2.3 AEA 格式解包实现

#### 文件结构分析

```
[0x0-0x3]:    "AEA1" - Magic bytes
[0x4-0x7]:    未知（版本/标志）
[0x8-0xB]:    auth_data_size (4 bytes, little-endian)
[0xC...]:     签名证书链（plist）
[auth_data_size + 0x13c + 4]:  compressed_size (4 bytes)
[auth_data_size + 0x495c]:     LZFSE 压缩数据
```

#### 提取流程

```python
def _extract_from_aea(aea_data: bytes) -> bytes:
    # 1. 读取 auth_data_size
    auth_data_size = struct.unpack('<I', aea_data[0x8:0xC])[0]

    # 2. 计算压缩数据位置
    encoded_buf_offset = auth_data_size + 0x495c
    compressed_size_offset = auth_data_size + 0x13c + 4

    # 3. 提取压缩数据
    compressed_data = aea_data[encoded_buf_offset:encoded_buf_offset + compressed_size]

    # 4. LZFSE 解压 (使用 macOS compression_tool)
    subprocess.run(['compression_tool', '-decode', '-a', 'lzfse', ...])

    # 5. 提取 Apple Archive (使用 macOS aa 工具)
    subprocess.run(['aa', 'extract', ...])

    # 6. 读取 Shortcut.wflow (纯 plist)
    return wflow_path.read_bytes()
```

#### 更新 decode() 函数

```python
def decode(shortcut_path: str | Path) -> Dict[str, Any]:
    with open(path, 'rb') as f:
        file_data = f.read()

    # 自动检测格式
    if file_data[:4] == b'AEA1':
        plist_data = _extract_from_aea(file_data)
        return plistlib.loads(plist_data)
    else:
        return plistlib.loads(file_data)
```

---

## 3. 遇到的问题与解决方案

### 问题 1: iCloud 链接下载失败
- **现象**: curl 下载的是 HTML 页面，不是 .shortcut 文件
- **原因**: iCloud 链接需要在移动端或通过特定 API 访问
- **解决**: 指导用户从快捷指令 App 手动导出文件

### 问题 2: plistlib.InvalidFileException
- **现象**: `plistlib.load()` 无法解析 AEA 格式文件
- **原因**: iOS 15+ 使用 AEA 签名包装，不是纯 plist
- **解决**: 实现 AEA 解包流程

### 问题 3: aea 工具需要签名验证
- **现象**: `aea decrypt` 报错 `-sign-pub is required`
- **原因**: 官方工具强制验证签名
- **解决**: 自行实现提取逻辑，使用 compression_tool 和 aa 工具

### 问题 4: 依赖系统工具
- **现象**: 需要 macOS 系统工具 (compression_tool, aa)
- **影响**: 工具目前仅支持 macOS
- **权衡**: 符合项目环境（开发环境是 macOS），暂不跨平台

---

## 4. 测试验证

### 4.1 单元测试

**文件**: `tests/test_shortcut_tool.py`
- ✅ test_encode_decode_simple - 基础编解码
- ✅ test_verify_roundtrip - 无损转换验证
- ✅ test_decode_nonexistent_file - 错误处理
- ✅ test_encode_creates_parent_dirs - 目录自动创建

**文件**: `tests/test_aea_extraction.py`
- ✅ test_decode_aea_signed_shortcut - AEA 格式解码
- ✅ test_aea_to_unsigned_conversion - 签名转无签名

### 4.2 真实数据验证

```bash
# 测试文件: samples/demo-notification.shortcut (22KB, AEA 签名)
python3 tools/shortcut_tool.py decode samples/demo-notification.shortcut
# ✅ 成功解码，12 个顶级键

python3 tools/shortcut_tool.py verify samples/demo-notification.shortcut samples/output.shortcut
# ✅ 无损转换验证通过
# 输出: samples/output.shortcut (1.3KB, 纯 plist)
```

**关键发现**:
- AEA 签名文件: 22KB (包含证书链)
- 纯 plist 文件: 1.3KB (仅数据)
- 数据完全一致，无损转换 ✓

---

## 5. 技术决策

### 5.1 依赖选择
- ✅ **使用标准库**: plistlib, struct, subprocess, tempfile
- ✅ **系统工具**: compression_tool (LZFSE), aa (Apple Archive)
- ❌ **未使用第三方库**: 保持零依赖，符合项目哲学

### 5.2 API 设计
- ✅ **自动检测**: decode() 透明处理 AEA/plist 两种格式
- ✅ **向后兼容**: 同时支持签名和未签名 shortcuts
- ✅ **类型提示**: 完整的 type hints，IDE 友好

### 5.3 错误处理
- ✅ 文件不存在 → `FileNotFoundError`
- ✅ 无效 plist → `plistlib.InvalidFileException`
- ✅ AEA 解包失败 → `ValueError`

---

## 6. 产出文件

```
tools/
  └── shortcut_tool.py          # 核心工具 (180 行)
tests/
  ├── test_shortcut_tool.py     # 基础测试 (4 个)
  └── test_aea_extraction.py    # AEA 测试 (2 个)
samples/
  ├── demo-notification.shortcut   # 测试样本 (AEA 签名)
  └── output.shortcut              # 验证输出 (纯 plist)
```

---

## 7. 遵守的核心铁律

✅ **二进制闭环**: 使用 `plistlib.dump(fmt=FMT_BINARY)` 严格序列化
✅ **无损转换**: verify_roundtrip() 验证数据完整性 100%
✅ **零依赖**: 仅使用 Python 标准库 + macOS 系统工具

---

## 8. 下一步建议

### 8.1 功能增强（可选）
- [ ] 添加 JSON 导出功能 (用于查看 shortcuts 结构)
- [ ] 跨平台支持 (Linux/Windows 需要 LZFSE 库)
- [ ] 纯 Python LZFSE 解压 (移除系统工具依赖)

### 8.2 Phase 1 剩余任务
- [ ] Task 1.4: 在 iPhone 上验证 `output.shortcut` 可导入
- [ ] Task 1.5: 确认二进制读写闭环无误 (Milestone)

### 8.3 Phase 2 准备
- 已具备读取 shortcuts 完整数据的能力
- 可以开始设计数据清洗 Schema

---

## 9. 参考资料

- [Apple Encrypted Archive - The Apple Wiki](https://theapplewiki.com/wiki/Apple_Encrypted_Archive)
- [Shortcuts File Format Documentation](https://zachary7829.github.io/blog/shortcuts/fileformat)
- [AEA extraction gist](https://gist.github.com/0xilis/776d873475a5626aa612804fa9821199)
- [ipsw AEA Guide](https://blacktop.github.io/ipsw/docs/guides/aea/)

---

**总结**: Task 1.2 和 1.3 已完成，超出预期地解决了 AEA 签名格式问题，验证了 plistlib 的无损转换能力。工具已准备好用于后续的数据清洗和 Schema 设计。
