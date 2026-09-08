---
name: understanding-doc
description: Step 2 of the discovery suite. Build and incrementally update the cumulative project understanding document from ingested transcripts, with confidence tags, transcript citations, a decision log with supersession, and an open-questions register. Use after transcript-intake, or when asked what we know so far.
---

# Understanding Document

Builds and incrementally maintains the cumulative project understanding document
from normalized call transcripts. Every statement is tagged with a confidence
level and cited back to the exact transcript segment it came from.

**Step 2** of the pre-build discovery suite:

```
transcript-intake → [understanding-doc] → brd-builder → frd → architecture → azure → plan
```

## Use this skill when

- New transcripts have been ingested and the project understanding needs updating
- The user asks "what do we know so far", "update the understanding doc", "what's changed"
- Before running `brd-builder` — the BRD reads this document, not raw transcripts

## What this document is

An **internal** working document. It is candid by design: it names contradictions
between stakeholders, marks assumptions as assumptions, and records where the
client seemed unsure. It is not a client deliverable — do not soften it. If the
user wants something client-safe, that is the BRD.

It is also the **citation index** for everything downstream. The BRD, FRD and
architecture documents follow citations from here into the transcripts. Precision
matters more than prose quality.

## Non-negotiable rules

1. **Every statement carries a confidence tag and at least one citation.** No exceptions. A statement you inferred is `[ASSUMED]` with the citations that led you to infer it.
2. **Never delete a statement.** Understanding changes by supersession, not erasure. A reversed decision gets marked superseded and stays visible.
3. **Never silently resolve a contradiction.** If two stakeholders said different things, that is a finding, not a problem to tidy away. Tag it `[CONTESTED]` and record both positions with attribution.
4. **Never invent a citation.** Before writing `[[T04:012]]`, verify that segment exists and says what you claim. Grep the transcript.
5. **Preserve the client's vocabulary.** If they say "member" not "customer", the document says "member". Record the mapping in the glossary.
6. **Do not design.** No solutions, no technology choices, no architecture. This document records what is true and what is wanted.

## Confidence tags

| Tag | Meaning |
|-----|---------|
| `CONFIRMED` | Stated explicitly by a stakeholder with authority over that area |
| `ASSUMED` | Inferred by us, or stated by someone without authority. Needs validation |
| `CONTESTED` | Stakeholders have said conflicting things. Both positions recorded |
| `OPEN` | Raised but unanswered. Has a matching `Q-nnn` entry |

Write tags with the source person where it matters for authority:
`[CONFIRMED · Priya Sharma]`.

## Citation syntax

`[[T04:012]]` — transcript 4, segment 12. Multiple citations space-separated.
A statement synthesised across calls cites all of them.

## Files this skill owns

```
01-understanding/
  understanding.md     # the schema'd cumulative document
  decisions.md         # decision log with supersession chain
  open-questions.md    # gap register
  _changelog.md        # what changed on each run
```

---

## Procedure

### Step 1 — Establish what's new

Read `00-transcripts/_index.md` and the `transcripts_covered` list in
`understanding.md` front matter. The difference is your work queue.

If `understanding.md` does not exist, this is the first run: every transcript is
new, and you create the document from the schema below.

If there is nothing new, say so and stop. Don't regenerate the document for no
reason.

### Step 2 — Extract claims from each new transcript

Read each new transcript in full. Do not skim — the important constraint is
usually a throwaway half-sentence in minute 41.

Pull out every statement that bears on: business drivers, current systems, data,
pain points, desired outcomes, scope boundaries, constraints, volumes, timelines,
compliance, dependencies, and organisational realities (who decides what, who is
resistant, what has failed before).

For each claim record: the statement, who said it, their apparent authority, and
the segment ID.

### Step 3 — Reconcile against the existing document

This is the core of the skill. For each extracted claim, classify it against what
the document already says, and act:

| Classification | Action |
|---|---|
| **NEW** | Add to the correct schema section with tag and citation |
| **CORROBORATES** | Append the new citation to the existing statement. If the new speaker has authority and the statement was `ASSUMED`, promote it to `CONFIRMED` and note the promotion in the changelog |
| **REFINES** | Update the statement text to the more precise version. Keep both citations. Log it |
| **CONTRADICTS** | Retag the statement `CONTESTED`. Record both positions with attribution and citations. Raise a `Q-nnn` asking which holds. If it reverses a logged decision, supersede that decision |
| **RESOLVES** an open question | Close the `Q-nnn`, write a `D-nnn` decision entry, add the resulting statement to the document |

Never overwrite a `CONFIRMED` statement with a contradicting one just because the
new call is more recent. Recency is evidence, not authority. Mark it contested and
surface it.

