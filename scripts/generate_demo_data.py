"""Generate anonymous, reproducible demo customer churn data."""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
ROW_COUNT = 500


def generate_demo_data(row_count: int = ROW_COUNT, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    plan = rng.choice(["Starter", "Growth", "Enterprise"], row_count, p=[0.48, 0.35, 0.17])
    base_revenue = {"Starter": 149, "Growth": 649, "Enterprise": 2_400}
    revenue = np.array([base_revenue[value] for value in plan]) * rng.lognormal(0, 0.28, row_count)
    age = rng.integers(2, 97, row_count)
    renewal = rng.integers(1, 366, row_count)
    logins = np.clip(rng.poisson(19, row_count), 0, 80)
    usage_drop = np.clip(rng.normal(18, 18, row_count), 0, 90)
    days_since_login = np.clip(rng.gamma(2, 6, row_count), 0, 90).round()
    tickets = np.clip(rng.poisson(1.8, row_count), 0, 12)
    unresolved = np.array([rng.integers(0, value + 1) for value in tickets])
    payment_failures = np.clip(rng.poisson(0.35, row_count), 0, 5)
    satisfaction = np.clip(rng.normal(7.2, 1.6, row_count), 1, 10)

    logit = (
        -3.5
        + 0.035 * usage_drop
        + 0.75 * payment_failures
        + 0.43 * unresolved
        + 0.027 * days_since_login
        - 0.30 * (satisfaction - 5)
        + 0.85 * (renewal <= 30)
        - 0.025 * logins
        - 0.006 * age
        + rng.normal(0, 0.35, row_count)
    )
    probability = 1 / (1 + np.exp(-logit))
    churned = rng.binomial(1, probability)
    previous = np.clip(probability + rng.normal(-0.015, 0.11, row_count), 0.01, 0.99)

    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{1001 + index}" for index in range(row_count)],
            "plan": plan,
            "monthly_revenue": revenue.round(2),
            "account_age_months": age,
            "renewal_days": renewal,
            "logins_30d": logins,
            "usage_drop_percent": usage_drop.round(1),
            "days_since_last_login": days_since_login.astype(int),
            "support_tickets_30d": tickets,
            "unresolved_tickets": unresolved,
            "payment_failures_90d": payment_failures,
            "satisfaction_score": satisfaction.round(1),
            "previous_risk": previous.round(4),
            "churned": churned,
        }
    )


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "data/demo/customer_churn_demo.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    generate_demo_data().to_csv(destination, index=False)
    print(f"Generated {ROW_COUNT} anonymous rows at {destination}")


if __name__ == "__main__":
    main()
