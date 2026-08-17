# StateVault: Resilient Multi-Region Memory-as-a-Service for AI Agents

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CockroachDB](https://img.shields.io/badge/CockroachDB-Serverless%20%2B%20pgvector-5f33e1.svg)](https://cockroachlabs.cloud)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20Bedrock%20%7C%20SQS-ff9900.svg)](https://aws.amazon.com)

**CockroachDB × AWS Hackathon 2026 Submission**  
- **Live Demo Site:** [statevault.github.io](https://statevault.github.io)  
- **Devpost Submission Package:** [docs/SUBMISSION.md](docs/SUBMISSION.md)  
- **MCP Configuration Guide:** [docs/MCP_CONFIG.md](docs/MCP_CONFIG.md)  

---

## What is StateVault?

StateVault is an always-on, multi-region memory layer designed for autonomous AI agent fleets. It unifies **ACID transactional state (JSONB)** and **high-dimensional semantic memory (1024d pgvector with HNSW)** into a single database cluster, executing both writes within a **single atomic transaction**.

This eliminates the catastrophic "Split-Brain" problem where external vector databases fail during updates, leaving agent memory permanently desynchronized.

---

## CockroachDB & AWS Toolchain Alignment

- **CockroachDB Managed MCP Server:** Hosted connection (`https://cockroachlabs.cloud/mcp`) for read-only agent schema introspection.
- **Distributed Vector Indexing:** 1024-dimensional HNSW cosine distance search (`vector_cosine_ops`).
- **Agent-Ready `ccloud` CLI:** Automated health inspection via `scripts/ccloud_check.sh`.
- **Open-Source Agent Skills:** Codified schema verification via `scripts/run_skills_audit.sh`.
- **Amazon Bedrock:** Dynamic generation of 1024d embeddings via `amazon.titan-embed-text-v2:0`.
- **AWS Lambda & SQS:** Connection-pooled atomic dual-sync and decoupled usage buffering.

---

## Quickstart & Local Verification

### 1. Run Automated Test Suite
```bash
.venv/bin/pytest -v
```

### 2. Run Interactive Failure & Outage Simulation
```bash
python scripts/demo_simulation.py
```

### 3. Run CockroachDB Toolchain Auditors
```bash
bash scripts/ccloud_check.sh
bash scripts/run_skills_audit.sh
```

### 4. Deploy Infrastructure (AWS SAM)
```bash
bash scripts/deploy.sh
```

---

## License

This project is licensed under the [MIT License](LICENSE).
