# Task 3C-7: 多平台配置、调试开关与推理深度

## 1. 需求

在 `modify_3full.py` 中重构 API 配置方案，替代 3C-6 的简单外置：

1. **调试模式** — Boolean 开关，默认关闭。关闭时跳过 API 前后的通知。
2. **平台选择** — 火山引擎(默认) / DeepSeek / 其他。根据选择自动应用对应 URL 和密钥。
3. **模型选择** — 编号制（1-5），内置映射字典自动解析模型名，用户无需手打。
4. **reasoning_effort** — minimal(默认) / low / medium / high。

## 2. 核心设计决策

### 2.1 动态字典查找（避免嵌套条件分支）

**已验证**: `WFDictionaryKey` 支持 `WFTextTokenString`（3-full.xml line 1666，用"随机数"输出做动态 key）。

利用这一能力，平台调度只需 **4 个 action**（而非嵌套 conditional 的 16+ 个）：

```
gettext "密钥(￼)" → 动态构造 key 名
getvalueforkey [动态key] from 密钥字典 → 取值
```

密钥字典中按 `密钥(平台名)` / `地址(平台名)` 的命名规律存储，运行时拼接查找。

### 2.2 内置映射字典（模型编号 → 模型名）

用户在配置中填数字编号（1-5），运行时通过一个**内置的 dictionary action**（hardcoded，用户不可见）映射为真实模型名。避免用户手打 `doubao-seed-2-0-mini-260215` 这类长字符串。

### 2.3 命名变量共享数据

模型调度有"其他"分支，需 conditional。用 `setvariable` 在分支间共享结果（无 `getvariable` action，下游用 `{Type: "Variable", VariableName: "model"}` 引用）。

### 2.4 无 Dropdown UI

Shortcuts 配置界面只有 文本/数字/布尔 字段，没有下拉选择。平台和 reasoning_effort 通过 ImportQuestions Text 描述文字引导用户填写；模型用编号制降低出错概率。

---

## 3. 密钥字典 29C441EE 改动

### 3.1 重命名

| 原 Key | 新 Key | 说明 |
|--------|--------|------|
| `密钥` | `密钥(火山引擎)` | 火山引擎平台 API Key |

### 3.2 新增条目

| Key | WFItemType | 默认值 | 说明 |
|-----|-----------|--------|------|
| `密钥(DeepSeek)` | 0 (Text) | `""` (空) | DeepSeek API Key |
| `密钥(其他)` | 0 (Text) | `""` (空) | 自定义平台 API Key |
| `地址(火山引擎)` | 0 (Text) | `https://ark.cn-beijing.volces.com/api/v3/chat/completions` | 预填，一般无需修改 |
| `地址(DeepSeek)` | 0 (Text) | `https://api.deepseek.com/v1/chat/completions` | 预填，一般无需修改 |
| `地址(其他)` | 0 (Text) | `""` (空) | 用户自填 |
| `自定义模型` | 0 (Text) | `""` (空) | 仅当 模型=5 时使用 |

### 3.3 删除（不再添加）3C-6 条目

以下 3C-6 新增的条目不再添加（被本方案替代）：

- ~~`API地址`~~ → 被 `地址(平台名)` 替代
- ~~`模型`~~ → 移到配置字典 588A56AF（编号制）
- ~~`max_tokens`~~ → 移到配置字典 588A56AF

### 3.4 实现方式

```python
# 1. 重命名：找到 "密钥" 条目，改 key
for item in key_items:
    if item.get('WFKey', {}).get('Value', {}).get('string', '') == '密钥':
        item['WFKey']['Value']['string'] = '密钥(火山引擎)'
        break

# 2. 追加新条目
new_key_entries = [
    ('密钥(DeepSeek)', 0, {'string': ''}),
    ('密钥(其他)',     0, {'string': ''}),
    ('地址(火山引擎)', 0, {'string': 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'}),
    ('地址(DeepSeek)', 0, {'string': 'https://api.deepseek.com/v1/chat/completions'}),
    ('地址(其他)',     0, {'string': ''}),
    ('自定义模型',     0, {'string': ''}),
]
```

---

## 4. 配置字典 588A56AF 新增条目

在 `WFDictionaryFieldValueItems` 末尾追加 5 项：

