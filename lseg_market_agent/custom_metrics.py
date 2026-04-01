from google.adk.evaluation.evaluator import EvaluationResult, PerInvocationResult
from google.adk.evaluation.eval_metrics import EvalStatus
from google.adk.evaluation.eval_case import get_all_tool_calls

def name_only_in_order_match(
    eval_metric,
    actual_invocations,
    expected_invocations,
    conversation_scenario=None,
):
    """Matches tool trajectories by name only, ignoring arguments."""
    per_invocation_results = []
    total_score = 0.0
    num_invocations = 0

    # Ensure expected_invocations is not None
    if expected_invocations is None:
         expected_invocations = [None] * len(actual_invocations)

    for actual, expected in zip(actual_invocations, expected_invocations):
        actual_calls = get_all_tool_calls(actual.intermediate_data) if actual else []
        expected_calls = get_all_tool_calls(expected.intermediate_data) if expected else []

        match = False
        if not expected_calls:
            match = True # No expected tools, vacuously pass? Or fail if actual has tools? 
            # Standard TrajectoryEvaluator says if not expected, True.
        elif not actual_calls:
            match = False
        else:
            expected_names = set([c.name for c in expected_calls])
            actual_names = set([c.name for c in actual_calls])
            
            # Subset matching (order-independent)
            match = expected_names.issubset(actual_names)

        score = 1.0 if match else 0.0

        total_score += score
        num_invocations += 1

        # Use criterion.threshold as fallback since framework clears eval_metric.threshold for custom metrics
        threshold = eval_metric.criterion.threshold if eval_metric.criterion else 0.5
        
        per_invocation_results.append(PerInvocationResult(
            actual_invocation=actual,
            expected_invocation=expected,
            score=score,
            eval_status=EvalStatus.PASSED if score >= threshold else EvalStatus.FAILED
        ))

    overall_score = total_score / num_invocations if num_invocations > 0 else 0.0
    threshold = eval_metric.criterion.threshold if eval_metric.criterion else 0.5
    return EvaluationResult(
        overall_score=overall_score,
        overall_eval_status=EvalStatus.PASSED if overall_score >= threshold else EvalStatus.FAILED,
        per_invocation_results=per_invocation_results
    )
