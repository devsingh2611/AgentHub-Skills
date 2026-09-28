# Capability → Azure service selection

The binding tables. Each row is a **default with a named condition for choosing
otherwise**, so a binding is a decision with a reason rather than a preference.

Two standing rules:

- **The default wins unless a stated NFR or client constraint rules it out.** Not "unless something newer looks interesting".
- **Azure service names, tiers and limits change.** Treat this file as the decision structure, not as a datasheet. Verify current tiers and quotas before committing to a SKU, and never quote a price from memory — the Azure Pricing Calculator is the only source for that.

## Compute and hosting

| Capability the HLD declared | Default binding | Choose otherwise when |
|---|---|---|
| Managed container runtime, HTTP | **AKS** — one namespace per application on the existing cluster | — |
| Background or queue-driven worker | **AKS** Deployment in the same namespace, scaled on queue depth (KEDA) | — |
| Scheduled batch or job | **AKS** CronJob in the same namespace | Databricks Workflows already owns the data pipeline schedule |
| Small, purely event-triggered glue | **Azure Functions** (Flex Consumption) | Only where the platform team agrees AKS adds no value — record the reason. If the logic grows past glue it moves back into the namespace |
| Windows or legacy .NET lift-and-shift | **App Service** | — |
| Low-code integration workflow, connector-heavy with minimal custom logic | **Azure Logic Apps (Standard)** | The flow needs real business logic beyond wiring connectors together — build it in the AKS namespace instead. A Logic App that has grown a chain of "compose" and "condition" actions doing actual decisioning is a service that should have been code |
| Container images | **Azure Container Registry**, one per environment tier, with image scanning | — |

AKS is the default because the client platform team already owns and operates
the cluster, so the project provisions a namespace and the Kubernetes objects
inside it — never the cluster, node pools or CNI configuration. See
`../../hld-architect/references/standards-stack.md`. One namespace per
application; every container belonging to that application deploys inside it.

The cost that made AKS exceptional in an earlier version of this file is cluster
*ownership*, and on the house model the platform team carries it. So the two
directions that now need a reason are the opposite ones: standing up a cluster
this project would own, and standing up a second container platform (Container
Apps, App Service) alongside a cluster the platform team already runs. Both
split the operational model, and both need an `AD`.

## Relational and operational stores

| Capability | Default binding | Choose otherwise when |
|---|---|---|
| Managed relational, transactional | **Azure Database for PostgreSQL — Flexible Server** | The client's DBA team standardises on **Azure SQL Database**. That is a legitimate constraint; bind it and record the driver |
| High availability for the store | Zone-redundant HA where the availability NFR requires it | A stated RTO the zone-redundant option cannot meet |
| Point-in-time restore | Automated backups sized to the stated RPO | — |
| Object storage | **Azure Blob Storage** | The lakehouse reads it — then **ADLS Gen2** (hierarchical namespace on) |
| Shared file system | **Azure Files** | Rarely correct. A shared filesystem between services is usually a missing interface |
| Document / flexible schema at scale | **Cosmos DB** | Only against a stated need for global distribution, single-digit-ms latency, or genuinely schemaless documents. Cosmos is easy to bind and expensive to unwind |
| Cache | **Azure Cache for Redis** | Only against a *measured* latency target that is being missed. See the rejected defaults in `standards-stack.md` |

PostgreSQL Flexible Server is the default because the house backend stack is
Python and SQLAlchemy. The Azure SQL alternative is not worse — it is a
different constraint, and which one applies is a client question, not a
technical one.

## Analytical and data platform

Only where the HLD declared a genuine analytical component.

| Capability | Default binding |
|---|---|
| Lakehouse compute | **Azure Databricks** |
| Lake storage | **ADLS Gen2**, bronze/silver/gold containers |
| Governance, access control, lineage | **Unity Catalog** |
| Pipeline orchestration | **Databricks Workflows** |
| Ingestion from operational sources | Databricks jobs, or **Azure Data Factory** where the client already runs it |
| Serving the application | A gold-layer table in the operational store, **not** the lakehouse |
| BI | **Power BI**, reading the serving layer |

