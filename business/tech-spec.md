## tech-spec.md – Payment‑Cortex v1

### 1. Stack
| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Language** | **Go (1.22)** | Compiled, low‑latency, excellent concurrency primitives, native TLS support, easy static binary deployment. |
| **Web Framework** | **Echo v4** | Minimal overhead, middleware ecosystem (rate‑limit, JWT, request ID), good OpenAPI generation. |
| **Runtime** | **Docker 24.x** (scratch base) | Guarantees reproducible builds, isolates dependencies, works on any cloud provider. |
| **Message Bus** | **NATS JetStream** | High‑throughput pub/sub with at‑least‑once delivery, built‑in persistence, ideal for transaction events. |
| **Database** | **CockroachDB v23.2** (SQL, distributed, strong consistency) | Horizontal scalability, ACID guarantees across regions – essential for cross‑border settlement. |
| **Cache / Rate‑limit store** | **Redis 7 (free tier on Upstash)** | Fast in‑memory store for idempotency keys, token buckets, and session data. |
| **Crypto / Signing** | **libsodium (via Go bindings)** | Modern, vetted primitives for HMAC, Ed25519 signatures on payment messages. |
| **OpenAPI / Docs** | **Swaggo** (auto‑generate from Go annotations) | Guarantees API spec stays in sync with code. |
| **Testing** | **Testify + GoMock** | Unit & contract testing with mockable interfaces. |
| **CI/CD** | **GitHub Actions** (self‑hosted runner optional) | Free tier covers most builds; can push to Docker Hub / GHCR. |

---

### 2. Hosting (Free‑Tier‑First)

| Component | Provider (Free Tier) | Deployment Model |
|-----------|----------------------|------------------|
| **Container Registry** | GitHub Container Registry (public) | Store `payment-cortex` image. |
| **Compute** | **Fly.io** (free 3‑CPU‑hour/month, 256 MiB RAM) – can run 1‑node dev cluster. | Docker container, auto‑TLS, global edge. |
| **Database** | **CockroachDB Serverless** (free 5 GB storage, 1 vCPU) | Managed, multi‑region (US‑East, EU‑West). |
| **Message Bus** | **NATS Cloud (Free tier – 1 GiB storage, 100 k msgs/s)** | Hosted JetStream cluster. |
| **Cache** | **Upstash Redis** (free 10 MB) | Serverless, TLS‑enabled. |
| **Observability** | **Grafana Cloud Free** (metrics + logs) + **OpenTelemetry Collector** (Docker sidecar) | Scrape Prometheus metrics, forward logs. |
| **Secrets Management** | **GitHub Environments + Actions Secrets** (encrypted at rest) | Injected at runtime via Docker env vars. |

*When scaling beyond free limits, migrate to same‑provider equivalents (Fly.io paid plan, CockroachDB Dedicated, NATS on Render/Equinix Metal, Upstash paid tier).*

---

### 3. Data Model

| Table / Collection | Primary Key | Key Fields | Description |
|--------------------|-------------|------------|-------------|
| **accounts** | `account_id` (UUID) | `customer_id`, `currency`, `balance_cents`, `status`, `created_at`, `updated_at` | Holds ledger accounts for each participant (banks, exchanges, corp). |
| **transactions** | `tx_id` (UUID) | `from_account_id`, `to_account_id`, `amount_cents`, `currency`, `status` (`pending`, `settled`, `failed`), `created_at`, `settled_at`, `signature` (Ed25519), `metadata` (JSONB) | Immutable audit trail of every payment. |
| **settlements** | `settlement_id` (UUID) | `tx_batch_id`, `total_amount_cents`, `currency`, `status`, `initiated_at`, `completed_at` | Grouped cross‑border settlements for batch processing. |
| **exchange_rates** | `pair` (e.g., `USD/EUR`) | `rate` (float64), `source` (e.g., `FXProviderX`), `valid_until` (timestamp) | Cached FX rates; refreshed every 5 min via external provider. |
| **idempotency_keys** | `key` (string) | `tx_id`, `expires_at` | Guarantees exactly‑once semantics for POST /transactions. |
| **audit_logs** | `log_id` (UUID) | `entity_type`, `entity_id`, `action`, `actor`, `timestamp`, `details` (JSONB) | Write‑only table for compliance (PCI‑DSS, GDPR). |

*All tables are CockroachDB `CREATE TABLE ... PRIMARY KEY (id)` with `INTERLEAVE IN PARENT` where appropriate for locality (e.g., `transactions` interleaved in `accounts`).*

---

### 4. API Surface (OpenAPI 3.1)

