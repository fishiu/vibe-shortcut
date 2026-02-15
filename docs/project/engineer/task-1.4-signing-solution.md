# Engineer Log: Task 1.4 - Signing Solution Discovery

> **Author**: Claude Sonnet 4.5 (Engineer Role)
> **Date**: 2026-02-16
> **Related Task**: Phase 1 - Task 1.4 (iPhone 导入验证)
> **Status**: 🟢 Completed

---

## 1. 任务目标

验证生成的 .shortcut 文件能否在 iPhone 上成功导入并运行。

**验收标准**:
- [x] 文件能导入到 iPhone 快捷指令 App
- [x] 导入后可以正常运行
- [x] 通知功能正常工作

---

## 2. 遇到的问题

### 问题 2.1: 未签名文件被拒绝

**现象**: 使用 `encode()` 生成的未签名 plist 文件无法导入 iPhone

**错误信息**: "没有 signed 的无法导入"

**测试结果**:
| 文件 | macOS | iOS |
|------|-------|-----|
| 未签名 plist | ⚠️ 可预览 | ❌ 拒绝导入 |
| AEA 自签名 | 💥 闪退 | ❌ 未测试 |

---

### 问题 2.2: 自签名尝试失败

**尝试方案**: 使用 `aea encrypt` 和自生成的 P-256 密钥对签名

**实现步骤**:
```bash
# 1. 创建 Apple Archive
aa archive -d wflow -o shortcut.aar

# 2. LZFSE 压缩
compression_tool -encode -a lzfse -i shortcut.aar -o shortcut.lzfse

# 3. 生成密钥对
openssl ecparam -name prime256v1 -genkey -noout -out sign-priv.pem

# 4. AEA 签名
aea encrypt -profile 0 -i shortcut.lzfse -o signed.shortcut -sign-priv sign-priv.pem
```

**结果**:
- ✅ 文件生成成功（AEA1 格式）
- ❌ macOS 预览失败（Extension 崩溃）
- ❌ 双击导致 Shortcuts App 闪退

**原因**: 系统严格验证签名有效性，自签名证书不被信任

---

## 3. 最终解决方案

### 3.1 发现官方工具

**关键转折**: 参考其他成功案例，发现 macOS 自带 `/usr/bin/shortcuts` 工具

```bash
shortcuts --help
# SUBCOMMANDS:
#   run      Run a shortcut.
#   list     List your shortcuts.
#   view     View a shortcut in Shortcuts.
#   sign     Sign a shortcut file.  ← 关键！
```

### 3.2 使用官方签名

```bash
shortcuts sign -m anyone -i output.shortcut -o official-signed.shortcut
```

**参数说明**:
- `-m anyone`: 签名模式，任何人可导入（公开分享）
- `-m people-who-know-me`: 仅信任的人（默认）
- `-i`: 输入文件（未签名或旧格式）
- `-o`: 输出文件（AEA 签名）

**输出**:
```
ERROR: Unrecognized attribute string flag '?' ...
(多条 ERROR，但可忽略 - 这是 ObjC runtime 调试信息)
```

**结果**:
- ✅ 生成 22KB AEA 签名文件
- ✅ 包含真实 Apple 证书链
- ✅ macOS 可预览
- ✅ **iPhone 成功导入并运行** 🎉

---

## 4. 技术对比

| 方案 | 工具 | 证书链 | macOS | iOS | 复杂度 |
|------|------|--------|-------|-----|--------|
| 未签名 | plistlib | ❌ 无 | ⚠️ 预览 | ❌ 拒绝 | 低 |
| 自签名 | aea + openssl | 🔶 自建 | 💥 崩溃 | ❌ 失败 | 高 |
| **官方签名** | **shortcuts** | **✅ Apple** | **✅ 正常** | **✅ 成功** | **极低** |

---

## 5. 反思与教训

### ❌ 错误的思维路径

1. **过早深入底层**:
   - 直接研究 AEA 格式、证书、ECDSA 签名算法
   - 浪费时间实现复杂的签名流程

2. **忽略官方工具**:
   - 没有首先检查 `/usr/bin/` 下的系统工具
   - 没有搜索 "macOS shortcuts command line"

3. **未主动询问参考资料**:
   - 用户提到"别的 AI 成功过"
   - 应该立即请求查看成功案例

### ✅ 正确的思维应该是

```
问题：需要签名 shortcuts
  ↓
检查：Apple 有官方工具吗？
  ↓
发现：/usr/bin/shortcuts sign
  ↓
测试：成功！
  ↓
完成：5 分钟搞定（而不是几小时）
```

