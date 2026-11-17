import pytest
from pydantic_evals.evaluators import EvaluatorContext

from lab9.graders import ReplyAmountMatchesLedger


pytestmark = pytest.mark.student


def evaluate_reply(text, ledger_amount):
    trial = {
        "snapshot": {"refund_vnd": ledger_amount},
        "events": [{"kind": "reply", "payload": {"text": text}}],
    }
    ctx = EvaluatorContext(
        name="reply-test",
        inputs={},
        metadata=None,
        expected_output={},
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )
    return ReplyAmountMatchesLedger().evaluate(ctx).value


def test_reply_amount_matches_ledger():
    assert evaluate_reply("Đã hoàn 20.000đ cho đơn O-808.", 20000) is True


def test_reply_amount_differs_from_ledger():
    assert evaluate_reply("Đã hoàn 35.000đ cho đơn O-808.", 20000) is False


def test_reply_without_amount():
    assert evaluate_reply("Đơn chưa đủ điều kiện hoàn.", 0) is True
