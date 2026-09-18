# Well-Architected review

A structured pass over the bindings before the document is shared, following the
five pillars of the Azure Well-Architected Framework. It exists to catch the
things that are invisible in a resource diagram.

Work through it as a checklist. **Every item is answered either with the
mechanism, or with an accepted risk and a named owner.** "Not applicable" is a
legitimate answer where it is genuinely true; "we should look at that" is not.

Record the output as a table in the document — pillar, finding, and either the
mechanism or the accepted risk. A pillar with no findings is a suspicious
pillar; look again.

## Reliability

- Every component's availability target, and the mechanism that delivers it — replica count, zone redundancy, health probes
- Behaviour when each dependency is unavailable, matching the HLD's failure model. The binding must not contradict it
- Backup configuration per data store, sized to the stated RPO — and whether a restore has ever been *tested*, not just configured
- Retry policy on every service-to-service and outbound call, with backoff
- Quota and limits per service, and the behaviour when one is hit
- Single points of failure. Name them, or state that there are none and why
- Whether the stated RTO is achievable by the bound configuration. If the RTO is 4 hours and recovery means restoring a database and reconfiguring DNS, do the arithmetic

## Security

- Public network access disabled on every data service, or an accepted risk with an owner
- Private endpoints and DNS resolution, including from on-premises
- Managed identity everywhere. Any remaining secret has a rotation mechanism and an owner
- Key Vault access policy or RBAC scoped per component — not one identity with access to everything
- Encryption at rest (default) and whether customer-managed keys are required by policy or compliance
- TLS in transit everywhere, with minimum version set explicitly
- Data classification per store, matching the tags, and the PII handling the FRD requires
- WAF in front of every public ingress
- Least privilege on the deployment identity. A pipeline identity with subscription Owner is a finding
- Defender for Cloud enabled, and who receives its alerts
- Audit logging: what is retained, for how long, and whether it is tamper-evident where compliance requires that
- For AI components: the agent's identity and its permissions. An agent running with a union of all users' permissions is a privilege-escalation path, whatever the prompt says

## Cost optimisation

Cost estimation itself is opt-in (see the main `SKILL.md`) — this pillar is
answered structurally by default, not with a priced figure. Only the
figure-dependent items below (costed environments, quantified savings, named
cost risk) apply when a cost estimate was actually requested.

- Scale-to-zero or auto-pause in non-production
- Right-sized tiers, with the sizing assumption stated
- Storage lifecycle rules matching the retention policy
- Spend caps or budget alerts configured on token-metered AI services (Azure OpenAI, Document Intelligence) — this one is a structural safety control worth having regardless of whether a cost estimate was requested, since it bounds a runaway bill rather than predicting one
- *If cost estimation was requested:* all environments costed, not just production; reserved capacity or savings plan flagged as a client decision with the saving quantified; the single largest cost risk named, with what would trigger it

## Operational excellence

- Everything deployable from code. Nothing created by hand in any environment
- The same artifact promoted through environments, never rebuilt
- One alert rule per failure mode named in the HLD
- Dashboards that answer "is it healthy" without a query being written
- Correlation id propagated end to end, so a single request can be traced across components
- Runbook per failure mode, not per component
- Who operates this after go-live, and whether they have the access the runbooks assume — the delivery team's standard on-call/paging setup applies by default; do not interview for escalation-policy or paging-tool specifics, which are an operational detail settled at build time, not an architecture decision
- Deployment rollback path, and whether it has been exercised

## Performance efficiency

- Each latency and throughput NFR mapped to the bound configuration, with the arithmetic where a target is tight
- Scaling trigger and limits per component. A scale rule with no upper bound is a cost incident; one with no lower bound is a cold-start problem
- Cold start acceptable on scale-to-zero components, or a minimum replica set — and if a minimum replica is set, it is a cost line
- Database sizing against the stated volumes, including index and growth headroom
- Connection pooling, particularly where a scale-to-zero service meets a connection-limited database. This is a common and unpleasant interaction
- The batch critical path against its window, with the headroom stated
- Caching only where a measured target requires it

## Two questions to end on

**What is the most likely thing to go wrong in the first month?** Answer it
concretely, and check that the observability bindings would actually catch it.
This question surfaces more real problems than any single checklist item.

**What in this architecture would we regret in a year?** Write it into the risks
section. It is usually a coupling that was convenient, a store chosen for speed
of delivery, or a limit nobody expected to reach.