### Step 4 — Run the NFR sweep

Non-functional requirements are the most consequential thing missing from
discovery calls, and their absence is invisible until architecture. After each
update, check section U7 against this checklist and raise an open question for
every category still empty:

- Data volumes today and growth rate
- Throughput and latency expectations
- Availability target, RTO, RPO
- Retention and archival policy
- PII classification and applicable regimes (GDPR, DPDP, HIPAA, CCPA, PCI)
- Security model, authentication, authorisation granularity
- Concurrent users and peak patterns
- Integration SLAs with upstream and downstream systems
- Audit and lineage requirements
- Environment strategy and data masking in lower environments
- Cost ceiling or budget envelope
- Localisation, multi-region, data residency

Do not fabricate values. An empty NFR is a question, not a guess.

### Step 5 — Write the files

**`understanding.md`** — fixed schema, stable anchors, so updates are surgical and
downstream skills can target sections:

```markdown
---
project: ACME-CDP
doc: understanding
version: 4
last_updated: 2026-08-28
transcripts_covered: [T01, T02, T03]
audience: internal
---

# Project Understanding — <client> <project>

> Internal working document. Candid by design. Not for client circulation.

## U1. Engagement snapshot
## U2. Business context and drivers
## U3. Stakeholders and actors
## U4. Current state
### U4.1 Systems landscape
### U4.2 Data landscape
### U4.3 Processes and pain points
## U5. Target state
## U6. Capabilities in scope
## U7. Non-functional requirements and constraints
## U8. Assumptions
## U9. Explicitly out of scope
## U10. Risks, dependencies and organisational realities
## U11. Glossary and client vocabulary
```

Statements look like:

```markdown
- [CONFIRMED · Priya Sharma] Customer data is fragmented across Salesforce,
  a legacy Oracle CRM, the loyalty platform and Braze. [[T01:001]]
- [CONTESTED] Latency expectation for the unified profile.
  - Priya Sharma (Head of Data): nightly batch is sufficient for Phase 1,
    real-time is a Phase 2+ conversation. [[T01:003]]
  - Anita Desai (Call Centre Ops): near-real-time has been requested for two
    years; accepts batch if it lands by 06:00. [[T01:004]]
  - See Q-004.
```

Keep U3 aligned with the participant table in the transcript index, adding
influence and decision authority where the calls reveal it.

**`decisions.md`** — append-only, with supersession:

```markdown
### D-007 — Phase 1 uses nightly batch, not streaming
- **Status:** ACTIVE            <!-- ACTIVE | SUPERSEDED by D-nnn | REVERSED -->
- **Decided:** 2026-08-14, call T01
- **Decided by:** Priya Sharma (Head of Data — has authority)
- **Decision:** Unified profile refreshes nightly; batch must complete by 06:00.
- **Rationale:** Real-time integration cost not justified for Phase 1 use cases.
- **Dissent:** Anita Desai flagged sustained call-centre demand for
  near-real-time. [[T01:004]]
- **Evidence:** [[T01:003]] [[T01:004]]
```

When a decision is reversed, set the old one to `SUPERSEDED by D-nnn` and write a
new entry that references what it replaces and why. Never edit the original.

**`open-questions.md`**:

```markdown
| ID | Question | Raised in | Owner | Blocks | Status |
|----|----------|-----------|-------|--------|--------|
| Q-004 | Is nightly batch acceptable to call-centre ops, or is 06:00 a hard SLA? | T01 | Anita Desai | BRD scope, HLD | OPEN |
| Q-005 | Retention policy for behavioural data? | — | Kevin Tan | NFR, storage design | OPEN |
```

`Blocks` matters — it tells the user which questions are actually urgent. A
question blocking the HLD is more pressing than one blocking a Phase 3 decision.

Mark resolved questions `RESOLVED (D-nnn, T04)` and keep them in the table.

**`_changelog.md`** — prepend a new entry each run:

```markdown
## Run 2026-08-28 — added T03
- 6 new statements, 3 corroborations, 1 refinement
- 1 CONTESTED raised: unified-profile latency (U5) — Priya vs Anita
- D-007 superseded by D-012 (batch window moved to 04:00)
- 2 open questions resolved, 5 raised (3 from NFR sweep)
- 1 statement promoted ASSUMED → CONFIRMED: record volume ~40M
```

### Step 6 — Report

Do not paste the document into chat. Report the **diff**: what changed, what's now
contested, what was superseded, and the open questions that block downstream work
— ranked by what they block, not by when they were raised.

Then state what's needed next: either "run `brd-builder`" if the picture is
coherent, or "these N questions should be answered before the BRD" if it isn't.

Offer to draft an agenda for the next client call from the open-questions list.
