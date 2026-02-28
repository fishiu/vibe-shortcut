#!/usr/bin/env python3
"""
Unit tests for shortcut_tool.py
"""

import pytest
import plistlib
from pathlib import Path
import sys

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from shortcut_tool import decode, encode, verify_roundtrip, dump_xml, load_xml, sign


def test_encode_decode_simple(tmp_path):
    """Test basic encode/decode round-trip with simple data."""
    # Create a simple plist structure similar to shortcuts
    test_data = {
        "WFWorkflowActions": [],
        "WFWorkflowClientVersion": "1113",
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": 59511,
            "WFWorkflowIconStartColor": 4282601983
        },
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowName": "Test Shortcut",
        "WFWorkflowTypes": ["NCWidget", "WatchKit"]
    }

    # Encode
    output_file = tmp_path / "test.shortcut"
    encode(test_data, output_file)

    # Verify file exists and is binary plist
    assert output_file.exists()

    # Decode
    decoded_data = decode(output_file)

    # Verify data matches
    assert decoded_data == test_data
    assert decoded_data["WFWorkflowName"] == "Test Shortcut"
    assert len(decoded_data["WFWorkflowActions"]) == 0


def test_verify_roundtrip(tmp_path):
    """Test verify_roundtrip function."""
    test_data = {
        "TestKey": "TestValue",
        "TestNumber": 42,
        "TestList": [1, 2, 3],
        "TestDict": {"nested": "value"}
    }

    input_file = tmp_path / "input.shortcut"
    output_file = tmp_path / "output.shortcut"

    # Create initial file
    encode(test_data, input_file)

    # Verify round-trip
    result = verify_roundtrip(input_file, output_file)

    assert result is True
    assert output_file.exists()


def test_decode_nonexistent_file():
    """Test decode raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        decode("nonexistent.shortcut")


def test_encode_creates_parent_dirs(tmp_path):
    """Test encode creates parent directories if needed."""
    nested_path = tmp_path / "deep" / "nested" / "path" / "test.shortcut"
    test_data = {"test": "data"}

    encode(test_data, nested_path)

    assert nested_path.exists()
    assert decode(nested_path) == test_data


def test_dump_xml_load_xml_roundtrip(tmp_path):
    """Test dump_xml → load_xml is lossless."""
    import datetime
    test_data = {
        "StringField": "hello",
        "IntField": 42,
        "BoolField": True,
        "ListField": [1, "two", 3.0],
        "NestedDict": {"inner": "value"},
        "BytesField": b"\x89PNG\r\n\x1a\n",
        "DateField": datetime.datetime(2026, 2, 16, 12, 0, 0),
    }

    xml_path = tmp_path / "test.xml"
    dump_xml(test_data, xml_path)

    assert xml_path.exists()
    assert xml_path.read_bytes().startswith(b'<?xml')

    reloaded = load_xml(xml_path)
    assert reloaded == test_data


def test_load_xml_nonexistent_file():
    """Test load_xml raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_xml("nonexistent.xml")


def test_dump_xml_creates_parent_dirs(tmp_path):
    """Test dump_xml creates parent directories if needed."""
    nested_path = tmp_path / "a" / "b" / "test.xml"
    dump_xml({"key": "val"}, nested_path)
    assert nested_path.exists()
    assert load_xml(nested_path) == {"key": "val"}


def test_sign_nonexistent_file():
    """Test sign raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        sign("nonexistent.shortcut", "output.shortcut")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
