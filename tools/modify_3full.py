#!/usr/bin/env python3
"""
Task 3C-2: Replace icost.vip API call with DeepSeek in 3-full.xml

Surgical modification:
  1. Insert 3 actions before downloadurl (OCR + JSON body builder + newline cleaner)
  2. Replace downloadurl (icost.vip → DeepSeek API)
  3. Insert 3 actions after downloadurl (parse DeepSeek response chain)
  4. Modify detect.dictionary input to reference parsed content

Usage:
    python tools/modify_3full.py
"""

import copy
import plistlib
import uuid
from pathlib import Path

# === File paths ===
BASE = Path(__file__).parent.parent
INPUT = BASE / 'samples' / 'money' / '3-full.xml'
OUTPUT = BASE / 'samples' / 'money' / '3-full-deepseek.xml'

# === Existing UUIDs (from 3-full.xml) ===
UUID_IMAGE_RESIZE = '0B4F4A02-1E9A-4B90-9391-CE8950343539'
UUID_EXP_FIRST    = '6724C445-3E84-42FA-AD33-1CD9AEA79FF3'
UUID_EXP_SECOND   = '1EDA8BA8-63C6-49BC-A435-B06E25F90FC2'
UUID_INCOME       = '7FEC0A01-66F2-42BA-8663-E5A3755B7C43'
UUID_ASSET        = '2493C32C-EF78-4A09-88B7-B7AA729FCED7'
UUID_TAG          = 'E6362569-6744-4835-BBAA-12428853205C'
UUID_CUSTOM_RULES = '4856151E-17D0-45C6-B4F0-DC03CE6B5E6D'
UUID_API_KEY      = 'D625BA13-A5F8-4D69-955E-29681DF71DD6'
UUID_DOWNLOAD     = '86D23FE2-31E6-489C-86BE-1B351FE246C5'
UUID_DETECT_DICT  = 'CDA2A1C9-17AB-4840-AF03-C0701246A682'
UUID_CONFIG_DICT  = '588A56AF-C875-493B-BF05-B5347751087B'
UUID_RANDOM_START = 'F53BB049-980B-4EA5-86C6-15B821935C1D'
UUID_RANDOM_END   = 'E6974843-33AE-4819-9651-6BC90DE5F949'
UUID_KEY_DICT     = '29C441EE-B4F5-4A97-9435-A2E321437957'

