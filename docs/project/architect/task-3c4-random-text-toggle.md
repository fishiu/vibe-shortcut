# Task 3C-4: 随机文字开关

## 1. 需求

在 `modify_3full.py` 中新增逻辑：给 3-full-deepseek 加一个 `显示随机文字` 配置开关。

- 开关位于 UI 配置字典 `588A56AF`（与界面风格、识别优惠同级）
- 默认 `false`（关闭）
- 关闭时：**跳过整个随机文字流程**（含 icost.vip 网络请求），零延迟
- 打开时：保持原有行为（调 icost.vip API → 弹通知）

## 2. 当前随机文字流程

位于 3-full.xml 的 10 个连续 action，**在主 OCR 流程之前、image.resize 之前**：

| # | Action | UUID | 说明 |
|---|--------|------|------|
| 1 | getvalueforkey | `F53BB049` | 从通知字典取 `通知内容` 类别编号 |
| 2 | conditional BEGIN | `31BA3D7A` | if 类别 ≥ 0（随机模式） |
| 3 | number.random | `2CDBC4B0` | 随机 1-15 |
| 4 | conditional ELSE | `68FFA143` | |
| 5 | number | `01DB64EE` | 用指定类别编号 |
| 6 | conditional END | `D558ACC5` | |
| 7 | downloadurl | `68593622` | **GET icost.vip/wapi/v1/public/text/text{N}** ← 延迟来源 |
| 8 | text.split | `3417F735` | 按换行拆分返回文本 |
| 9 | getitemfromlist | `5EE5A682` | Random Item |
| 10 | notification | `E6974843` | 弹出随机句子 |

**块起点** = action #1（UUID `F53BB049`）
**块终点** = action #10（UUID `E6974843`）
**块后紧接** = `image.resize`（UUID `0B4F4A02`，主流程起点）

## 3. 改动设计

### 3.1 配置字典 `588A56AF` 新增条目

在 `WFDictionaryFieldValueItems` 数组末尾追加：

```python
{
    'WFItemType': 4,   # Boolean
    'WFKey': {
        'Value': {'string': '显示随机文字'},
        'WFSerializationType': 'WFTextTokenString'
    },
    'WFValue': {
        'Value': False,
        'WFSerializationType': 'WFNumberSubstitutableState'
    }
}
```

### 3.2 配置注释更新

在 comment action（line 155-160 区域）的文本末尾追加一行：

```
🎲 显示随机文字：是否在截图后弹出随机句子（弱智吧金句/诗词等），关闭可加快记账速度。
```

### 3.3 用 conditional 包裹 10 个 action

在 10 个 action **之前**插入 2 个新 action，**之后**插入 1 个新 action：

#### 新 action W1: getvalueforkey（读取开关值）

```python
W1 = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
    'WFWorkflowActionParameters': {
        'UUID': NEW_UUIDS['show_random_getval'],
        'WFDictionaryKey': '显示随机文字',
        'WFInput': {
            'Value': {
                'OutputName': '词典',
                'OutputUUID': UUID_CONFIG_DICT,   # 588A56AF
                'Type': 'ActionOutput'
            },
            'WFSerializationType': 'WFTextTokenAttachment'
        }
    }
}
```

#### 新 action W2: conditional BEGIN（判断 == 1，即 true）

```python
W2 = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
    'WFWorkflowActionParameters': {
        'GroupingIdentifier': NEW_UUIDS['show_random_group'],
        'UUID': NEW_UUIDS['show_random_begin'],
        'WFCondition': 0,           # equals
        'WFControlFlowMode': 0,     # BEGIN
        'WFInput': {
            'Type': 'Variable',
            'Variable': {
                'Value': {
                    'Aggrandizements': [{
                        'CoercionItemClass': 'WFNumberContentItem',
                        'Type': 'WFCoercionVariableAggrandizement'
                    }],
                    'OutputName': '词典值',
                    'OutputUUID': NEW_UUIDS['show_random_getval'],
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        },
        'WFNumberValue': '1'
    }
}
```

