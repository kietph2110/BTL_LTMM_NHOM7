"""Kiểm thử CLOCK_S — thanh ghi S (phi tuyến, 100 bit) của MICKEY 2.0.

Công thức lấy từ đặc tả eSTREAM (mickey_p3), không chép từ src/registers.py:

    S^_0  = 0
    S^_i  = s{i-1} XOR ((s_i XOR COMP0_i) AND (s{i+1} XOR COMP1_i))   với 1 <= i <= 98
    S^_99 = s98
    FEEDBACK_BIT = s99 XOR INPUT_BIT
    CONTROL_BIT = 0:  s'_i = S^_i XOR (FB0_i AND FEEDBACK_BIT)   với 0 <= i <= 99
    CONTROL_BIT = 1:  s'_i = S^_i XOR (FB1_i AND FEEDBACK_BIT)

Chạy: python -m pytest tests/test_clock_s.py -v
"""
import random

import pytest

from src.constants import COMP0, COMP1, FB0, FB1
from src.registers import clock_s


def comp0(i):
    """COMP0_i. Đặc tả chỉ có COMP0 cho 1 <= i <= 98 (98 giá trị).
    Nếu nhóm lưu bảng dài 100 (có chỗ đệm) thì dùng thẳng chỉ số i.
    Nếu cách lưu của nhóm khác hai kiểu này, chỉ cần sửa ở đây."""
    return COMP0[i - 1] if len(COMP0) == 98 else COMP0[i]


def comp1(i):
    """COMP1_i, cùng quy ước với comp0."""
    return COMP1[i - 1] if len(COMP1) == 98 else COMP1[i]


def fb(ctrl):
    return FB1 if ctrl else FB0


def ones_at(*positions):
    state = [0] * 100
    for pos in positions:
        state[pos] = 1
    return state


def spec_clock_s(S, inp, ctrl):
    """Oracle viết lại từ công thức đặc tả, để đối chiếu hàng loạt trạng thái."""
    feedback = S[99] ^ inp
    hat = [0] * 100
    for i in range(1, 99):
        hat[i] = S[i - 1] ^ ((S[i] ^ comp0(i)) & (S[i + 1] ^ comp1(i)))
    hat[99] = S[98]
    table = fb(ctrl)
    return [hat[i] ^ (table[i] & feedback) for i in range(100)]


def random_states(count, seed=2026):
    rng = random.Random(seed)
    return [[rng.randint(0, 1) for _ in range(100)] for _ in range(count)]


def xor_lists(a, b):
    return [x ^ y for x, y in zip(a, b)]


def test_constant_tables_have_spec_sizes_and_binary_values():
    """FB0, FB1 có đủ 100 giá trị. COMP0, COMP1 có 98 (i = 1..98) hoặc 100 nếu có đệm."""
    assert len(FB0) == 100
    assert len(FB1) == 100
    assert len(COMP0) in (98, 100)
    assert len(COMP1) in (98, 100)
    for table in (COMP0, COMP1, FB0, FB1):
        assert set(table) <= {0, 1}


@pytest.mark.parametrize("ctrl", [0, 1])
def test_all_zero_state_without_input_leaves_only_comp_product(ctrl):
    """S toàn 0, INPUT = 0: feedback = 0, S^_i = COMP0_i AND COMP1_i với 1 <= i <= 98."""
    expected = [0] + [comp0(i) & comp1(i) for i in range(1, 99)] + [0]
    assert clock_s([0] * 100, 0, ctrl) == expected


@pytest.mark.parametrize("ctrl", [0, 1])
def test_position_0_is_only_the_feedback_term(ctrl):
    """S^_0 = 0 nên s'_0 = FB_ctrl[0] AND feedback."""
    for state in random_states(20):
        for inp in (0, 1):
            feedback = state[99] ^ inp
            assert clock_s(state, inp, ctrl)[0] == (fb(ctrl)[0] & feedback)