# === Generate new UUIDs ===
NEW_UUIDS = {k: str(uuid.uuid4()).upper() for k in [
    'ocr', 'body', 'clean', 'choices', 'first', 'content',
    'show_random_getval', 'show_random_begin', 'show_random_else',
    'show_random_end', 'show_random_group',
    'notif_before', 'notif_after',
    # 配置读取
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

PH = '\ufffc'  # U+FFFC placeholder character

# === JSON body template ===
# Contains 10 ￼ placeholders for runtime substitution by Shortcuts.
# ￼1=模型, ￼2=日期, ￼3-7=iCost实体, ￼8=自定义规则, ￼9=OCR文本, ￼10=max_tokens
# \n and \" are literal two-character sequences (JSON encoding).
TEMPLATE = (
    '{"model":"' + PH +
    '","messages":[{"role":"system","content":"'
    '你是记账识别助手。分析用户提供的OCR文字，提取账单信息。只返回JSON，不要输出任何其他内容。'
    '\\n\\n返回格式：\\n'
    '{\\"answer\\":[{\\"type\\":\\"支出\\",\\"amount\\":0,\\"CC\\":\\"分类名\\",'
    '\\"date\\":\\"YYYY-MM-DD HH:mm\\",\\"shop\\":\\"商户名\\",\\"remark\\":\\"备注\\",'
    '\\"tag\\":\\"标签\\",\\"currency\\":\\"CNY\\",\\"account\\":\\"账户名\\",'
    '\\"from_account\\":\\"\\",\\"to_account\\":\\"\\",\\"fee\\":0,\\"discount\\":0}]}'
    '\\n\\n字段规则：\\n'
    '- type: 支出/收入/转账\\n'
    '- CC: 必须从下方分类列表中选择\\n'
    '- account: 必须从下方账户列表中选择\\n'
    '- tag: 如匹配下方标签列表则填写，否则留空\\n'
    '- date: 格式YYYY-MM-DD HH:mm，无法识别则用今天: ' + PH +
    '\\n- amount: 金额数字\\n'
    '- 多笔返回多个对象，无法识别返回{\\"answer\\":[]}\\n\\n'
    '支出分类：' + PH +
    '\\n支出子分类：' + PH +
    '\\n收入分类：' + PH +
    '\\n账户：' + PH +
    '\\n标签：' + PH +
    '\\n' + PH +
    '"},{"role":"user","content":"文字内容：\\n'
    + PH +
    '"}],"max_tokens":' + PH +
    ',"temperature":0'
    ',"reasoning_effort":"' + PH +
    '","thinking":{"type":"disabled"}}'
)


# === Helper functions ===

def find_positions(s, ch):
    """Find all positions of character ch in string s."""
    positions = []
    idx = 0
    while True:
        pos = s.find(ch, idx)
        if pos == -1:
            break
        positions.append(pos)
        idx = pos + 1
    return positions


def find_action_idx(actions, target_uuid):
    """Find action index by exact UUID match."""
    for i, action in enumerate(actions):
        params = action.get('WFWorkflowActionParameters', {})
        if params.get('UUID') == target_uuid:
            return i
    raise ValueError(f"Action with UUID {target_uuid} not found")


def find_attachment_for_uuid(obj, target_uuid):
    """Recursively find attachment dict with matching OutputUUID. Returns deep copy."""
    if isinstance(obj, dict):
        if obj.get('OutputUUID') == target_uuid:
            return copy.deepcopy(obj)
        for v in obj.values():
            if isinstance(v, (dict, list)):
                result = find_attachment_for_uuid(v, target_uuid)
                if result:
                    return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_attachment_for_uuid(item, target_uuid)
            if result:
                return result
    return None


def make_simple_entity_attachment(uuid_str, output_name):
    """Fallback: .name property attachment without data block."""
    return {
        'Aggrandizements': [{
            'PropertyName': 'name',
            'PropertyUserInfo': {
                'WFLinkEntityContentPropertyUserInfoPropertyIdentifier': 'name'
            },
            'Type': 'WFPropertyVariableAggrandizement'
        }],
        'OutputName': output_name,
        'OutputUUID': uuid_str,
        'Type': 'ActionOutput'
    }


# === Main ===

def main():
    print("=== Task 3C-2: Replace icost.vip with DeepSeek ===\n")

    # Load source XML
    data = plistlib.loads(INPUT.read_bytes())
    actions = data['WFWorkflowActions']
    print(f"Loaded {INPUT.name}: {len(actions)} actions")

    # Fix 1: Change 界面风格 from "3" (简易) to "1" (小票, full features)
    cfg_idx = find_action_idx(actions, UUID_CONFIG_DICT)
    cfg_items = actions[cfg_idx]['WFWorkflowActionParameters']['WFItems']['Value']['WFDictionaryFieldValueItems']
    for item in cfg_items:
        key_str = item.get('WFKey', {}).get('Value', {}).get('string', '')
        if key_str == '界面风格':
            old_val = item['WFValue']['Value']['string']
            item['WFValue']['Value']['string'] = '1'
            print(f"  Fix 1a: 界面风格 '{old_val}' → '1' (at action index {cfg_idx})")
        if key_str == '识别优惠':
            old_val = item['WFValue']['Value']
            item['WFValue']['Value'] = False
            print(f"  Fix 1b: 识别优惠 {old_val} → False")
        # 3C-8b: 显示记录详情 保持原值 true，gettext 中精简内容（只显示入账账本）

    # Fix 1c: Sync WFWorkflowImportQuestions DefaultValue for config dict (ActionIndex=2)
    for iq in data.get('WFWorkflowImportQuestions', []):
        if iq.get('ActionIndex') == cfg_idx and iq.get('ParameterKey') == 'WFItems':
            dv_items = iq['DefaultValue']['Value']['WFDictionaryFieldValueItems']
            for dv_item in dv_items:
                k = dv_item.get('WFKey', {}).get('Value', {}).get('string', '')
                if k == '界面风格':
                    dv_item['WFValue']['Value']['string'] = '1'
                    print(f"  Fix 1c: ImportQuestions 界面风格 → '1'")
                if k == '识别优惠':
                    dv_item['WFValue']['Value'] = False
                    print(f"  Fix 1c: ImportQuestions 识别优惠 → False")
                # 3C-8b: 显示记录详情 保持原值 true
            # Add 显示随机文字 entry
            dv_items.append({
                'WFItemType': 4,
                'WFKey': {
                    'Value': {'string': '显示随机文字'},
                    'WFSerializationType': 'WFTextTokenString'
                },
                'WFValue': {
                    'Value': False,
                    'WFSerializationType': 'WFNumberSubstitutableState'
                }
            })
            print(f"  Fix 1c: ImportQuestions added '显示随机文字' = false")
            # Update Text description
            iq['Text'] = iq['Text'].rstrip() + \
                '\n🎲 显示随机文字：是否在截图后弹出随机句子（弱智吧金句/诗词等），关闭可加快记账速度。'
            print(f"  Fix 1c: ImportQuestions Text updated")
            break

    # Fix 2: Add 显示随机文字 toggle + conditional wrapper around random text block
    # 2a: Add config entry to dict 588A56AF
    cfg_items.append({
        'WFItemType': 4,   # Boolean
        'WFKey': {
            'Value': {'string': '显示随机文字'},
            'WFSerializationType': 'WFTextTokenString'
        },
        'WFValue': {
            'Value': False,
            'WFSerializationType': 'WFNumberSubstitutableState'
        }
    })
    print(f"  Fix 2a: Added '显示随机文字' = false to config dict")

    # Fix 1e: Add 5 multi-platform config entries to 588A56AF
    new_cfg_entries = [
        ('平台',             0, {'string': '火山引擎'}),
        ('模型',             3, {'string': '5'}),
        ('max_tokens',       3, {'string': '1000'}),
        ('reasoning_effort', 0, {'string': 'minimal'}),
        ('调试模式',         4, None),  # Boolean, value=False
    ]
    for key_name, item_type, value_dict in new_cfg_entries:
        entry = {
            'WFItemType': item_type,
            'WFKey': {
                'Value': {'string': key_name},
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFValue': {
                'Value': value_dict if value_dict is not None else False,
                'WFSerializationType': 'WFTextTokenString' if item_type != 4 else 'WFNumberSubstitutableState'
            }
        }
        cfg_items.append(entry)
        print(f"  Fix 1e: Added '{key_name}' to config dict")

    # Fix 1f: Sync 5 new entries to ImportQuestions for config dict
    for iq in data.get('WFWorkflowImportQuestions', []):
        if iq.get('ActionIndex') == cfg_idx and iq.get('ParameterKey') == 'WFItems':
            dv_items = iq['DefaultValue']['Value']['WFDictionaryFieldValueItems']
            for key_name, item_type, value_dict in new_cfg_entries:
                dv_items.append({
                    'WFItemType': item_type,
                    'WFKey': {
                        'Value': {'string': key_name},
                        'WFSerializationType': 'WFTextTokenString'
                    },
                    'WFValue': {
                        'Value': value_dict if value_dict is not None else False,
                        'WFSerializationType': 'WFTextTokenString' if item_type != 4 else 'WFNumberSubstitutableState'
                    }
                })
            # Append Text description
            iq['Text'] = iq['Text'].rstrip() + (
                '\n🖥️ 平台：API 平台（填写: 火山引擎 / DeepSeek / 其他），默认火山引擎。'
                '\n🤖 模型：选择编号'
                '\n  1 = doubao-seed-2-0-mini-260215（默认）'
                '\n  2 = deepseek-chat'
                '\n  3 = doubao-seed-1-6-flash-250828'
                '\n  4 = deepseek-v3-2-251201'
                '\n  5 = doubao-seed-1-6-flash-250615'
                '\n  6 = 其他（需在密钥字典中填写「自定义模型」）'
                '\n📏 max_tokens：最大输出 token 数，默认 1000。'
                '\n⚡ reasoning_effort：推理深度（填写: minimal / low / medium / high），默认 minimal。'
                '\n🔧 调试模式：开启后在 API 调用前后弹出通知，用于排查问题。'
            )
            print(f"  Fix 1f: ImportQuestions synced for 5 new config entries")
            break

    # 2b: Update comment action text — prepend key dict guide + append config guide
    for action in actions:
        params = action.get('WFWorkflowActionParameters', {})
        comment = params.get('WFCommentActionText', '')
        if isinstance(comment, str) and '界面风格' in comment and '延迟截图' in comment:
            key_dict_guide = (
                '═══ 🔑 密钥与地址设置（上方词典）═══\n\n'
                '在你使用的平台对应的「密钥」字段粘贴 API Key。\n'
                '地址已预填，一般无需修改。\n\n'
                '• 密钥(火山引擎)：火山引擎/豆包平台的 API Key\n'
                '• 密钥(DeepSeek)：DeepSeek 平台的 API Key\n'
                '• 密钥(其他)：自定义平台的 API Key\n'
                '• 地址(其他)：自定义平台的 API 端点 URL\n'
                '• 自定义模型：当「模型」设为 6 时填写模型名\n\n'
                '⚠️ 请勿修改「开发者」「版本号」及预填地址。\n\n'
                '═══ 📋 配置项说明（下方词典）═══\n\n'
            )
            config_guide = (
                '\n🎲 显示随机文字：截图后弹出随机句子，关闭可加快记账速度。'
                '\n\n─── 🌐 AI 识别配置 ───'
                '\n🖥️ 平台：填写 火山引擎 / DeepSeek / 其他'
                '\n🤖 模型：填写编号'
                '\n  1 = doubao-seed-2-0-mini-260215（默认）'
                '\n  2 = deepseek-chat'
                '\n  3 = doubao-seed-1-6-flash-250828'
                '\n  4 = deepseek-v3-2-251201'
                '\n  5 = doubao-seed-1-6-flash-250615'
                '\n  6 = 其他（需在上方密钥字典中填写「自定义模型」）'
                '\n📏 max_tokens：最大输出 token 数，默认 1000'
                '\n⚡ reasoning_effort：推理深度，填写 minimal / low / medium / high'
                '\n🔧 调试模式：开启后 API 调用前后弹通知，用于排查问题'
                '\n🗃️ 显示记录详情：是否显示入账账本信息'
            )
            # 3C-8b: Update 显示记录详情 description in original comment
            comment = comment.replace(
                '🗃️ 显示记录详情：是否显示操作员名称、记录次数等',
                '🗃️ 显示记录详情：是否显示入账账本信息'
            )
            params['WFCommentActionText'] = key_dict_guide + comment + config_guide
            print(f"  Fix 2b: Updated comment action text")
            break

    # 2c: Wrap 10 random text actions in conditional
    rand_start = find_action_idx(actions, UUID_RANDOM_START)
    rand_end = find_action_idx(actions, UUID_RANDOM_END)
    assert rand_end == rand_start + 9, \
        f"Random text block should be 10 consecutive actions (got {rand_end - rand_start + 1})"

    W1 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['show_random_getval'],
            'WFDictionaryKey': '显示随机文字',
            'WFInput': {
                'Value': {
                    'OutputName': '词典',
                    'OutputUUID': UUID_CONFIG_DICT,
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }
    W2 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': NEW_UUIDS['show_random_group'],
            'UUID': NEW_UUIDS['show_random_begin'],
            'WFCondition': 4,           # greater than or equal to
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
    W2_ELSE = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': NEW_UUIDS['show_random_group'],
            'UUID': NEW_UUIDS['show_random_else'],
            'WFControlFlowMode': 1      # ELSE
        }
    }
    W3 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': NEW_UUIDS['show_random_group'],
            'UUID': NEW_UUIDS['show_random_end'],
            'WFControlFlowMode': 2      # END
        }
    }

    # Insert back to front to preserve indices
    actions.insert(rand_end + 1, W3)         # END
    actions.insert(rand_end + 1, W2_ELSE)    # ELSE (right after 10 actions)
    actions.insert(rand_start, W2)           # BEGIN
    actions.insert(rand_start, W1)           # getvalueforkey
    print(f"  Fix 2c: Wrapped random text block [{rand_start}:{rand_end}] with conditional (+4 actions)")

    # Fix 3: Rewrite key dict 29C441EE for multi-platform config
    key_idx = find_action_idx(actions, UUID_KEY_DICT)
    key_items = actions[key_idx]['WFWorkflowActionParameters']['WFItems']['Value']['WFDictionaryFieldValueItems']

    # 3a: Rename 密钥 → 密钥(火山引擎)
    for item in key_items:
        if item.get('WFKey', {}).get('Value', {}).get('string', '') == '密钥':
            item['WFKey']['Value']['string'] = '密钥(火山引擎)'
            print(f"  Fix 3a: Renamed '密钥' → '密钥(火山引擎)'")
            break

    # 3b: Append 6 new entries
    new_key_entries = [
        ('密钥(DeepSeek)', 0, {'string': ''}),
        ('密钥(其他)',     0, {'string': ''}),
        ('地址(火山引擎)', 0, {'string': 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'}),
        ('地址(DeepSeek)', 0, {'string': 'https://api.deepseek.com/v1/chat/completions'}),
        ('地址(其他)',     0, {'string': ''}),
        ('自定义模型',     0, {'string': ''}),
    ]
    for key_name, item_type, value_dict in new_key_entries:
        key_items.append({
            'WFItemType': item_type,
            'WFKey': {
                'Value': {'string': key_name},
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFValue': {
                'Value': value_dict,
                'WFSerializationType': 'WFTextTokenString'
            }
        })
        print(f"  Fix 3b: Added '{key_name}' to key dict")

    # 3c: Sync ImportQuestions for key dict
    for iq in data.get('WFWorkflowImportQuestions', []):
        if iq.get('ActionIndex') == key_idx and iq.get('ParameterKey') == 'WFItems':
            dv_items = iq['DefaultValue']['Value']['WFDictionaryFieldValueItems']
            # Rename 密钥 → 密钥(火山引擎) in DefaultValue
            for dv_item in dv_items:
                if dv_item.get('WFKey', {}).get('Value', {}).get('string', '') == '密钥':
                    dv_item['WFKey']['Value']['string'] = '密钥(火山引擎)'
                    break
            # Append same 6 entries
            for key_name, item_type, value_dict in new_key_entries:
                dv_items.append({
                    'WFItemType': item_type,
                    'WFKey': {
                        'Value': {'string': key_name},
                        'WFSerializationType': 'WFTextTokenString'
                    },
                    'WFValue': {
                        'Value': value_dict,
                        'WFSerializationType': 'WFTextTokenString'
                    }
                })
            # Update Text
            iq['Text'] = (
                '🔑 API 密钥与地址配置\n\n'
                '在你使用的平台对应的「密钥」字段粘贴 API Key。\n'
                '地址已预填，一般无需修改。\n\n'
                '• 密钥(火山引擎)：火山引擎/豆包平台的 API Key\n'
                '• 密钥(DeepSeek)：DeepSeek 平台的 API Key\n'
                '• 密钥(其他)：自定义平台的 API Key\n'
                '• 地址(其他)：自定义平台的 API 端点 URL\n'
                '• 自定义模型：当「模型」设为 6 时，在此填写模型名\n\n'
                '⚠️ 请勿修改「开发者」「版本号」及预填地址。'
            )
            print(f"  Fix 3c: ImportQuestions synced for key dict")
            break

    # === 3C-8a: Set DefaultValue for 自定义规则 ImportQuestions ===
    CUSTOM_RULES_DEFAULT = (
        '备注(remark)字段规则：简洁且表意完整，让人一眼能看明白这笔消费。'
        '网购写明平台、商家、商品（如 淘宝 xx旗舰店 数据线），信息不全只写已知部分；'
        '线下写明商户和内容（如 瑞幸 生椰拿铁）。不要捏造OCR中没有的信息。'
    )
    custom_rules_idx = find_action_idx(actions, UUID_CUSTOM_RULES)
    for iq in data.get('WFWorkflowImportQuestions', []):
        if iq.get('ActionIndex') == custom_rules_idx and iq.get('ParameterKey') == 'WFTextActionText':
            iq['DefaultValue'] = CUSTOM_RULES_DEFAULT
            iq['Text'] = (
                '🗣️ 自定义规则\n\n'
                '如果有个性化需求，可在下方文本框输入自定义识别规则。\n'
                '默认已填入备注写法规则，可根据需要修改或清空。\n'
                '示例：识别到 xxx 则分类归为"xxx"，或标签为"xxx"'
            )
            print(f"  3C-8a: Updated 自定义规则 DefaultValue and Text (ActionIndex={custom_rules_idx})")
            break

    # 3C-8a: Also set the gettext action's own WFTextActionText to the default rules
    actions[custom_rules_idx]['WFWorkflowActionParameters']['WFTextActionText'] = CUSTOM_RULES_DEFAULT
    print(f"  3C-8a: Set gettext {UUID_CUSTOM_RULES} WFTextActionText to default rules")

    # 3C-8a: Update 自定义规则 comment action text
    for action in actions:
        params = action.get('WFWorkflowActionParameters', {})
        comment = params.get('WFCommentActionText', '')
        if isinstance(comment, str) and '🗣️ 自定义规则' in comment and '个性化' in comment:
            params['WFCommentActionText'] = (
                '🗣️ 自定义规则\n\n'
                '如果有个性化需求，可在下方文本框输入自定义识别规则。\n'
                '默认已填入备注写法规则，可根据需要修改或清空。\n'
                '示例：识别到 xxx 则分类归为"xxx"，或标签为"xxx"'
            )
            print(f"  3C-8a: Updated 自定义规则 comment action text")
            break

    # === 3C-8b: Modify gettext 5499E009 to show only 入账账本 ===
    UUID_DETAIL_GETTEXT = '5499E009-3080-4D7C-BB04-55BA02F6AC53'
    for action in actions:
        params = action.get('WFWorkflowActionParameters', {})
        if params.get('UUID') == UUID_DETAIL_GETTEXT:
            text_val = params['WFTextActionText']['Value']
            text_val['string'] = f'入账账本： {PH} '
            text_val['attachmentsByRange'] = {
                '{6, 1}': {
                    'Type': 'Variable',
                    'VariableName': 'ledger'
                }
            }
            print(f"  3C-8b: Modified gettext {UUID_DETAIL_GETTEXT} → '入账账本： ￼ '")
            break

    # Find key action indices
    dl_idx = find_action_idx(actions, UUID_DOWNLOAD)
    dd_idx = find_action_idx(actions, UUID_DETECT_DICT)
    print(f"  downloadurl at index {dl_idx}")
    print(f"  detect.dictionary at index {dd_idx}")
    assert dd_idx == dl_idx + 1, \
        f"detect.dictionary should be right after downloadurl (expected {dl_idx+1}, got {dd_idx})"

    # Calculate placeholder positions in template
    pos = find_positions(TEMPLATE, PH)
    assert len(pos) == 11, f"Expected 11 placeholders, got {len(pos)}"
    labels = ['模型', '当前日期', '支出分类', '支出子分类', '收入分类', '账户', '标签', '自定义规则', 'OCR文本', 'max_tokens', 'reasoning_effort']
    print("\nPlaceholder positions:")
    for i, p in enumerate(pos):
        print(f"  ￼{i+1} {labels[i]}: {{{p}, 1}}")

    # Extract Aggrandizement dicts (with data blocks) from existing downloadurl
    old_dl = actions[dl_idx]
    entity_refs = {}
    for name, uid, out_name in [
        ('exp_first',  UUID_EXP_FIRST,  '分类'),
        ('exp_second', UUID_EXP_SECOND, '分类'),
        ('income',     UUID_INCOME,     '分类'),
        ('asset',      UUID_ASSET,      '账户'),
        ('tag',        UUID_TAG,        '标签'),
    ]:
        att = find_attachment_for_uuid(old_dl, uid)
        if att:
            entity_refs[name] = att
            has_data = any(
                'WFLinkEntityContentPropertyUserInfoEnumMetadata' in
                (a.get('PropertyUserInfo', {}) if isinstance(a, dict) else {})
                for a in att.get('Aggrandizements', [])
            )
            print(f"  ✓ {name}: extracted (data block: {has_data})")
        else:
            entity_refs[name] = make_simple_entity_attachment(uid, out_name)
            print(f"  ⚠ {name}: using fallback (no data block)")

    # === Build new actions ===

    # A1: extracttextfromimage (local OCR on resized image)
    A1 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.extracttextfromimage',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['ocr'],
            'WFImage': {
                'Value': {
                    'OutputName': '调整大小后的图像',
                    'OutputUUID': UUID_IMAGE_RESIZE,
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }

    # A2: gettext (build DeepSeek JSON body with 10 ￼ placeholders)
    attachments = {}

    # ￼1: 模型 (Variable "model" — set by Phase 2 model dispatch)
    attachments[f'{{{pos[0]}, 1}}'] = {
        'Type': 'Variable',
        'VariableName': 'model'
    }

    # ￼2: CurrentDate (yyyy-MM-dd HH:mm format, with time precision)
    attachments[f'{{{pos[1]}, 1}}'] = {
        'Aggrandizements': [{
            'WFDateFormatStyle': 'Custom',
            'WFDateFormat': 'yyyy-MM-dd HH:mm',
            'WFISO8601IncludeTime': True,
            'Type': 'WFDateFormatVariableAggrandizement'
        }],
        'Type': 'CurrentDate'
    }

    # ￼3-7: iCost entity references (.name property)
    for i, name in enumerate(['exp_first', 'exp_second', 'income', 'asset', 'tag']):
        attachments[f'{{{pos[i + 2]}, 1}}'] = entity_refs[name]

    # ￼8: User custom rules (plain ActionOutput, no Aggrandizement)
    attachments[f'{{{pos[7]}, 1}}'] = {
        'OutputName': '文本',
        'OutputUUID': UUID_CUSTOM_RULES,
        'Type': 'ActionOutput'
    }

    # ￼9: OCR text
    attachments[f'{{{pos[8]}, 1}}'] = {
        'OutputName': 'Text from Image',
        'OutputUUID': NEW_UUIDS['ocr'],
        'Type': 'ActionOutput'
    }

    # ￼10: max_tokens (from config S3)
    attachments[f'{{{pos[9]}, 1}}'] = {
        'OutputName': '词典值',
        'OutputUUID': NEW_UUIDS['cfg_maxtokens'],
        'Type': 'ActionOutput'
    }

    # ￼11: reasoning_effort (from config S4)
    attachments[f'{{{pos[10]}, 1}}'] = {
        'OutputName': '词典值',
        'OutputUUID': NEW_UUIDS['cfg_reasoning'],
        'Type': 'ActionOutput'
    }

    A2 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['body'],
            'WFTextActionText': {
                'Value': {
                    'attachmentsByRange': attachments,
                    'string': TEMPLATE
                },
                'WFSerializationType': 'WFTextTokenString'
            }
        }
    }

    # A3: text.replace (clean real newlines → spaces in JSON body)
    # CRITICAL: WFInput must use WFTextTokenString, not WFTextTokenAttachment (3C-1 §8)
    A3 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.text.replace',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['clean'],
            'WFInput': {
                'Value': {
                    'attachmentsByRange': {
                        '{0, 1}': {
                            'OutputName': 'Text',
                            'OutputUUID': NEW_UUIDS['body'],
                            'Type': 'ActionOutput'
                        }
                    },
                    'string': PH
                },
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFReplaceTextFind': '\n',
            'WFReplaceTextReplace': ' '
        }
    }

    # B: downloadurl (POST to DeepSeek API) — keeps original UUID
    B = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
        'WFWorkflowActionParameters': {
            'UUID': UUID_DOWNLOAD,
            'ShowHeaders': True,
            'WFHTTPMethod': 'POST',
            'WFHTTPBodyType': 'File',
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
            },
            'WFHTTPHeaders': {
                'Value': {
                    'WFDictionaryFieldValueItems': [
                        {
                            'WFItemType': 0,
                            'WFKey': {
                                'Value': {'string': 'Authorization'},
                                'WFSerializationType': 'WFTextTokenString'
                            },
                            'WFValue': {
                                'Value': {
                                    'attachmentsByRange': {
                                        '{7, 1}': {
                                            'OutputName': '词典值',
                                            'OutputUUID': NEW_UUIDS['resolved_key'],
                                            'Type': 'ActionOutput'
                                        }
                                    },
                                    'string': f'Bearer {PH}'
                                },
                                'WFSerializationType': 'WFTextTokenString'
                            }
                        },
                        {
                            'WFItemType': 0,
                            'WFKey': {
                                'Value': {'string': 'Content-Type'},
                                'WFSerializationType': 'WFTextTokenString'
                            },
                            'WFValue': {
                                'Value': {'string': 'application/json'},
                                'WFSerializationType': 'WFTextTokenString'
                            }
                        }
                    ]
                },
                'WFSerializationType': 'WFDictionaryFieldValue'
            },
            'WFRequestVariable': {
                'Value': {
                    'OutputName': 'Updated Text',
                    'OutputUUID': NEW_UUIDS['clean'],
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }

    # C1: getvalueforkey "choices" from DeepSeek response
    C1 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['choices'],
            'WFDictionaryKey': 'choices',
            'WFInput': {
                'Value': {
                    'OutputName': 'Contents of URL',
                    'OutputUUID': UUID_DOWNLOAD,
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }

    # C2: getitemfromlist — take choices[0] (index 1 in Shortcuts)
    C2 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getitemfromlist',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['first'],
            'WFInput': {
                'Value': {
                    'OutputName': 'Value for Key',
                    'OutputUUID': NEW_UUIDS['choices'],
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            },
            'WFItemIndex': 1
        }
    }

    # C3: getvalueforkey "message.content" (dot notation for nested access)
    C3 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['content'],
            'WFDictionaryKey': 'message.content',
            'WFInput': {
                'Value': {
                    'OutputName': 'Item from List',
                    'OutputUUID': NEW_UUIDS['first'],
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }

    # D: detect.dictionary — modify input reference (keep original UUID)
    D = copy.deepcopy(actions[dd_idx])
    D['WFWorkflowActionParameters']['WFInput'] = {
        'Value': {
            'OutputName': 'Value for Key',
            'OutputUUID': NEW_UUIDS['content'],
            'Type': 'ActionOutput'
        },
        'WFSerializationType': 'WFTextTokenAttachment'
    }

    # === Phase 0: Read config from 588A56AF (5 actions) ===
    def make_cfg_read(uuid_key, dict_key):
        return {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': NEW_UUIDS[uuid_key],
                'WFDictionaryKey': dict_key,
                'WFInput': {
                    'Value': {
                        'OutputName': '词典',
                        'OutputUUID': UUID_CONFIG_DICT,
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

    # === Phase 1: Platform dispatch — dynamic dict lookup (4 actions) ===

    # T_URL: gettext "地址(￼)" where ￼ = S1 platform name
    T_URL = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['url_label'],
            'WFTextActionText': {
                'Value': {
                    'attachmentsByRange': {
                        '{3, 1}': {
                            'OutputName': '词典值',
                            'OutputUUID': NEW_UUIDS['cfg_platform'],
                            'Type': 'ActionOutput'
                        }
                    },
                    'string': f'地址({PH})'
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
                    'OutputUUID': UUID_KEY_DICT,
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }

    # T_KEY: gettext "密钥(￼)" where ￼ = S1 platform name
    T_KEY = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['key_label'],
            'WFTextActionText': {
                'Value': {
                    'attachmentsByRange': {
                        '{3, 1}': {
                            'OutputName': '词典值',
                            'OutputUUID': NEW_UUIDS['cfg_platform'],
                            'Type': 'ActionOutput'
                        }
                    },
                    'string': f'密钥({PH})'
                },
                'WFSerializationType': 'WFTextTokenString'
            }
        }
    }

    # R_KEY: getvalueforkey [T_KEY output] from 29C441EE → resolved API key
    R_KEY = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['resolved_key'],
            'WFDictionaryKey': {
                'Value': {
                    'attachmentsByRange': {
                        '{0, 1}': {
                            'OutputName': 'Text',
                            'OutputUUID': NEW_UUIDS['key_label'],
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
                    'OutputUUID': UUID_KEY_DICT,
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }

    # === Phase 2: Model dispatch — number mapping (7 actions) ===

    MODEL_MAP = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.dictionary',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['model_map'],
            'WFItems': {
                'Value': {
                    'WFDictionaryFieldValueItems': [
                        {
                            'WFItemType': 0,
                            'WFKey': {'Value': {'string': '1'}, 'WFSerializationType': 'WFTextTokenString'},
                            'WFValue': {'Value': {'string': 'doubao-seed-2-0-mini-260215'}, 'WFSerializationType': 'WFTextTokenString'}
                        },
                        {
                            'WFItemType': 0,
                            'WFKey': {'Value': {'string': '2'}, 'WFSerializationType': 'WFTextTokenString'},
                            'WFValue': {'Value': {'string': 'deepseek-chat'}, 'WFSerializationType': 'WFTextTokenString'}
                        },
                        {
                            'WFItemType': 0,
                            'WFKey': {'Value': {'string': '3'}, 'WFSerializationType': 'WFTextTokenString'},
                            'WFValue': {'Value': {'string': 'doubao-seed-1-6-flash-250828'}, 'WFSerializationType': 'WFTextTokenString'}
                        },
                        {
                            'WFItemType': 0,
                            'WFKey': {'Value': {'string': '4'}, 'WFSerializationType': 'WFTextTokenString'},
                            'WFValue': {'Value': {'string': 'deepseek-v3-2-251201'}, 'WFSerializationType': 'WFTextTokenString'}
                        },
                        {
                            'WFItemType': 0,
                            'WFKey': {'Value': {'string': '5'}, 'WFSerializationType': 'WFTextTokenString'},
                            'WFValue': {'Value': {'string': 'doubao-seed-1-6-flash-250615'}, 'WFSerializationType': 'WFTextTokenString'}
                        },
                    ]
                },
                'WFSerializationType': 'WFDictionaryFieldValue'
            }
        }
    }

    # MODEL_LOOKUP: getvalueforkey [S2] from MODEL_MAP → model name (dynamic key)
    MODEL_LOOKUP = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['model_lookup'],
            'WFDictionaryKey': {
                'Value': {
                    'attachmentsByRange': {
                        '{0, 1}': {
                            'OutputName': '词典值',
                            'OutputUUID': NEW_UUIDS['cfg_model'],
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
                    'OutputUUID': NEW_UUIDS['model_map'],
                    'Type': 'ActionOutput'
                },
                'WFSerializationType': 'WFTextTokenAttachment'
            }
        }
    }

    # SV_MODEL_DEFAULT: setvariable "model" = MODEL_LOOKUP output
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

    # MC_BEGIN: conditional (S2 as Number ≥ 6) — custom model branch
    # Use WFCondition=4 (≥) which is verified for number mode. Model 1-5 skip, 6+ enters.
    MC_BEGIN = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': NEW_UUIDS['model_cond_group'],
            'UUID': NEW_UUIDS['model_cond_begin'],
            'WFCondition': 4,                         # ≥ (number mode, verified)
            'WFNumberValue': '6',
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
            }
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

    # SV_MODEL_OVERRIDE: setvariable "model" = MC_CUSTOM output
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

    # MC_END: conditional END (no ELSE)
    MC_END = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
        'WFWorkflowActionParameters': {
            'GroupingIdentifier': NEW_UUIDS['model_cond_group'],
            'UUID': NEW_UUIDS['model_cond_end'],
            'WFControlFlowMode': 2                    # END
        }
    }

    # === Phase 4: Debug notification BEFORE API call (3 actions) ===

    def make_debug_cond(group_key, uuid_key, mode):
        d = {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.conditional',
            'WFWorkflowActionParameters': {
                'GroupingIdentifier': NEW_UUIDS[group_key],
                'UUID': NEW_UUIDS[uuid_key],
                'WFControlFlowMode': mode,
            }
        }
        if mode == 0:  # BEGIN
            d['WFWorkflowActionParameters'].update({
                'WFCondition': 4,                     # ≥
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
            })
        return d

    DB1_BEGIN = make_debug_cond('debug1_group', 'debug1_begin', 0)
    DB1_END   = make_debug_cond('debug1_group', 'debug1_end', 2)

    # N1: notification "⏳ 正在调用 {平台} API..." (embed S1 platform name)
    N1 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['notif_before'],
            'WFNotificationActionBody': {
                'Value': {
                    'attachmentsByRange': {
                        '{7, 1}': {
                            'OutputName': '词典值',
                            'OutputUUID': NEW_UUIDS['cfg_platform'],
                            'Type': 'ActionOutput'
                        }
                    },
                    'string': f'⏳ 正在调用 {PH} API...'
                },
                'WFSerializationType': 'WFTextTokenString'
            }
        }
    }

    # === Phase 6: Debug notification AFTER API call (3 actions) ===

    DB2_BEGIN = make_debug_cond('debug2_group', 'debug2_begin', 0)
    DB2_END   = make_debug_cond('debug2_group', 'debug2_end', 2)

    # N2: notification showing raw response for debugging
    N2 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['notif_after'],
            'WFNotificationActionBody': {
                'Value': {
                    'attachmentsByRange': {
                        '{2, 1}': {
                            'OutputName': 'Contents of URL',
                            'OutputUUID': UUID_DOWNLOAD,
                            'Type': 'ActionOutput'
                        }
                    },
                    'string': f'✅ {PH}'
                },
                'WFSerializationType': 'WFTextTokenString'
            }
        }
    }

    # === Apply modifications ===
    # Replace 2 original actions with 30 new actions
    new_actions = [
        # Phase 0: read config (5)
        S1, S2, S3, S4, S5,
        # Phase 1: platform dispatch (4)
        T_URL, R_URL, T_KEY, R_KEY,
        # Phase 2: model dispatch (7)
        MODEL_MAP, MODEL_LOOKUP, SV_MODEL_DEFAULT, MC_BEGIN, MC_CUSTOM, SV_MODEL_OVERRIDE, MC_END,
        # Phase 3: OCR + JSON body (3)
        A1, A2, A3,
        # Phase 4: debug notification before (3)
        DB1_BEGIN, N1, DB1_END,
        # Phase 5: API call (1)
        B,
        # Phase 6: debug notification after (3)
        DB2_BEGIN, N2, DB2_END,
        # Phase 7: parse response (4)
        C1, C2, C3, D
    ]
    actions[dl_idx:dd_idx + 1] = new_actions

    print(f"\nReplaced actions[{dl_idx}:{dd_idx+1}] with {len(new_actions)} new actions")
    print(f"  Total actions: {len(actions)} (was {len(actions) - 28})")

    # === Save output ===
    with open(OUTPUT, 'wb') as f:
        plistlib.dump(data, f, fmt=plistlib.FMT_XML)

    print(f"\n✓ Saved to {OUTPUT}")
    print(f"\nGenerated UUIDs:")
    for k, v in NEW_UUIDS.items():
        print(f"  {k}: {v}")

    # Verification: check template integrity in saved file
    saved = plistlib.loads(OUTPUT.read_bytes())
    saved_actions = saved['WFWorkflowActions']
    # A2 is at index: dl_idx + 5(S1-S5) + 4(T/R_URL/KEY) + 7(model) + 1(A1) = dl_idx + 17
    a2_idx = dl_idx + 17
    gettext_action = saved_actions[a2_idx]
    saved_template = gettext_action['WFWorkflowActionParameters']['WFTextActionText']['Value']['string']
    saved_attachments = gettext_action['WFWorkflowActionParameters']['WFTextActionText']['Value']['attachmentsByRange']
    n_ph = saved_template.count(PH)
    n_att = len(saved_attachments)
    print(f"\nVerification:")
    print(f"  A2 (gettext) at index {a2_idx}")
    print(f"  Template placeholders: {n_ph} (expected 11)")
    print(f"  Attachments: {n_att} (expected 11)")
    assert n_ph == 11, f"Template has {n_ph} placeholders, expected 11"
    assert n_att == 11, f"Template has {n_att} attachments, expected 11"
    print("  ✓ All checks passed")


if __name__ == '__main__':
    main()