| # | Method | Path | Purpose | Request Body (JSON) | Response (JSON) |
|---|--------|------|---------|---------------------|-----------------|
| 1 | **POST** | `/v1/accounts` | Create a new ledger account | `{ "customer_id": "string", "currency": "ISO4217", "initial_balance_cents": int }` | `201 Created` → `{ "account_id": "uuid", "balance_cents": int, "status": "active" }` |
| 2 | **GET** | `/v1/accounts/{account_id}` | Retrieve account details | – | `200 OK` → full account record (excluding internal fields) |
| 3 | **POST** | `/v1/transactions` | Initiate a cross‑border payment (idempotent) | `{ "from_account_id": "uuid", "to_account_id": "uuid", "amount_cents": int, "currency": "ISO4217", "metadata": {...}, "idempotency_key": "string" }` | `202 Accepted` → `{ "tx_id": "uuid", "status": "pending" }` |
| 4 | **GET** | `/v1/transactions/{tx_id}` | Query transaction status & details | – | `200 OK` → transaction record |
| 5 | **POST** | `/v1/settlements/batch` | Trigger batch settlement for pending transactions (admin only) | `{ "tx_ids": ["uuid", …] }` | `202 Accepted` → `{ "settlement_id": "uuid", "status": "in_progress" }` |
| 6 | **GET** | `/v1/settlements/{settlement_id}` | Get settlement progress | – | `200 OK` → settlement record |
| 7 | **GET** | `/v1/rates/{pair}` | Fetch latest FX rate (cached) | – | `200 OK` → `{ "pair": "USD/EUR", "rate": 0.9123, "valid_until": "ISO8601" }` |
| 8 | **POST** | `/v1/webhooks/payment-status` | Receive asynchronous status updates from external clearing houses (signed) | `{ "tx_id": "uuid", "status": "settled|failed", "signature": "base64" }` | `200 OK` |
| 9 | **GET** | `/healthz` | Liveness / readiness probe | – | `200 OK` |
|10| **GET** | `/metrics` | Prometheus metrics endpoint | – | text/plain |

*All request/response schemas are defined in `docs/openapi.yaml` generated via Swaggo annotations.*

---

### 5. Security Model

| Aspect | Implementation |
|--------|----------------|
| **Authentication** | **OAuth 2.0 Client Credentials** (internal services) + **Mutual TLS** for external partners. JWT signed with RSA‑2048, `aud` = `payment-cortex`. |
| **Authorization (IAM)** | Role‑Based Access Control (RBAC) stored in `iam_roles` table: `admin`, `operator`, `partner_read`, `partner_write`. Middleware checks `scope` claim in JWT against required role per endpoint. |
| **Transport Security** | Enforced TLS 1.3 everywhere (Fly.io edge TLS + internal mTLS). HTTP Strict Transport Security (HSTS) header set. |
| **Secrets Management** | All keys (JWT signing RSA private key, Ed25519 signing key, DB passwords, NATS credentials) stored in GitHub Environments → injected as env vars. Rotation pipeline via GitHub Actions scheduled weekly. |
| **Data‑at‑Rest Encryption** | CockroachDB encrypts data automatically with AES‑256. Redis uses TLS. |
| **Message Signing** | Every outgoing payment message is signed with Ed25519 private key; inbound webhook payloads validated against shared public key. |
| **Idempotency** | `idempotency_key` table ensures exactly‑once POST /transactions. |
| **Compliance** | PCI‑DSS v4.0 scope: card‑holder data never stored; only tokenized transaction IDs. Audit logs are immutable and write‑only. |
| **Rate Limiting** | Global per‑IP limit 100 req/s via Echo middleware; per‑partner quota configurable in Redis token bucket. |
| **Vulnerability Scanning** | Trivy scan on Docker image in CI; Dependabot alerts enabled. |

---

### 6. Observability

| Signal | Tool / Exporter | Details |
|--------|----------------|---------|
| **Logs** | **Fluent Bit** sidecar → **Grafana Loki** (free tier) | Structured JSON logs (`time`, `level`, `request_id`, `service`, `msg`). |
| **Metrics** | **Prometheus** client library (built‑in Echo) → **Grafana Cloud** | Key metrics: `http_requests_total`, `http_request_duration_seconds`, `tx_created_total`, `tx_settled_total`, `db_query_latency_seconds`, `nats_msg_in/out`. |
| **Traces** | **OpenTelemetry Collector** (Docker sidecar) → **Grafana Tempo** (free) | End‑to‑end trace across API → DB → NATS → settlement worker. |
| **Health** | `/healthz` + `/readyz` endpoints scraped by Fly.io health checks. |
| **Alerting** | Grafana alerts → Slack webhook (free tier) for: > 5% transaction failures, DB latency > 200 ms, NATS backlog > 10 k msgs. |
| **Dashboards** | Pre‑built Grafana dashboards for: transaction volume, latency heatmap, error rates, FX rate freshness. |

---

### 7. Build / CI

| Stage | Tool | Steps |
|-------|------|-------|
| **Lint / Static Analysis** | `golangci-lint` (GitHub Action) | Run on PRs; fail on any warning. |
| **Unit Tests** | `go test ./... -cover` | Must achieve ≥ 80 % coverage. |
| **Integration Tests** | Docker Compose (cockroachdb, nats, redis) + `go test -tags=integration` | Runs against real services in CI. |
| **Security Scan** | `trivy image` on built Docker image | Fail on CVEs > MEDIUM. |
| **Build Image** | `docker buildx` multi‑arch (linux/amd64, linux/arm64) | Tag: `ghcr.io/arkashira/payment-cortex:${{ github.sha }}` |
| **Push** | `docker push` to GHCR | Only on `main` merge. |
| **Deploy** | Fly.io `flyctl deploy` (via GitHub Action) | Deploys to `payment-cortex-prod` app; uses secrets from GitHub Envs. |
| **Version Bump** | `semantic-release` (commit‑message driven) | Auto‑generates changelog, tags `vX.Y.Z`. |
| **Rollback** | Fly.io `flyctl releases rollback` | Triggered via manual GitHub workflow dispatch. |

*All pipelines are defined in `.github/workflows/ci.yml`. The workflow is free‑tier friendly: total runtime < 20 min per commit, using GitHub’s shared runners.*