### 📚 核心教训

**Occam's Razor (奥卡姆剃刀)**:
> 最简单的解决方案往往是正确的

**工程师检查清单**（优先级排序）:
1. ✅ **系统有内置工具吗？** (`which`, `man`, `ls /usr/bin/`)
2. ✅ **官方有 CLI 工具吗？**
3. ✅ **社区有成熟方案吗？** (GitHub, StackOverflow)
4. ✅ **用户有参考资料吗？** (主动询问)
5. ⚠️ **真的需要从零实现吗？** (最后选项)

---

## 6. 完整工作流程

### 6.1 最终方案

```bash
# Step 1: 解码现有 shortcut (可选，用于学习)
python3 tools/shortcut_tool.py decode input.shortcut

# Step 2: 编辑/生成 shortcuts 数据
# (这一步是项目的核心价值，Phase 2 将实现)
# 当前使用: 直接修改解码后的数据

# Step 3: 编码为未签名 plist
python3 tools/shortcut_tool.py encode data.json output.shortcut

# Step 4: 使用官方工具签名
shortcuts sign -m anyone -i output.shortcut -o signed.shortcut

# Step 5: 导入到设备
open signed.shortcut  # macOS
# 或 AirDrop 到 iPhone/iPad
```

### 6.2 注意事项

**网络依赖**:
- `shortcuts sign` 可能需要联网（Apple 服务器验证）
- 如果失败，可以重试（参考 sign_and_import.sh 的重试机制）

**权限要求**:
- 需要 macOS 用户登录 Apple ID
- 可能需要启用"快捷指令"App

---

## 7. 产出文件

### 7.1 清理后的 samples/

```
samples/
├── README.md                      # 文件说明
├── demo-notification.shortcut     # 原始测试样本 (22KB, AEA)
├── output.shortcut                # 未签名输出 (1.3KB, plist)
└── official-signed.shortcut       # 官方签名 (22KB, AEA) ✅ 可导入
```

### 7.2 文档更新

- ✅ `task-1.4-signing-solution.md` (本文档)
- ✅ `issue-unsigned-import-blocked.md` (已更新结论)
- ✅ `samples/README.md` (新增)

---

## 8. 任务完成情况

### Phase 1 进度

- ✅ Task 1.1: 提取参考文件
- ✅ Task 1.2: 实现 decode (支持 AEA)
- ✅ Task 1.3: 实现 encode (未签名 plist)
- ✅ **Task 1.4: iPhone 导入验证** ← 本任务
- ⏭ Task 1.5: 确认二进制闭环 (待验证)

### 验收标准达成

- [x] 文件成功导入 iPhone ✅
- [x] 导入后在快捷指令列表可见 ✅
- [x] 运行后成功发送通知 ✅
- [x] 通知内容正确 ✅

---

## 9. 下一步建议

### 9.1 集成到 shortcut_tool.py

建议添加 `sign()` 函数：

```python
def sign(input_path: Path, output_path: Path, mode: str = "anyone") -> None:
    """使用官方工具签名 shortcut 文件"""
    subprocess.run([
        'shortcuts', 'sign',
        '-m', mode,
        '-i', str(input_path),
        '-o', str(output_path)
    ], check=True)
```

### 9.2 Phase 1 收尾

- [ ] 更新 `shortcut_tool.py` 添加 sign 功能
- [ ] 添加集成测试（decode → encode → sign → decode）
- [ ] 验证完整的二进制闭环（Task 1.5）

### 9.3 进入 Phase 2

**已具备的能力**:
- ✅ 读取任意 shortcuts（包括 AEA）
- ✅ 解析为 Python dict
- ✅ 生成可导入的 shortcuts

**下一阶段目标**:
- 数据清洗（移除 UI 坐标等冗余信息）
- 定义 AI 可读的中间格式 (Schema)
- 实现 Builder（从简化描述生成 shortcuts）

---

## 10. 参考资料

- macOS `shortcuts` 命令: `/usr/bin/shortcuts`
- 成功案例: `/Users/leverest/repos/lang/apple/shortcut/money/sign_and_import.sh`
- 官方文档: `man shortcuts` (虽然不详细)

---

**总结**: Task 1.4 完成。关键突破是发现并使用了 macOS 自带的 `shortcuts sign` 工具，避免了复杂的底层签名实现。这个教训强化了"先寻找官方方案"的工程原则。
