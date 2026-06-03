# Enterprise AI-Powered PDF Compliance & Governance Platform

This platform is a production-grade GRC (Governance, Risk, and Compliance) solution designed to audit enterprise documents. It extracts, flags, reviews, and redacts sensitive data (PII, Confidential Information, Abusive/Unlawful Content, and Encoding Inconsistencies) from PDFs.

Leveraging **LangGraph** multi-agent orchestration, **AWS Bedrock** models, **SQLite** persistence, **FAISS** vector store, and **ReportLab** PDF generation, this app represents a complete enterprise governance pipeline.

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
 │ • PII Agent       │      │ • Bedrock LLM     │      │ • SQLite DB       │
 │ • Confidential Agt│      │ • Embedding Serv  │      │ • FAISS Vector DB │
 │ • Abuse Agent     │      │ • Rule Service    │      └───────────────────┘
 │ • Encoding Agent  │      └───────────────────┘
 │ • Reviewer Agent  │
 │ • Risk Agent      │
 └───────────────────┘
```

---

## 🧠 LangGraph Workflow Orchestration

The PDF analysis uses a structured parallel state graph implemented using **LangGraph**:

1. **PDF Extractor Node**: Extracts PDF texts page-by-page using PyMuPDF and validates text health.
2. **Parallel Agent Execution**:
   - **PII Detection Agent**: Checks for emails, cards, addresses, Aadhaar, and PAN. Runs regex pre-checks to bypass LLM on clean pages.
   - **Confidential Agent**: Scans for financial projections, trade secrets, and source code.
   - **Abuse Agent**: Checks for harassment, threats, or slurs.
   - **Encoding Agent**: Programmatically detects Mojibake or decoding errors.
3. **Reviewer / Consensus Node**: Filters false positives, resolves duplicate alerts, and establishes severity consensus.
4. **RAG Policy Validation Node**: Performs semantic checks against corporate policies stored in FAISS, linking violations to matching policies.
5. **Risk Scoring Node**: Aggregates violation weights and outputs a compliance score (0-100) and risk level.
6. **Report Generator Node**: Renders a PDF audit ledger and outputs a redacted version of the original document.

---

## 🔒 AWS Bedrock Integration & IAM Permissions

The platform uses:
- **Claude Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`): Used for fast-pass entity extractions (PII, Abuse classification).
- **Claude Sonnet** (`anthropic.claude-3-5-sonnet-20241022-v2:0`): Used for consensus reviews, policy checks, and executive risk summaries.
- **Titan Embeddings** (`amazon.titan-embed-text-v2:0`): Used to vectorize and query corporate directives.

### Required IAM Policy

Ensure that the IAM principal executing this platform has the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🚀 Setup & Execution

### 1. Configure the Environment
Copy `.env.example` to `.env` and fill in your AWS details:

```bash
cp .env.example .env
```

If you do not have AWS Bedrock keys set up, you can run the app in **Simulated Fallback Mode** by leaving `SIMULATION_MODE=True`. The application will simulate Bedrock responses and Titan embeddings deterministically, allowing local validation of all interfaces.

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
docker build -t pdf-compliance-platform .

# Run Container
docker run -p 8501:8501 --env-file .env pdf-compliance-platform
```

---

## 📊 Demo Steps

1. **Policy Upload (RAG)**:
   - Navigate to `⚖️ Corporate Policy Manager`.
   - Upload any policy guidance PDF (e.g. SEC financial policies or PII policies).
   - Click `Ingest and Index Guidelines` to register it into the FAISS index.
2. **Configure Rules**:
   - Go to `⚙️ Compliance Rules Configurator`.
   - Add a custom keyword/regex pattern (e.g. custom product code or proprietary term) and assign a severity.
3. **Execute Scan**:
   - Navigate to `📤 Upload & Scan PDF`.
   - Upload your test document and run `Execute Compliance Scan`.
   - Observe the agent logs and dynamic dashboard update.
4. **Approve Violations**:
   - Visit `👥 Human Review Interface`.
   - Approve, Reject or add notes to the pending violations to test the feedback loop.
5. **Download Artifacts**:
   - Go to `Document Scanning History` on the scanning page.
   - Download the generated ReportLab compliance report and the redacted document copy.

---

## 📈 Scalability & Future Enhancements

- **Queue-based Batching**: In production, files can be queued using Celery/Redis for asynchronous scale.
- **Database Scaling**: Swap SQLite with AWS Aurora/PostgreSQL for highly concurrent multi-tenant transaction tracking.
- **Vector Database**: Deploy a dedicated Amazon OpenSearch or Pinecone cluster instead of local FAISS for multi-million policy segment scale.
- **OCR fallback**: Add OCR support (e.g., Tesseract or Amazon Textract) for scanned/image-only PDFs.
