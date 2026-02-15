#!/usr/bin/env python3
"""
Tests for AEA (Apple Encrypted Archive) signed shortcut extraction
"""

import pytest
from pathlib import Path
import sys

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from shortcut_tool import decode, encode


def test_decode_aea_signed_shortcut():
    """Test decoding AEA signed shortcut (real iOS 15+ file)."""
    shortcut_path = Path(__file__).parent.parent / "samples" / "demo-notification.shortcut"

    if not shortcut_path.exists():
        pytest.skip("AEA sample file not found")

    # Decode signed shortcut
    data = decode(shortcut_path)

    # Verify expected structure
    assert isinstance(data, dict)
    assert "WFWorkflowActions" in data
    assert "WFWorkflowClientVersion" in data
    assert "WFWorkflowIcon" in data


def test_aea_to_unsigned_conversion(tmp_path):
    """Test converting AEA signed shortcut to unsigned plist."""
    shortcut_path = Path(__file__).parent.parent / "samples" / "demo-notification.shortcut"

    if not shortcut_path.exists():
        pytest.skip("AEA sample file not found")

    # Decode AEA
    data = decode(shortcut_path)

    # Encode as unsigned
    output_path = tmp_path / "unsigned.shortcut"
    encode(data, output_path)

    # Verify output is pure plist (not AEA)
    with open(output_path, 'rb') as f:
        magic = f.read(8)

    assert magic[:6] == b'bplist'  # Pure plist, not AEA1
    assert output_path.stat().st_size < shortcut_path.stat().st_size  # Smaller without signature

    # Verify can be decoded again
    decoded_again = decode(output_path)
    assert decoded_again == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
