#!/usr/bin/env python3
"""Decode microdsp serial output into CSV.

Reads any of the formats the library actually emits and writes a CSV file:

  exportJSON            {"type":"microdsp","label":"sine","data":[0.0,0.7,...]}
  exportCSVRow          [label] 1.5,2.25,3.125
  exportCSV             one value per line, optionally after a label line
  exportObfuscatedXOR   zero-padded hex byte pairs, one float per line

The 1.x version of this script expected a base64-wrapped JSON string, which the
library never produced, so it could not decode anything at all. It now parses
what the library sends, and auto-detects which format it is looking at.

Examples
--------
    # live from a board
    python export_decoder.py --port COM3 --baud 9600 --out data.csv

    # from a captured log
    python export_decoder.py --input capture.txt --out data.csv

    # undo the XOR obfuscation (the key you passed on the device)
    python export_decoder.py --input capture.txt --xor-key 0x5A --out data.csv

    # paste a single line interactively
    python export_decoder.py --out data.csv
"""

import argparse
import csv
import json
import re
import struct
import sys

XOR_LINE = re.compile(r"^\s*(?:[0-9A-Fa-f]{2}\s+){3}[0-9A-Fa-f]{2}\s*$")
LABELLED_ROW = re.compile(r"^\s*\[(?P<label>[^\]]*)\]\s*(?P<body>.*)$")


class Dataset:
    """A label plus the float values that followed it."""

    def __init__(self, label="", values=None, source=""):
        self.label = label
        self.values = values if values is not None else []
        self.source = source

    def __len__(self):
        return len(self.values)


def _floats(text):
    """Parse a comma- or whitespace-separated list of floats, skipping junk."""
    out = []
    for token in re.split(r"[,\s]+", text.strip()):
        if not token:
            continue
        try:
            out.append(float(token))
        except ValueError:
            return None
    return out


def decode_json_line(line):
    line = line.strip()
    if not (line.startswith("{") and line.endswith("}")):
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "data" not in obj:
        return None
    try:
        values = [float(v) for v in obj["data"]]
    except (TypeError, ValueError):
        return None
    return Dataset(str(obj.get("label", "")), values, "json")


def decode_row_line(line):
    """A single comma-separated row, optionally prefixed with [label]."""
    label = ""
    body = line
    match = LABELLED_ROW.match(line)
    if match:
        label = match.group("label")
        body = match.group("body")

    if "," not in body:
        return None
    values = _floats(body)
    if not values:
        return None
    return Dataset(label, values, "csv-row")


def decode_xor_line(line, key):
    """One float per line as four XOR'd, zero-padded hex bytes."""
    if not XOR_LINE.match(line):
        return None
    raw = bytes((int(b, 16) ^ key) & 0xFF for b in line.split())
    # The device writes native byte order, little-endian on AVR/ESP/ARM.
    return struct.unpack("<f", raw)[0]


def decode_stream(lines, xor_key=None):
    """Turn an iterable of lines into a list of Datasets."""
    datasets = []
    plain = Dataset(source="csv-column")   # accumulates bare one-per-line values
    xor = Dataset(label="xor", source="xor")

    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line.strip():
            continue

        found = decode_json_line(line)
        if found:
            datasets.append(found)
            continue

        if xor_key is not None:
            value = decode_xor_line(line, xor_key)
            if value is not None:
                xor.values.append(value)
                continue

        found = decode_row_line(line)
        if found:
            datasets.append(found)
            continue

        # A lone number belongs to the running one-value-per-line set.
        single = _floats(line)
        if single is not None and len(single) == 1:
            plain.values.append(single[0])
            continue

        # Anything else is a label or annotation. Start a new column set so a
        # label line separates the block that follows it.
        if plain.values:
            datasets.append(plain)
        plain = Dataset(label=line.strip().rstrip(":"), source="csv-column")

    if plain.values:
        datasets.append(plain)
    if xor.values:
        datasets.append(xor)
    return datasets


def save_csv(datasets, path):
    """Write one column per dataset, padded to the longest."""
    if not datasets:
        print("Nothing decoded, so no file was written.", file=sys.stderr)
        return False

    longest = max(len(d) for d in datasets)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index"] + [d.label or f"series{i}" for i, d in enumerate(datasets)])
        for row in range(longest):
            writer.writerow([row] + [
                (f"{d.values[row]:.6g}" if row < len(d) else "") for d in datasets
            ])

    print(f"Wrote {path}: {len(datasets)} series, {longest} rows")
    for d in datasets:
        print(f"  {d.label or '(unlabelled)':<20} {len(d):>6} values  [{d.source}]")
    return True


def read_serial(port, baud, seconds):
    try:
        import serial   # pyserial
    except ImportError:
        print("Reading a port needs pyserial:  pip install pyserial", file=sys.stderr)
        return None

    import time
    print(f"Reading {port} at {baud} baud for {seconds}s...")
    lines = []
    with serial.Serial(port, baud, timeout=1) as link:
        deadline = time.time() + seconds
        while time.time() < deadline:
            raw = link.readline()
            if not raw:
                continue
            text = raw.decode("utf-8", errors="replace")
            lines.append(text)
            print("  " + text.rstrip())
    return lines


def parse_key(text):
    if text is None:
        return None
    return int(text, 0) & 0xFF     # accepts 0x5A, 90, 0b1011010


def main():
    parser = argparse.ArgumentParser(
        description="Decode microdsp serial output into CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples")[-1],
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", help="read from a captured log file")
    source.add_argument("--port", help="read live from a serial port, e.g. COM3")
    parser.add_argument("--baud", type=int, default=9600, help="baud rate (default 9600)")
    parser.add_argument("--seconds", type=float, default=10.0,
                        help="how long to read the port for (default 10)")
    parser.add_argument("--xor-key", help="key used with exportObfuscatedXOR, e.g. 0x5A")
    parser.add_argument("--out", default="output.csv", help="CSV file to write")
    args = parser.parse_args()

    key = parse_key(args.xor_key)

    if args.port:
        lines = read_serial(args.port, args.baud, args.seconds)
        if lines is None:
            return 1
    elif args.input:
        with open(args.input, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    else:
        print("Paste microdsp output, then Ctrl-Z + Enter (Windows) or Ctrl-D:")
        lines = sys.stdin.readlines()

    datasets = decode_stream(lines, key)
    return 0 if save_csv(datasets, args.out) else 1


if __name__ == "__main__":
    sys.exit(main())
