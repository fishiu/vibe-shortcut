#!/usr/bin/env python3
"""
VibeShortcut - Basic Tool for .shortcut file processing

This module provides simple decode/encode functions to verify
plistlib's lossless conversion of .shortcut files.

Task 1.2 & 1.3: Validate binary round-trip without data cleaning.

Supports both:
- Signed .shortcut files (AEA1 format, iOS 15+)
- Unsigned .shortcut files (pure binary plist)
"""

import plistlib
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict


def _extract_from_aea(aea_data: bytes) -> bytes:
    """
    Extract plist data from AEA (Apple Encrypted Archive) signed shortcut.

    Based on: https://gist.github.com/0xilis/776d873475a5626aa612804fa9821199

    Args:
        aea_data: Raw bytes of AEA signed .shortcut file

    Returns:
        Extracted plist data as bytes

    Raises:
        ValueError: If AEA extraction fails
    """
    # Verify AEA magic
    if aea_data[:4] != b'AEA1':
        raise ValueError("Not an AEA1 file")

    # Read auth_data_size from offset 0x8-0xB
    auth_data_size = struct.unpack('<I', aea_data[0x8:0xC])[0]

    # Calculate offsets
    encoded_buf_offset = auth_data_size + 0x495c
    compressed_size_offset = auth_data_size + 0x13c + 4

    # Read compressed size
    compressed_size = struct.unpack('<I', aea_data[compressed_size_offset:compressed_size_offset+4])[0]

    # Extract compressed data
    compressed_data = aea_data[encoded_buf_offset:encoded_buf_offset + compressed_size]

    # Decompress using system compression_tool (LZFSE)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.lzfse') as tmp_in:
        tmp_in.write(compressed_data)
        tmp_in_path = tmp_in.name

    with tempfile.NamedTemporaryFile(delete=False, suffix='.aar') as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        # Decompress LZFSE
        subprocess.run(
            ['compression_tool', '-decode', '-a', 'lzfse', '-i', tmp_in_path, '-o', tmp_out_path],
            check=True,
            capture_output=True
        )

        # Extract Apple Archive
        with tempfile.TemporaryDirectory() as extract_dir:
            subprocess.run(
                ['aa', 'extract', '-d', extract_dir, '-i', tmp_out_path],
                check=True,
                capture_output=True
            )

            # Read Shortcut.wflow file
            wflow_path = Path(extract_dir) / 'Shortcut.wflow'
            if not wflow_path.exists():
                raise ValueError("Shortcut.wflow not found in archive")

            return wflow_path.read_bytes()

    finally:
        # Cleanup temp files
        Path(tmp_in_path).unlink(missing_ok=True)
        Path(tmp_out_path).unlink(missing_ok=True)


def decode(shortcut_path: str | Path) -> Dict[str, Any]:
    """
    Decode a .shortcut file to Python dict.

    Automatically handles both:
    - AEA signed shortcuts (iOS 15+, starts with 'AEA1')
    - Unsigned shortcuts (pure binary plist)

    Args:
        shortcut_path: Path to the .shortcut file

    Returns:
        Decoded plist data as Python dictionary

    Raises:
        FileNotFoundError: If shortcut file doesn't exist
        plistlib.InvalidFileException: If file is not a valid plist
        ValueError: If AEA extraction fails
    """
    path = Path(shortcut_path)

    if not path.exists():
        raise FileNotFoundError(f"Shortcut file not found: {path}")

    with open(path, 'rb') as f:
        file_data = f.read()

    # Check if it's an AEA signed shortcut
    if file_data[:4] == b'AEA1':
        # Extract plist from AEA container
        plist_data = _extract_from_aea(file_data)
        return plistlib.loads(plist_data)
    else:
        # Try to load as direct plist
        return plistlib.loads(file_data)


def encode(data: Dict[str, Any], output_path: str | Path) -> None:
    """
    Encode Python dict to .shortcut file.

    Args:
        data: Dictionary containing shortcut data
        output_path: Path where the .shortcut file will be saved

    Raises:
        TypeError: If data cannot be serialized to plist format
    """
    path = Path(output_path)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'wb') as f:
        plistlib.dump(data, f, fmt=plistlib.FMT_BINARY)


def verify_roundtrip(input_path: str | Path, output_path: str | Path) -> bool:
    """
    Verify lossless round-trip conversion.

    Args:
        input_path: Original .shortcut file
        output_path: Path for re-encoded .shortcut file

    Returns:
        True if round-trip is lossless, False otherwise
    """
    # Decode original file
    original_data = decode(input_path)

    # Encode to output file
    encode(original_data, output_path)

    # Decode the output file
    reencoded_data = decode(output_path)

    # Compare
    return original_data == reencoded_data


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  Decode: python shortcut_tool.py decode <input.shortcut>")
        print("  Encode: python shortcut_tool.py encode <input.json> <output.shortcut>")
        print("  Verify: python shortcut_tool.py verify <input.shortcut> <output.shortcut>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "decode":
        data = decode(sys.argv[2])
        print(f"Successfully decoded: {len(data)} top-level keys")
        for key in data.keys():
            print(f"  - {key}")

    elif command == "verify":
        result = verify_roundtrip(sys.argv[2], sys.argv[3])
        if result:
            print("✓ Round-trip verification PASSED - Lossless conversion confirmed")
        else:
            print("✗ Round-trip verification FAILED - Data mismatch detected")
        sys.exit(0 if result else 1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
