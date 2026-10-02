from datetime import datetime
from pydantic import BaseModel, Field


class InteractionCreate(BaseModel):
    customer_id: str | None = Field(default=None, max_length=20)
    channel: str = Field(pattern="^(email|phone|chat|meeting|other)$")
    subject: str = Field(min_length=2, max_length=160)
    notes: str | None = Field(default=None, max_length=4000)
    sentiment: str = Field(default="neutral", pattern="^(positive|neutral|negative)$")
    status: str = Field(default="open", pattern="^(open|follow-up|resolved)$")


class InteractionResponse(InteractionCreate):
    id: int
    user_id: int
    created_at: datetime
    model_config = {"from_attributes": True}
