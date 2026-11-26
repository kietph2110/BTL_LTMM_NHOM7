import json

import pytest

from trace import TraceRecorder


def test_luu_trang_thai_thanh_ghi_tai_thoi_diem_ghi(tmp_path):
    """Trạng thái trong JSON vẫn đúng dù bên gọi sửa thanh ghi hoặc sự kiện đã nhận."""
    recorder = TraceRecorder()
    before = [0] * 100
    after = [1] * 100
    event = recorder.record_clock_step(
        operation="clock_kg",
        r_before=before,
        s_before=before,
        r_after=after,
        s_after=after,
    )
    before[0] = 1
    after[0] = 0
    event.operation = "changed"
    event.s_after = None

    path = tmp_path / "output" / "trace.json"
    assert recorder.export_json(path) == path
    row, = json.loads(path.read_text(encoding="utf-8"))
    assert row["phase"] == "clock"
    assert row["operation"] == "clock_kg"
    assert row["r_before"] == row["s_before"] == [0] * 100
    assert row["r_after"] == row["s_after"] == [1] * 100


@pytest.mark.parametrize(
    "field, value, error",
    [
        ("phase", " ", ValueError),
        ("operation", "", ValueError),
        ("mixing", 1, TypeError),
        ("input_bit", True, ValueError),
        ("control_bit_r", 2, ValueError),
        ("control_bit_s", -1, ValueError),
        ("keystream_bit", "1", ValueError),
        ("r_before", [0] * 99, ValueError),
        ("s_before", "1" * 101, ValueError),
        ("r_after", [0] * 99 + [2], ValueError),
        ("s_after", "0" * 99 + "x", ValueError),
    ],
)
def test_su_kien_khong_hop_le_khong_chiem_so_thu_tu(field, value, error):
    """Sau khi từ chối sự kiện lỗi, bộ ghi cấp số 0 cho sự kiện hợp lệ đầu tiên."""
    recorder = TraceRecorder()
    fields = {"phase": "clock", "operation": "clock_kg"}
    fields[field] = value
    with pytest.raises(error):
        recorder.record(**fields)
    assert recorder.record(phase="clock", operation="clock_kg").sequence == 0


def test_thanh_ghi_ngan_van_chi_chap_nhan_bit_0_va_1(tmp_path):
    """Khi bỏ giới hạn độ dài, thanh ghi ngắn được phép chứa các bit 0 và 1."""
    recorder = TraceRecorder(strict_register_length=False)
    recorder.record_clock_step(operation="example", r_before="01", s_before=[1, 0])
    with pytest.raises(ValueError):
        recorder.record_clock_step(operation="example", r_before="02")

    path = recorder.export_json(tmp_path / "trace.json")
    row, = json.loads(path.read_text(encoding="utf-8"))
    assert row["r_before"] == "01"
    assert row["s_before"] == [1, 0]
