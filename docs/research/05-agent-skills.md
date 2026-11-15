# 5. Existing Claude Code and agent skills for governance, security and evals

## Findings

There's no single canonical "governance + evals + security" skill pack. The candidates worth reviewing for the `agent-standards` repo are:

| Candidate | What it covers | Possible use |
|---|---|---|
| OWASP secure-agent-playbook (Tessl registry) | A security and ethics checklist across 13 categories of AI apps | A base for the pre-release review gate |
| AWS samples `skill-eval` | A security and quality evaluation framework *for skills*, with a security checklist | Vetting our own skills before we publish them |
| `agentic-actions-auditor` (popey) | Audits GitHub Actions workflows that use AI agents | Reviewing M3/M6 workflows |
| `skill-base` (danhdox) | A cross-agent skill library with security and code-review checklists | Reference for structure |
| `governance` skill (wrsmith108) | Code-governance enforcement with a check script | Reference for the "run governance checklist" skill |
| An ISO 42001 governance skill (community list) | Risk, ethics, transparency and compliance prompts | Reference only. Authorship unverified. |

**Caveats from the sources.** Skills can run code and reach connected tools, so vet third-party skills like any dependency: check the license, maintenance and a security review. Skills don't sync between Claude.ai, the API and Claude Code, so each surface needs its own copy. Agent Skills and code execution are not ZDR (zero data retention)-eligible, which matters if client data ever goes through them.

## Implications

1. In M4, the four skills the brief §10 asks for (scaffold a new agent, write an eval set from documents, run the governance checklist, monthly policy digest) are written **ourselves**, borrowing structure from the candidates above. Nothing is installed wholesale.
2. Add a "vet a third-party skill" item to the standards pack's do's and don'ts.

## Sources

- [skill-base (GitHub)](https://github.com/danhdox/skill-base)
- [OWASP secure-agent-playbook (Tessl)](https://tessl.io/registry/skills/github/OWASP/secure-agent-playbook)
- [agentic-actions-auditor (Tessl)](https://tessl.io/registry/skills/github/popey/claude-code-skills/agentic-actions-auditor)
- [AWS samples skill-eval](https://skillselion.com/skills/aws-samples/sample-agent-skill-eval/skill-eval)
- [Governance skill (wrsmith108)](https://agent-skills.md/skills/wrsmith108/governance-claude-skill/governance)
- [MintMCP: Claude Skills explained (governance and security)](https://www.mintmcp.com/blog/claude-skills-explained)
- [DEV: a governance layer for AI agent skills](https://dev.to/artemr_rudenko_0bf2c2c505/i-built-a-governance-layer-for-ai-agent-skills-with-an-ai-agent-as-my-pair-programmer-4jkb)
- [Agent skills security audit guide](https://automationswitch.vercel.app/ai-workflows/agent-skills-security-audit-guide-how-to-verify-skill-md-files-before-you-install)
- [Governance checklist generator (skills.sh)](https://skills.sh/jeremylongshore/claude-code-plugins-plus-skills/governance-checklist-generator/security/agent-trust-hub)
