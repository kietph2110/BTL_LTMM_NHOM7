import json

import pytest

import trace
from src.mickey2 import clock_kg, crypt


KEY = bytes.fromhex("00112233445566778899")
IV = bytes.fromhex("11223344556677889900")


def test_ma_hoa_hello_ghi_dung_tung_nhip(tmp_path):
    """Đối chiếu bản mã và kiểm tra bit điều khiển, trạng thái thanh ghi ở từng nhịp."""
    recorder = trace.TraceRecorder()
    result = recorder.trace_execution(key=KEY, iv=IV, data=b"HELLO")
    path = recorder.export_json(tmp_path / "trace.json")
    rows = json.loads(path.read_text(encoding="utf-8"))

    assert result["ciphertext"] == bytes.fromhex("69c3207d8b")
    assert result["event_count"] == len(rows) == 305
    assert result["key_bits"] == result["iv_bits"] == 80
    expected_phases = (
        ["init_iv"] * 80 + ["init_key"] * 80 + ["preclock"] * 100
        + (["keystream"] * 8 + ["encrypt"]) * 5
    )
    assert [row["phase"] for row in rows] == expected_phases
    assert [row["sequence"] for row in rows] == list(range(305))

    r, s = [0] * 100, [0] * 100
    for row in rows:
        if row["phase"] == "encrypt":
            assert row["operation"] == "xor_byte"
            continue
        step = row["sequence"]
        assert row["operation"] == "clock_kg", step
        assert (row["r_before"], row["s_before"]) == (r, s), step
        assert row["control_bit_r"] == s[34] ^ r[67], step
        assert row["control_bit_s"] == s[67] ^ r[33], step
        generating = row["phase"] == "keystream"
        assert row["mixing"] == (not generating), step
        assert row["keystream_bit"] == (r[0] ^ s[0] if generating else None), step
        r, s = clock_kg(r, s, row["mixing"], row["input_bit"])
        assert (row["r_after"], row["s_after"]) == (r, s), step


def test_dem_rieng_su_kien_va_luu_lich_su_tung_lan_chay(tmp_path):
    """Mỗi lần chạy có mã và số sự kiện riêng, với số thứ tự liên tục trong JSON."""
    recorder = trace.TraceRecorder()
    first = recorder.trace_execution(key=KEY, iv=b"", note="Lần đầu")
    second = recorder.trace_execution(key=KEY, iv=b"\xa7", iv_bits=3, data=b"A")
    assert first["ciphertext"] == b""
    assert second["ciphertext"] == crypt(KEY, b"\xa7", b"A", iv_bits=3)
    assert first["event_count"] == 180
    assert second["event_count"] == 192
    assert first["run_id"] != second["run_id"]

    path = recorder.export_json(tmp_path / "trace.json")
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert [row["sequence"] for row in rows] == list(range(372))
    assert [row["run_id"] for row in rows] == (
        [first["run_id"]] * 180 + [second["run_id"]] * 192
    )
    assert rows[0]["note"] == "Lần đầu"
    assert all(row.get("note") is None for row in rows[1:])
    assert [row["input_bit"] for row in rows[180:183]] == [1, 0, 1]
    assert rows[183]["phase"] == "init_key"


@pytest.mark.parametrize(
    "key, iv, iv_bits, error",
    [
        (KEY[:-1], IV, None, ValueError),
        (KEY + b"x", IV, None, ValueError),
        (KEY, IV, -1, ValueError),
        (KEY, IV + b"x", 81, ValueError),
        (KEY, b"\x00", 9, ValueError),
        (KEY, IV, True, TypeError),
        (KEY, IV, 1.5, TypeError),
    ],
)
def test_tu_choi_khoa_hoac_do_dai_iv_khong_hop_le(key, iv, iv_bits, error):
    """Báo đúng loại lỗi khi khóa sai độ dài hoặc số bit IV không hợp lệ."""
    with pytest.raises(error):
        trace.TraceRecorder().trace_execution(key=key, iv=iv, iv_bits=iv_bits)


def test_demo_ghi_json_cung_thu_muc_voi_trace_py(tmp_path, monkeypatch):
    """Demo ghi đủ 305 sự kiện vào tệp JSON nằm cạnh trace.py."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(trace, "__file__", str(project / "trace.py"))
    monkeypatch.chdir(tmp_path)

    trace.run_demo()

    rows = json.loads((project / "trace_demo.json").read_text(encoding="utf-8"))
    assert len(rows) == 305
    assert not (tmp_path / "trace_demo.json").exists()
