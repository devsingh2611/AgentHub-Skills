---
name: transcript-intake
description: Step 1 of the discovery suite. Initialize a project workspace and normalize call transcripts (Teams VTT, Zoom, Otter, plain text) into citable evidence records with permanently stable segment IDs. Use when new call recordings or transcripts need ingesting, or a new client project is starting.
---

# Transcript Intake

Initializes a discovery project workspace and converts raw call recordings into
**citable evidence records** with permanently stable segment IDs.

This is **step 1** of the pre-build discovery suite:

```
transcript-intake → understanding-doc → brd-builder → frd → architecture → azure → plan
```

Everything downstream cites back to the segment IDs this skill creates. If these
IDs are not stable, the whole traceability chain breaks. Treat the rules below as
hard constraints, not preferences.

## Use this skill when

- The user has new call transcripts or recordings to add (Teams `.vtt`, Zoom, Otter, Fireflies, plain text)
- A new client project or engagement is starting
- Before running `understanding-doc`, whenever calls have happened since the last run

## Non-negotiable rules

1. **Transcript IDs are permanent.** `T04` always means the same call, forever. Never renumber, never reuse a retired ID.
2. **Segment IDs are permanent.** Re-running normalization on the same source bytes must produce byte-identical segment IDs. This is why a script does the parsing, not you.
3. **Never rewrite segment text.** It is evidence. No summarizing, no cleaning up grammar, no "improving" what someone said. The script's whitespace normalization is the only permitted change.
4. **Never ingest the same source twice.** Check the `source_sha256_16` against the index first.
5. **Never interpret here.** Do not extract requirements, decisions or conclusions in this skill. That is `understanding-doc`'s job. Intake produces *facts about the call*, not *findings from the call*.

## Project layout

```
<project>/
  project.yaml               # engagement config, ID conventions, standards overrides
  _tooling/vtt_normalize.py  # written on first run
  00-transcripts/
    _index.md                # the transcript register
    _raw/                    # original untouched source files
    T01_2026-08-14_cdp-kickoff.md
    T02_2026-08-19_data-platform-review.md
  01-understanding/
  02-brd/
  03-frd/
  04-architecture/
  05-azure/
  06-plan/
```

## Step 1 — Locate or initialize the project

Find the project folder. If the user hasn't said which, ask; don't guess.

If `project.yaml` does not exist, this is a new engagement. Ask for:

- Client / organisation name
- Project name
- A short project code, 3–8 chars uppercase (e.g. `ACME-CDP`) — offer a suggestion
- Known delivery phases, if any (fine to leave `TBD`)

Then create the folder tree above and write `project.yaml` from Appendix A.

If `project.yaml` exists, read it and continue.

## Step 2 — Ensure tooling exists

If `<project>/_tooling/vtt_normalize.py` is missing, write it verbatim from
Appendix B. Do not modify it. If it exists, leave it alone.

## Step 3 — Ingest each new source

For every raw transcript the user is adding:

1. **Copy the original** into `00-transcripts/_raw/` unchanged. Never delete or edit raw sources.

2. **Probe it** to check for duplicates and see what you're dealing with:
   ```
   python3 <project>/_tooling/vtt_normalize.py --input <raw file> --probe
   ```
   Compare the reported `source_sha256_16` against the index. If it already
   appears there, tell the user this call is already ingested and skip it —
   unless they explicitly say the file has been re-exported with more content,
   in which case re-normalize to the **same** transcript ID (segment IDs for the
   existing content stay put; new content appends with new numbers).

3. **Determine the meeting date and a slug.** Prefer the date in the source
   filename or in the transcript's opening lines. If you cannot determine it
   confidently, ask — do not invent a date.

4. **Assign the next transcript ID.** Read `_index.md`; take the highest existing
   ID and add one. First transcript is `T01`.

5. **Normalize:**
   ```
   python3 <project>/_tooling/vtt_normalize.py \
     --input <project>/00-transcripts/_raw/<file> \
     --tid T04 \
     --out <project>/00-transcripts/T04_<YYYY-MM-DD>_<slug>.md
   ```

