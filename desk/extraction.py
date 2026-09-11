from pydantic import BaseModel, Field
from pydantic_ai import Agent


class ConfirmationData(BaseModel):
    """Fields extracted from a contract confirmation text."""

    bale_code: str = Field(description="Bale code mentioned in the text")
    buyer: str = Field(description="Buyer name mentioned in the text")
    price_per_kg: str = Field(
        description="Price per kg as a decimal string, e.g.: '6.85'"
    )


extraction_agent = Agent(
    "google:gemini-2.5-flash",
    output_type=ConfirmationData,
    system_prompt=(
        "You extract structured data from cotton sale contract confirmations. "
        "Read the free text and return the bale code, the buyer name, and the "
        "price per kg, exactly as they appear in the text."
    ),
    defer_model_check=True,
)


def extract_confirmation_data(text: str) -> ConfirmationData:
    """Uses the PydanticAI agent to extract structured fields from free text."""
    result = extraction_agent.run_sync(text)
    return result.output
