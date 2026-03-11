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
NEW_UUIDS = {k: str(uuid.uuid4()).upper() for k in
             ['ocr', 'body', 'clean', 'choices', 'first', 'content',
              'show_random_getval', 'show_random_begin', 'show_random_else', 'show_random_end', 'show_random_group',
              'notif_before', 'notif_after',
              'cfg_url', 'cfg_model', 'cfg_maxtokens']}

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
    ',"temperature":0,"thinking":{"type":"disabled"}}'
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
        if key_str == '显示记录详情':
            old_val = item['WFValue']['Value']
            item['WFValue']['Value'] = False
            print(f"  Fix 1d: 显示记录详情 {old_val} → False")

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
                if k == '显示记录详情':
                    dv_item['WFValue']['Value'] = False
                    print(f"  Fix 1c: ImportQuestions 显示记录详情 → False")
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

    # 2b: Update comment action text (append random text description)
    for action in actions:
        params = action.get('WFWorkflowActionParameters', {})
        comment = params.get('WFCommentActionText', '')
        if isinstance(comment, str) and '界面风格' in comment and '延迟截图' in comment:
            params['WFCommentActionText'] = comment + \
                '\n🎲 显示随机文字：是否在截图后弹出随机句子（弱智吧金句/诗词等），关闭可加快记账速度。'
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

    # Fix 3: Add API config entries to key dict 29C441EE
    key_idx = find_action_idx(actions, UUID_KEY_DICT)
    key_items = actions[key_idx]['WFWorkflowActionParameters']['WFItems']['Value']['WFDictionaryFieldValueItems']
    api_cfg_entries = [
        ('API地址', 0, {'string': 'https://api.deepseek.com/v1/chat/completions'}),
        ('模型',   0, {'string': 'deepseek-chat'}),
        ('max_tokens', 3, {'string': '300'}),
    ]
    for key_name, item_type, value_dict in api_cfg_entries:
        entry = {
            'WFItemType': item_type,
            'WFKey': {
                'Value': {'string': key_name},
                'WFSerializationType': 'WFTextTokenString'
            },
            'WFValue': {
                'Value': value_dict,
                'WFSerializationType': 'WFTextTokenString'
            }
        }
        if item_type == 3:  # Number
            entry['WFValue']['WFSerializationType'] = 'WFTextTokenString'
        key_items.append(entry)
        print(f"  Fix 3: Added '{key_name}' to key dict 29C441EE")

    # Fix 3b: Sync ImportQuestions for key dict
    for iq in data.get('WFWorkflowImportQuestions', []):
        if iq.get('ActionIndex') == key_idx and iq.get('ParameterKey') == 'WFItems':
            dv_items = iq['DefaultValue']['Value']['WFDictionaryFieldValueItems']
            for key_name, item_type, value_dict in api_cfg_entries:
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
            # Update Text description
            iq['Text'] = iq['Text'].rstrip() + \
                '\n\n🌐 API地址：API 端点 URL\n🤖 模型：模型名称\n📏 max_tokens：最大输出 token 数'
            print(f"  Fix 3b: ImportQuestions synced for key dict")
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
    assert len(pos) == 10, f"Expected 10 placeholders, got {len(pos)}"
    labels = ['模型', '当前日期', '支出分类', '支出子分类', '收入分类', '账户', '标签', '自定义规则', 'OCR文本', 'max_tokens']
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

    # ￼1: 模型 (from config)
    attachments[f'{{{pos[0]}, 1}}'] = {
        'OutputName': '词典值',
        'OutputUUID': NEW_UUIDS['cfg_model'],
        'Type': 'ActionOutput'
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

    # ￼10: max_tokens (from config)
    attachments[f'{{{pos[9]}, 1}}'] = {
        'OutputName': '词典值',
        'OutputUUID': NEW_UUIDS['cfg_maxtokens'],
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
                            'OutputUUID': NEW_UUIDS['cfg_url'],
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
                                            'OutputUUID': UUID_API_KEY,
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

    # N1: notification before DeepSeek call
    N1 = {
        'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
        'WFWorkflowActionParameters': {
            'UUID': NEW_UUIDS['notif_before'],
            'WFNotificationActionBody': '⏳ 正在调用 DeepSeek...'
        }
    }

    # N2: notification after DeepSeek call — show raw response for debugging
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

    # GV1/GV2/GV3: read API config from key dict 29C441EE
    def make_gv(uuid_key, dict_key):
        return {
            'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
            'WFWorkflowActionParameters': {
                'UUID': NEW_UUIDS[uuid_key],
                'WFDictionaryKey': dict_key,
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

    GV1 = make_gv('cfg_url', 'API地址')
    GV2 = make_gv('cfg_model', '模型')
    GV3 = make_gv('cfg_maxtokens', 'max_tokens')

    # === Apply modifications ===
    # Replace 2 original actions (downloadurl + detect.dictionary) with 13 new actions
    new_actions = [GV1, GV2, GV3, A1, A2, A3, N1, B, N2, C1, C2, C3, D]
    actions[dl_idx:dd_idx + 1] = new_actions

    print(f"\nReplaced actions[{dl_idx}:{dd_idx+1}] with {len(new_actions)} new actions")
    print(f"  Total actions: {len(actions)} (was {len(actions) - 11})")

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
    gettext_action = saved_actions[dl_idx + 4]  # A2 is at dl_idx + 4 (after GV1/GV2/GV3/A1)
    saved_template = gettext_action['WFWorkflowActionParameters']['WFTextActionText']['Value']['string']
    saved_attachments = gettext_action['WFWorkflowActionParameters']['WFTextActionText']['Value']['attachmentsByRange']
    n_ph = saved_template.count(PH)
    n_att = len(saved_attachments)
    print(f"\nVerification:")
    print(f"  Template placeholders: {n_ph} (expected 10)")
    print(f"  Attachments: {n_att} (expected 10)")
    assert n_ph == 10, f"Template has {n_ph} placeholders, expected 10"
    assert n_att == 10, f"Template has {n_att} attachments, expected 10"
    print("  ✓ All checks passed")


if __name__ == '__main__':
    main()
