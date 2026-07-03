# Evaluation

Automated evaluation for the trading assistant, split into two layers.

## 1. Deterministic unit / integration tests (`tests/`)

Fast, no GCP or model required — run on every push in CI.

```bash
pip install -r requirements-dev.txt
pytest tests -m "not adk"
```

Covers tool-argument validation (`schemas.py`) and the observability layer
(redaction, structured logging).

## 2. ADK agent evalset (LLM-in-the-loop)

`trading_assistant.evalset.json` defines intent → expected-tool-trajectory
cases. Thresholds live in `test_config.json`
(`tool_trajectory_avg_score`, `response_match_score`).

Requires a live model + GCP credentials, so it is opt-in:

```bash
# via ADK CLI
adk eval trading_assistant eval/trading_assistant.evalset.json --config_file_path eval/test_config.json

# or via pytest
RUN_ADK_EVAL=1 pytest tests/test_agent_eval.py -v
```

Add new cases by capturing sessions in `adk web` ("Save as eval case") or by
appending entries to `eval_cases`.
