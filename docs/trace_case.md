# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường                    | Nội dung                                                                                       |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| Trial                     | `seeded_regression C-002@11`; run ID `E-seeded_regression-20261117-df81` trong `reports/eval_seeded_regression.json` |
| Triệu chứng               | Grader Lab 8 báo `status resolved != denied`; ledger hoàn 20.000đ thay vì 0đ                   |
| Bước sai đầu tiên         | Event 3, `model_override`: `{"delay_days": 5}`                                                 |
| Vì sao là bước *đầu tiên* | Theo mã variant, agent dùng số ngày từ ticket ghi đè số ngày DB trước khi tính khoản hoàn      |
| Failure mode              | FM-03 — ticket\_trust                                                                          |
| Đối chứng                 | `fixed C-002@11`: quote 0đ, ledger 0đ, trạng thái `denied`                                     |
| Regression test           | `tests/test_lab9_trace_case.py::test_c002_ticket_override_regression`: xác nhận variant lỗi có `model_override`, ledger 20.000đ và Lab 8 FAIL; `fixed` không override, ledger 0đ và Lab 8 PASS. Test chạy thành công: 1 passed. |
| Chưa chắc chắn            | Output trace đang bị cắt ngắn nên chưa thấy đầy đủ giá trị ngày trong DB                       |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
