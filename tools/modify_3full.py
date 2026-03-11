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

# === Generate new UUIDs ===
NEW_UUIDS = {k: str(uuid.uuid4()).upper() for k in
             ['ocr', 'body', 'clean', 'choices', 'first', 'content']}

PH = '\ufffc'  # U+FFFC placeholder character

# === DeepSeek JSON body template (§4.4) ===
# Contains 8 ￼ placeholders for runtime substitution by Shortcuts.
# \n and \" are literal two-character sequences (JSON encoding).
TEMPLATE = (
    '{"model":"deepseek-chat","messages":[{"role":"system","content":"'
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
    '"}]}'
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
            print(f"  Fix 1: 界面风格 '{old_val}' → '1' (at action index {cfg_idx})")
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
    assert len(pos) == 8, f"Expected 8 placeholders, got {len(pos)}"
    labels = ['当前日期', '支出分类', '支出子分类', '收入分类', '账户', '标签', '自定义规则', 'OCR文本']
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

    # A2: gettext (build DeepSeek JSON body with 8 ￼ placeholders)
    attachments = {}

    # ￼1: CurrentDate (yyyy-MM-dd HH:mm format, with time precision)
    attachments[f'{{{pos[0]}, 1}}'] = {
        'Aggrandizements': [{
            'WFDateFormatStyle': 'Custom',
            'WFDateFormat': 'yyyy-MM-dd HH:mm',
            'WFISO8601IncludeTime': True,
            'Type': 'WFDateFormatVariableAggrandizement'
        }],
        'Type': 'CurrentDate'
    }

    # ￼2-6: iCost entity references (.name property)
    for i, name in enumerate(['exp_first', 'exp_second', 'income', 'asset', 'tag']):
        attachments[f'{{{pos[i + 1]}, 1}}'] = entity_refs[name]

    # ￼7: User custom rules (plain ActionOutput, no Aggrandizement)
    attachments[f'{{{pos[6]}, 1}}'] = {
        'OutputName': '文本',
        'OutputUUID': UUID_CUSTOM_RULES,
        'Type': 'ActionOutput'
    }

    # ￼8: OCR text
    attachments[f'{{{pos[7]}, 1}}'] = {
        'OutputName': 'Text from Image',
        'OutputUUID': NEW_UUIDS['ocr'],
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
            'WFURL': 'https://api.deepseek.com/v1/chat/completions',
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

    # === Apply modifications ===
    # Replace 2 original actions (downloadurl + detect.dictionary) with 8 new actions
    new_actions = [A1, A2, A3, B, C1, C2, C3, D]
    actions[dl_idx:dd_idx + 1] = new_actions

    print(f"\nReplaced actions[{dl_idx}:{dd_idx+1}] with {len(new_actions)} new actions")
    print(f"  Total actions: {len(actions)} (was {len(actions) - 6})")

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
    gettext_action = saved_actions[dl_idx + 1]  # A2 is at dl_idx + 1
    saved_template = gettext_action['WFWorkflowActionParameters']['WFTextActionText']['Value']['string']
    saved_attachments = gettext_action['WFWorkflowActionParameters']['WFTextActionText']['Value']['attachmentsByRange']
    n_ph = saved_template.count(PH)
    n_att = len(saved_attachments)
    print(f"\nVerification:")
    print(f"  Template placeholders: {n_ph} (expected 8)")
    print(f"  Attachments: {n_att} (expected 8)")
    assert n_ph == 8, f"Template has {n_ph} placeholders, expected 8"
    assert n_att == 8, f"Template has {n_att} attachments, expected 8"
    print("  ✓ All checks passed")


if __name__ == '__main__':
    main()
