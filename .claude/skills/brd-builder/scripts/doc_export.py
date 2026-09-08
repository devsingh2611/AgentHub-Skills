#!/usr/bin/env python3
"""
doc_export.py - Discovery Suite citation validator and Word exporter.

Two jobs:
  1. --check   Verify every [[Tnn:nnn]] citation in a document resolves to a real
               transcript segment. This is the hallucination guard: run it before
               any document is shown to a client.
  2. export    Move citations into a source-traceability appendix (with the
               verbatim quote) and render the document to .docx via pandoc.

Usage:
    python3 doc_export.py --input 02-brd/BRD.md --transcripts 00-transcripts --check
    python3 doc_export.py --input 02-brd/BRD.md --transcripts 00-transcripts \
        --out 02-brd/BRD.docx --mode appendix

Modes: appendix (default) | inline | stripped
Exit code 2 means at least one citation is broken.
"""

import argparse
import glob
import os
import re
import subprocess
import sys

CITE = re.compile(r"\[\[(T\d{2,3}):(\d{3})\]\]")
SEG = re.compile(r"^\[(T\d{2,3}):(\d{3})\]\s+(\S+)\s+(.*)$")
REQ = re.compile(r"\b((?:BR|NFR)-\d{3}|FR-[A-Za-z0-9]+-\d{3}|C-\d{2}|D-\d{3})\b")


def load_segments(tdir):
    """{(tid, seg): {speaker, text, time, title}}"""
    segs, titles = {}, {}
    for path in sorted(glob.glob(os.path.join(tdir, "T*.md"))):
        tid_here, title = None, os.path.basename(path)
        lines = open(path, encoding="utf-8").read().split("\n")
        for i, ln in enumerate(lines):
            if ln.startswith("meeting_title:"):
                title = ln.split(":", 1)[1].strip()
            m = SEG.match(ln)
            if not m:
                continue
            tid, num, time, speaker = m.group(1), m.group(2), m.group(3), m.group(4)
            tid_here = tid
            body = []
            for nxt in lines[i + 1:]:
                if not nxt.strip() or SEG.match(nxt):
                    break
                body.append(nxt.strip())
            segs[(tid, num)] = {"speaker": speaker, "time": time,
                                "text": " ".join(body), "file": os.path.basename(path)}
        if tid_here:
            titles[tid_here] = title
    for (tid, num), v in segs.items():
        v["title"] = titles.get(tid, "")
    return segs


def scan(text, segs):
    """Return (ordered [(req, tid, num)], broken set)."""
    found, broken, req = [], [], None
    for ln in text.split("\n"):
        r = REQ.search(ln)
        if r:
            req = r.group(1)
        for tid, num in CITE.findall(ln):
            found.append((req or "—", tid, num))
            if (tid, num) not in segs:
                broken.append((req or "—", tid, num))
    return found, broken


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--out")
    ap.add_argument("--mode", default="appendix",
                    choices=["appendix", "inline", "stripped"])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--reference-doc", help="pandoc --reference-doc for house styling")
    a = ap.parse_args()

    text = open(a.input, encoding="utf-8").read()
    segs = load_segments(a.transcripts)
    found, broken = scan(text, segs)

    uniq = sorted({(t, n) for _, t, n in found})
    print(f"citations: {len(found)} ({len(uniq)} unique) | "
          f"transcript segments available: {len(segs)} | broken: {len(broken)}")
    if broken:
        print("\nBROKEN CITATIONS — these do not resolve to any transcript segment:")
        for req, tid, num in broken:
            print(f"  {req}: [[{tid}:{num}]]")
        print("\nFix these before the document goes anywhere. A citation that does "
              "not resolve is an unsupported claim.")
    if a.check:
        sys.exit(2 if broken else 0)
    if broken:
        sys.exit(2)
    if not a.out:
        sys.exit("ERROR: --out required unless --check")

    body = text
    if a.mode in ("appendix", "stripped"):
        body = CITE.sub("", body)
        body = re.sub(r"[ \t]+([.,;)])", r"\1", body)
        body = re.sub(r"[ \t]{2,}", " ", body)
        body = re.sub(r"[ \t]+$", "", body, flags=re.M)

    if a.mode == "appendix" and found:
        rows = ["", "\\newpage", "", "# Appendix — Source traceability", "",
                "Each requirement below is traced to the recorded discussion it "
                "originated from.", ""]
        by_req = {}
        for req, tid, num in found:
            by_req.setdefault(req, [])
            if (tid, num) not in by_req[req]:
                by_req[req].append((tid, num))
        for req in sorted(by_req, key=lambda r: (r == "—", r)):
            rows.append(f"**{req}**")
            rows.append("")
            rows.append("| Source | Speaker | What was said |")
            rows.append("|---|---|---|")
            for tid, num in by_req[req]:
                s = segs[(tid, num)]
                quote = s["text"].replace("|", "\\|")
                if len(quote) > 400:
                    quote = quote[:400].rsplit(" ", 1)[0] + " …"
                label = f"{tid}:{num} @ {s['time']}"
                rows.append(f"| {label} | {s['speaker']} | \"{quote}\" |")
            rows.append("")
        body = body.rstrip() + "\n" + "\n".join(rows) + "\n"

    md_tmp = a.out + ".prepared.md"
    with open(md_tmp, "w", encoding="utf-8") as f:
        f.write(body)

    cmd = ["pandoc", md_tmp, "-o", a.out, "--from",
           "markdown+pipe_tables+yaml_metadata_block", "--toc", "--toc-depth=2"]
    if a.reference_doc and os.path.exists(a.reference_doc):
        cmd += ["--reference-doc", a.reference_doc]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"pandoc failed:\n{e.stderr}")
    os.remove(md_tmp)
    print(f"wrote {a.out} (mode={a.mode})")


if __name__ == "__main__":
    main()
