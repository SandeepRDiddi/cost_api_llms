from cost_explorer.parsing import money_to_float, split_labeled_money_values


def test_money_to_float():
    assert money_to_float("$1.25") == 1.25
    assert money_to_float("5,000 prompts then $14 / 1,000 search queries") == 14.0
    assert money_to_float("Not available") is None


def test_split_labeled_money_values():
    assert split_labeled_money_values("$0.25 (text / image / video) $0.50 (audio)") == [
        ("text / image / video", 0.25),
        ("audio", 0.50),
    ]
    assert split_labeled_money_values("$1.50") == [("default", 1.50)]