`Microsoft Fabric` and `Synapse` are bound only where the client already runs
them. Introducing a second analytical platform alongside Databricks needs an
`AD` and a very good reason.

That serving row matters most. An application querying the lakehouse directly
inherits its latency and concurrency limits, and the coupling is expensive to
undo once dashboards depend on it.

## Messaging and events

| Capability | Default binding |
|---|---|
| Work queue — must be processed, once | **Azure Service Bus** queue, with dead-lettering |
| Ordered processing per key | Service Bus **sessions** |
| Publish/subscribe to internal consumers | Service Bus **topics** |
| High-volume telemetry or a replayable stream | **Event Hubs** |
| Reacting to Azure resource events | **Event Grid** |

The distinction that gets confused: Service Bus for *work that must not be lost*,
Event Hubs for *many events with a retention window and replay*. Binding Event
Hubs to a work queue gives up dead-lettering and per-message handling; binding
Service Bus to high-volume telemetry costs far more than it should.

Every consumer needs a stated dead-letter destination and a named owner who
monitors it. A DLQ nobody watches is a silent data-loss path.

## AI and document processing

| Capability | Default binding | Notes |
|---|---|---|
| LLM inference | **Azure OpenAI** | Deployment version pinned. Provisioned throughput only against a stated latency or throughput commitment — pay-as-you-go otherwise |
| Document extraction with per-field confidence | **Azure AI Document Intelligence** | Prebuilt models first; a custom model is a labelling and retraining commitment, so it needs an `AD` |
| Retrieval / vector search | **Azure AI Search**, hybrid vector plus keyword | Index refresh strategy must be stated, not implied |
| Input and output content filtering | **Azure AI Content Safety** | Where the FRD's guardrail section requires it |
| Agent audit trail | Application-owned store, correlated per interaction | "Reconstructable" is a design requirement, not a logging level. See the FRD's agentic archetype |

Quota is the trap here. Azure OpenAI capacity is regional and quota-limited, and
a model deployment that works in dev can fail to provision in the production
region. Confirm quota in the target region before the binding is final, and
record it as a dependency if it is not yet granted.

## Microsoft 365 and mailbox integration

| Capability | Default binding | Notes |
|---|---|---|
| Send or read mail from a mailbox the application owns (e.g. a shared mailbox pattern) | **Microsoft Graph API**, application permissions via a dedicated app registration, client-credential flow | No IMAP/POP/SMTP — Graph is the house default for any M365 mailbox access. Application permissions, not delegated, so the binding does not depend on a real user's signed-in session |
| Other M365 object access (calendar, files in SharePoint/OneDrive, Teams) | **Microsoft Graph API**, same app registration pattern, scoped to only the permissions the FR actually needs | Least-privilege matters more here than most bindings — an over-scoped Graph app registration is a standing organisational risk, not just this project's |

Graph app registrations are tenant-level objects a platform or M365 admin team
typically has to approve and grant consent for — treat the lead time the same
way as a resource-group request in `standards-delivery.md`, and raise it as a
dependency early rather than at build time.

## Identity, secrets and network

