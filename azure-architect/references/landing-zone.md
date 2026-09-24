# Landing zone — the question to ask first

**This is the Tier 1 gap for every engagement.** The answer changes the network
topology, the identity model, several service bindings, who owns DNS, and what
the delivery team is even permitted to create. Getting it wrong means an
architecture that cannot be deployed in the client's tenant.

## What to actually ask

Ask it before binding anything:

> Is there an existing enterprise landing zone we deploy into, or are we
> standing up a subscription of our own?

Then ask exactly one follow-up the first answer never covers:

1. Is there an **approved-services list**, and is this project's stack on it? Does the platform team already provide a shared Container Registry, so this project does not provision its own?

That is the whole interview. Earlier versions of this file asked three more
follow-ups every time (public ingress, DNS/firewall/peering ownership, Azure
Policy specifics) — those are now house defaults for Mode A, below, not
questions. Repeat-client engagements (the common case) already have answers to
all three that do not change project to project; asking anyway trains the
client to expect an interview that produces no new information.

## House defaults for Mode A — do not ask these

Once Mode A is established, apply these without asking. They are deliberately
opinionated so the interview stays short; state each as a default in the
document (Section 3, Section 6) rather than as an open item, and only revisit
one if the client explicitly says otherwise for this engagement:

- **Public ingress: none.** Every application defaults to corporate-network-only
  access — private endpoints and internal ingress only, reachable via VPN or
  ExpressRoute. Do not offer or ask about a public-ingress option; bind the
  network design assuming it does not exist. If a genuine external-user
  requirement surfaces later (the FRD would have said so), that is a new `AD`,
  not a default interview question.
- **DNS, firewall rules and network peering already exist.** Do not model these
  as a fresh, unknown-duration lead-time dependency to request — a repeat
  client's platform team has already provisioned the landing zone's network
  foundation. State it as already in place in Section 3.3, not as an open item
  blocking the design.
- **Azure Policy specifics are the platform team's gate, not this skill's
  concern.** Do not ask what policies apply or try to enumerate them — the
  platform team's own deployment pipeline will refuse anything non-compliant,
  and that is their control to own, not ours to pre-validate. Note in Section
  3.4 that placement and policy compliance are the platform team's
  responsibility and move on.
- **Region and data residency are the platform team's placement decision.** Do
  not ask which region, and do not name one as an assumption requiring
  confirmation — write "region assigned by the platform team at provisioning"
  and bind everything else relative to that, rather than picking a region
  yourself.
- **A third party's own authentication method into a resource this project
  owns (e.g. a SaaS partner writing into our storage account) is that vendor's
  concern, not an open architecture question.** Bind assuming the vendor
  supports a standard method — a SAS token or an Azure AD app registration —
  and note the binding as vendor-managed. Do not raise "how does the vendor
  authenticate" as a gap blocking sign-off; that is between the vendor's
  integration team and whoever administers the storage account at build time.

None of this applies to Mode B, where these are still genuinely this project's
decisions — see below.

The one item that surfaces late and hurts, in *either* mode, is a policy that
denies public IPs, requires private endpoints on every data service, or
restricts regions — which is exactly why Mode A's default above is "private,
corporate-network-only, no region chosen by us" rather than something optimistic
that a policy might later reject.

## Mode A — enterprise landing zone

The common case in a large organisation, and the one to assume for a McKesson-
scale tenant until told otherwise.

**What is already decided, and not ours to choose:**

- Hub-and-spoke topology. We get a spoke; the hub is someone else's
- Egress through a central firewall or NVA. Direct internet egress is usually denied
- Private DNS zones managed centrally, with resolution via the hub
- Management group policy inheritance — regions, allowed SKUs and required tags may all be constrained
- Log Analytics may be centralised, so telemetry lands in a workspace we do not own
- Deployment identity is federated and scoped, often to a single resource group

**What this changes in the bindings — the house defaults above, restated as a table:**

| Concern | In a landing zone |
|---|---|
| Data services | Private endpoint only. `publicNetworkAccess` disabled by default |
| Public ingress | None — corporate-network-only by default (see "House defaults for Mode A"), not a central Front Door or our own Application Gateway |
| DNS, peering | Assumed already provisioned by the platform team as part of the landing zone — not a fresh request this engagement models with a lead time |
| Subscription split | Usually already fixed by the client's model. Do not propose one |
| Policy compliance | The platform team's own gate (see "House defaults for Mode A") — not enumerated here |

**What to write in the document:** the spoke's address space and the subnets and
their delegations, the private endpoints and which zone resolves each. Do not
enumerate platform-team lead times or policy constraints by default — those are
the platform team's concern per the house defaults above, unless the user
states this specific engagement is genuinely a first-time setup rather than a
repeat client's existing landing zone.

**When the lead-time risk is real:** if this is a *new* platform relationship
(no existing spoke, no prior project on this tenant), the house defaults above
do not apply yet — treat DNS, peering and policy as genuinely open in that case,
the way earlier versions of this file always did, and name the platform-team
lead time explicitly as a project-plan risk.

## Mode B — standalone subscription

Greenfield, a proof of concept, or a client without a central platform function.

**Compute hosting is an open decision in this mode.** The house AKS default
assumes a platform team owns and operates the cluster. In Mode B there is none,
so both directions need an `AD`: a cluster we provision means we own its
lifecycle, upgrades and patching, and a serverless container platform is a
deviation from the standard. Neither is wrong — but write the decision rather
than inheriting a default that assumed someone else was there.

**What we own, and therefore must specify:**

- Virtual network and subnet design, with delegations for any managed service that needs one
- Private DNS zones and their vnet links
- Egress: NAT Gateway for stable outbound addressing where a partner allowlists us
- Public ingress: Front Door or Application Gateway with WAF, ours to configure
- Log Analytics workspace, and its retention per table
- Policy assignments we choose to impose on ourselves
- The subscription and resource-group structure

**The trap:** it is quick to build something that works and slow to retrofit
network isolation. Bind private endpoints and disable public access on data
services from the first day, even in dev. Retrofitting them after the
application depends on public connection strings is a rework item nobody
budgeted.

## Either mode — always specify

- Which **regions**, primary and any secondary. In Mode A this is the platform
  team's placement decision (see house defaults) — state "assigned by the
  platform team," do not pick one. In Mode B this project chooses, and data
  residency is a compliance answer, not a latency preference
- The **deployment identity** per environment, and its scope. Federated credentials from the pipeline, never a long-lived secret
- Who can reach **production**, through what path, and with what approval
- Whether **lower environments** are network-isolated from production, and from each other
- The **break-glass** path: who can act when the normal identity route fails, and how that access is audited

## What gets forgotten

**Subnet sizing.** AKS node and pod address space, and several managed services, require a
delegated subnet with a minimum size, and a vnet sized without headroom cannot
be extended cleanly once peered. Size for the components you expect, plus room.

**Private DNS resolution from on-premises.** An internal user resolving a private
endpoint from the corporate network needs a conditional forwarder or a resolver
in the hub. This works in the cloud and fails from a desk, which is the worst
way to discover it.

**Quota.** Regional quota for vCPUs, Azure OpenAI capacity and public IPs is
per-subscription and often lower than expected in a fresh one. Check before the
binding is final, and record any ungranted quota as a dependency.

**Non-production cost.** Only relevant if cost estimation was requested (it is
opt-in by default — see the main `SKILL.md`). When it is: three environments
cost roughly three times one, and the estimate is usually built for production
alone. See `cost-model.md`.

**Who operates this after go-live.** It changes the observability requirement,
the alert routing and the runbook depth substantially — and it is a question the
architecture document is expected to have answered.
