import asyncio
import glob
import os
import sys

from dotenv import load_dotenv

# Load local .env for Google Cloud and LSEG MCP Client authentication
load_dotenv()

from google.adk.evaluation.agent_evaluator import AgentEvaluator


async def main():
    agent_module = "lseg_market_agent"

    # Optional: ensure we can be executed from workspace root or find the agent
    sys.path.insert(0, os.path.abspath("."))

    from google.adk.evaluation.custom_metric_evaluator import _CustomMetricEvaluator
    from google.adk.evaluation.eval_metrics import Interval, MetricInfo, MetricValueInfo
    from google.adk.evaluation.metric_evaluator_registry import (
        DEFAULT_METRIC_EVALUATOR_REGISTRY,
    )

    # Register custom evaluator for tool_trajectory_avg_score programmatically
    # This overrides the default strict TrajectoryEvaluator
    metric_info = MetricInfo(
        metric_name="tool_trajectory_avg_score",
        description="Custom name-only trajectory matcher",
        metric_value_info=MetricValueInfo(
            interval=Interval(min_value=0.0, max_value=1.0)
        )
    )
    DEFAULT_METRIC_EVALUATOR_REGISTRY.register_evaluator(
        metric_info, _CustomMetricEvaluator
    )



    # Match all individualized test files
    test_files = glob.glob("evals/*.test.json")
    # Sort to run sequentially
    test_files.sort()



    print(f"Starting evaluations for '{agent_module}'...")
    print(f"Found {len(test_files)} test files.\n")

    for eval_dataset in test_files:
        print(f"\n--- Running evaluation with dataset: {eval_dataset} ---")
        try:
            await AgentEvaluator.evaluate(
                agent_module=agent_module,
                eval_dataset_file_path_or_dir=eval_dataset,
                num_runs=1,
                print_detailed_results=True # Set to true to get more details on failures
            )
            print(f"✅ PASSED {eval_dataset}")
        except Exception as e:
            print(f"❌ FAILED {eval_dataset}: {e}")

if __name__ == "__main__":
    asyncio.run(main())

