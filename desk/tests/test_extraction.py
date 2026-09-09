from pydantic_ai.models.test import TestModel

from desk.extraction import extract_confirmation_data, extraction_agent


def test_extract_confirmation_data_returns_structured_fields():
    simulated_output = {
        "bale_code": "BR2026001000",
        "buyer": "Boa Vista Textile",
        "price_per_kg": "6.85",
    }

    with extraction_agent.override(
        model=TestModel(custom_output_args=simulated_output)
    ):
        data = extract_confirmation_data(
            "We confirm the purchase of bale BR2026001000 by Boa Vista Textile "
            "at a price of R$ 6.85/kg."
        )

    assert data.bale_code == "BR2026001000"
    assert data.buyer == "Boa Vista Textile"
    assert data.price_per_kg == "6.85"