| Key | WFItemType | 默认值 | 说明 |
|-----|-----------|--------|------|
| `平台` | 0 (Text) | `"火山引擎"` | 可选: 火山引擎 / DeepSeek / 其他 |
| `模型` | 3 (Number) | `"1"` | 编号: 1-4=预设模型, 5=其他（见 §5 Phase 2 映射表） |
| `max_tokens` | 3 (Number) | `"300"` | 最大输出 token 数 |
| `reasoning_effort` | 0 (Text) | `"minimal"` | 可选: minimal / low / medium / high |
| `调试模式` | 4 (Boolean) | `false` | 开启后 API 调用前后弹通知 |

Python dict 结构示例：

```python
# Number 类型 (模型编号)
{
    'WFItemType': 3,
    'WFKey': {
        'Value': {'string': '模型'},
        'WFSerializationType': 'WFTextTokenString'
    },
    'WFValue': {
        'Value': {'string': '1'},
        'WFSerializationType': 'WFTextTokenString'
    }
}
```

---

## 5. 运行时 Action 链设计

替换当前 `new_actions`（13 action）为新的 30 action 链。

### 完整 action 列表

```python
new_actions = [
    # Phase 0: 读取配置 (5)
    S1, S2, S3, S4, S5,
    # Phase 1: 平台调度 — URL + 密钥 (4)
    T_URL, R_URL, T_KEY, R_KEY,
    # Phase 2: 模型调度 — 编号映射 (7)
    MODEL_MAP, MODEL_LOOKUP, SV_MODEL_DEFAULT, MC_BEGIN, MC_CUSTOM, SV_MODEL_OVERRIDE, MC_END,
    # Phase 3: OCR + JSON body (3)
    A1, A2, A3,
    # Phase 4: 调试通知(前) (3)
    DB1_BEGIN, N1, DB1_END,
    # Phase 5: API 调用 (1)
    B,
    # Phase 6: 调试通知(后) (3)
    DB2_BEGIN, N2, DB2_END,
    # Phase 7: 解析响应 (4)
    C1, C2, C3, D
]
# Total: 5 + 4 + 7 + 3 + 3 + 1 + 3 + 4 = 30 actions
```

### Phase 0: 读取配置 (5 actions)

从配置字典 588A56AF 读取 5 个设置项：

```python
def make_cfg_read(uuid_key, dict_key):
    """读取 588A56AF 中的配置值"""
    return {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS[uuid_key],
            'WFDictionaryKey': dict_key,
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

S1 = make_cfg_read('cfg_platform', '平台')
S2 = make_cfg_read('cfg_model', '模型')
S3 = make_cfg_read('cfg_maxtokens', 'max_tokens')
S4 = make_cfg_read('cfg_reasoning', 'reasoning_effort')
S5 = make_cfg_read('cfg_debug', '调试模式')
```

### Phase 1: 平台调度 — 动态字典查找 (4 actions)

利用 `gettext` 拼接 key 名 + 动态 `WFDictionaryKey` 查找：

```python
# T_URL: gettext "地址(￼)" → "地址(火山引擎)"
T_URL = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
    'WFWorkflowActionParameters': {
        'UUID': NEW_UUIDS['url_label'],
        'WFTextActionText': {
            'Value': {
                'attachmentsByRange': {
                    '{3, 1}': {                     # "地址(" 是 3 个字符
                        'OutputName': '词典值',
                        'OutputUUID': NEW_UUIDS['cfg_platform'],
                        'Type': 'ActionOutput'
                    }
                },
                'string': '地址(￼)'                # ￼ 在 index 3
            },
            'WFSerializationType': 'WFTextTokenString'
        }
    }
}

# R_URL: getvalueforkey [T_URL output] from 29C441EE → resolved URL
R_URL = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
    'WFWorkflowActionParameters': {
        'UUID': NEW_UUIDS['resolved_url'],
        'WFDictionaryKey': {
            'Value': {
                'attachmentsByRange': {
                    '{0, 1}': {
                        'OutputName': 'Text',
                        'OutputUUID': NEW_UUIDS['url_label'],
                        'Type': 'ActionOutput'
                    }
                },
                'string': PH
            },
            'WFSerializationType': 'WFTextTokenString'
        },
        'WFInput': {
            'Value': {
                'OutputName': '词典',
                'OutputUUID': UUID_KEY_DICT,   # 29C441EE
                'Type': 'ActionOutput'
            },
            'WFSerializationType': 'WFTextTokenAttachment'
        }
    }
}

# T_KEY: gettext "密钥(￼)" → "密钥(火山引擎)"
# 同 T_URL 结构，string = '密钥(￼)'，attachment 位置 = {3, 1}

# R_KEY: getvalueforkey [T_KEY output] from 29C441EE → resolved API key
# 同 R_URL 结构
```

