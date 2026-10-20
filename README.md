# Bài tập lớn Lý thuyết mật mã - Nhóm 7

**Đề tài:** Cài đặt và mô phỏng thuật toán mã dòng MICKEY 2.0 (Mutual Irregular Clocking KEYstream generator).

## Giới thiệu thuật toán
MICKEY 2.0 là một thuật toán mã hóa luồng (stream cipher) được thiết kế bởi Steve Babbage và Matthew Dodd, thuộc dự án eSTREAM. Thuật toán được tối ưu hóa đặc biệt cho các thiết bị phần cứng có tài nguyên hạn chế.

**Đặc điểm kỹ thuật cốt lõi:**
- **Độ dài Khóa (Key):** 80 bit.
- **Độ dài Vector khởi tạo (IV):** Từ 0 đến 80 bit.
- **Kiến trúc:** Dựa trên hai thanh ghi dịch (Shift Registers) hoạt động song song:
  - **R (Linear Feedback Shift Register):** Thanh ghi tuyến tính 100 bit.
  - **S (Non-linear Feedback Shift Register):** Thanh ghi phi tuyến 100 bit.
- **Cơ chế Clocking:** Đặc trưng nhất của MICKEY 2.0 là cơ chế xung nhịp bất quy tắc tương hỗ (Mutual Irregular Clocking). Trạng thái của thanh ghi này sẽ quyết định cách dịch bit (clocking mode) của thanh ghi kia.

## Cấu trúc dự án
- `src/constants.py`: Chứa các bảng hằng số tĩnh (RTAPS, COMP0/1, FB0/1) từ đặc tả gốc.
- `src/registers.py`: Cài đặt logic dịch bit và phản hồi của hai thanh ghi R và S.
- `src/mickey2.py`: Điều phối xung nhịp (Clock_KG), nạp Key/IV và sinh Keystream.
- `src/trace.py`: Chạy mô phỏng, xuất log trạng thái các thanh ghi qua từng vòng.
- `tests/`: Chứa các kịch bản kiểm thử (Unit test) tự động.

## Hướng dẫn sử dụng
*(Sẽ được cập nhật sau khi hoàn thiện giao diện CLI)*

---
**Dành cho các thành viên trong nhóm:** 
Vui lòng đọc kỹ file [CONTRIBUTING.md](./CONTRIBUTING.md) trước khi tạo nhánh và bắt đầu code.
