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


@pytest.mark.django_db
def test_checkout_without_required_fields_returns_400(client):
    response = client.post(reverse("checkout"), {"buyer": "Boa Vista Textile"})

    assert response.status_code == 400
    error = response.json()["error"]
    assert "bale_id" in error
    assert "price_per_kg" in error


@pytest.mark.django_db
def test_checkout_with_unparseable_price_returns_400(client, bale):
    response = client.post(
        reverse("checkout"),
        {"bale_id": bale.id, "buyer": "Boa Vista Textile", "price_per_kg": "six reais"},
    )

    assert response.status_code == 400
    assert "price_per_kg" in response.json()["error"]


@pytest.mark.django_db
def test_checkout_with_unknown_bale_returns_404(client):
    response = client.post(
        reverse("checkout"),
        {"bale_id": 999999, "buyer": "Boa Vista Textile", "price_per_kg": "6.85"},
    )

    assert response.status_code == 404
