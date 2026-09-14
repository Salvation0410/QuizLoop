def is_correct_answer(correct: list[str], selected: list[str]) -> bool:
    return len(selected) == len(set(selected)) and set(correct) == set(selected)


def reward_for(correct_count: int, total: int) -> tuple[int, int]:
    if total <= 0 or correct_count < 0 or correct_count > total:
        raise ValueError("invalid score")
    return correct_count * 12, correct_count * 5
