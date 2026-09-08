---
name: brd-builder
description: Step 3 of the discovery suite. Draft or update a Business Requirements Document from the project understanding document, with every requirement cited to transcript evidence, validated against the transcripts, and exported to Word with a source-traceability appendix.
---

# BRD Builder

Produces a client-ready Business Requirements Document from the project
understanding document, with every requirement traced back to the recorded
conversation it came from.

**Step 3** of the pre-build discovery suite:

```
transcript-intake → understanding-doc → [brd-builder] → frd → architecture → azure → plan
```

## Use this skill when

- The understanding document is stable enough to commit to requirements
- The user asks to draft, update or export the BRD
- A new round of calls has changed the picture and the BRD needs revising

## Inputs

| File | Role |
|---|---|
| `01-understanding/understanding.md` | Primary source. Read it fully |
| `01-understanding/decisions.md` | Scope decisions and their supersession chain |
| `01-understanding/open-questions.md` | Becomes the "open items" section |
| `00-transcripts/T*.md` | Verbatim evidence. Follow citations here — never quote from memory |
| `project.yaml` | Project code, phases, custom template path, export mode |

If `project.yaml` sets `templates.brd`, use that structure instead of the default
in Appendix A. Map the content into their headings; do not argue with their
template.

## Hard rules

1. **No requirement without evidence.** Every `BR-nnn` and `NFR-nnn` carries at least one `[[Tnn:nnn]]` citation, or is explicitly marked `[ASSUMPTION — requires client confirmation]`. There is no third option.
2. **Verify every citation before writing it.** Grep the transcript for the segment and confirm it says what you claim. Then run the automated check in Step 6. A citation that does not resolve is a fabricated claim in a client document.
3. **Business language, not solution design.** A BR says what the business must be able to do and why it matters. The moment you write a table name, an API, a technology or a screen layout, you have drifted into the FRD's territory. Stop.
4. **Never resolve a `CONTESTED` item on your own authority.** It goes to section 14 as an open decision, or becomes a requirement with the conflict stated in the open. Picking a side silently is how scope disputes start.
5. **Priority must be evidenced.** MoSCoW comes from what the client said. If nobody prioritised it, write `Proposed: Must` and flag it for confirmation rather than inventing a priority.
6. **Do not pad.** A BRD with 60 requirements where 22 were discussed is worse than one with 22. Coverage gaps are reported, not filled with plausible-sounding filler.

## Procedure

### Step 1 — Read everything

Read the understanding document in full, plus decisions and open questions. Note
the `transcripts_covered` list — if transcripts have been ingested but not folded
into the understanding document, stop and tell the user to run `understanding-doc`
first. Building a BRD on a stale understanding wastes everyone's time.

### Step 2 — Decompose into candidate requirements

Work through understanding sections U2, U5 and U6 (drivers, target state, in-scope
capabilities) and derive candidate business requirements. Work through U7 for
non-functional requirements.

For each candidate, hold: proposed ID, one-line statement, rationale, evidenced
priority, phase, and the citations from the understanding document.

### Step 3 — Checkpoint with the user (do not skip)

Before writing the document, present the candidate list as a compact table:

| ID | Requirement | Priority | Phase | Evidence | Confidence |
|---|---|---|---|---|---|
| BR-001 | Single consolidated customer profile | Must | P1 | T01:001, T03:022 | CONFIRMED |
| BR-007 | Consent capture at point of sale | Should | P2 | — | ASSUMPTION |

Alongside it, state plainly:

- Which candidates rest on assumptions rather than evidence
- Which understanding sections produced no requirements, and whether that's correct
- Which `CONTESTED` items you are *not* resolving, and where they'll appear

Ask the user to confirm, merge, split or drop before you write prose. A wrong
decomposition reviewed at this stage costs a minute; reviewed after drafting it
costs an afternoon.

### Step 4 — Pull verbatim evidence

For each confirmed requirement, follow its citations into the transcripts and read
the actual segments. Two things happen here that matter:

- You catch requirements the understanding document paraphrased in a way that lost a constraint
- You get the exact wording for the traceability appendix

If a citation doesn't support the requirement as strongly as the understanding
document implied, weaken the requirement or reclassify it as an assumption. Do not
strengthen it to match.

### Step 5 — Write `02-brd/BRD.md`

