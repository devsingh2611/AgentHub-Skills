#!/usr/bin/env python3
"""
vtt_normalize.py - Discovery Suite transcript normalizer.

Converts a raw transcript (Teams/Zoom .vtt, .srt, or plain .txt) into a
citable, speaker-turn markdown record with STABLE segment IDs.

Stability contract: given the same input bytes and the same --tid, the output
segment IDs are always identical. Never edit a normalized file by hand.

Usage:
    python3 vtt_normalize.py --input RAW --tid T04 --out OUTFILE [--meta META.json]
    python3 vtt_normalize.py --input RAW --probe          # inspect only, no write

Options:
    --max-seconds N   cap a merged turn at N seconds (default 45)
    --max-words N     cap a merged turn at N words (default 150)
"""

import argparse
import hashlib
import json
import os
import re
import sys

TS = re.compile(
    r"(?P<s>\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})"
    r"\s*-->\s*"
    r"(?P<e>\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})"
)
VTAG = re.compile(r"<v\s+([^>]+?)\s*>(.*?)(?:</v>)?\s*$", re.S)
TAGS = re.compile(r"<[^>]+>")
# "Priya Sharma:" / "Priya Sharma (Acme):" / "PRIYA:" at line start
INLINE_SPK = re.compile(r"^\s*([A-Z][\w.'\-]*(?:\s+[\w.'\-]+){0,4}(?:\s*\([^)]{1,40}\))?)\s*:\s+(.*)$")
# Zoom plain-text transcripts: "00:14:32 Priya Sharma: text"
ZOOM_LINE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+([^:]{1,60}?):\s+(.*)$")


def to_seconds(t):
    t = t.replace(",", ".")
    parts = t.split(":")
    if len(parts) == 2:
        parts = ["0"] + parts
    h, m, s = parts
    return int(h) * 3600 + int(m) * 60 + float(s)


def hhmmss(sec):
    sec = int(round(sec))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def parse_cues(text):
    """Return list of dicts: {start, end, speaker, text}."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cues, i = [], 0
    while i < len(lines):
        m = TS.search(lines[i])
        if not m:
            i += 1
            continue
        start, end = to_seconds(m.group("s")), to_seconds(m.group("e"))
        i += 1
        body = []
        while i < len(lines) and lines[i].strip() and not TS.search(lines[i]):
            body.append(lines[i])
            i += 1
        raw = " ".join(body).strip()
        if not raw:
            continue
        speaker = None
        v = VTAG.match(raw)
        if v:
            speaker, raw = v.group(1).strip(), v.group(2)
        raw = TAGS.sub("", raw).strip()
        if speaker is None:
            s = INLINE_SPK.match(raw)
            if s and len(s.group(1)) <= 60:
                speaker, raw = s.group(1).strip(), s.group(2).strip()
        raw = re.sub(r"\s+", " ", raw).strip()
        if raw:
            cues.append({"start": start, "end": end,
                         "speaker": speaker or "Unknown", "text": raw})
    if cues:
        return cues, "timed"

    # No timestamps: try Zoom plain-text, then bare "Speaker: text"
    for ln in lines:
        z = ZOOM_LINE.match(ln)
        if z:
            sec = to_seconds(z.group(1) if z.group(1).count(":") == 2 else "0:" + z.group(1))
            cues.append({"start": sec, "end": sec, "speaker": z.group(2).strip(),
                         "text": re.sub(r"\s+", " ", z.group(3)).strip()})
    if cues:
        return cues, "zoom-text"

    speaker = "Unknown"
    for ln in lines:
        if not ln.strip():
            continue
        s = INLINE_SPK.match(ln)
        if s:
            speaker = s.group(1).strip()
            body = s.group(2).strip()
        else:
            body = ln.strip()
        if body:
            cues.append({"start": -1, "end": -1, "speaker": speaker,
                         "text": re.sub(r"\s+", " ", body)})
    return cues, ("plain" if cues else "empty")


def merge(cues, max_seconds=45, max_words=150):
    """Merge consecutive same-speaker cues into turns, capped by time and length."""
    turns = []
    for c in cues:
        if turns:
            t = turns[-1]
            same = t["speaker"] == c["speaker"]
            dur_ok = c["end"] < 0 or (c["end"] - t["start"]) <= max_seconds
            len_ok = t["words"] + len(c["text"].split()) <= max_words
            if same and dur_ok and len_ok:
                # Teams rolling captions: a cue that extends the previous text
                if c["text"].startswith(t["text"][-60:]) and len(t["text"]) > 60:
                    t["text"] = t["text"][:-60] + c["text"]
                elif t["text"].endswith(c["text"]):
                    pass  # exact repeat, drop
                else:
                    t["text"] += " " + c["text"]
                t["end"] = max(t["end"], c["end"])
                t["words"] = len(t["text"].split())
                continue
        turns.append({"start": c["start"], "end": c["end"], "speaker": c["speaker"],
                      "text": c["text"], "words": len(c["text"].split())})
    return turns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--tid")
    ap.add_argument("--out")
    ap.add_argument("--meta")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--max-seconds", type=int, default=45)
    ap.add_argument("--max-words", type=int, default=150)
    a = ap.parse_args()

    raw = open(a.input, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()[:16]
    text = raw.decode("utf-8", errors="replace").lstrip("﻿")

    cues, kind = parse_cues(text)
    if kind == "empty":
        sys.exit(f"ERROR: no parseable content in {a.input}")
    turns = merge(cues, a.max_seconds, a.max_words)

    speakers = {}
    for t in turns:
        speakers[t["speaker"]] = speakers.get(t["speaker"], 0) + t["words"]
    duration = max((t["end"] for t in turns), default=-1)

    meta = {
        "source_file": os.path.basename(a.input),
        "source_sha256_16": digest,
        "format_detected": kind,
        "segment_count": len(turns),
        "word_count": sum(t["words"] for t in turns),
        "duration": hhmmss(duration) if duration >= 0 else None,
        "speakers": [{"name": k, "words": v, "share_pct": round(100 * v / max(1, sum(speakers.values())))}
                     for k, v in sorted(speakers.items(), key=lambda x: -x[1])],
    }

    if a.probe:
        print(json.dumps(meta, indent=2))
        return

    if not (a.tid and a.out):
        sys.exit("ERROR: --tid and --out are required unless --probe")
    if not re.fullmatch(r"T\d{2,3}", a.tid):
        sys.exit("ERROR: --tid must look like T04")

    body = []
    for n, t in enumerate(turns, start=1):
        stamp = hhmmss(t["start"]) if t["start"] >= 0 else "--:--:--"
        body.append(f"[{a.tid}:{n:03d}] {stamp} {t['speaker']}\n{t['text']}\n")

    header = [
        "---",
        f"transcript_id: {a.tid}",
        f"source_file: {meta['source_file']}",
        f"source_sha256_16: {meta['source_sha256_16']}",
        f"format_detected: {kind}",
        f"segments: {meta['segment_count']}",
        f"words: {meta['word_count']}",
        f"duration: {meta['duration'] or 'unknown'}",
        "meeting_date: TBD",
        "meeting_title: TBD",
        "meeting_type: TBD",
        "attendees: []",
        "abstract: TBD",
        "---",
        "",
        f"# {a.tid} — normalized transcript",
        "",
        "> Machine-generated evidence record. Do not edit segment text or IDs.",
        f"> Cite as `[[{a.tid}:NNN]]`.",
        "",
    ]
    out = "\n".join(header) + "\n" + "\n".join(body)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    meta["output_file"] = a.out
    meta["transcript_id"] = a.tid
    if a.meta:
        with open(a.meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
