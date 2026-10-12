"""Student contracts; no RAGAS API calls."""
from types import SimpleNamespace
import sys
from unittest.mock import Mock

import pytest

from src.phase_a_ragas import (load_test_set_50q, group_by_distribution, run_ragas_50q,
                               bottom_10, cluster_analysis, RagasResult)

pytestmark = pytest.mark.student


@pytest.fixture
def dummy_results():
    return [RagasResult(i+1, dist, f"Q{i}", "A", ["C"], "GT", *scores)
            for i, (dist, scores) in enumerate([
                ("factual", (.9,.8,.7,.6)), ("multi_hop", (.3,.4,.5,.2)),
                ("adversarial", (.1,.2,.3,.4)), ("factual", (.8,.7,.9,.8)),
                ("multi_hop", (.2,.3,.1,.2))])]


def test_group_exact_counts():
    groups = group_by_distribution(load_test_set_50q())
    assert set(groups) == {"factual","multi_hop","adversarial"}
    assert [len(groups[d]) for d in ("factual","multi_hop","adversarial")] == [20,20,10]


def test_ragas_adapter_preserves_rows(monkeypatch):
    questions = load_test_set_50q()
    answers = [{**q, "answer": "A", "contexts": ["C"]} for q in questions]
    metrics = [SimpleNamespace(faithfulness=.8, answer_relevancy=.7,
                               context_precision=.6, context_recall=.5) for _ in answers]
    evaluator_models = ["evaluator-test", "embedding-test"]
    evaluate = Mock(return_value={"per_question": metrics,
                                  "metadata": {"evaluator_models": evaluator_models}})
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(evaluate_ragas=evaluate))
    evaluation = run_ragas_50q(answers)
    results = evaluation.results
    assert evaluation.evaluator_models == evaluator_models
    assert len(results) == 50
    assert [r.question_id for r in results] == [q["id"] for q in questions]
    assert results[0].faithfulness == .8
    evaluate.assert_called_once()
    assert list(evaluate.call_args.args[0]) == [q["question"] for q in questions]


@pytest.fixture
def adapter_input():
    return [{"id": 1, "distribution": "factual", "question": "Q",
             "answer": "A", "contexts": ["C"], "ground_truth": "GT"}]


@pytest.mark.parametrize("status", ["unavailable", "partial"])
def test_ragas_adapter_rejects_unmeasured_scores(monkeypatch, adapter_input, status):
    row = dict(faithfulness=0.0, answer_relevancy=0.0,
               context_precision=0.0, context_recall=0.0, status=status,
               missing_metrics=["faithfulness"])
    evaluate = Mock(return_value={"per_question": [row], "status": status,
                                  "metadata": {"evaluator_models": ["eval-test"]}})
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(evaluate_ragas=evaluate))
    with pytest.raises(ValueError, match="unavailable|partial|unmeasured"):
        run_ragas_50q(adapter_input)


@pytest.mark.parametrize("rows", [[], [{}, {}]])
def test_ragas_adapter_rejects_wrong_row_count(monkeypatch, adapter_input, rows):
    evaluate = Mock(return_value={"per_question": rows,
                                  "metadata": {"evaluator_models": ["eval-test"]}})
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(evaluate_ragas=evaluate))
    with pytest.raises(ValueError, match="row count"):
        run_ragas_50q(adapter_input)


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), -0.1, 1.1, True])
def test_ragas_adapter_rejects_invalid_metric(monkeypatch, adapter_input, value):
    row = dict(faithfulness=value, answer_relevancy=.7,
               context_precision=.6, context_recall=.5)
    evaluate = Mock(return_value={"per_question": [row],
                                  "metadata": {"evaluator_models": ["eval-test"]}})
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(evaluate_ragas=evaluate))
    with pytest.raises(ValueError, match="faithfulness"):
        run_ragas_50q(adapter_input)


def test_unavailable_evaluator_does_not_claim_models(monkeypatch, adapter_input):
    from src import m4_eval
    monkeypatch.setattr(m4_eval, "EVAL_ENABLED", False)
    result = m4_eval.evaluate_ragas(["Q"], ["A"], [["C"]], ["GT"])
    assert result["status"] == "unavailable"
    assert result["metadata"]["evaluator_models"] == []


def test_bottom_nonempty_sorted_complete(dummy_results):
    rows = bottom_10(dummy_results)
    assert len(rows) == 5
    assert [r["rank"] for r in rows] == [1,2,3,4,5]
    assert [r["avg_score"] for r in rows] == sorted(r["avg_score"] for r in rows)
    assert rows[0]["question_id"] == 5
    for row in rows:
        assert {"question_id","distribution","question","worst_metric",
                "diagnosis","suggested_fix"} <= row.keys()
        assert row["diagnosis"].strip() and row["suggested_fix"].strip()


def test_bottom_capped_at_ten(dummy_results):
    repeated = [RagasResult(i+1,r.distribution,r.question,r.answer,r.contexts,r.ground_truth,
                           r.faithfulness,r.answer_relevancy,r.context_precision,r.context_recall)
                for i,r in enumerate(dummy_results*4)]
    assert len(bottom_10(repeated)) == 10


def test_cluster_matrix(dummy_results):
    result = cluster_analysis(dummy_results)
    assert result["matrix"] == {
        "faithfulness":{"factual":0,"multi_hop":0,"adversarial":1},
        "answer_relevancy":{"factual":1,"multi_hop":0,"adversarial":0},
        "context_precision":{"factual":0,"multi_hop":1,"adversarial":0},
        "context_recall":{"factual":1,"multi_hop":1,"adversarial":0}}
    assert result["dominant_failure_metric"] == "context_recall"
    assert result["insight"].strip()


def test_weakest_distribution_is_quality_not_size():
    results = []
    for dist,count,value in [("factual",20,.95),("multi_hop",20,.70),("adversarial",10,.10)]:
        for _ in range(count):
            results.append(RagasResult(len(results)+1,dist,"Q","A",["C"],"GT",
                                       value,value,value,value))
    assert cluster_analysis(results)["dominant_failure_distribution"] == "adversarial"
