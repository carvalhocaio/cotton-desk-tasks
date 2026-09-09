import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_checkout_registers_confirmation_to_run_after_commit(
    client, bale, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks() as callbacks:
        response = client.post(
            reverse("checkout"),
            {
                "bale_id": bale.id,
                "buyer": "Boa Vista Textile",
                "price_per_kg": "6.85",
            },
        )

    assert response.status_code == 201
    assert len(callbacks) == 1
