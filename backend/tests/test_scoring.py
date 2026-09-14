import pytest

from app.domain.scoring import is_correct_answer, reward_for


@pytest.mark.parametrize(
    ("correct", "selected", "expected"),
    [
        (["A"], ["A"], True),
        (["A", "C"], ["C", "A"], True),
        (["A", "C"], ["A"], False),
        (["A"], ["Z"], False),
    ],
)
def test_answers_are_scored_as_sets(correct, selected, expected):
    assert is_correct_answer(correct, selected) is expected


def test_rewards_only_count_correct_answers():
    assert reward_for(5, 5) == (60, 25)
    assert reward_for(2, 5) == (24, 10)
    assert reward_for(0, 5) == (0, 0)
