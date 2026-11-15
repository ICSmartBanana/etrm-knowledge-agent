# Incident process

| | |
|---|---|
| Status | **Draft, awaiting review** |
| Version | 0.1 (15 Nov 2026, milestone M4) |
| Owner | Parag (POC owner, incident lead) |
| Review | After every incident, and quarterly with the regulatory register |

How a leak or harmful answer is **reported, contained and reviewed** (brief §8). The POC uses synthetic data, so no real person or client can be harmed. We still run the process as written, so that it's tested before real data arrives.

## What counts as an incident

| Severity | Examples | Response |
|---|---|---|
| **S1: critical** | Another client's information in an answer or trace (cross-tenant leak). Real or seeded PII disclosed. Inference-only content quoted. A secret (API key) exposed. A hard gate failing on `main` or in the weekly run. | Contain **immediately**. Same-day review. |
| **S2: major** | A wrong answer someone acted on, or could plausibly have acted on, for example a wrong deadline or payment term. A successful prompt injection or system-prompt extraction. The disclosure notice missing. | Contain within one working day. Review within a week. |
| **S3: minor** | A wrong answer caught before anyone relied on it. An unjustified refusal. Cost or latency well outside normal. | Log it and fix in the next iteration. No review meeting. |

When in doubt, take the higher severity and downgrade later.

## 1. Report

Anyone can report: a user, a reviewer, a test, or an alert. Report to the incident lead (POC: Parag) with:

- the **trace ID** shown with the answer, or the time, client and question
- what was wrong, and whether anyone acted on it
- a screenshot if available. **Don't paste leaked content or PII into chat, email or the issue tracker.** Point to the trace instead.

The incident lead opens a **private** GitHub issue labelled `incident` with the severity. A private repo is required, because the issue may describe sensitive content.

Automatic sources: a failing leakage, PII or inference-only gate in CI or the weekly run, and Langfuse alerts once they exist (risk-register action A4).

## 2. Contain

Choose the smallest step that stops further harm, then widen if needed.

| Step | When | How |
|---|---|---|
| Take the agent offline | S1 leak or PII, or any case where the cause isn't yet understood | Stop the API service: `docker compose stop api`, or scale the container app to zero in Azure (M6). |
| Roll back the change | The incident followed a merge | Revert the commit on `main` and redeploy. Prompts, models and knowledge bases are versioned, so the previous version can be restored. |
| Remove a document | One document is the source, for example PII in a quotable class | Delete or reclassify the document and re-ingest. This creates a new `kb_version`. Other clients are untouched. |
| Rotate a secret | A key was exposed | Revoke and reissue it at the provider. Update `.env` and the GitHub secret. Check the provider's usage logs for misuse. |
| Purge traces | Sensitive content reached Langfuse or the local trace files | Delete the affected traces in Langfuse and in `.traces/`. Record what was deleted, not the content itself. |

Record each step with its time in the issue.

## 3. Notify

- **POC (synthetic data):** no external notification. Record the incident and its outcome.
- **Production:** the affected client's contact and the data-protection lead are told the same day for S1. GDPR Art. 33 requires notifying the supervisory authority within **72 hours** of becoming aware of a personal-data breach, unless it's unlikely to risk people's rights. India's DPDP Rules add breach-notice duties from May 2027. The [regulatory register](regulatory-register.md) lists the current duties per region. The client contract may add stricter terms.

## 4. Review

S1 and S2 incidents get a blameless review, written in the issue, within the time in the severity table:

1. **Timeline:** when it happened, when it was found, when it was contained.
2. **Cause:** which control should have stopped it, and why it didn't. Use the [risk register](risk-register.md) IDs.
3. **New test:** every incident becomes at least one eval case or pytest test that would have caught it (brief §6: "every failure found... becomes a new test case"). The fix isn't done until that test is in the regression set or the test suite and passes.
4. **Register updates:** adjust the risk register (likelihood, mitigation, covering tests) and, if relevant, the use-case classification and the model card's known limits.
5. **CHANGELOG entry** for the fix.

Close the issue once the new test is merged and the registers are updated.

## Drills

The M3 leaky-change demo (PR #7) acted as a first drill for the *detection* side: removing both isolation layers was blocked by the isolation tests, the governance check and the leakage gate (85 failures). A containment drill (take the agent offline, roll back, re-ingest a client) should be run before M6 deployment.

## Incident log

| ID | Date | Severity | Summary | Issue | Closed |
|---|---|---|---|---|---|
| none yet | | | | | |
