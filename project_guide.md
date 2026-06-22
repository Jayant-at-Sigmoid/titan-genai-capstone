# Enterprise GRC Compliance Portal: Full Technical Project Guide

This guide provides a comprehensive breakdown of the AI-powered Governance, Risk, and Compliance (GRC) Compliance Portal. It explains every design choice, structural component, workflow node, database compatibility abstraction, and runtime optimization.

---

## 📂 Project Directory Structure

```text
├── app.py                      # Main Streamlit Entrypoint & UI Layout
├── requirements.txt            # Python Packages Dependencies
├── Dockerfile                  # Container Deployment Definition
├── README.md                   # Project Overview & Setup Instructions
│
├── agents/                     # Specialist Compliance LLM Agents
│   ├── abuse_agent.py          # Safety, Threat & Harassment Specialist
│   ├── confidential_agent.py   # Intellectual Property & Finance Specialist
│   ├── pii_agent.py            # Personal Data Validator (Regex + LLM)
│   ├── encoding_agent.py       # Programmatic Text & Mojibake Check
│   ├── reviewer_agent.py       # Consensus, False-Positive Filter & Merge Node
│   └── risk_agent.py           # Multi-Weight Scoring & Risk Evaluator
│
├── graph/                      # LangGraph Workflow Orchestration
│   ├── state.py                # Typed State Definition
│   ├── nodes.py                # Graph Work Nodes (Extraction, Agent runs, RAG)
│   └── workflow.py             # Graph Compilation (LangGraph StateGraph)
│
├── services/                   # Core Infrastructure Layer
│   ├── llm_service.py          # AWS Bedrock Client (Nova), Latency & Cost Tracker
│   ├── email_service.py        # SMTP Email Alerts (Gmail / Mock Fallback)
│   ├── sync_service.py         # Background S3 Sync Daemon
│   ├── rule_service.py         # Keyword & Regex Rules Database Interface
│   └── vector_service.py       # FAISS Search Interface
│
├── database/                   # Data Persistence Layer
│   ├── db.py                   # SQLite to PostgreSQL Compatible Translation Layer
│   └── models.py               # Database ORM Schema definition references
│
├── utils/                      # Helper Utilities
│   ├── pdf_parser.py           # PyMuPDF Extractor & Non-PDF Text-Chunking Fallback
│   ├── report_generator.py     # ReportLab PDF Compliance Report Engine
│   ├── redaction.py            # PyMuPDF Coordinate Redactor
│   ├── validators.py           # PDF Upload Structure & Prompt Injection Scanner
│   └── logger.py               # Unified Log File Configuration
│
├── analytics/                  # Reporting Analytics
│   └── dashboard.py            # Plotly Visualization Dashboard (KPI, Timeline)
│
└── rules/                      # System Configurations
    └── rules.json              # Bootstrapped Regex & Keyword Violations List
```

---

## ⚙️ Core Architecture & System Features

