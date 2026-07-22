from scripts.generate_demo_data import generate_demo_data


def test_generation_is_reproducible_and_anonymous():
    first = generate_demo_data()
    second = generate_demo_data()
    assert len(first) == 50
    assert first.equals(second)
    assert first.customer_id.str.match(r"CUST-\d+").all()
    assert set(first.churned) == {0, 1}
    assert not {"name", "email", "phone"} & set(first.columns)


def test_high_signal_group_has_more_churn():
    frame = generate_demo_data(5_000)
    high = frame[(frame.usage_drop_percent >= 30) & (frame.satisfaction_score <= 5)]
    low = frame[(frame.usage_drop_percent < 15) & (frame.satisfaction_score >= 7)]
    assert high.churned.mean() > low.churned.mean()