**位置计算**:
- `地址(` = 2 汉字 + 1 左括号 = 3 字符 → attachment 位置 `{3, 1}`
- `密钥(` = 2 汉字 + 1 左括号 = 3 字符 → attachment 位置 `{3, 1}`

> ⚠️ **风险**: 动态 WFDictionaryKey 在 3-full.xml line 1666 已验证可用。但若 iPhone 行为不一致，回退方案见 §5.9。

### Phase 2: 模型调度 — 编号映射 (7 actions)

#### 模型编号映射表

| 编号 | 模型名 |
|------|--------|
| 1 | `doubao-seed-2-0-mini-260215`（默认） |
| 2 | `deepseek-chat` |
| 3 | `doubao-seed-1-6-flash-250828` |
| 4 | `deepseek-v3-2-251201` |
| 5 | 其他（读取密钥字典中的「自定义模型」字段） |

#### Action 链

```python
# MODEL_MAP: 内置映射字典（hardcoded，用户不可见）
MODEL_MAP = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.dictionary',
    'WFWorkflowActionParameters': {
        'UUID': NEW_UUIDS['model_map'],
        'WFItems': {
            'Value': {
                'WFDictionaryFieldValueItems': [
                    # key "1" → "doubao-seed-2-0-mini-260215"
                    {
                        'WFItemType': 0,
                        'WFKey': {'Value': {'string': '1'}, 'WFSerializationType': 'WFTextTokenString'},
                        'WFValue': {'Value': {'string': 'doubao-seed-2-0-mini-260215'}, 'WFSerializationType': 'WFTextTokenString'}
                    },
                    # key "2" → "deepseek-chat"
                    {
                        'WFItemType': 0,
                        'WFKey': {'Value': {'string': '2'}, 'WFSerializationType': 'WFTextTokenString'},
                        'WFValue': {'Value': {'string': 'deepseek-chat'}, 'WFSerializationType': 'WFTextTokenString'}
                    },
                    # key "3" → "doubao-seed-1-6-flash-250828"
                    {
                        'WFItemType': 0,
                        'WFKey': {'Value': {'string': '3'}, 'WFSerializationType': 'WFTextTokenString'},
                        'WFValue': {'Value': {'string': 'doubao-seed-1-6-flash-250828'}, 'WFSerializationType': 'WFTextTokenString'}
                    },
                    # key "4" → "deepseek-v3-2-251201"
                    {
                        'WFItemType': 0,
                        'WFKey': {'Value': {'string': '4'}, 'WFSerializationType': 'WFTextTokenString'},
                        'WFValue': {'Value': {'string': 'deepseek-v3-2-251201'}, 'WFSerializationType': 'WFTextTokenString'}
                    },
                ]
            },
            'WFSerializationType': 'WFDictionaryFieldValue'
        }
    }
}

# MODEL_LOOKUP: getvalueforkey [S2] from MODEL_MAP → 模型名（动态 key）
MODEL_LOOKUP = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
    'WFWorkflowActionParameters': {
        'UUID': NEW_UUIDS['model_lookup'],
        'WFDictionaryKey': {
            'Value': {
                'attachmentsByRange': {
                    '{0, 1}': {
                        'OutputName': '词典值',
                        'OutputUUID': NEW_UUIDS['cfg_model'],   # S2 的输出
                        'Type': 'ActionOutput'
                    }
                },
                'string': PH
            },
            'WFSerializationType': 'WFTextTokenString'
        },
        'WFInput': {
            'Value': {
                'OutputName': '词典',
                'OutputUUID': NEW_UUIDS['model_map'],           # MODEL_MAP 的输出
                'Type': 'ActionOutput'
            },
            'WFSerializationType': 'WFTextTokenAttachment'
        }
    }
}

# SV_MODEL_DEFAULT: setvariable "model" = MODEL_LOOKUP 输出（编号 1-4 直接命中）
SV_MODEL_DEFAULT = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
    'WFWorkflowActionParameters': {
        'WFVariableName': 'model',
        'WFInput': {
            'Value': {
                'OutputName': '词典值',
                'OutputUUID': NEW_UUIDS['model_lookup'],
                'Type': 'ActionOutput'
            },
            'WFSerializationType': 'WFTextTokenAttachment'
        }
    }
}

# MC_BEGIN: conditional (S2 ≥ 5)
# 编号 5 在 MODEL_MAP 中无对应 → lookup 返空 → 需读自定义模型
# ⚠️ 原设计用 WFCondition=0 文本等于，iPhone 实测仍按数值解析为"小于"
# 修正为 WFCondition=4（≥5），编号 1-4 不满足跳过，编号 5 进入自定义分支
MC_BEGIN = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
    'WFWorkflowActionParameters': {
        'GroupingIdentifier': NEW_UUIDS['model_cond_group'],
        'UUID': NEW_UUIDS['model_cond_begin'],
        'WFCondition': 4,                        # ≥ (数值模式)
        'WFControlFlowMode': 0,                   # BEGIN
        'WFInput': {
            'Type': 'Variable',
            'Variable': {
                'Value': {
                    'Aggrandizements': [{
                        'CoercionItemClass': 'WFNumberContentItem',
                        'Type': 'WFCoercionVariableAggrandizement'
                    }],
                    'OutputName': '词典值',
                    'OutputUUID': NEW_UUIDS['cfg_model'],
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        },
        'WFNumberValue': '5'
    }
}

# MC_CUSTOM: getvalueforkey "自定义模型" from 29C441EE
MC_CUSTOM = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
    'WFWorkflowActionParameters': {
        'UUID': NEW_UUIDS['model_custom'],
        'WFDictionaryKey': '自定义模型',
        'WFInput': {
            'Value': {
                'OutputName': '词典',
                'OutputUUID': UUID_KEY_DICT,
                'Type': 'ActionOutput'
            },
            'WFSerializationType': 'WFTextTokenAttachment'
        }
    }
}

# SV_MODEL_OVERRIDE: setvariable "model" = MC_CUSTOM output (覆盖默认空值)
SV_MODEL_OVERRIDE = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.setvariable',
    'WFWorkflowActionParameters': {
        'WFVariableName': 'model',
        'WFInput': {
            'Value': {
                'OutputName': '词典值',
                'OutputUUID': NEW_UUIDS['model_custom'],
                'Type': 'ActionOutput'
            },
            'WFSerializationType': 'WFTextTokenAttachment'
        }
    }
}

# MC_END: conditional END（无 ELSE — 编号 1-4 时 model 已由 lookup 赋值）
MC_END = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
    'WFWorkflowActionParameters': {
        'GroupingIdentifier': NEW_UUIDS['model_cond_group'],
        'UUID': NEW_UUIDS['model_cond_end'],
        'WFControlFlowMode': 2                    # END
    }
}
```

