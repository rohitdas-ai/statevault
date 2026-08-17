# CockroachDB Managed MCP Server Configuration

Connect AI coding agents (Claude Code, Cursor, Antigravity CLI) directly to your CockroachDB Cloud cluster with zero custom database proxies.

## Managed MCP Endpoint
- **Hosted Endpoint:** `https://cockroachlabs.cloud/mcp`
- **Transport:** Server-Sent Events (SSE)
- **Security:** Read-only mode by default with cluster-level audit logging.

## Client Configuration (`~/.gemini/antigravity-cli/settings.json` or `.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "cockroachdb-cloud": {
      "type": "sse",
      "url": "https://cockroachlabs.cloud/mcp",
      "headers": {
        "mcp-cluster-id": "YOUR_COCKROACH_CLUSTER_ID",
        "Authorization": "Bearer YOUR_MCP_API_TOKEN"
      }
    },
    "cockroachdb-skills": {
      "command": "npx",
      "args": ["-y", "@cockroachlabs/skills-mcp"],
      "env": {
        "COCKROACH_DB_URL": "YOUR_COCKROACH_DB_URL"
      }
    }
  }
}
```

## Supported Operations
1. **Schema Discovery:** Discover tables, foreign key constraints, vector index topologies.
2. **Statement Fingerprinting:** Analyze database query execution plans and index utilization.
3. **Anti-Pattern Detection:** Verify `pgvector` HNSW indexes and UUID distribution strategies.
