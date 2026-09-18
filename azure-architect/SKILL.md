---
name: azure-architect
description: "Step 6 of the discovery suite. Bind every architecture component from the HLD to concrete Azure resources, each with a justification, a rejected alternative and a SKU assumption. Produces the Azure deployment and network diagrams and a Well-Architected review. Cost estimation is opt-in — only produced if explicitly asked for. Use when an HLD needs its Azure design or an Azure deployment diagram."
---

# Azure Architect

Turns the HLD's capability requirements into concrete Azure resources — with a
reason recorded for each, a rejected alternative, and a Well-Architected review.
A cost model is produced only when explicitly requested — see "Cost estimation
is opt-in" below.

**Step 6** of the delivery suite:

```
transcript-intake → understanding-doc → brd-builder → frd-builder → hld-architect → [azure-architect] → project-plan → build-tasks → build-code
```

## Use this skill when

- An HLD is complete enough to bind to infrastructure
- The user asks for the Azure design, an Azure component or deployment diagram, or a cloud cost estimate
- The landing zone answer has arrived and an existing binding needs revising

## The working model

**Bind. Justify. Review.**

The HLD already declared what each component needs — "managed relational store,
~50 GB, transactional, PII-bearing, PITR to 24h". This skill's job is not to
re-derive the architecture. It is to bind each of those to a resource, record
*why that one and not the obvious alternative*, and then check the whole thing
against reliability, security, operations and performance.

The one thing that genuinely cannot be defaulted is **which landing-zone mode**
applies (Mode A vs. Mode B) — ask that first, see Step 2. Once the mode is
known, most of what used to be asked *within* Mode A is now a house default —
see "House defaults for Mode A" in `references/landing-zone.md`. Interview only
what is genuinely engagement-specific, not what a repeat client's platform team
already has standing.

### Cost estimation is opt-in

**Do not produce a cost estimate, and do not ask costing questions, unless the
user explicitly asks for one.** Section 13 (Cost estimate) and Step 8 are
skipped by default — omit the section entirely rather than filling it with
unpriced placeholder rows. This was a standing source of unwanted interview
questions (page-volume estimates, budget ceilings, chargeback models) for a
number nobody was asking for. If the user asks for a cost estimate later, run
Step 8 against `references/cost-model.md` at that point and add Section 13 to
the document as an addendum.

## What this skill adds to the chain

```
BR-002 → FR-P1-004 → C-03 → AZ-07 (AKS namespace, 0.5 vCPU/1 GiB requests)
```

Every binding is an `AZ-nn` entry pointing back at its component, so "why is
there an Event Hub in this design" has an answer that survives the person who
made the decision leaving.

## Inputs

| File | Role |
|---|---|
| `specs/04-architecture/HLD-<phase>-<feature>.md` | **Primary source.** Section 14, the capability requirements summary, is what gets bound |
| `specs/04-architecture/decisions.md` | `AD-nnn` decisions already taken. Do not contradict them; supersede if you must |
| `specs/04-architecture/_sessions/S*.md` | Design answers from the HLD interview |
| `specs/03-frd/FRD-*.md` | NFR detail, guardrails, and evaluation requirements for AI components |
| `specs/02-brd/BRD.md` | Compliance constraints |
| `specs/01-understanding/understanding.md` | Existing client platform, and constraints stated in the calls |
| `specs/project.yaml` | Phases, `standards.azure` override, export mode |
| `references/service-selection.md` | Capability → service binding tables, and the bindings that always need an `AD` |
| `references/landing-zone.md` | **Read first.** The Tier 1 question, and both modes |
| `references/cost-model.md` | Cost drivers per service, required table, honest uncertainty |
| `references/well-architected.md` | The five-pillar review checklist |

If `project.yaml` sets `standards.azure`, that file replaces
`service-selection.md`. Follow the client's approved services; do not argue with
their platform team's list.

## Hard rules

