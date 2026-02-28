# Engineer Log: Task 2.9 - Sample C 分析

> **Author**: Claude Opus 4.6 (Engineer Role)
> **Date**: 2026-02-28
> **Related Task**: Phase 2 - Task 2.9
> **Status**: 🟢 Completed

---

## 1. 样本信息

- **文件**: `samples/money/3-full.shortcut` (AEA 签名)
- **功能**: 完全体记账工具（OCR 截屏识别 + DeepSeek API 解析 + 多账本/分类/账户/货币/标签管理 + 转账 + 配置系统）
- **Actions 数量**: 1140
- **独立 Action 类型**: 43 种（22 种新增）
- **导出 XML**: `samples/money/3-full.xml` (39607 行)

---

## 2. 新增 Action 类型（22 种）

### 新增系统 Action（16 种）

| Action ID | 简称 | 出现次数 | 类别 |
|-----------|------|:--------:|------|
| `number` | 数字字面量 | 10 | 数据 |
| `calculateexpression` | 计算表达式 | 3 | 数据 |
| `number.random` | 随机数 | 2 | 数据 |
| `text.split` | 文本分割 | 1 | 数据 |
| `filter.files` | 过滤/查询 | 5 | 数据 |
| `repeat.count` | 循环(固定次数) | 8 | 控制流 |
| `repeat.each` | 循环(遍历列表) | 2 | 控制流 |
| `delay` | 延迟 | 2 | 系统 |
| `getdevicedetails` | 获取设备信息 | 3 | 系统 |
| `openurl` | 打开 URL | 7 | 系统 |
| `openapp` | 打开 App | 1 | 系统 |
| `image.crop` | 裁剪图片 | 1 | 图片 |
| `image.resize` | 调整图片大小 | 1 | 图片 |
| `vibrate` | 震动 | 1 | 系统 |
| `showresult` | 显示结果 | 1 | 交互 |
| `setclipboard` | 设置剪贴板 | 1 | 系统 |

### 新增第三方 Action（6 种）

| Action ID | 简称 | 出现次数 |
|-----------|------|:--------:|
| `*.ICMarkAShortcutTransferRecordIntent` | 记录转账 | 7 |
| `*.ICRouterShortcut` | 路由/导航 | 4 |
| `*.ICSearchBookEntity` | 查询账本 | 2 |
| `*.ICSearchCurrencyEntity` | 查询货币 | 3 |
| `*.ICSearchTagEntity` | 查询标签 | 2 |
| `com.apple.ShortcutsActions.ShowControlCenterAction` | 控制中心 | 1 |

---

## 3. 关键技术发现

### 3.1 循环结构 — repeat.count / repeat.each

与 conditional 和 choosefrommenu 相同的 `GroupingIdentifier` + `WFControlFlowMode` 模式：

**repeat.count（固定次数循环）**:
- mode=0 (BEGIN): 含 `WFRepeatCount`（循环次数，float 类型）
- mode=2 (END): 结束标记，有 UUID
- **没有 mode=1**（与 conditional 的 else 不同）

**repeat.each（遍历列表）**:
- mode=0 (BEGIN): 含 `WFInput`（要遍历的列表，WFTextTokenAttachment）
- mode=2 (END): 结束标记，有 UUID
- 循环体内通过 action UUID 引用 "Repeat Item"

### 3.2 WFCondition=100 — "有任何值" (Has Any Value)

新发现的比较运算符。完整运算符表更新：

| 值 | 含义 | 适用类型 |
|:-:|------|---------|
| 0 | 等于 (=) | 数字/文本 |
| 1 | 不等于 (≠) | 数字/文本 |
| 2 | 小于 (<) | 数字 |
| 3 | 大于 (>) | 数字 |
| 4 | 大于等于 (≥) | 数字 |
| 5 | 小于等于 (≤) | 数字 |
| 100 | 有任何值 (Has Any Value) | 任意 |

WFCondition=100 用于检查变量是否非空/非 nil。配合 `WFConditionalActionString` 参数可指定包含文本的匹配。

### 3.3 WFItemType 完整值

| 值 | 类型 | 示例 |
|:-:|------|------|
| 0 | Text (文本) | `api_key: "sk-xxx"` |
| 1 | Dictionary (词典) | 嵌套词典值 |
| 3 | Number (数字) | `版本号: 2.42` |
| 4 | Boolean (布尔) | `显示交易属性: True` |
| 5 | Array (数组) | 列表值 |

### 3.4 WFContentPredicateTableTemplate — 过滤查询

`filter.files` 和部分第三方 action 使用的查询条件序列化类型：

```
WFContentItemFilter:
  WFSerializationType: WFContentPredicateTableTemplate
  Value:
    WFActionParameterFilterPrefix: 1
    WFContentPredicateBoundedDate: false
    WFActionParameterFilterTemplates:
      - Operator: 4       # 比较运算符
        Property: Name    # 属性名
        Removable: true
        Values:
          String: "xxx"   # 比较值
          Unit: ...
```

### 3.5 calculateexpression — 表达式计算

输入是 WFTextTokenString，可以在表达式中嵌入变量：
- 示例: `Input.string = "￼+￼"`（两个变量相加）
- 支持数学运算符：`+`, `-`, `*`, `/` 等

### 3.6 验证遗留项结果

**WFCondition=4**：Sample C 中出现 82 次，结合大量数字比较场景，确认为 **≥ (大于等于)**。

**WFItemType**：确认 5 种值（0=Text, 1=Dictionary, 3=Number, 4=Boolean, 5=Array），注意 **没有 2**。

---

## 4. 产出文件

- `samples/money/3-full.xml` — XML plist 无损导出
- `docs/project/engineer/task-2.9-sample-c-analysis.md` — 本分析文档
