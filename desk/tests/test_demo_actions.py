import pytest
from django.urls import reverse

from desk.models import Contract, PriceIndex


@pytest.mark.django_db
def test_demo_report_enqueues_generate_season_report(client):
    response = client.post(reverse("demo_report"), {"season": "2025/2026"})

    assert response.status_code == 202
    assert "task_id" in response.json()


@pytest.mark.django_db
def test_demo_price_enqueues_record_index_reading(client):
    response = client.post(reverse("demo_price"))

    assert response.status_code == 202
    assert "task_id" in response.json()
    assert PriceIndex.objects.filter(code="ICE-CT2").exists()


@pytest.mark.django_db
def test_demo_contract_closes_contract_with_most_recent_bale(client, bale):
    response = client.post(reverse("demo_contract"))

    assert response.status_code == 201
    assert Contract.objects.filter(bale=bale).exists()


@pytest.mark.django_db
def test_demo_contract_without_available_bale_returns_error(client):
    response = client.post(reverse("demo_contract"))

    assert response.status_code == 409
    assert "error" in response.json()


def test_demo_slow_enqueues_demo_task(client):
    response = client.post(reverse("demo_slow"))

    assert response.status_code == 202
    assert "task_id" in response.json()
