import asyncio
import os
import sys
import glob
from dotenv import load_dotenv

# Load local .env for Google Cloud and LSEG MCP Client authentication
load_dotenv()

from google.adk.evaluation.agent_evaluator import AgentEvaluator

async def main():
    agent_module = "lseg_market_agent"
    
    # Optional: ensure we can be executed from workspace root or find the agent
    sys.path.insert(0, os.path.abspath("."))

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
                print_detailed_results=False # Set to false to reduce noise
            )
            print(f"✅ PASSED {eval_dataset}")
        except Exception as e:
            print(f"❌ FAILED {eval_dataset}: {e}")

if __name__ == "__main__":
    asyncio.run(main())

