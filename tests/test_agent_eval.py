"""ADK agent evaluation (LLM-in-the-loop).

Requires a live model + GCP credentials, so it is skipped unless RUN_ADK_EVAL=1.
Run locally with:

    RUN_ADK_EVAL=1 pytest tests/test_agent_eval.py -v
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_ADK_EVAL"),
    reason="set RUN_ADK_EVAL=1 (plus GCP credentials) to run the ADK evalset",
)


@pytest.mark.asyncio
async def test_trading_assistant_evalset():
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    await AgentEvaluator.evaluate(
        agent_module="trading_assistant",
        eval_dataset_file_path_or_dir="eval/trading_assistant.evalset.json",
    )
