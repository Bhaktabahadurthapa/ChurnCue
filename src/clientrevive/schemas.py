"""Domain schemas and boundary constants."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

HIGH_RISK_THRESHOLD = 0.75
MEDIUM_RISK_THRESHOLD = 0.45


class CustomerRecord(BaseModel):
    """Loose customer row with strict key/value boundary validation."""

    model_config = ConfigDict(extra="allow")
    customer_id: str = Field(min_length=1, max_length=100)

    @field_validator("customer_id")
    @classmethod
    def anonymous_id(cls, value: str) -> str:
        if not value.startswith("CUST-"):
            raise ValueError("customer_id must be an anonymous CUST- identifier")
        return value


class ScoredCustomer(BaseModel):
    model_config = ConfigDict(extra="allow")
    customer_id: str = Field(min_length=1, max_length=100)
    churn_probability: float = Field(ge=0, le=1)
    risk_level: Literal["High", "Medium", "Low"]
    monthly_revenue: float = Field(ge=0)
    annual_revenue_at_risk: float = Field(ge=0)
    top_risk_factors: list[str] = Field(max_length=10)
    previous_risk: float | None = Field(default=None, ge=0, le=1)


def risk_level(probability: float) -> str:
    if probability >= HIGH_RISK_THRESHOLD:
        return "High"
    if probability >= MEDIUM_RISK_THRESHOLD:
        return "Medium"
    return "Low"


JsonDict = dict[str, Any]