@pytest.mark.parametrize("ctrl", [0, 1])
def test_position_99_takes_s98_plus_feedback_term(ctrl):
    """S^_99 = s98 nên s'_99 = s98 XOR (FB_ctrl[99] AND feedback)."""
    for state in random_states(20):
        for inp in (0, 1):
            feedback = state[99] ^ inp
            expected = state[98] ^ (fb(ctrl)[99] & feedback)
            assert clock_s(state, inp, ctrl)[99] == expected


@pytest.mark.parametrize("a", [0, 1])
@pytest.mark.parametrize("b", [0, 1])
@pytest.mark.parametrize("i", [1, 2, 50, 97, 98])
def test_nonlinear_term_is_an_and_of_the_two_xors(i, a, b):
    """Đặt s_{i-1} = 0, s_i = COMP0_i XOR a, s_{i+1} = COMP1_i XOR b, feedback = 0.
    Khi đó s'_i = a AND b. Ca (1,1) cho 1, ba ca còn lại cho 0 — bắt được lỗi
    nhầm AND thành OR hoặc XOR."""
    state = [0] * 100
    state[i] = comp0(i) ^ a
    state[i + 1] = comp1(i) ^ b
    inp = state[99]  # feedback = s99 XOR inp = 0, nên FB không tác động
    result = clock_s(state, inp, 0)
    assert result[i] == (a & b)
    assert clock_s(state, inp, 1)[i] == (a & b)


@pytest.mark.parametrize("ctrl", [0, 1])
def test_flipping_input_xors_the_fb_table(ctrl):
    """S^ không phụ thuộc INPUT, chỉ feedback phụ thuộc. Đổi INPUT 0 -> 1 làm
    đảo feedback, nên kết quả đổi đúng bằng bảng FB tương ứng."""
    for state in random_states(30):
        diff = xor_lists(clock_s(state, 0, ctrl), clock_s(state, 1, ctrl))
        assert diff == fb(ctrl)


def test_control_has_no_effect_when_feedback_is_zero():
    """feedback = 0 thì FB0 và FB1 đều không được cộng vào, ctrl không đổi kết quả."""
    for state in random_states(30):
        inp = state[99]  # feedback = 0
        assert clock_s(state, inp, 0) == clock_s(state, inp, 1)


def test_control_selects_fb0_or_fb1_when_feedback_is_one():
    """feedback = 1: hai kết quả của ctrl = 0 và ctrl = 1 khác nhau đúng FB0 XOR FB1."""
    for state in random_states(30):
        inp = state[99] ^ 1  # feedback = 1
        diff = xor_lists(clock_s(state, inp, 0), clock_s(state, inp, 1))
        assert diff == xor_lists(FB0, FB1)



@pytest.mark.parametrize("position", [0, 1, 2, 49, 50, 97, 98, 99])
@pytest.mark.parametrize("inp", [0, 1])
@pytest.mark.parametrize("ctrl", [0, 1])
def test_single_bit_matches_spec(position, inp, ctrl):
    state = ones_at(position)
    assert clock_s(state, inp, ctrl) == spec_clock_s(state, inp, ctrl)


def test_all_zero_matches_spec():
    for inp in (0, 1):
        for ctrl in (0, 1):
            assert clock_s([0] * 100, inp, ctrl) == spec_clock_s([0] * 100, inp, ctrl)


def test_all_ones_matches_spec():
    state = [1] * 100
    for inp in (0, 1):
        for ctrl in (0, 1):
            assert clock_s(state, inp, ctrl) == spec_clock_s(state, inp, ctrl)


def test_random_states_match_spec():
    """300 trạng thái ngẫu nhiên (seed cố định nên chạy lại vẫn ra cùng kết quả)."""
    for state in random_states(300):
        for inp in (0, 1):
            for ctrl in (0, 1):
                assert clock_s(state, inp, ctrl) == spec_clock_s(state, inp, ctrl)



def test_output_is_100_binary_bits():
    result = clock_s([(i + 1) % 2 for i in range(100)], 1, 1)
    assert len(result) == 100
    assert set(result) <= {0, 1}


def test_input_register_is_not_modified():
    state = random_states(1)[0]
    original = state.copy()
    clock_s(state, 1, 1)
    assert state == original
