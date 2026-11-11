"""Kiểm thử CLOCK_R — thanh ghi R (LFSR 100 bit) của MICKEY 2.0.

Công thức lấy từ đặc tả eSTREAM (mickey_p3), không chép từ src/registers.py:

    FEEDBACK_BIT = r99 XOR INPUT_BIT
    r'0 = 0
    r'i = r{i-1}                  với 1 <= i <= 99
    r'i = r'i XOR FEEDBACK_BIT    với mọi i thuộc RTAPS
    nếu CONTROL_BIT = 1:
        r'i = r'i XOR ri          với 0 <= i <= 99

Chạy: python -m pytest tests/test_clock_r.py -v
"""
import pytest

from src.constants import RTAPS
from src.registers import clock_r


def ones_at(*positions):
    state = [0] * 100
    for pos in positions:
        state[pos] = 1
    return state


def spec_clock_r(R, inp, ctrl):
    """Oracle viết lại từ công thức đặc tả, để đối chiếu hàng loạt trạng thái."""
    feedback = R[99] ^ inp
    shifted = [0] + R[:99]
    for tap in RTAPS:
        shifted[tap] ^= feedback
    if ctrl == 1:
        shifted = [shifted[i] ^ R[i] for i in range(100)]
    return shifted


def test_all_zero_stays_zero():
    """Không có bit 1 và không có đầu vào thì trạng thái sau nhịp vẫn toàn 0."""
    assert clock_r([0] * 100, 0, 0) == [0] * 100


def test_input_bit_sets_exactly_the_tap_positions():
    """R toàn 0, INPUT = 1: feedback = 1, chỉ các vị trí RTAPS bật lên."""
    expected = ones_at(*RTAPS)
    assert clock_r([0] * 100, 1, 0) == expected
    # CONTROL = 1 nhưng trạng thái cũ toàn 0 nên XOR thêm không đổi gì.
    assert clock_r([0] * 100, 1, 1) == expected


def test_r99_and_input_cancel():
    """feedback = r99 XOR inp. Cả hai bằng 1 thì feedback = 0 và bit 99 bị đẩy ra."""
    assert clock_r(ones_at(99), 1, 0) == [0] * 100


def test_r99_alone_feeds_every_tap():
    """Chỉ r99 = 1, inp = 0: feedback = 1, các tap bật, bit 99 không còn trong thanh ghi."""
    assert clock_r(ones_at(99), 0, 0) == ones_at(*RTAPS)


def test_shift_moves_a_non_tap_bit_one_step():
    """Vị trí 2 không thuộc RTAPS. inp = 0 nên feedback = 0, bit chỉ dịch từ 2 sang 3."""
    assert 2 not in RTAPS
    assert clock_r(ones_at(2), 0, 0) == ones_at(3)


def test_bit_98_shifts_into_99():
    """98 không phải tap. Bit ở 98 phải sang đúng ô 99."""
    assert 98 not in RTAPS
    assert clock_r(ones_at(98), 0, 0) == ones_at(99)


def test_control_mixes_old_state_after_the_shift():
    """ctrl = 0 chỉ dịch. ctrl = 1 còn XOR thêm trạng thái cũ."""
    state = ones_at(0)
    assert clock_r(state, 0, 0) == ones_at(1)
    assert clock_r(state, 0, 1) == ones_at(0, 1)


def test_control_on_a_non_tap_keeps_both_old_and_shifted_bit():
    state = ones_at(2)
    assert clock_r(state, 0, 1) == ones_at(2, 3)


def test_shift_and_feedback_cancel_on_a_tap():
    """r0 = 1 dịch thành r'1 = 1, nhưng 1 thuộc RTAPS và feedback = 1 nên r'1 bị xóa."""
    state = ones_at(0, 99)
    expected = ones_at(*RTAPS)
    expected[1] = 0
    assert clock_r(state, 0, 0) == expected


def test_feedback_does_not_touch_a_cell_outside_rtaps():
    """Bit dịch vào ô 98 (không thuộc RTAPS) vẫn còn sau khi XOR feedback."""
    assert 98 not in RTAPS
    state = ones_at(97, 99)
    expected = ones_at(*RTAPS, 98)
    assert clock_r(state, 0, 0) == expected


@pytest.mark.parametrize("position", [0, 1, 49, 50, 97, 98, 99])
@pytest.mark.parametrize("inp", [0, 1])
@pytest.mark.parametrize("ctrl", [0, 1])
def test_single_bit_matches_spec(position, inp, ctrl):
    state = ones_at(position)
    assert clock_r(state, inp, ctrl) == spec_clock_r(state, inp, ctrl)


def test_mixed_pattern_matches_spec():
    state = [(i * 7 + 3) % 2 for i in range(100)]
    for inp in (0, 1):
        for ctrl in (0, 1):
            assert clock_r(state, inp, ctrl) == spec_clock_r(state, inp, ctrl)


def test_all_ones_matches_spec():
    state = [1] * 100
    for inp in (0, 1):
        for ctrl in (0, 1):
            assert clock_r(state, inp, ctrl) == spec_clock_r(state, inp, ctrl)


def test_output_is_100_binary_bits():
    result = clock_r([(i + 1) % 2 for i in range(100)], 1, 1)
    assert len(result) == 100
    assert set(result) <= {0, 1}


def test_input_register_is_not_modified():
    state = [(i * 3) % 2 for i in range(100)]
    original = state.copy()
    clock_r(state, 1, 1)
    assert state == original


def test_rtaps_are_50_unique_indexes():
    """CLOCK_R phụ thuộc đúng 50 tap trong đặc tả, không trùng, nằm trong 0..99."""
    assert len(RTAPS) == 50
    assert len(set(RTAPS)) == 50
    assert RTAPS == sorted(RTAPS)
    assert RTAPS[0] == 0
    assert RTAPS[-1] == 97
    assert all(0 <= tap <= 99 for tap in RTAPS)
