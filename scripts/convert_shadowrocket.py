#!/usr/bin/env python3
"""Convert Sukka's Surge ruleset (ruleset.skk.moe /List) into Shadowrocket-compatible files.

Usage:
    python3 scripts/convert_shadowrocket.py <surge_dir> <shadowrocket_dir>

Layout is mirrored:  <surge_dir>/{domainset,non_ip,ip}/*.conf -> <shadowrocket_dir>/{domainset,non_ip,ip}/*.list

Conversion rules (based on the Shadowrocket manual, https://github.com/LOWERTOP/Shadowrocket):
  * domainset/*  : Shadowrocket DOMAIN-SET uses the same syntax as Surge (".example.com" = suffix,
                   "example.com" = exact), so lines are copied unchanged.
  * non_ip/*, ip/*:
      - DEST-PORT                  -> DST-PORT
      - PROCESS-NAME               -> dropped (not available on iOS)
      - SRC-IP / unknown types     -> dropped
      - AND / OR / NOT             -> kept only when every sub-rule is supported (sub-rules are renamed
                                      the same way); otherwise the whole logical rule is dropped,
                                      because dropping only part of it would change its meaning.
      - everything else (DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, DOMAIN-WILDCARD, USER-AGENT, URL-REGEX,
        IP-CIDR, IP-CIDR6, IP-ASN, GEOIP, PROTOCOL, DST-PORT) is copied unchanged, including no-resolve.
"""

from __future__ import annotations

import re
import shutil
import sys
from collections import Counter
from pathlib import Path

RENAME = {"DEST-PORT": "DST-PORT"}
SUPPORTED = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "USER-AGENT",
    "URL-REGEX",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "GEOIP",
    "PROTOCOL",
    "DST-PORT",
}
LOGICAL = {"AND", "OR", "NOT"}
RULE_DIRS = ("non_ip", "ip")
DOMAINSET_DIR = "domainset"
HEADER_NOTE = "# Converted for Shadowrocket by https://github.com/uclort/Rule\n"

# Matches "(TYPE," at the start of every sub-rule inside a logical rule.
SUB_RULE_TYPE = re.compile(r"\(\s*([A-Z0-9-]+)\s*,")


def rename_type(rule_type: str) -> str:
    return RENAME.get(rule_type, rule_type)


def convert_logical(line: str, rule_type: str, stats: Counter) -> str | None:
    body = line[len(rule_type) + 1 :]
    sub_types = SUB_RULE_TYPE.findall(body)
    if not sub_types:
        stats[f"drop:{rule_type}(unparsable)"] += 1
        return None
    for sub in sub_types:
        sub = rename_type(sub)
        if sub not in SUPPORTED and sub not in LOGICAL:
            stats[f"drop:{rule_type}(with {sub})"] += 1
            return None
    for old, new in RENAME.items():
        body = re.sub(rf"\(\s*{re.escape(old)}\s*,", f"({new},", body)
    stats[f"keep:{rule_type}"] += 1
    return f"{rule_type},{body}"


def convert_rule_line(line: str, stats: Counter) -> str | None:
    rule_type = line.split(",", 1)[0].strip()
    if rule_type in LOGICAL:
        return convert_logical(line, rule_type, stats)
    new_type = rename_type(rule_type)
    if new_type not in SUPPORTED:
        stats[f"drop:{rule_type}"] += 1
        return None
    if new_type != rule_type:
        stats[f"rename:{rule_type}->{new_type}"] += 1
        return new_type + line[len(rule_type) :]
    stats[f"keep:{rule_type}"] += 1
    return line


def add_header_note(lines: list[str]) -> list[str]:
    """Insert the conversion note right after the leading comment banner's first line."""
    if lines and lines[0].startswith("#"):
        return [lines[0], HEADER_NOTE, *lines[1:]]
    return [HEADER_NOTE, *lines]


def convert_rule_file(src: Path, dst: Path, stats: Counter) -> None:
    out: list[str] = []
    for raw in src.read_text(encoding="utf-8").splitlines(keepends=True):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            out.append(raw)
            continue
        converted = convert_rule_line(stripped, stats)
        if converted is not None:
            out.append(converted + "\n")
    dst.write_text("".join(add_header_note(out)), encoding="utf-8")


def convert_domainset_file(src: Path, dst: Path, stats: Counter) -> None:
    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    stats["keep:DOMAIN-SET-ENTRY"] += sum(1 for l in lines if l.strip() and not l.lstrip().startswith("#"))
    dst.write_text("".join(add_header_note(lines)), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    surge_dir, sr_dir = Path(sys.argv[1]), Path(sys.argv[2])
    if not (surge_dir / DOMAINSET_DIR).is_dir():
        print(f"error: {surge_dir}/{DOMAINSET_DIR} not found", file=sys.stderr)
        return 1

    if sr_dir.exists():
        shutil.rmtree(sr_dir)

    stats: Counter = Counter()
    files = 0
    for sub in (DOMAINSET_DIR, *RULE_DIRS):
        src_dir = surge_dir / sub
        if not src_dir.is_dir():
            continue
        dst_dir = sr_dir / sub
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(src_dir.glob("*.conf")):
            dst = dst_dir / (src.stem + ".list")
            if sub == DOMAINSET_DIR:
                convert_domainset_file(src, dst, stats)
            else:
                convert_rule_file(src, dst, stats)
            files += 1

    print(f"converted {files} files into {sr_dir}")
    for key, count in sorted(stats.items()):
        print(f"  {key:40} {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
