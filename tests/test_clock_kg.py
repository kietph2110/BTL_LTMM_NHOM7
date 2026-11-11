"""Kiểm thử CLOCK_KG và các bit trung gian trả về cho trace.

Theo đặc tả eSTREAM (mickey_p3):

    CONTROL_BIT_R = s34 XOR r67
    CONTROL_BIT_S = s67 XOR r33
    INPUT_BIT_R   = INPUT_BIT XOR s50   nếu MIXING, ngược lại = INPUT_BIT
    INPUT_BIT_S   = INPUT_BIT

Chạy: python -m pytest tests/test_clock_kg.py -v
"""
import random

import pytest

from src.mickey2 import clock_kg, clock_kg_step
from src.registers import clock_r, clock_s


def ones_at(*positions):
    state = [0] * 100
    for pos in positions:
        state[pos] = 1
    return state


def random_state(rng):
    return [rng.randint(0, 1) for _ in range(100)]


@pytest.mark.parametrize("seed", range(20))
@pytest.mark.parametrize("mixing", [False, True])
@pytest.mark.parametrize("inp", [0, 1])
def test_step_gives_same_registers_as_clock_kg(seed, mixing, inp):
    rng = random.Random(seed)
    R, S = random_state(rng), random_state(rng)
    step = clock_kg_step(R, S, mixing, inp)
    assert (step.R, step.S) == clock_kg(R, S, mixing, inp)


@pytest.mark.parametrize("seed", range(20))
def test_step_matches_spec(seed):
    rng = random.Random(seed)
    R, S = random_state(rng), random_state(rng)
    mixing, inp = rng.randint(0, 1), rng.randint(0, 1)

    ctrl_r = S[34] ^ R[67]
    ctrl_s = S[67] ^ R[33]
    inp_r = inp ^ S[50] if mixing else inp

    step = clock_kg_step(R, S, mixing, inp)
    assert step.ctrl_r == ctrl_r
    assert step.ctrl_s == ctrl_s
    assert step.fb_r == R[99] ^ inp_r
    assert step.fb_s == S[99] ^ inp
    assert step.R == clock_r(R, inp_r, ctrl_r)
    assert step.S == clock_s(S, inp, ctrl_s)


def test_ctrl_r_uses_s34_and_r67():
    assert clock_kg_step(ones_at(67), [0] * 100, False, 0).ctrl_r == 1
    assert clock_kg_step([0] * 100, ones_at(34), False, 0).ctrl_r == 1
    assert clock_kg_step(ones_at(67), ones_at(34), False, 0).ctrl_r == 0


def test_ctrl_s_uses_s67_and_r33():
    assert clock_kg_step(ones_at(33), [0] * 100, False, 0).ctrl_s == 1
    assert clock_kg_step([0] * 100, ones_at(67), False, 0).ctrl_s == 1
    assert clock_kg_step(ones_at(33), ones_at(67), False, 0).ctrl_s == 0


def test_mixing_feeds_s50_into_r_only():
    S = ones_at(50)
    on = clock_kg_step([0] * 100, S, True, 0)
    off = clock_kg_step([0] * 100, S, False, 0)
    assert on.fb_r == 1 and off.fb_r == 0
    assert on.fb_s == off.fb_s == 0


def test_feedback_uses_bit_99():
    step = clock_kg_step(ones_at(99), ones_at(99), False, 1)
    assert step.fb_r == 0
    assert step.fb_s == 0


def test_all_zero_with_zero_input_stays_zero():
    step = clock_kg_step([0] * 100, [0] * 100, True, 0)
    assert step.R == [0] * 100
    assert (step.ctrl_r, step.ctrl_s, step.fb_r, step.fb_s) == (0, 0, 0, 0)


def test_inputs_are_not_modified():
    R, S = ones_at(0, 33, 67, 99), ones_at(34, 50, 67, 99)
    R0, S0 = R[:], S[:]
    clock_kg_step(R, S, True, 1)
    assert R == R0 and S == S0