**工作原理**:
- 编号 1-4: `MODEL_LOOKUP` 从映射字典命中真实模型名 → `setvariable "model"` 生效 → conditional 不触发
- 编号 5: `MODEL_LOOKUP` 返空（映射字典无 key "5"）→ `setvariable "model"` 设为空 → conditional 触发 → 从密钥字典读 `自定义模型` 覆盖

### Phase 3: OCR + JSON body (3 actions)

与现有 A1/A2/A3 相同，但 A2 的 TEMPLATE 和 attachment 映射变更（见 §6）。

### Phase 4 & 6: 调试通知 (各 3 actions)

用 conditional 包裹 N1/N2，仅调试模式开启时弹通知：

```python
# DB1_BEGIN: conditional (S5 coerce Number ≥ 1)
DB1_BEGIN = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
    'WFWorkflowActionParameters': {
        'GroupingIdentifier': NEW_UUIDS['debug1_group'],
        'UUID': NEW_UUIDS['debug1_begin'],
        'WFCondition': 4,                         # ≥
        'WFControlFlowMode': 0,                   # BEGIN
        'WFInput': {
            'Type': 'Variable',
            'Variable': {
                'Value': {
                    'Aggrandizements': [{
                        'CoercionItemClass': 'WFNumberContentItem',
                        'Type': 'WFCoercionVariableAggrandizement'
                    }],
                    'OutputName': '词典值',
                    'OutputUUID': NEW_UUIDS['cfg_debug'],
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        },
        'WFNumberValue': '1'
    }
}

# N1: notification "⏳ 正在调用 {平台} API..."
# N1 body 用 WFTextTokenString，嵌入 S1（平台名）

DB1_END = {
    'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
    'WFWorkflowActionParameters': {
        'GroupingIdentifier': NEW_UUIDS['debug1_group'],
        'UUID': NEW_UUIDS['debug1_end'],
        'WFControlFlowMode': 2                    # END
    }
}

# DB2 同理，包裹 N2
```

