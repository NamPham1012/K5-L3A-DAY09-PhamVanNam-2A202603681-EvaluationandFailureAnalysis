# Judge audit

Chạy từ `src`: `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5` và thay tên file bằng `judge_helpful_public.csv` để kiểm tra tiêu chí helpful.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có | Có thể dùng trong phạm vi calibration này |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không | Loại khỏi gate |

## Audit 5 case bất đồng về tone

Đánh giá dưới đây dựa trên nhãn và ghi chú trong CSV công khai; các quy tắc đề xuất cần được chủ sở hữu rubric xác nhận. Với H-017, tuổi khách hàng được ghi trong note nhưng không thể suy ra chỉ từ câu trả lời.

| Case | Judge | Người | Nhận định theo ghi chú | Đề xuất sửa rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Đồng ý nhãn người nếu quy định giọng điệu loại xưng `em` và từ `nha` trong ngữ cảnh này. | Nêu cụ thể cách xưng hô và từ thân mật được phép; thêm ví dụ đối chiếu. |
| H-017 | PASS | FAIL | Note cho biết cách gọi `bạn` không phù hợp với khách lớn tuổi; cần cung cấp ngữ cảnh này cho judge để kiểm chứng. | Yêu cầu judge xét thông tin khách khi có; nếu không có thì nêu thiếu ngữ cảnh thay vì đoán tuổi. |
| H-029 | PASS | FAIL | Đồng ý nhãn người theo tiêu chí tránh giọng ra lệnh: câu bảo khách không cần nhắn thêm. | Đánh giá toàn bộ câu, kể cả mệnh lệnh ở cuối, thay vì chỉ dựa vào lời mở đầu lịch sự. |
| H-042 | FAIL | PASS | Đồng ý nhãn người theo note: câu ngắn nhưng lịch sự; không phải mọi trường hợp đều cần xin lỗi. | Chỉ yêu cầu xin lỗi khi ngữ cảnh hoặc chính sách yêu cầu, không phạt mặc định. |
| H-051 | FAIL | PASS | Đồng ý nhãn người nếu quy định CS cho phép dùng `refund`, như note ghi. | Liệt kê thuật ngữ tiếng Anh được chấp nhận; không coi mọi từ tiếng Anh là lỗi tone. |

## Kết luận và giới hạn

- Tone: ma trận `TP=24, FP=4, FN=6, TN=66`; đạt cả ba ngưỡng trên tập replay công khai. Vẫn có lỗi bỏ sót và báo nhầm.
- Helpful: `TP=9, FP=0, FN=21, TN=70`. Precision cao nhưng recall chỉ 0.300: judge bỏ sót 21/30 lỗi, nên không dùng làm gate.
- Tone có tỷ lệ FAIL quan sát 0.28, hiệu chỉnh Rogan–Gladen 0.30; helpful có tỷ lệ quan sát 0.09, hiệu chỉnh 0.30. Các ước lượng phụ thuộc vào chất lượng nhãn người và các giả định về độ nhạy, độ đặc hiệu.
- Đây là CSV replay công khai, không phải kiểm định trên dữ liệu mới hay held-out thực sự. Cần thu thập và gán nhãn độc lập dữ liệu mới, sau đó hiệu chuẩn lại trước khi khái quát cho môi trường thực tế.
