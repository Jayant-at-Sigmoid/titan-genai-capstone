# Enterprise AI-Powered GRC Compliance & Governance Platform

This platform is a production-grade Governance, Risk, and Compliance (GRC) solution designed to audit enterprise documents. It extracts, flags, reviews, and redacts sensitive data (PII, Confidential Information, Abusive/Unlawful Content, and Encoding Inconsistencies) from both PDFs and plain-text/code formats.

Leveraging **LangGraph** multi-agent orchestration, **AWS Bedrock** models (Amazon Nova), **PostgreSQL / SQLite** persistence, **FAISS** vector store, and **ReportLab** PDF generation, this application represents a complete, secure enterprise governance pipeline.

---

## 🏗️ System Architecture

The platform operates on a modular, multi-tier pattern separating user interface, agent workflows, backend database, and vector systems:

```
                          ┌────────────────────────┐
                          │      Streamlit UI      │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │   LangGraph Workflow   │
                          └───────────┬────────────┘
                                      │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
  ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
  │   Agent Nodes     │      │   Services Layer  │      │  Database/Storage │
  ├───────────────────┤      ├───────────────────┤      ├───────────────────┤
  │ • PII Agent       │      │ • Bedrock LLM     │      │ • PostgreSQL /    │
  │ • Confidential Agt│      │ • Embedding Serv  │      │   SQLite DB       │
  │ • Abuse Agent     │      │ • Rule Service    │      │ • FAISS Vector DB │
  │ • Encoding Agent  │      └───────────────────┘      └───────────────────┘
  │ • Reviewer Agent  │
  │ • Risk Agent      │
  └───────────────────┘
```

---

## 🔥 Key Enterprise Features

### 1. Multi-Format File Auditing
Supports auditing file types other than PDFs, including:
* **Code/Text files**: `.txt`, `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.cs`, `.go`, `.sh`, `.json`, `.csv`, `.md`, `.html`, `.css`, `.yaml`, `.yml`.
* **Fallback Chunking Parser**: Non-PDF files are read using UTF-8 (with error replacement) and parsed into 3,000-character chunks that simulate "pages" so they can flow seamlessly through the parallel agent pipeline.

### 2. Multi-Agent Orchestration & Consensus (LangGraph)
Uses the **Mixture-of-Experts** agent pattern:
* **Specialist Analysis**: Parallel agents scan pages for specific violation domains (PII, Confidentiality, Abuse).
* **Consensus Filtering**: A **Reviewer Agent** runs consensus checks to filter false positives, resolve duplicate alerts, and normalize severity ratings.
* **Vector-based RAG Validation**: Integrates FAISS to match findings against your indexed Corporate Policy guidelines and uses the LLM to justify the violation.

### 3. Dynamic Database Compatibility (PostgreSQL & SQLite)
Features a database translation layer in `database/db.py`:
* **Local Development**: Uses local `compliance.db` (SQLite).
* **Production Deployment**: Automatically detects if `DATABASE_URL` is set to PostgreSQL (e.g. Supabase, Neon) and handles syntax conversions on the fly:
  * Translates placeholders (`?` to `%s`).
  * Converts custom SQLite keywords (`INSERT OR IGNORE`/`INSERT OR REPLACE` to `ON CONFLICT DO NOTHING/UPDATE`).
  * Automatically appends `RETURNING id` during inserts to dynamically support `lastrowid` fetches.
  * Replicates `sqlite3.Row` dictionary-and-tuple indexing behavior.

### 4. System Observability & Diagnostics Console
* **Diagnostics Control Panel**: Real-time health diagnostic tools directly inside the UI displaying system configurations, database connection status, and background ingestion health.
* **Interactive Regex Sandbox**: A playground to inspect how pre-check regex rules process custom text before calling the LLM.
* **API Performance & Latency Analytics**: Detailed Plotly graphs charting latency timelines and pricing counts per model to analyze token usages and costs.

### 5. Automated SMTP Email Alerts
* **Failure Alerts**: Dispatches detailed email logs if the parsing or scanning pipeline encounters exceptions.
* **Violation Alerts**: Instantly emails the security/governance team if a scan detects an overall `CRITICAL` risk or severe policy violation.
* **Fallback Simulation**: Logs simulated emails locally if SMTP credentials are left blank.

---

## 🧠 Model Selection & Cost Optimization
The platform leverages **Amazon Bedrock**:
* **Amazon Nova Micro** (`amazon.nova-micro-v1:0`): Default fast model for rapid classification tasks ($0.000035/1k input tokens).
* **Amazon Nova Lite** (`amazon.nova-lite-v1:0`): Default text model for complex reasoning, consensus, and RAG matching ($0.00006/1k input tokens).
* **Titan Embeddings** (`amazon.titan-embed-text-v2:0`): Vectorizes corporate guidelines.

### Cost Control Engine
To minimize token consumption, the **PII Agent** runs a regex pre-check on the text first. If no matching candidate patterns (like card structures or email syntax) are found, it skips the LLM call entirely, saving up to 80% on scanning costs.

---

## 🚀 Setup & Execution

### 1. Configure the Environment
Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
```

To run in **Simulated Fallback Mode** (without connecting to AWS Bedrock), set `SIMULATION_MODE=True` in your `.env` file.

### 2. Local Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run Unit Tests
python3 -m unittest discover -s tests

# Launch Streamlit Application
streamlit run app.py
```

### 3. Docker Deployment
```bash
# Build Docker Image
docker build -t grc-compliance-portal .

# Run Container
docker run -p 8501:8501 --env-file .env grc-compliance-portal
```

---

## ☁️ Deployment to Streamlit Community Cloud

### Step 1: Commit and Push to GitHub
Ensure you add a `.gitignore` to prevent uploading your database and local secrets:
```text
.env
*.db
__pycache__/
.streamlit/config.toml
```

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and select your repository, branch (`main`), and file (`app.py`).
2. Click **Advanced Settings** -> **Secrets**.
3. Paste your configurations in **TOML** format:

```toml
# AWS Bedrock Authentication
AWS_ACCESS_KEY_ID = "AKIA..."
AWS_SECRET_ACCESS_KEY = "oreJT..."
AWS_REGION = "us-east-1"

# Bedrock Model Identifiers
BEDROCK_TEXT_MODEL = "amazon.nova-lite-v1:0"
BEDROCK_FAST_MODEL = "amazon.nova-micro-v1:0"
BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"

# Application Settings
SIMULATION_MODE = "False"

# Database (PostgreSQL Connection Pooler string - Port 6543)
DATABASE_URL = "postgresql://postgres.[REF_ID]:[PASS]@aws-0-[REG].pooler.supabase.com:6543/postgres?sslmode=require"

# Email Alert Configuration (SMTP)
GRC_ALERT_EMAIL = "your-alerts@email.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "sender@gmail.com"
SMTP_PASS = "xxxx xxxx xxxx xxxx" # App Password
```

4. Click **Deploy**.