**N1 通知文本**: `"⏳ 正在调用 ￼ API..."` 其中 ￼ = S1 平台名（需用 WFTextTokenString + attachmentsByRange）

**N2 通知文本**: `"✅ ￼"` 其中 ￼ = downloadurl 原始响应（同现有 N2）

### Phase 5: API 调用 (1 action)

downloadurl B 的变更：
- **WFURL**: 引用 R_URL 的输出（`NEW_UUIDS['resolved_url']`），不再硬编码
- **Authorization**: `Bearer ￼` 其中 ￼ = R_KEY 的输出（`NEW_UUIDS['resolved_key']`），不再引用 UUID_API_KEY

### Phase 7: 解析响应 (4 actions)

C1/C2/C3/D 与现有相同，无变更。

### 5.9 回退方案（若动态 WFDictionaryKey 不可用）

如果 iPhone 测试中动态字典查找不工作，用嵌套 conditional + setvariable 替代 Phase 1：

```
if 平台 == "火山引擎":
    setvariable "api_url" = text "https://ark..."
    setvariable "api_key" = getvalueforkey "密钥(火山引擎)"
elif 平台 == "DeepSeek":
    setvariable "api_url" = text "https://api.deepseek..."
    setvariable "api_key" = getvalueforkey "密钥(DeepSeek)"
else:
    setvariable "api_url" = getvalueforkey "地址(其他)"
    setvariable "api_key" = getvalueforkey "密钥(其他)"
```

这需要 ~18 actions 替代 Phase 1 的 4 actions。代价大但保证兼容。

---

## 6. TEMPLATE 变更 (10 → 11 占位符)

新增 ￼11 = reasoning_effort：

```python
TEMPLATE = (
    '{"model":"' + PH +                           # ￼1 模型名 (Variable "model")
    '","messages":[{"role":"system","content":"'
    ...（中间不变）...
    + PH +                                         # ￼9 OCR文本
    '"}],"max_tokens":' + PH +                     # ￼10 max_tokens (S3)
    ',"temperature":0'
    ',"reasoning_effort":"' + PH +                 # ￼11 reasoning_effort (S4) ← NEW
    '","thinking":{"type":"disabled"}}'
)
```

### 占位符映射 (11 个)

| # | 字段 | 引用 | 类型 |
|---|------|------|------|
| ￼1 | 模型 | Variable "model" | `{Type: "Variable", VariableName: "model"}` |
| ￼2 | 当前日期 | CurrentDate yyyy-MM-dd HH:mm | `{Type: "CurrentDate", ...}` |
| ￼3-￼7 | iCost 实体 | 原有 5 个 entity ref | `{Type: "ActionOutput", ...}` |
| ￼8 | 自定义规则 | UUID_CUSTOM_RULES | `{Type: "ActionOutput", ...}` |
| ￼9 | OCR 文本 | A1 (extracttextfromimage) | `{Type: "ActionOutput", ...}` |
| ￼10 | max_tokens | S3 (cfg_maxtokens) | `{Type: "ActionOutput", ...}` |
| ￼11 | reasoning_effort | S4 (cfg_reasoning) | `{Type: "ActionOutput", ...}` |

**关键变更**: ￼1 从 ActionOutput 改为 **Variable** 引用：

