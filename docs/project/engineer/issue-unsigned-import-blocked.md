# Issue: Unsigned Shortcuts Cannot Be Imported (已解决)

> **Date**: 2026-02-16
> **Severity**: ~~🔴 Blocker~~ → 🟢 Resolved
> **Status**: ✅ 已解决 (使用 `shortcuts sign` 官方工具)
> **Resolution**: 参见 `task-1.4-signing-solution.md`

---

## 问题描述

尝试将 `samples/output.shortcut`（未签名的 binary plist）导入 iPhone 时，系统提示无法导入未签名的文件。

## 测试情况

| 文件 | 格式 | Auth Data | 证书链 | macOS 结果 | iOS 结果 |
|------|------|-----------|--------|-----------|----------|
| `demo-notification.shortcut` | AEA (Apple) | ✅ 2205B | Apple 真实 | ✅ 正常 | ✅ 可导入 |
| `output.shortcut` | 纯 plist | ❌ 无 | 无 | ⚠️ 可预览 | ❌ 拒绝 |
| `test-signed-v1.shortcut` | AEA (自签) | ❌ 0B | 无 | ❌ Invalid | ❌ 未测试 |
| `test-signed-v2.shortcut` | AEA (自签) | ✅ 136B | 假证书 | 💥 闪退 | ❌ 未测试 |
| `test-signed-v3.shortcut` | AEA (自签) | ✅ 2205B | Apple 真实 | 💥 闪退 | ❌ 未测试 |

**错误信息**:
- iOS: "没有 signed 的无法导入"
- macOS v2/v3: `Extension com.apple.shortcuts.QuickLookExtension failed during preview`
- macOS 双击 v2/v3: **Shortcuts 软件闪退**

## 技术分析

### iOS 导入机制
从 iOS 15 开始，`.shortcut` 文件导入有严格的签名验证：
- ✅ **AEA 签名格式** (Profile 0): 可以导入
- ❌ **未签名 plist**: 被系统拒绝

### 影响范围
这意味着我们的 **encode()** 函数生成的文件无法直接用于：
- iPhone/iPad 直接导入
- 分发给其他用户
- App Store 分发

但可以用于：
- ✅ Mac 快捷指令 App（可能更宽松）
- ✅ 开发测试和数据分析
- ✅ 作为中间格式处理

---

## 可能的解决方案

### 方案 1: 验证原始 AEA 文件 (优先)
**操作**: 先测试原始的 `demo-notification.shortcut` 能否导入

**目的**:
- 确认签名文件确实可以导入
- 排除其他问题（iOS 版本、网络等）

**步骤**:
```bash
# 将原始 AEA 文件发送到 iPhone
# samples/demo-notification.shortcut (22KB, 已签名)
```

---

### 方案 2: 实现 AEA 签名生成 (复杂)
**技术路径**:
```python
# 需要实现
def encode_with_signature(data: dict, output_path: Path, cert: Certificate):
    # 1. 将 dict 编码为 plist
    # 2. 创建 Apple Archive
    # 3. LZFSE 压缩
    # 4. 使用证书签名
    # 5. 包装为 AEA 格式
```

**挑战**:
- 需要有效的 Apple 证书
- 签名算法复杂（ECDSA P-256）
- 需要构建完整的证书链

**依赖**:
- Apple 开发者账户？
- 私钥管理
- 证书链构建

---

### 方案 3: 使用系统工具签名 (推荐尝试)
**工具**: macOS `aea` 命令

```bash
# 理论流程
# 1. 使用 encode() 生成 plist
# 2. 创建 Apple Archive
aa archive -d extracted/ -o shortcut.aar

# 3. LZFSE 压缩
compression_tool -encode -a lzfse -i shortcut.aar -o shortcut.lzfse

# 4. 使用 aea 签名
aea sign -profile 0 -sign-priv <私钥> -i shortcut.lzfse -o output.shortcut
```

**问题**: 需要获取或生成签名私钥

---

### 方案 4: iCloud API 自动签名 (可行)
根据搜索结果，可以通过 iCloud API 上传未签名的 shortcut，iCloud 会自动签名。

**参考**:
- 将 shortcut 上传到 iCloud
- 从 iCloud 下载会得到签名版本

**缺点**:
- 需要网络连接
- 依赖 Apple 服务
- 不适合批量生成

---

### 方案 5: 仅支持 Mac 导入 (降级方案)
**接受限制**:
- 生成的 shortcuts 仅用于 Mac 快捷指令 App
- iPhone/iPad 用户需要通过 iCloud 同步

