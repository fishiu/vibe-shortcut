# Samples Directory

测试用的 shortcuts 文件。

## 文件说明

| 文件 | 描述 | 用途 |
|------|------|------|
| `demo-notification.shortcut` | 原始测试样本 (AEA 签名) | 用于测试 decode 功能，作为参考文件 |
| `output.shortcut` | 未签名的 plist 文件 | encode() 函数的输出，用于验证无损转换 |
| `official-signed.shortcut` | 官方签名的文件 | 使用 `shortcuts sign` 生成，**可导入 iPhone** ✅ |

## 生成流程

```bash
# 1. 解码原始文件
python3 tools/shortcut_tool.py decode demo-notification.shortcut

# 2. 编码为未签名 plist
python3 tools/shortcut_tool.py encode <data> output.shortcut

# 3. 使用官方工具签名
shortcuts sign -m anyone -i output.shortcut -o official-signed.shortcut

# 4. 导入到设备
open official-signed.shortcut  # macOS
# 或 AirDrop 到 iPhone
```

## 文件大小对比

- 未签名 (plist): ~1.3 KB
- 已签名 (AEA): ~22 KB (包含 Apple 证书链)

---

**注意**: 仅 `official-signed.shortcut` 可以导入到 iOS/iPadOS 设备。未签名的文件会被系统拒绝。
