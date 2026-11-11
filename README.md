# BTL Lý thuyết mật mã - Nhóm 7

Đề tài: cài đặt và mô phỏng mã dòng **MICKEY 2.0** bằng Python.

## Thành viên

| STT | MSSV | Họ và tên |
| :-: | :-: | --- |
| 1 | 20233483 | Phạm Nguyễn Anh Kiệt |
| 2 | 20233373 | Nguyễn Khắc Giang |
| 3 | 20233308 | Nguyễn Văn Đạt |
| 4 | 20233473 | Đặng Trung Kiên |
| 5 | 20233468 | Hoàng Tuấn Khôi |
| 6 | 20233451 | Nguyễn Quang Huy |

## Sơ qua về MICKEY 2.0

MICKEY 2.0 do Steve Babbage và Matthew Dodd thiết kế, nằm trong danh mục phần cứng (profile 2) của eSTREAM. Thuật toán dùng khóa 80 bit, IV dài từ 0 đến 80 bit.

Trạng thái bên trong gồm hai thanh ghi 100 bit:

- **R**: thanh ghi tuyến tính, phản hồi tại 50 vị trí trong bảng `RTAPS`.
- **S**: thanh ghi phi tuyến, dùng các bảng `COMP0`, `COMP1`, `FB0`, `FB1`.

Điểm đáng chú ý là hai thanh ghi điều khiển lẫn nhau. Ở mỗi nhịp, bit điều khiển của R lấy từ `S[34] ^ R[67]`, còn của S lấy từ `S[67] ^ R[33]`. Nhờ vậy cách dịch của R và S thay đổi liên tục, không đoán trước được.

Quá trình chạy gồm 4 bước:

1. Đặt R, S về 0.
2. Nạp lần lượt từng bit IV, rồi 80 bit khóa (chế độ mixing bật).
3. Chạy thêm 100 nhịp với bit vào bằng 0 (preclock).
4. Sinh keystream: mỗi nhịp lấy ra một bit `R[0] ^ S[0]`, sau đó clock tiếp với mixing tắt.

Mã hóa và giải mã đều là XOR bản tin với keystream.

## Cấu trúc thư mục

```
src/
  constants.py   bảng RTAPS, COMP0, COMP1, FB0, FB1 chép từ đặc tả
  registers.py   clock_r, clock_s
  mickey2.py     clock_kg, init_state, keystream, crypt
tests/           test cho từng phần, chạy bằng pytest
trace.py         ghi lại trạng thái R, S qua từng nhịp, xuất ra JSON
docs/            đặc tả gốc (PDF) và bảng test vector
```

## Cài đặt và chạy

Cần Python 3.10 trở lên. Ngoài `pytest` để chạy test thì không cần thư viện nào khác.

```bash
python -m pip install pytest
```

### Dùng thử

Chạy từ thư mục gốc của repo:

```python
from src.mickey2 import crypt, keystream

key = bytes.fromhex("123456789abcdef01234")   # đúng 10 byte
iv = bytes.fromhex("21436587")

print(keystream(key, iv, 10).hex())   # 9821e10c5ed28d32bbc3

c = crypt(key, iv, b"Xin chao")
print(crypt(key, iv, c))              # b'Xin chao'
```

Nếu IV không chẵn byte thì truyền thêm `iv_bits`, ví dụ `keystream(key, iv, 16, iv_bits=31)` chỉ lấy 31 bit đầu của `iv`.

### Chạy test

```bash
python -m pytest -v
```

Hiện có 177 test, tất cả đều qua. Phần test vector có 2 vector lấy từ bộ test của tác giả trên eSTREAM, cộng thêm một số trường hợp biên (key toàn 0, IV rỗng, IV 1 bit, IV 31 bit...). Chi tiết xem ở [docs/test_vectors.md](docs/test_vectors.md).

### Xem trace

```bash
python trace.py --demo
```

Lệnh này mã hóa chuỗi `HELLO` với một cặp key/IV cố định và ghi từng nhịp clock (pha, bit vào, bit điều khiển, R và S trước/sau, bit keystream) vào file `trace_demo.json`. Lưu ý file được ghi ra thư mục **cha** của repo chứ không nằm trong repo.

## Tài liệu tham khảo

- S. Babbage, M. Dodd, *The Stream Cipher MICKEY 2.0* - [docs/mickey_p3.pdf](docs/mickey_p3.pdf)
- S. Babbage, M. Dodd, *The Stream Cipher MICKEY-128 2.0* - [docs/mickey128_p3.pdf](docs/mickey128_p3.pdf)
- Trang eSTREAM: https://www.ecrypt.eu.org/stream/

## Dành cho thành viên nhóm

Đọc [CONTRIBUTING.md](CONTRIBUTING.md) trước khi tạo nhánh và code.