```python
# 旧: ￼1 = GV2 的输出 (ActionOutput)
attachments[f'{{{pos[0]}, 1}}'] = {
    'OutputName': '词典值',
    'OutputUUID': NEW_UUIDS['cfg_model'],
    'Type': 'ActionOutput'
}

# 新: ￼1 = Variable "model"
attachments[f'{{{pos[0]}, 1}}'] = {
    'Type': 'Variable',
    'VariableName': 'model'
}
```

pos 断言从 `assert len(pos) == 10` 改为 `assert len(pos) == 11`。

---

## 7. downloadurl B 变更

### WFURL

```python
# 新: 引用 R_URL (resolved_url) 的 OutputUUID
'WFURL': {
    'Value': {
        'attachmentsByRange': {
            '{0, 1}': {
                'OutputName': '词典值',
                'OutputUUID': NEW_UUIDS['resolved_url'],
                'Type': 'ActionOutput'
            }
        },
        'string': PH
    },
    'WFSerializationType': 'WFTextTokenString'
}
```

### Authorization Header

```python
# 新: 引用 R_KEY (resolved_key)，不再引用 UUID_API_KEY (D625BA13)
'{7, 1}': {
    'OutputName': '词典值',
    'OutputUUID': NEW_UUIDS['resolved_key'],
    'Type': 'ActionOutput'
}
```

---

## 8. modify_3full.py 改动清单

### 8.1 NEW_UUIDS 变更

删除: `cfg_url`（被 `url_label` + `resolved_url` 替代）

新增:
```python
NEW_UUIDS = {k: str(uuid.uuid4()).upper() for k in [
    # 保留
    'ocr', 'body', 'clean', 'choices', 'first', 'content',
    'show_random_getval', 'show_random_begin', 'show_random_else',
    'show_random_end', 'show_random_group',
    'notif_before', 'notif_after',
    # 配置读取 (替换 cfg_url/cfg_model/cfg_maxtokens)
    'cfg_platform', 'cfg_model', 'cfg_maxtokens', 'cfg_reasoning', 'cfg_debug',
    # 平台调度
    'url_label', 'resolved_url', 'key_label', 'resolved_key',
    # 模型调度
    'model_map', 'model_lookup',
    'model_cond_group', 'model_cond_begin', 'model_cond_end', 'model_custom',
    # 调试条件
    'debug1_group', 'debug1_begin', 'debug1_end',
    'debug2_group', 'debug2_begin', 'debug2_end',
]}
```

### 8.2 Fix 3 (密钥字典) 重写

- 找到 `密钥` 条目 → 重命名为 `密钥(火山引擎)`
- 追加 6 个新条目（见 §3.2）
- **不再**追加 API地址/模型/max_tokens

### 8.3 Fix 1 (配置字典) 补充

在 cfg_items 末尾追加 5 个新条目（见 §4）

### 8.4 TEMPLATE 更新

末尾添加 `,"reasoning_effort":"` + PH + `"` ，占位符从 10 → 11

### 8.5 new_actions 重建

从 `[GV1, GV2, GV3, A1, A2, A3, N1, B, N2, C1, C2, C3, D]` (13)
改为 30 action 链（见 §5 完整列表）

### 8.6 A2 attachment 映射

- ￼1 改为 Variable "model" 引用
- 新增 ￼11 (reasoning_effort → S4)

### 8.7 downloadurl B

- WFURL 引用 resolved_url
- Authorization 引用 resolved_key

### 8.8 GV1/GV2/GV3 及 make_gv 函数删除

不再需要，被 S1-S5、平台调度和模型调度替代。

---

## 9. ImportQuestions 同步

### 9.1 密钥字典 (ActionIndex=0)

1. DefaultValue 中重命名 `密钥` → `密钥(火山引擎)`
2. DefaultValue 追加 6 个新条目
3. Text 更新为:

```
🔑 API 密钥与地址配置

在你使用的平台对应的「密钥」字段粘贴 API Key。
地址已预填，一般无需修改。

• 密钥(火山引擎)：火山引擎/豆包平台的 API Key
• 密钥(DeepSeek)：DeepSeek 平台的 API Key
• 密钥(其他)：自定义平台的 API Key
• 地址(其他)：自定义平台的 API 端点 URL
• 自定义模型：当「模型」设为 5 时，在此填写模型名

⚠️ 请勿修改「开发者」「版本号」及预填地址。
```