If the source is a format the script reports as `plain` with a single `Unknown`
speaker, warn the user that citations will be weaker without speaker attribution,
and ask whether a better export is available.

## Step 4 — Enrich the header

The script leaves several front-matter fields as `TBD`. Read the first ~15% and
last ~10% of the normalized transcript and fill in:

- `meeting_date` — ISO format
- `meeting_title` — what this call actually was, in the client's own vocabulary
- `meeting_type` — one of: `business discovery`, `product`, `technical architecture`, `data walkthrough`, `stakeholder review`, `workshop`, `status`, `other`
- `attendees` — name, role and organisation where stated. Use the speaker list the script reports. If a speaker's role is never stated, write `role unknown` rather than guessing.
- `abstract` — 3–5 lines: what ground the call covered. Topics, not conclusions.
- `topics` — 4–8 short tags

Then append a `## Coverage notes` section below the header recording anything a
downstream reader must know: audio gaps, a whiteboard referenced but not
described, a document shared on screen, someone joining late, a portion where the
transcript is clearly garbled.

**Edit only the front matter and append the coverage notes.** Do not touch a
single `[Tnn:nnn]` line.

## Step 5 — Update the index

Maintain `00-transcripts/_index.md` in this shape:

```markdown
# Transcript index — <PROJECT CODE>

| ID | Date | Title | Type | Duration | Segs | Source file | sha256_16 |
|----|------|-------|------|----------|------|-------------|-----------|
| T01 | 2026-08-14 | CDP kickoff | business discovery | 00:52:10 | 84 | kickoff.vtt | 121104fa60ce |

## Participants seen so far
| Name | Role | Org | Calls |
|------|------|-----|-------|
| Priya Sharma | Head of Data | Acme Retail | T01, T02 |

## Abstracts
### T01 — CDP kickoff, 2026-08-14 (business discovery)
<abstract>
**Coverage notes:** <if any>
```

Keep the participant table cumulative and deduplicated — it becomes the
stakeholder list the BRD needs later.

## Step 6 — Report and hand off

Give the user a short table: transcript ID, title, date, duration, segments,
speaker split. Flag anything that needs their attention (unknown speakers,
missing dates, suspected duplicates, poor transcript quality).

Then say plainly which transcripts are now ingested but **not yet reflected in the
understanding document**, and suggest running `understanding-doc` next.

---

## Appendix A — `project.yaml` template

```yaml
project:
  code: ACME-CDP
  client: Acme Retail
  name: Customer Data Platform
  started: 2026-08-01
  lead: <name>

phases:
  - id: P1
    name: TBD
    status: planned

# ID conventions — do not change mid-project
conventions:
  transcript: "T<nn>"
  segment: "T<nn>:<nnn>"
  business_requirement: "BR-<nnn>"
  functional_requirement: "FR-<phase>-<nnn>"
  component: "C-<nn>"
  decision: "D-<nnn>"
  open_question: "Q-<nnn>"
  risk: "R-<nnn>"

# Confidence vocabulary used throughout the suite
confidence:
  - CONFIRMED   # stated explicitly by an accountable stakeholder
  - ASSUMED     # inferred by us, not yet validated
  - CONTESTED   # stakeholders have said conflicting things
  - OPEN        # raised, unanswered

output:
  citations_in_export: appendix   # inline | appendix | stripped
  understanding_doc_audience: internal

templates:
  brd: null        # path to a custom BRD template; null uses the suite default

standards:
  architecture: null
  azure: null
```

## Appendix B — the normalizer script

`vtt_normalize.py` ships with this skill at `scripts/vtt_normalize.py`.

On first use in a project, copy it to `<project>/_tooling/vtt_normalize.py` so
the project stays self-contained and reproducible even if the skill changes
later. If a copy already exists there, use it as-is — do not overwrite it
mid-project, because a changed parser means changed segment IDs.