### 1. Ingestion & Document Processing Pipeline
* **Code Location**: [pdf_parser.py](file:///Users/as-mac-1214/Desktop/genai-project/utils/pdf_parser.py)
* **Mechanics**:
  * For PDFs: Loads document using `fitz` (PyMuPDF), checks if it is encrypted, checks for zero-page errors, and extracts text page-by-page.
  * For plain text/code (e.g. `.py`, `.csv`, `.json`, `.yaml`): Opens the file with UTF-8 encoding (handling errors using `"replace"`), splits it into **3,000-character chunks**, and outputs them as simulated "pages" so they flow through the same pipeline.

### 2. Security Validation Layer
* **Code Location**: [validators.py](file:///Users/as-mac-1214/Desktop/genai-project/utils/validators.py)
* **Mechanics**:
  * Validates file size (limit 10MB) and checks if the file extension is allowed.
  * Scans extracted text for prompt injection keywords (e.g., `ignore previous instructions`, `system override`, `you are now an assistant`). If flagged, halts the execution immediately.

### 3. LangGraph Orchestration Flow
* **Code Location**: [workflow.py](file:///Users/as-mac-1214/Desktop/genai-project/graph/workflow.py) and [nodes.py](file:///Users/as-mac-1214/Desktop/genai-project/graph/nodes.py)
* **Mechanics**:
  * Orchestrated using `StateGraph(ComplianceState)`.
  * Passes through `extract_pdf_node` to extract text.
  * Parallelizes execution of four checking nodes: `pii_agent_node`, `confidential_agent_node`, `abuse_agent_node`, and `encoding_agent_node`.
  * Aggregates outputs and feeds them into the `reviewer_consensus_node`.
  * Validates approved violations against corporate rules in the `rag_policy_validation_node`.
  * Computes overall statistics in the `risk_scoring_node`.
  * Builds reports and redacts files in the `report_generator_node`.

```mermaid
graph TD
    Start([File Path]) --> Extract[extract_pdf_node]
    Extract --> PII[pii_agent_node]
    Extract --> Conf[confidential_agent_node]
    Extract --> Abuse[abuse_agent_node]
    Extract --> Enc[encoding_agent_node]
    
    PII --> Review[reviewer_consensus_node]
    Conf --> Review
    Abuse --> Review
    Enc --> Review
    
    Review --> RAG[rag_policy_validation_node]
    RAG --> Risk[risk_scoring_node]
    Risk --> Report[report_generator_node]
    Report --> End([Completed State])
```

### 4. Specialist Agent Logic
* **PII Agent** ([pii_agent.py](file:///Users/as-mac-1214/Desktop/genai-project/agents/pii_agent.py)): Runs pre-check regexes (e.g., matching emails, phones, card boundaries). If no matches are found, **bypasses LLM** to save tokens. If patterns match, invokes LLM with PII instructions.
* **Confidential Agent** ([confidential_agent.py](file:///Users/as-mac-1214/Desktop/genai-project/agents/confidential_agent.py)): Identifies proprietary code, financial forecasts, trade secrets, and pricing lists using a zero-temperature fast model.
* **Abuse Agent** ([abuse_agent.py](file:///Users/as-mac-1214/Desktop/genai-project/agents/abuse_agent.py)): Detects threats, hate speech, blackmail, and harassment.
* **Reviewer Agent** ([reviewer_agent.py](file:///Users/as-mac-1214/Desktop/genai-project/agents/reviewer_agent.py)): Standardizes alerts, resolves overlaps, and assigns severity classes (LOW, MEDIUM, HIGH, CRITICAL).
* **Risk Agent** ([risk_agent.py](file:///Users/as-mac-1214/Desktop/genai-project/agents/risk_agent.py)): Calculates overall compliance score. Starts at `100.0` and deducts:
  * `-25` points for CRITICAL violations.
  * `-15` points for HIGH violations.
  * `-10` points for MEDIUM violations.
  * `-5` points for LOW violations.
  * Sets the overall risk classification based on the lowest score threshold.

### 5. PostgreSQL & SQLite Compatibility Layer
* **Code Location**: [db.py](file:///Users/as-mac-1214/Desktop/genai-project/database/db.py)
* **Mechanics**:
  * Resolves `DATABASE_URL`. If it contains `postgresql` or `postgres`, wraps the connection using the custom `PostgreSQLConnection` and `PostgreSQLCursor` classes. Otherwise, instantiates `sqlite3`.
  * Intercepts SQL strings on-the-fly:
    * Replaces `?` parameter placeholders with `%s` (Postgres syntax).
    * Replaces `INTEGER PRIMARY KEY AUTOINCREMENT` with `SERIAL PRIMARY KEY`.
    * Converts `INSERT OR IGNORE` and `INSERT OR REPLACE` to standard SQL `ON CONFLICT DO NOTHING` and `ON CONFLICT DO UPDATE`.
    * Transparently appends `RETURNING id` to inserts, captures the returned ID, and exposes it via `cursor.lastrowid` so the ORM queries don't need changes.
    * Replicates `sqlite3.Row` functionality via `PostgreSQLRow` which allows indexing by both integers (tuple behavior) and strings (dict behavior).

### 6. SMTP Email Alerting
* **Code Location**: [email_service.py](file:///Users/as-mac-1214/Desktop/genai-project/services/email_service.py)
* **Mechanics**:
  * Initiates secure SMTP transport over TLS (using port 587 and starttls).
  * Sends HTML or text alerts to target recipients.
  * Falls back to **Simulated Mode** if `SMTP_USER` or `SMTP_PASS` is not provided, writing simulated alerts to logs to avoid blocking.

### 7. ReportLab PDF Generation
* **Code Location**: [report_generator.py](file:///Users/as-mac-1214/Desktop/genai-project/utils/report_generator.py)
* **Mechanics**:
  * Generates an audit ledger report with custom canvas hooks to draw running headers, running footers, and page numbers.
  * Utilizes `ParagraphStyle` templates (e.g. `MetricTitleCustom`, `MetricValCustom`) with explicit `leading` constraints to prevent text overlap.

---

## 💻 Detailed Code Walkthrough

### 1. Streamlit Entrypoint (`app.py`)
Defines the multi-tab layout and sets the dashboard style system:
* **Sidebar Setup**: Uses custom CSS to style the sidebar with a deep dark blue background (`#0A192F` or `#0F172A`), adds white-bordered active tab selectors, and keeps the collapse icon always visible.
* **Observe Page**: Displays the live **GRC Infrastructure Health Diagnostics Console**, showing database URL configurations, AWS runtime status, and thread pools.
* **Sandbox Tab**: Renders the **Interactive Regex Sandbox** where users can input text and see which regex pre-check rules match instantly.

### 2. AWS Bedrock Invoker (`llm_service.py`)
Tracks tokens, cost rates, and response latency:
* **Pricing Rates (per 1k tokens)**:
  * Nova Micro: Input: `$0.000035`, Output: `$0.00014`
  * Nova Lite: Input: `$0.00006`, Output: `$0.00024`
* **Log Metrics**: Translates token statistics and writes them directly to the `model_metrics` database table on every execution.

### 3. Background Sync Loop (`sync_service.py`)
Pulls documents from S3 buckets:
* **Startup delay**: Includes a 5-second sleep at the start of the thread `_run_loop()` to guarantee that the main Streamlit thread completes table creation in `init_db()` before queries start.
* **Download and Scan**: Checks S3 metadata, compares SHA-256 hashes to prevent duplicate scans, downloads new files, runs the compliance graph, and logs audits.

---

## ⚡ Deployment & Settings Guide

### 1. Local Configuration (`.env`)
Make sure `.env` contains:
```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
SIMULATION_MODE=False
DATABASE_URL=compliance.db # Local SQLite
```

### 2. Streamlit Cloud Secrets (`secrets.toml`)
Ensure the production PostgreSQL pooler URL is configured to avoid networking issues:
```toml
# Use the Pooler URI (port 6543) instead of direct connection (port 5432) to support IPv4
DATABASE_URL = "postgresql://postgres.[REF_ID]:[PASS]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
```