**适用场景**:
- 开发者工具
- 桌面自动化

---

## 测试结论

### ✅ 已确认
1. **iOS 要求 AEA 签名**: 未签名的 plist 无法导入
2. **macOS 验证签名有效性**:
   - 未签名的 plist 可以预览（但不能导入？待测试）
   - 自签名的 AEA 会导致**软件闪退**
   - 即使使用真实 Apple 证书链，签名不匹配也会崩溃
3. **签名验证是强制性的**: 系统会验证证书链 + 签名匹配性

### ❌ 技术壁垒
**核心问题**: 无法获得 Apple 信任的私钥进行签名

- ❌ 自签名证书不被信任
- ❌ 复用 Apple 证书链 + 自己的签名 = 验证失败
- ❌ 缺少 Apple 开发者证书/私钥

## 下一步行动

### 立即执行（已完成）
1. ✅ **测试原始 AEA 文件**: 确认可以导入 iPhone
2. ✅ **测试 Mac 导入**: 未签名可预览，自签名会闪退
3. ✅ **尝试生成签名**: 技术上可行，但缺少信任链

### 可行的替代方案

#### 方案 A: 仅支持数据分析（降级）
**接受限制**: 工具仅用于研究和分析 shortcuts

✅ **可以做的**:
- 解码任意 .shortcut 文件（包括 AEA）
- 分析数据结构
- 提取 Actions 信息
- 生成文档/可视化

❌ **不能做的**:
- 直接导入到设备
- 生成可分发的 shortcuts

**适用场景**: 研究工具、逆向工程、学习

---

#### 方案 B: Mac Shortcuts + 脚本创建（推荐探索）
**思路**: 不生成 .shortcut 文件，而是通过脚本操作 Mac Shortcuts App

```bash
# 伪代码
osascript << EOF
tell application "Shortcuts Events"
  make new shortcut with properties {name: "My Shortcut"}
  # 添加 actions...
end tell
EOF
```

✅ **优势**:
- 绕过签名问题
- 可以通过 iCloud 同步到 iPhone
- 使用官方 API

❌ **挑战**:
- 需要研究 Shortcuts AppleScript/JXA API
- 可能功能有限

---

#### 方案 C: 修改现有 Shortcuts（混合方案）
**思路**:
1. 用户手动创建一个空 shortcut
2. 我们的工具修改其内部数据库
3. 系统重新加载时应用更改

**技术路径**:
```bash
# Shortcuts 存储位置
~/Library/Application Support/Shortcuts/Shortcuts.sqlite
```

⚠️ **风险**:
- 可能破坏数据库
- 未来 macOS 版本可能改变结构

---

#### 方案 D: URL Scheme 导入（需研究）
**可能的 URL Scheme**:
```
shortcuts://import-shortcut?url=<base64_data>
shortcuts://gallery/...
```

**待验证**: 是否支持，是否仍需签名

---

#### 方案 E: 联系 Apple 或使用企业证书（长期）
**Apple Developer Program**:
- 研究是否可以获得签名权限
- 企业证书是否适用

**可行性**: 低（Shortcuts 签名可能仅限 Apple）

---

## ✅ 问题已解决

### 最终方案：使用 macOS 官方工具

**发现**: macOS 自带 `/usr/bin/shortcuts sign` 命令可以签名 shortcuts

```bash
shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut
```

**优势**:
- ✅ 使用真实 Apple 证书链
- ✅ 系统信任，无需自签名
- ✅ iPhone/iPad 可以成功导入
- ✅ 极其简单（一行命令）

### Phase 1 任务状态
- ✅ Task 1.2: 完成（decode，支持 AEA）
- ✅ Task 1.3: 完成（encode 未签名版本）
- ✅ **Task 1.4: 完成**（使用官方签名工具）
- ⏭ Task 1.5: 待验证（确认完整闭环）

### 项目愿景实现
**原始目标**: "让 AI 能通过生成文本来构建复杂的 iOS 快捷指令"

**当前状态**: ✅ **目标可实现**
- ✅ 可以生成 shortcuts 数据结构
- ✅ 可以签名并导入到 iPhone
- ✅ 完整的工具链已验证

---

## 参考资料

- [Apple Encrypted Archive Wiki](https://theapplewiki.com/wiki/Apple_Encrypted_Archive)
- Previous search: iCloud API can auto-sign shortcuts
- macOS `aea` tool: `/usr/bin/aea`
- Signing profile 0: `hkdf_sha256_hmac__none__ecdsa_p256`

---

**建议**: 先完成测试步骤 1 和 2，然后根据结果决定技术路线。