| Capability | Default binding |
|---|---|
| User authentication | **Entra ID**, OIDC, app roles |
| Service-to-service identity | **Managed identity**. No service principals with secrets, no exceptions worth taking |
| Secrets and certificates | **Key Vault**, read via managed identity at runtime |
| Workload network isolation | **Azure Virtual Network**, one per environment, peered to the platform team's hub where a landing zone exists |
| Data-service network exposure | **Private Endpoint** plus Private DNS, inside the workload VNet. Public network access disabled |
| Public web ingress, regional | **Application Gateway** with WAF — only where a genuine external-user requirement exists; the Mode A default is no public ingress at all (`../hld-architect/../azure-architect/references/landing-zone.md`'s house defaults) |
| Public web ingress, global or CDN-backed | **Azure Front Door** with WAF — same condition as above |
| API product for external consumers | **API Management** |

API Management is **not** a default. It is correct when there are external
consumers, quota and subscription management, or several backends behind one
facade. Binding it to a single internal API adds cost and an operational
surface for a gateway that does nothing the ingress did not already do.

## Observability

**Dynatrace is the house default APM/observability platform across every
project** — not Azure Monitor, Log Analytics or Application Insights. This is a
firm-wide standard, not a per-client decision: apply it without asking, on every
engagement, regardless of client.

| Capability | Default binding |
|---|---|
| Traces, logs, metrics, APM | **Dynatrace** — OneAgent where a full-stack agent can be installed on the AKS nodes, OpenTelemetry export otherwise |
| Application telemetry | Dynatrace, fed by OpenTelemetry from every service — the HLD's "managed observability platform" capability binds here, not to Azure Monitor |
| Alerting | Dynatrace problem detection, with a notification integration to whatever the delivery team's paging tool is |
| Dashboards | Dynatrace dashboards |
| Azure platform/infrastructure metrics (resource health, activity log, AKS control-plane metrics) | Azure Monitor platform metrics remain the source for these — Dynatrace does not replace Azure's own resource-health signal — forwarded to Dynatrace where practical |

Historical note: earlier engagements on this suite defaulted to Azure Monitor +
Log Analytics + Application Insights. That is no longer the house default as of
2026-09-08 — if a project's `standards.azure` override or an existing client
platform specifically mandates Log Analytics instead, treat that as the
exception needing an `AD`, not the default.

## Legacy: Azure Monitor / Log Analytics (only where Dynatrace is not the platform)

| Capability | Default binding |
|---|---|
| Traces, logs, metrics | **Azure Monitor** with a **Log Analytics** workspace |
| Application telemetry | **Application Insights**, workspace-based, fed by OpenTelemetry |
| Alerting | Azure Monitor alert rules with action groups |
| Dashboards | Azure Monitor workbooks, or Grafana where the client runs it |

One alert rule per failure mode named in the HLD's failure model, in whichever
platform is bound (Dynatrace by default, Log Analytics only in the legacy case
above). An observability binding with no alert rules is telemetry collection,
not monitoring — and `azure_check.py` will not distinguish them, so this one is
on you.

Log Analytics ingestion and retention was a real and frequently underestimated
cost line under the old default; under Dynatrace the equivalent cost driver is
host-unit/ingest licensing, which this project does not provision or pay for
directly (Dynatrace is a firm-wide platform, not a per-project Azure resource).
If cost estimation is explicitly requested for a legacy Log Analytics binding,
set a retention period per table deliberately and put it in the cost table.

## Governance and structure

| Concern | Default |
|---|---|
| Subscription strategy | One per environment where the client's model allows it; otherwise resource-group isolation with separate deployment identities |
| Resource groups | One per workload per environment |
| Naming | `<workload>-<component>-<env>-<region>-<type>`, consistent across every resource |
| Required tags | `workload`, `environment`, `owner`, `cost-centre`, `data-classification` |
| Policy | Owned and enforced by the platform team in Mode A — not enumerated in this document (`landing-zone.md`'s house defaults). In Mode B, **Azure Policy** for the guardrails this project chooses to impose on itself |
| Posture | **Defender for Cloud** enabled |

Tags are not bookkeeping. `data-classification` is what makes a later question
about PII answerable without re-reading the architecture, and `cost-centre` is
what makes the cost table verifiable against the actual bill.

## Bindings that need an AD every time

Each of these is defensible and each is regularly bound without a reason:

- **A cluster this project provisions and owns** — the default is a namespace on the platform team's existing AKS cluster. Owning a cluster needs a named owner for its lifecycle, upgrades and patching, not just a justification
- **Container Apps, App Service, or any second container platform** — a deviation from the house AKS default. Needs a reason and the platform team's agreement
- **Cosmos DB** — needs a stated global-distribution or latency requirement
- **API Management** — needs external consumers or several backends
- **Azure Cache for Redis** — needs a measured, missed latency target
- **Microsoft Fabric or Synapse alongside Databricks** — needs an existing client investment
- **Multi-region anything** — needs an RTO/RPO single-region cannot meet
- **Provisioned throughput on Azure OpenAI** — needs a committed throughput floor
- **A custom Document Intelligence model** — needs the labelling and retraining commitment accepted by a named owner
