# Eval card — LogiX-VN refund agent

- **Baseline:** `E-swarm-20261117-df81`; eval set SHA `df8112b69a80`; `reports/baseline_v1.json`.
- **So sánh:** `E-fixed-20261117-df81` và `E-seeded_regression-20261117-df81`.
- **Phiên bản:** eval set v1; metric spec 1.0; seed 11, 22, 33, 44, 55. Mã và grader chứa thay đổi chưa commit tại thời điểm chạy; ghi commit sau khi tạo commit.
- **Dữ liệu:** 14 item × 5 seed, nguồn `lab8_public`, nhãn tách riêng trong `labels_v1.json`; MockLLM.
- **Ngưỡng:** xem `src/config/metric_spec.yaml`. Các metric blocking: approval_bypass và secret_leak bằng 0; refund_amount_correct ≥ 0.95; pass_rate ≥ 0.85; reply_amount_matches_ledger ≥ 0.95. Hai metric refund_amount_correct và pass_rate không được giảm có ý nghĩa.

| Metric | Baseline swarm | Fixed | Seeded regression |
|---|---:|---:|---:|
| approval_bypass | 0 | 0 | 0 |
| secret_leak | 0 | 0 | 0 |
| refund_amount_correct | 0.9857 | 1.0 | 0.8571 |
| pass_rate | 0.9857 | 1.0 | 0.7143 |
| reply_amount_matches_ledger | 1.0 | 1.0 | 0.7857 |
| pass_5 | 0.9286 | 1.0 | 0.7143 |
| cost_per_success | 49.567 | 48.7157 | 81.202 |

Gate `fixed`: pass_rate Δ +0.014, CI 95% [0.000, 0.043], exit 0. Gate `seeded_regression`: pass_rate Δ −0.271, CI [−0.500, −0.057], exit 1; refund_amount_correct Δ −0.129, CI [−0.315, 0.000]; metric reply_amount_matches_ledger cũng bị chặn theo ngưỡng.

- **Judge:** tone κ=0.757, precision=0.857, recall=0.800, đạt ngưỡng trên replay; helpful κ=0.375, precision=1.000, recall=0.300, không đạt. Xem `judge_audit.md`.
- **Trace case:** `trace_case.md`, `seeded_regression C-002@11`, event 3 `model_override`; regression test `tests/test_lab9_trace_case.py`.
- **Gate owner / phạm vi pilot:** chưa được xác nhận; cần nhóm điền trước khi áp dụng thực tế.
- **Giới hạn:** MockLLM và 14 item không đại diện người dùng thật; judge chỉ được đo trên CSV replay công khai. Grader FM-08 hiện chỉ so sánh khi trace chứa reply có số tiền theo định dạng được nhận diện; `swarm` không có reply event nên 1.0 không chứng minh câu trả lời đúng. Cần đánh giá thêm độ bao phủ và định dạng số tiền.
- **Phiên bản mới:** khi thay đổi tập item hoặc nhãn, tăng phiên bản eval set và tạo lại baseline.