1. **No binding without a justification and a rejected alternative.** An `AZ` entry naming only the chosen service is a note, not a decision. `azure_check.py` fails without both.
2. **Every component in the HLD gets bound**, or is explicitly recorded as needing no Azure resource of its own (a logical component inside another's deployable). Silence is not an answer.
3. **Bind only what a capability requirement asked for.** A resource in this document with no capability behind it is scope you invented. If the HLD's section 14 is too thin to bind, say so and go back to `hld-architect` — do not fill the gap with a plausible service.
4. **Cost estimation is opt-in — see above.** When it is requested: never quote a price from memory. Every figure comes from the Azure Pricing Calculator or the client's agreed rates, with the date and region stated. See `cost-model.md`.
5. **When costing is requested, cost every environment.** Production-only estimates presented as the cost are the most common failure of a cost section.
6. **Private by default.** Public network access on a data service is a decision requiring an `AD`, not a default. Same for any secret that is not a managed identity.
7. **Do not re-open the HLD's decisions.** If a binding reveals that a component boundary was wrong, that is a finding to report and take back to step 5 — not something to quietly redesign here.
8. **The bindings listed in `service-selection.md` as needing an `AD` always need one.** A project-owned AKS cluster (rather than a namespace on the platform team's), a second container platform alongside it, Cosmos DB, API Management, Redis, multi-region, provisioned OpenAI throughput, custom Document Intelligence models. Note the direction: a namespace on the existing cluster is the house default and needs no `AD` — leaving it does.
9. **Never invent a landing zone answer.** If it is unknown, produce the design for the mode you assume, mark it `[ASSUMPTION]` throughout, and make it the top open item. It is the assumption most likely to invalidate the document.
10. **Never more than 8 questions in a batch**, ranked by consequence.
11. **Every sentence names the thing, never its id.** "The extraction worker runs on the shared cluster", not "C-04 binds to AZ-07". Ids live in the markdown's labels, tables and `[internal]` sections — see below. `doc_export.py --check` fails on one that reached the reader.
12. **12 pages.** Not a suggestion — see below.

## Two audiences, one file

The markdown keeps every id, because `azure_check.py` proves component coverage
through them and `project-plan` estimates against them. The .docx keeps none:
`AZ-07` and `C-04` name nothing a reader recognises, and a design whose every
sentence opens with two ids reads as machine output.

`doc_export.py --audience client`, the default, removes the scaffolding on the
way to Word:

| In the markdown | In the .docx |
|---|---|
| `### AZ-03 — Health Mart feed ingestion` | *Health Mart feed ingestion* — the name, and no id |
| `**Binds:** C-09` | removed — a cross-reference |
| `**Region:**`, `**Network:**`, `**Identity:**`, `**Scale:**`, `**Rejected alternative:**`, `**Cost driver:**`, `**Confidence:**` | removed — see the binding entry format below |
| `\| ID \| Resource \| Component \| Service \|` | `\| Resource \| Service \|` — both id columns dropped |
| `- **AD-008** — extraction is asynchronous` | `- extraction is asynchronous` |
| `## Traceability [internal]` — the C → AZ matrix | removed, heading and all |
| a run of `**Label:**` lines | separate short paragraphs, not one wall of prose |

The consequences: **write component and service names in prose and in diagram
labels**, and put anything the checkers need but a reader does not behind
`## Traceability [internal]` or inside `<!--internal-->` …
`<!--/internal-->`. `--check` lists every id that survived, and exits 6.

## Length and readability

**Target: 12 pages in Word**, measured on what reaches the reader — so an
`[internal]` matrix costs nothing and a binding that argues its own case costs
everything. `doc_export.py --audience client --budget 12` must pass before
export.

The first real Azure design this suite produced was **49 pages** from 11
bindings, measured by Word — because each binding argued its own case at length.
One `Cost driver` field was four sentences of speculation about a chargeback
model; one `Rejected alternative` spent a paragraph relitigating a decision the
HLD had already made. Splitting traceability out took it to 37; rule 1 is most
of the rest.

0. **Watch table geometry.** Pandoc gives every column an equal share of the
   page width, so a cell wraps against roughly `18 / columns` words per line —
   **the longest cell and the column count multiply.** Keep a row under six
   lines: 27 words at 4 columns, 21 at 5, 18 at 6. The cost table, the
   alert-rule table and the traceability matrix are all prone to this. Merge
   columns, or move the long cell to a note below the table. `--budget` names
   every table that breaks this and the cell length that would fix each.
1. **One sentence per binding field.** `Justification`, `Rejected alternative`,
   `Cost driver`, `Data classification` are each one sentence. Where the
   reasoning genuinely needs more, it is an `AD-nnn` in `decisions.md` and the
   field cites the id. This is the single largest saving available in this
   document.
2. **Do not re-argue the HLD.** If `AD-008` already mandates AKS, the binding
   says so and cites it. Repeating the platform-team rationale here is a second
   copy that will drift from the first.
3. **Lead section 5 with a binding register table** — id, component, service,
   SKU, region. A reviewer costing the design reads that table and nothing else.
4. **Never print an empty field.** Omit it. `azure_check.py` now treats a dash
   as absence, so padding a required field with one fails the check rather than
   satisfying it.
5. **An open item is a marked assumption, not an essay.** Write
   `[ASSUMPTION — GAP-A1]` inline and put the explanation in section 16, once,
   with an owner and what it blocks. Repeating the landing-zone caveat under
   eleven `Region:` fields costs a page and tells the reader nothing the first
   one didn't.
6. **Cross-reference only when the reader must go and read it.** This document
   had 42 inline `(see …)` and `(§n)` pointers. Keep the ones aimed at an `AD`,
   a `GAP`, or the cost table; cut the rest.
7. **Two diagrams minimum, four maximum** — component, network, and only then
   environment and trust-boundary views if they show something the first two
   don't.

## Files this skill owns

```
specs/05-azure/
  _index.md                             # which Azure designs exist, which HLD each binds
  AZURE-P1-customer-profile.md
  decisions.md                          # AD-nnn continuing the HLD's numbering
  _diagrams/                            # rendered PNGs, written by doc_export.py
  _sessions/
    _gaps-AZURE-P1-customer-profile.md
    S14_2026-09-05_azure-landing-zone.md
```

`AD` and `S` numbering **continues from the HLD's**, not from 1. Read the highest
id already used in `specs/04-architecture/` and carry on above it. `doc_export.py`
refuses to run on a session-id collision.

---

## Procedure

### Step 1 — Read the HLD and check the handoff is usable

Read the HLD in full, but section 14 — the capability requirements summary — is
what you actually bind. Also read `decisions.md`: an `AD` there may already
constrain a binding.

Before going further, check the handoff is complete. Every component needs
capability requirements, a data classification and an expected scale. If several
do not, stop and report it — running `arch_check.py` on the HLD will name them:

```
python <project>/specs/_tooling/arch_check.py \
  --hld <project>/specs/04-architecture/HLD-P1-customer-profile.md \
  --frd <project>/specs/03-frd/FRD-P1-customer-profile.md
```

A `NO CAPABILITY` finding means this skill has nothing to bind for that
component. Binding it anyway means inventing the requirement, which is exactly
what the seam between these two skills exists to prevent.

### Step 2 — Establish the landing zone

Read `references/landing-zone.md` before binding anything. Ask **only** whether
Mode A (enterprise landing zone) or Mode B (standalone subscription) applies,
plus whether this stack is on an approved-services list — see "What to actually
ask" in `landing-zone.md`. The other historical follow-ups (public ingress, DNS
ownership, policy specifics, region/residency) are now house defaults for Mode A
and are **not** interview questions — apply them from
`landing-zone.md`'s "House defaults for Mode A" section instead of asking.

If the user does not know the mode, they usually know *who* knows. Ask for that
person, record it as a dependency with an owner, and proceed under a stated
assumption: **assume Mode A, the enterprise landing zone**, for any client of a
size where a central platform team is likely. Designing for Mode A and
discovering Mode B is a simplification; the reverse is a redesign.

Mark every affected binding `[ASSUMPTION — pending landing zone confirmation]`
and make it open item number one.

### Step 3 — Bind each component

Work through the HLD's section 14 row by row, using
`references/service-selection.md`. For each component produce one or more `AZ`
entries in the format below.

The default binding wins unless a stated NFR or a client constraint rules it
out. You are not choosing the most interesting service; you are choosing the one
the team can operate, and recording why the obvious alternative was not it.

Where a capability is genuinely ambiguous — a "managed relational store" whose
transaction volume was never stated — that is a gap, not a coin toss. Register
it.

### Step 4 — Design the shared infrastructure

Beyond the per-component bindings, specify once:

- **Network**: vnet and subnet layout with delegations, private endpoints and which DNS zone resolves each, egress path, ingress path — corporate-network-only by default in Mode A (see `landing-zone.md`); design the private path, do not ask whether public ingress is wanted
- **Identity**: the managed identity per component and its role assignments, scoped per component rather than one identity with everything
- **Secrets**: Key Vault layout and access model
- **Observability**: **Dynatrace** (OneAgent / OpenTelemetry ingestion) is the house default APM/observability platform across every project — not Azure Monitor or Log Analytics. Bind an alert (Dynatrace problem detection) per failure mode in the HLD's failure model. See `service-selection.md`'s Observability section.
- **Governance**: resource groups, naming convention, the five required tags — policy assignments are the platform team's concern in Mode A, not something to enumerate here (see `landing-zone.md`)
- **Environments**: what differs between dev, uat and prod — which should be tier and scale only, never topology

In Mode A, network/DNS/peering/policy are the platform team's and are already
provisioned as part of the landing zone, not a fresh request this engagement
makes — do not model them as an open lead-time dependency unless the user
states otherwise for this specific client.

### Step 5 — Build the gap register and interview

Write `_sessions/_gaps-<name>.md` in the suite's usual shape, tiered by
consequence. This list is deliberately shorter than it used to be — see "Cost
estimation is opt-in" above and `landing-zone.md`'s house defaults for what is
no longer asked:

- **Tier 1** — landing zone mode, approved services, who operates this after go-live, anything genuinely engagement-specific that a house default cannot answer
- **Tier 2** — HA and backup levels against the stated RTO/RPO, quota needs, retention per store
- **Tier 3** — naming and tagging specifics beyond the house convention

Interview up to 8 at a time, Tier 1 first, each with a proposed answer. Log
answers immediately to `_sessions/S<nn>_<date>_<slug>.md` in the same format
`frd-builder` and `hld-architect` use, continuing the project's `S` numbering.

Tier 1 questions worth asking on every engagement, because the client usually
has an answer and rarely volunteers it:

- Is there an approved-services list, and is our stack on it? Does the platform team already provide a shared Container Registry?
- Who operates this after go-live — us, the client, or shared?
- Is there existing Azure OpenAI quota in the target region, or does it need requesting? (Only relevant where the HLD actually declares an LLM component — do not ask this on a project with no Azure OpenAI capability requirement.)

Do **not** ask: public ingress (default corporate-network-only, `landing-zone.md`),
region/data residency (the platform team's placement decision), Azure Policy
specifics (the platform team's compliance gate, not this skill's concern),
budget envelope (no cost estimation by default — see above), or how a
third-party system authenticates into a resource this project owns (bind
assuming the vendor supports a standard method — SAS or an Azure AD app
registration — and note it as vendor-managed, not an open architecture
question).

### Step 6 — Write the decision log

Every binding that needed a real choice becomes an `AD-nnn` in
`specs/05-azure/decisions.md`, continuing the HLD's numbering, append-only with
supersession:

```markdown
### AD-011 — One AKS namespace on the platform team's cluster for all application compute

- **Status:** ACTIVE
- **Decided:** 2026-09-05, session S14
- **Drivers:** House standard (`standards-stack.md`); the platform team already
  operates the cluster and confirmed a namespace on request (S14:03); NFR-011
  availability target met by the cluster's existing zone spread
- **Decision:** All application components deploy as Kubernetes objects in a
  single namespace, `<app>`, on the platform team's existing cluster. This
  project provisions the namespace and its contents only — never the cluster,
  node pools or CNI configuration.
- **Options considered:**
  - *Container Apps* — rejected: a second container platform alongside a cluster
    the platform team already runs, splitting the operational model and the
    deployment story for no stated requirement.
  - *A cluster this project provisions and owns* — rejected: no service-mesh or
    custom-scheduling requirement, and it would move cluster lifecycle,
    upgrades and patching onto the delivery team with no named owner.
- **Consequences:** We inherit the platform team's cluster upgrade cadence and
  their admission policies, so a policy that blocks a manifest is a dependency
  on them, not a fix we can make. Namespace creation carries their standard lead
  time — see section 3.3.
- **Evidence:** [[S14:03]] [[T05:088]]
```

Every service on `service-selection.md`'s always-needs-an-`AD` list gets one.
So does every deviation from the house Azure standards, and every case where a
data service is left publicly accessible.

### Step 7 — Draw the diagrams

Follow `../hld-architect/references/diagram-conventions.md` — same conventions,
same shape vocabulary, same twenty-node ceiling.

Two mandatory, four maximum — each costs about half a page of the 12-page
budget:

- **Azure component diagram** (mandatory) — the bound resources, grouped by resource group or tier, each labelled with its service name and the component it hosts. Not the `AZ-nn`: the diagram is the one place a reader learns what runs where, so it has to read on its own
- **Network topology** (mandatory) — vnet, subnets, private endpoints, ingress and egress paths, and the hub in Mode A
- **Data flow with trust boundaries** — where a request crosses from untrusted to trusted. The single most useful thing this document can show a security reviewer, so prefer it over the environment view if only one slot is left
- **Environment view** — only if dev/uat/prod differ in more than SKU size; a table says it better otherwise

Label every node with the Azure service and what it hosts —
`FEED[AKS CronJob - Health Mart feed]`, not `AZ03[AZ-03 CronJob]`. The diagram
is the one place a reader learns what runs where, so it has to read on its own.
`azure_check.py` matches a binding to its diagram by name as well as by id, so
the ids are not needed to keep the two from drifting.

### Step 8 — Cost the design (only if explicitly requested)

**Skip this step by default.** Do not produce Section 13, and do not ask any
costing question (page volumes, budget ceilings, chargeback models) unless the
user has explicitly asked for a cost estimate. If asked, follow
`references/cost-model.md`: produce the required table, then the total per
environment, the top three cost drivers, the biggest cost risk, and what is
excluded.

Get the figures from the Azure Pricing Calculator and state the date and region.
If you cannot access it, produce the table complete with SKU assumptions and
quantity drivers, leave the estimate column empty, and say plainly that the
figures need filling from the calculator. **An empty column is honest; a
remembered price is not.**

### Step 9 — Run the Well-Architected review

Work through `references/well-architected.md` and record the output as a table:
pillar, finding, and either the mechanism or the accepted risk with an owner.
Where cost estimation was not requested (the default), answer the Cost
Optimisation pillar structurally (scale-to-zero configured, tiers stated) rather
than with a spend figure — it does not need Section 13 to exist.

End on its two questions — what is most likely to go wrong in the first month,
and what would we regret in a year. Both go in the risks section.

### Step 10 — Validate

Both checks are mandatory before the document is shared.

```
python <project>/specs/_tooling/azure_check.py \
  --azure <project>/specs/05-azure/AZURE-P1-customer-profile.md \
  --hld <project>/specs/04-architecture/HLD-P1-customer-profile.md
```

```
python <project>/specs/_tooling/doc_export.py \
  --input <project>/specs/05-azure/AZURE-P1-customer-profile.md \
  --transcripts <project>/specs/00-transcripts \
  --sessions <project>/specs/03-frd/_sessions \
  --sessions <project>/specs/04-architecture/_sessions \
  --sessions <project>/specs/05-azure/_sessions \
  --check --audience client --budget 12 --max-cites 2 \
  --reference-doc <project>/specs/_tooling/house-reference.docx
```

Exit 5 is over budget, with the heaviest sections and any table whose rows run
tall named. Trim before exporting, in this order:

1. Tag the traceability matrix `[internal]`.
2. Cut every `Service`, `Justification` and `Data classification` over its word limit — `azure_check.py` names each one and the count.
3. Delete any per-binding statement of the house posture — private endpoint, managed identity, platform-assigned region. It is asserted once in the landing-zone section and detailed once in the network and identity sections.
4. Drop columns from the remaining wide tables.
5. Delete repeated landing-zone caveats down to one in the open-items section.
6. Cut `(see …)` pointers that aren't aimed at an `AD`, a gap or the cost table.

Exit 6 is an id in reader-facing text, listed with its line. Reword it, or move
the line inside `<!--internal-->` … `<!--/internal-->` where it has to stay
machine-readable — never strip an id from a label or matrix, which the checkers
read and the reader never sees.

`azure_check.py` reports unbound components, bindings with no justification or
no rejected alternative, missing SKU assumptions, resources missing from the
cost table, PII-bearing stores with no stated encryption or network isolation,
resources absent from every diagram, services that need an `AD` and do not have
one, and any binding to a service outside the client's approved list when one is
supplied via `--approved`.

A `[GAP-nn]` marker reports as `UNRESOLVED` but is advisory and does not fail the check: a deliberately deferred gap is meant to stay visible in the document.

If either script is missing from `specs/_tooling/`, run `transcript-intake` against the
project — it owns all suite tooling.

### Step 11 — Export and report

```
python <project>/specs/_tooling/doc_export.py \
  --input <project>/specs/05-azure/AZURE-P1-customer-profile.md \
  --transcripts <project>/specs/00-transcripts \
  --sessions <project>/specs/03-frd/_sessions \
  --sessions <project>/specs/04-architecture/_sessions \
  --sessions <project>/specs/05-azure/_sessions \
  --out <project>/specs/05-azure/AZURE-P1-customer-profile_v1.docx --mode companion --audience client \
  --reference-doc <project>/specs/_tooling/house-reference.docx
```

Update `specs/05-azure/_index.md`. Report to the user:

- Resource count by type, and component coverage against the HLD
- **Estimated page count against the 12-page budget**
- If (and only if) a cost estimate was requested: total cost per environment and across all environments, the top three drivers, and the biggest cost risk
- Every `AD` as one reviewable block, with the always-needs-an-`AD` bindings called out separately
- Well-Architected findings that became accepted risks, each with its owner — this is the list a security or platform reviewer will ask for
- Every lead-time dependency: platform-team requests, quota, peering, DNS. These go into the project plan, not a footnote
- Gaps still open, especially anything blocked on the landing zone
- **What `project-plan` will need that is not here yet** — typically the lead times above, and confirmation of who operates the system after go-live

---

## Binding entry format

**One shape, four printed fields.** The reader sees `Service`, `SKU / tier`,
`Justification` and `Data classification`. Everything else in the block is for
`azure_check.py`, the network and identity sections, and the next skill.

Lead the section with the register table, so a reviewer can see the whole design
without reading fifteen blocks. The `Resource` column is what the reader scans
by — the `ID` and `Component` columns are dropped on export, so a table without
it leaves them nothing to read:

```markdown
| ID | Resource | Component | Service | SKU / tier |
|---|---|---|---|---|
| **AZ-07** | Application workloads | C-02, C-03, C-04 | AKS, platform cluster, our namespace | Requests 0.5 vCPU / 1 GiB, 2 replicas |
| **AZ-08** | Operational store | C-05 | PostgreSQL Flexible Server | General Purpose, 2 vCore / 16 GiB |
```

`Region` is not a column: in an enterprise landing zone it is
"platform-assigned" on every row, and fifteen identical cells are a column of
noise. State it once in the landing-zone section.

Then one block per binding. `azure_check.py` parses these labels, so keep them
exactly — **one sentence each**:

```markdown
### AZ-07 — Application workloads

**Binds:** C-02, C-03, C-04
**Service:** AKS on the platform team's existing cluster, in our own namespace
**SKU / tier:** Requests 0.5 vCPU / 1 GiB, limits 1 vCPU / 2 GiB, 2 replicas, scaling to 6 on CPU
**Region:** Platform-assigned
**Justification:** The house standard for application compute; Container Apps was rejected as a second container platform for one application.
**Rejected alternative:** Container Apps — a second container platform for one app (`AD-011`).
**Network:** The cluster's existing vnet; ingress via the platform team's controller.
**Identity:** One user-assigned managed identity per component, each scoped to only what it calls.
**Data classification:** No persistence in this resource
**Confidence:** DESIGN DECISION [[S14:03]]
```

Four short paragraphs reach the reader. Note where the work went:

- **`Justification` names what it beat, in a clause** — "the house standard for application compute; Container Apps was rejected as a second container platform for one application". That is the whole argument a reviewer needs. The formal `Rejected alternative` label stays for `azure_check.py`, and where the trade-off was genuinely contested it becomes an `AD` and the justification cites nothing but the sentence.
- **`Binds`, `Region`, `Network`, `Identity` and `Scale` never print.** `Region` and the private-endpoint-and-managed-identity posture are the same house default on every row; asserted once in the landing-zone section, they are noise fifteen times over. The per-resource detail keeps its own sections — network design, and identities and role assignments — where a security reviewer reads it as one table rather than hunting fifteen blocks.
- **No id in prose.** "The same standard as the application workloads", not "same as AZ-01/AZ-02". `doc_export.py --check` exits 6 on one that survived.

Word limits, enforced by `azure_check.py`: `Service` 25 words,
`Justification` 35, `Data classification` 25.

`Cost driver` is omitted because cost estimation is opt-in (see above) — add it
only when Step 8 actually runs, and it does not print either: the cost table is
where a reader looks for it.

For a resource holding data, `Data classification` states the class and the
protection, and nothing else — the reasoning is in the data-protection section:

```markdown
**Data classification:** PII-bearing customer financial data. Encrypted at rest
and in transit, private endpoint only, retained 7 years
```

Confidence marking, as elsewhere in the suite — recorded in the markdown, never
printed, and reported to the user at the end of Step 11 instead:

- `CONFIRMED` — the client stated it, cites `[[Tnn:nnn]]`
- `DESIGN DECISION` — decided in a session, cites `[[Snn:nn]]`
- `STANDARD` — the default binding, no project-specific decision
- `ASSUMPTION` — neither, marked `[ASSUMPTION — requires confirmation]`

## Document structure

Budget per section, against the 12-page target, measured on what reaches the
reader. Section numbers below are for navigating the markdown - pandoc numbers
the exported document, after the [internal] sections have been dropped:

| Section | Budget | Shape |
|---|---|---|
| 1–3 control, scope, landing zone | 2.5 pp | Tables. Section 3.3 lead times feed the plan |
| 4 overview | 1.5 pp | Component diagram plus one paragraph |
| 5 resource bindings | 4 pp | Register table, then one block each: four printed fields, one sentence per field |
| 6–8 network, identity, secrets | 3 pp | Network diagram plus tables |
| 9–12 data protection, observability, environments, governance | 2.5 pp | Tables |
| 13 cost (only if requested) | 0–1 pp | One table, omitted entirely by default |
| 14 Well-Architected | 1 pp | One table |
| 15–16 decisions, risks | 1 pp | Tables. Section 15 is an `AD` index, not the entries |
| 17 traceability | 0 pp | `[internal]` — complete in the markdown, absent from the .docx |

```markdown
## 1. Document control
## 2. Scope
   2.1 The HLD this binds, and the components covered
   2.2 Out of scope
   2.3 Dependencies on other Azure designs
## 3. Landing zone and tenancy
   3.1 Mode, and what it means we do and do not own
   3.2 Subscriptions, resource groups, regions
   3.3 Platform-team dependencies, with lead times
   3.4 Policy constraints that shaped a binding
## 4. Azure architecture overview
   4.1 Azure component diagram
   4.2 The shape of the deployment, in a paragraph
## 5. Resource bindings              # register table, then AZ-nn entries
## 6. Network design
   6.1 Network topology diagram
   6.2 Vnet, subnets and delegations
   6.3 Private endpoints and DNS resolution
   6.4 Ingress, egress, and trust boundaries
## 7. Identity and access
   7.1 Managed identities and role assignments per component
   7.2 Human access to each environment, and the approval path
   7.3 Deployment identity and its scope
## 8. Secrets and key management
## 9. Data protection
   9.1 Classification per store
   9.2 Encryption, in transit and at rest
   9.3 Retention and lifecycle
   9.4 Lower-environment data handling
## 10. Observability and operations
   10.1 Telemetry collection and retention
   10.2 Alert rule per failure mode
   10.3 Alert routing, and who operates this
## 11. Environments                  # what differs, and what must not
## 12. Governance                    # naming, tags, policy, posture
## 13. Cost estimate                 # omit by default - only if the user asked for one, per cost-model.md
## 14. Well-Architected review       # per well-architected.md
## 15. Architecture decisions        # AD index; full entries in decisions.md
## 16. Risks, dependencies and open items
## 17. Traceability [internal]       # C → AZ matrix
```

Section 3.3 is the one that changes the project plan. A private-DNS record or a
peering change with a three-week lead time will hold up a finished environment
and is invisible in every diagram in this document. Give each one an owner and a
date.

Section 13, when it exists, is the one the sponsor reads — but it exists only on
request (see "Cost estimation is opt-in"). Section 14 is the one the client's
platform and security reviewers read, and it is never optional.