### 9.2 配置字典 (ActionIndex=cfg_idx)

1. DefaultValue 追加 5 个新条目
2. Text 追加:

```
🖥️ 平台：API 平台（填写: 火山引擎 / DeepSeek / 其他），默认火山引擎。
🤖 模型：选择编号
  1 = doubao-seed-2-0-mini-260215（默认）
  2 = deepseek-chat
  3 = doubao-seed-1-6-flash-250828
  4 = deepseek-v3-2-251201
  5 = 其他（需在密钥字典中填写「自定义模型」）
📏 max_tokens：最大输出 token 数，默认 300。
⚡ reasoning_effort：推理深度（填写: minimal / low / medium / high），默认 minimal。
🔧 调试模式：开启后在 API 调用前后弹出通知，用于排查问题。
```

---

## 10. 新增 UUID 列表

| Key | 用途 |
|-----|------|
| `cfg_platform` | S1: 读取 平台 |
| `cfg_model` | S2: 读取 模型编号（替代旧 cfg_model） |
| `cfg_maxtokens` | S3: 读取 max_tokens（替代旧 cfg_maxtokens） |
| `cfg_reasoning` | S4: 读取 reasoning_effort |
| `cfg_debug` | S5: 读取 调试模式 |
| `url_label` | T_URL: gettext "地址(￼)" |
| `resolved_url` | R_URL: 动态查找 URL |
| `key_label` | T_KEY: gettext "密钥(￼)" |
| `resolved_key` | R_KEY: 动态查找 API Key |
| `model_map` | MODEL_MAP: 内置编号→模型名映射字典 |
| `model_lookup` | MODEL_LOOKUP: 从 MODEL_MAP 查找模型名 |
| `model_cond_group` | 模型 conditional GroupingIdentifier |
| `model_cond_begin` | 模型 conditional BEGIN |
| `model_cond_end` | 模型 conditional END |
| `model_custom` | getvalueforkey "自定义模型" |
| `debug1_group` | 调试通知(前) GroupingIdentifier |
| `debug1_begin` | 调试通知(前) BEGIN |
| `debug1_end` | 调试通知(前) END |
| `debug2_group` | 调试通知(后) GroupingIdentifier |
| `debug2_begin` | 调试通知(后) BEGIN |
| `debug2_end` | 调试通知(后) END |

删除: `cfg_url`（旧 3C-6）

---

## 11. 验证要点

### 11.1 构建验证
- [ ] `modify_3full.py` 运行无报错
- [ ] `3-full-deepseek.xml` 中新增的 conditional 结构正确（GroupingIdentifier 配对）
- [ ] TEMPLATE 有 11 个 ￼ 占位符，attachments 有 11 项
- [ ] MODEL_MAP 字典包含 4 条映射

### 11.2 iPhone 验证 — 默认配置（火山引擎 + 模型 1）
- [ ] build → sign → 导入 iPhone 成功
- [ ] 配置页显示所有新字段
- [ ] 填入火山引擎 API Key，模型保持 1（默认），记账功能正常
- [ ] 默认调试模式关闭：API 调用前后**不弹**通知

### 11.3 iPhone 验证 — 切换平台
- [ ] 平台改为 `DeepSeek`，模型改为 `2`，填入 DeepSeek API Key → 记账正常
- [ ] 平台改为 `其他`，填入智谱 URL + Key，模型改为 `5`，自定义模型填 `glm-4.5-airx` → 记账正常
- [ ] **关键**: 动态字典查找能正确按平台名取值

### 11.4 iPhone 验证 — 调试模式
- [ ] 开启调试模式 → API 调用前弹"⏳ 正在调用 {平台} API..."，调用后弹"✅ {响应内容}"

### 11.5 iPhone 验证 — 模型编号映射
- [ ] 模型 1-4 各编号能正确映射为对应模型名（通过调试模式查看请求内容确认）
- [ ] 模型 5 能正确读取自定义模型名

---

## 12. 与 3C-6 的关系

本任务 **替代** 3C-6 的所有 API 配置逻辑。3C-6 的 GV1/GV2/GV3、key dict 的 API地址/模型/max_tokens 条目、以及固定 URL 的 downloadurl 均被本方案替代。

3C-6 的代码在 `modify_3full.py` 中直接被修改，无需先回滚。