**解释**: Boolean `true` coerce 为 Number = 1，Boolean `false` coerce 为 Number = 0。`WFCondition=0` 表示 "等于"，`WFNumberValue='1'` 表示与 1 比较。所以 `显示随机文字=false` → 0 ≠ 1 → 跳过块内容。

#### 新 action W3: conditional END

```python
W3 = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
    'WFWorkflowActionParameters': {
        'GroupingIdentifier': NEW_UUIDS['show_random_group'],
        'UUID': NEW_UUIDS['show_random_end'],
        'WFControlFlowMode': 2      # END
    }
}
```

### 3.4 插入位置

```python
# 找到块起点和终点的 action index
start_idx = find_action_idx(actions, 'F53BB049-980B-4EA5-86C6-15B821935C1D')
end_idx   = find_action_idx(actions, 'E6974843-33AE-4819-9651-6BC90DE5F949')

assert end_idx == start_idx + 9, "随机文字块应为连续 10 个 action"

# 先插后面（不影响前面的 index）
actions.insert(end_idx + 1, W3)     # conditional END

# 再插前面
actions.insert(start_idx, W2)       # conditional BEGIN
actions.insert(start_idx, W1)       # getvalueforkey（insert 到同一位置，W1 在 W2 前）
```

**注意插入顺序**：先 insert `end_idx + 1`（后方），再 insert `start_idx`（前方）。这样前方的 insert 不会影响后方已插入的位置。

### 3.5 新增 UUID 列表

在 `NEW_UUIDS` dict 中新增 4 个 key：

```python
NEW_UUIDS = {k: str(uuid.uuid4()).upper() for k in [
    'ocr', 'body', 'clean', 'choices', 'first', 'content',
    'show_random_getval', 'show_random_begin', 'show_random_end', 'show_random_group'
]}
```

## 4. 修改后的流程

```
[config dict 588A56AF]  显示随机文字 = false
        ↓
getvalueforkey 显示随机文字              ← W1 新增
conditional BEGIN (== 1? → false，跳过)  ← W2 新增
  ┊ getvalueforkey 通知内容             ← 原有，被跳过
  ┊ conditional (随机/指定)              ← 原有，被跳过
  ┊ downloadurl icost.vip               ← 原有，被跳过 ★
  ┊ text.split                          ← 原有，被跳过
  ┊ getitemfromlist Random               ← 原有，被跳过
  ┊ notification                        ← 原有，被跳过
conditional END                          ← W3 新增
image.resize (主流程继续)
```

## 5. 在 modify_3full.py 中的执行顺序

建议放在 Fix 1（界面风格）之后、Find key action indices 之前：

```
Fix 1: 界面风格 3→1                     ← 已有
Fix 2: 添加 显示随机文字 + conditional 包裹  ← 新增
Fix 3: CurrentDate HH:mm                ← 已有（在后续流程中）
主流程: 替换 downloadurl（DeepSeek）      ← 已有
```

**关键约束**：Fix 2 的 insert 会改变后续 action 的 index。由于 Fix 2 在 `find_action_idx(UUID_DOWNLOAD)` 之前执行，而 `find_action_idx` 按 UUID 查找（不依赖 index），所以**不会受影响**。

## 6. 验证要点

- [ ] `modify_3full.py` 运行无报错
- [ ] `3-full-deepseek.xml` 中 conditional 包裹结构正确（GroupingIdentifier 一致、BEGIN/END 配对）
- [ ] build → sign → 导入 iPhone
- [ ] 默认行为：截图后**不弹出**随机句子，直接进入 OCR 识别
- [ ] 修改配置 `显示随机文字=true` 后：截图后弹出随机句子（原有行为）
- [ ] 两种模式下记账主流程均正常
