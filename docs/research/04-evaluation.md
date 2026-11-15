# 4. RAG evaluation practice and how teams set thresholds

## Findings

- **Score retrieval and generation separately** (the brief §5 already asks for this). Reading the metrics together tells you where a problem is. If **context precision falls while faithfulness stays steady**, the retriever is getting worse and the model is faithfully using bad context. A side effect to watch: raising top-k can raise recall but lower precision, and then faithfulness drops because the model blends in irrelevant chunks.
- **Gate pattern: an absolute floor plus a drift budget.** Fail the build if a metric falls below its floor, **or** if it falls more than a set amount below the stored baseline, even when it's still above the floor. The drift budget catches slow erosion. A published illustrative config used faithfulness ≥ 0.88 (max drop 0.03) and context precision ≥ 0.78 (max drop 0.05). The authors say these numbers are *illustrative*. Ours get set from our own baseline in M2.
- **Two speeds of eval.** A small, fixed regression set gates PRs. A larger suite runs on a schedule. This matches brief §5 and our cost-control rule.
- **Comparability.** Changing the Ragas version or the judge model starts a **new metric series**. Pin both, and record them in each baseline file.
- **Promptfoo** offers deterministic assertions (`contains` and `icontains` variants, `javascript`, regex) and model-graded ones (`llm-rubric`, similarity). Third-party guides say the `not-` prefix negates any assertion (for example `not-contains`). **Verify** `not-icontains` in the official assertions docs before writing the PII and leakage suites.

## Implications for this project

1. Each baseline file (`evals/baselines/iteration-N.json`) records the Ragas version, the judge model ID, the eval-set hash, `prompt_version` and `kb_version` alongside the scores.
2. Gates: **leakage and PII must be exactly zero** (deterministic Promptfoo assertions against `data/pii_registry.json` and the per-tenant canary strings). Quality metrics use the floor-plus-drift pattern, with floors set from the M2 baseline and then raised over time.
3. Don't rely on an LLM judge for leakage and PII. Use deterministic string and n-gram checks, so the hard gates are reproducible and cost nothing to run.

## Sources

- [AI Engineer Playbook: RAG evaluation in CI/CD](https://aiengineerplaybook.substack.com/p/rag-evaluation-in-cicd-versioning)
- [TestDino: RAG evaluation framework, four QA checks](https://testdino.com/blog/rag-evaluation-framework)
- [MLflow: catch regressions with RAG evaluation](https://mlflow.org/articles/tags/rag-evaluation/)
- [QA Skills: Ragas faithfulness and answer relevancy](https://qaskills.sh/blog/ragas-faithfulness-answer-relevancy-guide) · [QA Skills: RAG QA testing guide](https://qaskills.sh/blog/rag-evaluation-metrics-complete-2026)
- [My Engineering Path: RAG evaluation with Ragas](https://myengineeringpath.dev/genai-engineer/rag-evaluation/) · [Autonoma: RAG evaluation metrics](https://getautonoma.com/blog/rag-evaluation-metrics)
- [Promptfoo assertions and metrics (official docs)](https://promptfoo.dev/docs/configuration/expected-outputs/) · [Luca Berton: LLM regression testing in CI with Promptfoo](https://lucaberton.com/blog/llm-regression-testing-ci-promptfoo/) · [DEV: Promptfoo deep dive](https://dev.to/himanshuai/testing-llms-like-software-a-promptfoo-deep-dive-for-qa-engineers-5hgl)
