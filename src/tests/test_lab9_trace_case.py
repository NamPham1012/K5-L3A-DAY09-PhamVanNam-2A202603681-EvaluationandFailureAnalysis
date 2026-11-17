import pytest

from lab9.trace_case import investigate

pytestmark = pytest.mark.student


def test_c002_ticket_override_regression():
    bad = investigate("seeded_regression", "C-002", 11)["trial"]
    fixed = investigate("fixed", "C-002", 11)["trial"]

    # Phiên bản có lỗi: ghi đè dữ liệu DB và hoàn tiền sai.
    assert any(event.get("kind") == "model_override" for event in bad["events"])
    assert bad["snapshot"]["refund_vnd"] == 20000
    assert bad["result"]["status"] == "resolved"
    assert bad["lab8_pass"] is False

    # Phiên bản sửa: không ghi đè, không hoàn tiền, từ chối đúng.
    assert not any(event.get("kind") == "model_override" for event in fixed["events"])
    assert fixed["snapshot"]["refund_vnd"] == 0
    assert fixed["result"]["status"] == "denied"
    assert fixed["lab8_pass"] is True
