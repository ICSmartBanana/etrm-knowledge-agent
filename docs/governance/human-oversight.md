# Human-oversight note

| | |
|---|---|
| Status | **Draft, awaiting review** |
| Version | 0.1 (15 Nov 2026, milestone M4) |
| Owner | Parag (POC owner) |
| Review | Monthly with the risk register, and after any incident |

This note says when and how a person reviews the agent's outputs, and where to escalate (brief §8). The agent is limited-risk under the EU AI Act, so Art. 14 human-oversight duties don't legally apply. We set them anyway, because answers about deadlines and settlement terms can cost money if they're wrong.

## Design principles

- **A person always decides.** The agent only answers questions. It has no tools and can't act on any system, so every answer passes through a person before anything happens.
- **Answers are checkable.** Every answer cites its source documents, and the UI shows them. When the agent doesn't know, it says so instead of guessing.
- **The user is told.** Every answer carries the notice: "You are chatting with an AI assistant. Answers are generated from your organisation's documents and can be wrong; check important details before acting on them."
- **Humans can override.** Any reviewer can stop a release, roll back a prompt, model or knowledge-base version, or take the agent offline (standards-pack principle).

## Oversight points

| When | Who | What they check | Evidence |
|---|---|---|---|
| **Every answer** (user) | The person asking | Before acting on a figure, deadline, threshold or term, open the cited document and confirm it. Always do this for anything that affects money, a nomination or a regulatory filing. | The disclosure notice and citations on every answer |
| **Every change** (pre-merge) | PR reviewer (POC: Parag) | The eval score table, the hard gates, and the CHANGELOG entry for any prompt, model, retrieval or knowledge-base change. Never merge a red PR. | The `eval` PR comment, CI checks, the governance check |
| **Knowledge-base update** | Knowledge-base owner (POC: Parag) | New or changed documents have the right `data_class` and `status`, superseded versions are marked, and no PII is in quotable classes. Spot-check a sample. | The data-source register, `tests/data/test_corpus.py`, the regression eval that the update triggers |
| **New eval sets** | Parag | Review generated eval items before committing them, and spot-check at least 20 % of golden items (brief §5). | `docs/evals/golden-spot-check.md` |
| **Weekly** | Parag | The full eval run (`weekly.yml`): hard gates still zero, no metric dropped. | The workflow run and its results artifact |
| **Monthly** | Parag | A sample of Langfuse traces: refusals, "don't know" answers, guard interventions and low retrieval scores. Turn any wrong answer into a new eval case. Review the risk register. | Langfuse; the risk register review log |
| **Release** (design, pre-release, post-release) | Named approvers in the standards pack's review gates | The gate checklist. | Signed gate checklist |

## What a reviewer looks for in traces

- **Output-guard interventions** (`output_guard` step flags). Each one means the model produced something it shouldn't have: PII, quoted inference-only text, or a system-prompt echo. The guard caught it, but the cause needs a look.
- **Declined and out-of-scope answers** that should have been answered, or the reverse.
- **Low top retrieval scores just above the abstain threshold.** These are the answers most likely to be wrong.
- **Cost or latency outliers.**

## Escalation path

| Situation | Action | Who |
|---|---|---|
| A wrong but harmless answer | Add the question and correct answer to an eval set; fix in the next iteration | Whoever finds it, then Parag |
| A wrong answer that someone acted on, or could have | Treat as an incident, severity S2 or higher | [Incident process](incident-process.md) |
| Any sign of another client's information, PII or quoted internal content in an answer or trace | Treat as an incident, **severity S1**: contain first | [Incident process](incident-process.md) |
| A hard-gate failure in CI | Don't merge. Fix or revert the change. If it fails on `main` or in the weekly run, it's an S1 incident. | PR author, then Parag |

## Open points

- **Named roles for production.** In the POC one person holds every role. A production deployment needs a separate knowledge-base owner per client, a PR reviewer who isn't the author, and an on-call contact. These are listed in the standards pack's review gates.
- **In-app feedback.** Users can't yet flag a bad answer from the UI. Feedback into Langfuse is planned for M5 (brief §9).
