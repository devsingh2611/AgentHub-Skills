# Cost model

**This entire file is opt-in.** Cost estimation is not part of `azure-architect`'s
default output — see "Cost estimation is opt-in" in `../SKILL.md`. Consult this
file only when the user explicitly asks for a cost estimate; do not ask costing
questions (page volumes, transaction counts, budget ceilings) as part of the
standard interview.

The cost table is the section a client sponsor reads first and the one most
likely to be wrong in a way nobody catches until the third monthly bill.

## Non-negotiable rules

1. **Never quote a price from memory.** Azure pricing changes, varies by region, and varies by agreement. Every figure comes from the Azure Pricing Calculator or the client's own agreed rates, and the document states which, plus the date and region.
2. **State the quantity driver, not just the number.** "AKS: $X/month" is unverifiable. "AKS namespace: 4 pods requesting 0.5 vCPU / 1 GiB each, burst to 10 for ~2h/day, cross-charged at the platform team's per-vCPU rate" can be checked, and re-costed when the assumption changes.
3. **Every assumption behind a figure is visible.** A cost estimate is a model, and a model with hidden inputs cannot be reviewed.
4. **Cost all environments.** Three environments cost roughly three times one. Estimating production alone and presenting it as the cost is the single most common error here.
5. **Mark confidence per line.** Some lines are near-certain (a fixed-tier database), some are entirely demand-driven (LLM tokens, Log Analytics ingestion). Presenting both with the same authority is misleading.

## Required output table

| Resource | Component | SKU / tier assumption | Quantity driver | Monthly estimate | Confidence |
|---|---|---|---|---|---|
| AKS namespace | C-03 | Platform cluster; requests 0.5 vCPU / 1 GiB per pod | 2 always-on pods + burst 10 for 2h/day, cross-charged | | Medium |
| PostgreSQL Flexible Server | C-06 | General Purpose, 2 vCore, 128 GB, zone-redundant HA | Fixed | | High |
| Azure OpenAI | C-08 | Pay-as-you-go, pinned deployment | ~4,000 interactions/month at ~8k tokens each | | **Low** |
| Log Analytics | C-10 | Pay-as-you-go ingestion, 90-day retention | ~15 GB/month | | Low |

Then, immediately after it:

- **Total per environment**, and the total across all environments
- **The top three cost drivers**, named
- **The biggest cost risk** — the line that could be several times the estimate, and what would cause that
- **What is excluded** — licences, client-side costs, egress to on-premises, support plan, anything the client pays for separately

## What drives cost, per service

Knowing the *driver* is what makes an estimate defensible when it turns out to
be wrong.

| Service | What actually drives the bill |
|---|---|
| AKS namespace (platform cluster) | Whether the platform team cross-charges, and on what basis — reserved requests, actual usage, or a flat namespace fee. Ask; do not assume it is free to us because the cluster already exists |
| AKS cluster we own | Node pool size, running continuously, whether or not anything is deployed |
| Container Apps / Functions | vCPU-seconds and memory-seconds. Always-on minimum replicas dominate; scale-to-zero changes the shape entirely |
| PostgreSQL / Azure SQL | Compute tier and whether HA is enabled — zone-redundant HA roughly doubles compute. Storage and backup beyond the included allowance |
| Blob / ADLS Gen2 | Stored GB by access tier, plus transaction counts. Transactions surprise people on chatty workloads |
| Cosmos DB | Provisioned RU/s, continuously, per region. The most common source of a shocking bill |
| Service Bus / Event Hubs | Tier plus operations or throughput units. Premium is a large step up from Standard |
| Azure OpenAI | Tokens in and out, per model. Provisioned throughput is a fixed monthly floor instead — cheaper only above a real, sustained volume |
| Document Intelligence | Pages processed, and higher for custom models |
| AI Search | Tier and replica/partition count, running continuously. Vector storage pushes the tier up |
| Log Analytics | **GB ingested**, then retention beyond the included period. Verbose application logging is a cost decision |
| Application Gateway / Front Door | Fixed hourly, plus capacity units or requests |
| API Management | Fixed by tier, and the Developer tier has no SLA — so it is not a production answer |
| Private endpoints | Per endpoint per hour, plus data processed. Small each; adds up across many data services |
| NAT Gateway | Fixed hourly plus data processed |
| Databricks | DBUs by workload type and tier, **plus** the underlying VM compute. Estimating DBUs alone understates it substantially |

## Levers to state, not silently assume

- **Scale to zero** in non-production. Dev and test do not need always-on replicas, and this is usually the largest easy saving
- **Reserved instances or a savings plan** for predictable production compute — a real discount, but a 1- or 3-year commitment, which is the client's decision to make, not ours
- **Dev/Test subscription pricing**, if the client's agreement includes it
- **Storage lifecycle rules** moving cold data to a cheaper tier, driven by the retention policy the HLD already states
- **Log Analytics retention per table** — verbose tables kept short, audit tables kept long
- **Auto-pause** on non-production databases where the tier supports it

## What gets forgotten

**Non-production.** Covered above, and it is worth repeating because it is the
most common single error.

**Log Analytics ingestion.** Frequently the second or third largest line, and
almost never in the first draft of an estimate.

**Databricks VM compute underneath the DBUs.** Two separate charges; estimating
one is estimating roughly half.

**Data egress**, particularly to on-premises or to a partner.

**The cost of the data migration itself** — one-off compute and transfer that
does not appear in a steady-state monthly view.

**Growth.** A figure for month one presented as "the cost" when volumes are
stated to grow. Give month one and a projection at the stated growth rate, or
say explicitly that growth is not modelled.

## How to present uncertainty honestly

Do not produce a single confident number for a demand-driven workload. Give the
model and a range:

> Azure OpenAI is the least predictable line. At the stated ~4,000 interactions
> per month it is modelled at £X. At double the volume it is £2X — this line
> scales linearly with use and has no ceiling unless a spend cap is configured
> (see AD-009). It is the line to watch in month one.

That paragraph is more useful to a sponsor than a total to two decimal places,
and it is the difference between an estimate and a guess with a currency symbol
in front of it.