Use the template in Appendix A (or the project's custom template). Requirement
entries look like:

```markdown
### BR-002 — Overnight refresh of the unified profile

The business must have the unified customer profile refreshed daily, with the
overnight cycle complete before the start of the business day, so that call-centre
and marketing teams work from same-day data. [[T01:003]] [[T01:004]]

| | |
|---|---|
| **Priority** | Must |
| **Phase** | P1 |
| **Requested by** | Priya Sharma (Head of Data) |
| **Rationale** | Real-time integration cost not justified for Phase 1 use cases (D-007) |
| **Acceptance criteria** | Refresh completes by 06:00 local on every business day; failures alert the operations team before 06:30 |
| **Note** | Call-centre operations have a standing request for near-real-time; accepted as out of Phase 1 scope on condition of the 06:00 window. See Open Item OI-003 |
```

Acceptance criteria at BRD level stay business-observable — a business user must
be able to tell whether it's met. Leave system-level criteria to the FRD.

Section 14 (Open items) is the one clients actually act on. Pull from
`open-questions.md`, but re-rank by what each blocks, and name an owner and a
"needed by" for each.

Version the document: increment `version` in front matter and add a row to the
revision history table each time you regenerate.

### Step 6 — Validate

Run the citation check. This is mandatory before the document is shown to anyone:

```
python3 <project>/_tooling/doc_export.py \
  --input <project>/02-brd/BRD.md \
  --transcripts <project>/00-transcripts \
  --check
```

If `_tooling/doc_export.py` is missing, write it verbatim from Appendix B.

Exit code 2 means at least one citation is broken. Fix the requirement — either
find the real evidence or downgrade it to an assumption. Never delete the citation
and leave the claim standing.

Then self-review against the hard rules: any requirement that names a technology,
any priority without evidence, any contested item quietly resolved.

### Step 7 — Export

```
python3 <project>/_tooling/doc_export.py \
  --input <project>/02-brd/BRD.md \
  --transcripts <project>/00-transcripts \
  --out <project>/02-brd/BRD_v<n>.docx \
  --mode appendix
```

`--mode appendix` (the project default) strips inline citation tags from the body
and builds a source-traceability appendix carrying the verbatim quote behind each
requirement. Use `--mode inline` if the client wants tags visible, `--mode
stripped` for a clean document with no traceability.

Pass `--reference-doc <house-style.docx>` to apply Tiger branding once a template
exists.

### Step 8 — Report

Give the user:

- Requirement count by priority and phase
- The assumption list — every requirement not backed by evidence, as a single reviewable block
- Contested items carried into open items
- Coverage gaps: understanding sections that produced nothing
- File paths for the markdown and the .docx

Then suggest the next step: `frd` for the phase they intend to build first, and
offer to draft a client-call agenda from the open items.

---

## Appendix A — Default BRD structure

```markdown
---
title: "Business Requirements Document — <client> <project>"
subtitle: "<project code>"
author: "Tiger Analytics"
date: "<date>"
version: 3
status: Draft for client review
---

## 1. Document control
Version, date, author, reviewers, approvers, distribution.
Revision history table: version | date | author | summary of change.

## 2. Executive summary
Half a page. The problem, what is being asked for, the shape of the response,
the phasing, and what the client must decide.

## 3. Business context and problem statement
Why this exists now. Cost of the status quo, in the client's own terms.

## 4. Objectives and success measures
Each objective paired with how success will be measured. Numbers where the
client gave numbers; "measure TBD" where they did not — never invented targets.

## 5. Scope
5.1 In scope
5.2 Out of scope (explicit — this section prevents arguments)
5.3 Deferred to later phases

## 6. Stakeholders
Name, role, organisation, interest, decision authority.

## 7. Current state summary
Systems, data, and process pain points, business-level only.

## 8. Proposed solution overview
Business view. What capability the client gets. No architecture.

## 9. Business requirements
Grouped by capability area. BR-nnn entries.

## 10. Non-functional requirements
NFR-nnn entries: volume, performance, availability, retention, security,
compliance, audit. Mark unanswered categories explicitly as open, not absent.

## 11. Assumptions, dependencies and constraints
11.1 Assumptions — every unevidenced statement the BRD relies on
11.2 Dependencies — on the client, on third parties, on other programmes
11.3 Constraints — budget, timeline, mandated technology, regulatory

## 12. Risks
R-nnn: description, likelihood, impact, owner, mitigation.

## 13. Phasing and roadmap
Which requirements land in which phase and why. Sequencing rationale.

## 14. Open items requiring client decision
| ID | Item | Blocks | Owner | Needed by |

## 15. Approval
Signature block.

## Appendix — Glossary
Client vocabulary from understanding U11.

<!-- Appendix — Source traceability is generated by doc_export.py -->
```

## Appendix B — the export and validation script

`doc_export.py` ships with this skill at `scripts/doc_export.py`. It is shared
by the BRD, FRD and architecture skills.

On first use in a project, copy it to `<project>/_tooling/doc_export.py`. If a
copy already exists there, use it.

Requires `pandoc` for the .docx export; `--check` needs only Python.
