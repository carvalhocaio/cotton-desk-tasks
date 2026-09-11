import io

import pytest
from django.urls import reverse

from desk import views
from desk.models import Bale, HVIReport

HEADER = (
    "code,season,producer,weight_kg,classification_date,"
    "micronaire,length,strength,uniformity\n"
)


def csv_file(content, name="reports.csv"):
    file = io.BytesIO(content.encode("utf-8"))
    file.name = name
    return file


@pytest.mark.django_db
def test_upload_batch_creates_bales_reports_and_enqueues_one_task_per_row(
    client, django_capture_on_commit_callbacks
):
    content = HEADER + (
        "BR2026001100,2025/2026,Bom Futuro Farm,218.00,2026-04-20,4.20,1.16,29.0,82.0\n"
        "BR2026001101,2025/2026,Bom Futuro Farm,221.00,2026-04-20,2.00,1.16,29.0,82.0\n"
    )

    with django_capture_on_commit_callbacks() as callbacks:
        response = client.post(
            reverse("upload_report_batch"), {"file": csv_file(content)}
        )
    body = response.json()

    assert response.status_code == 202
    assert body["created"] == 2
    assert len(body["report_ids"]) == 2
    # One summary scheduled per row, and only after the batch committed.
    assert len(callbacks) == 2
    assert HVIReport.objects.filter(bale__code="BR2026001100").exists()
    assert HVIReport.objects.filter(bale__code="BR2026001101").exists()


@pytest.mark.django_db
def test_upload_batch_without_file_returns_400(client):
    response = client.post(reverse("upload_report_batch"))

    assert response.status_code == 400
    assert "missing file" in response.json()["error"]


@pytest.mark.django_db
def test_upload_batch_with_missing_column_returns_400_naming_it(client):
    content = "code,season,producer\nBR2026001200,2025/2026,Bom Futuro Farm\n"

    response = client.post(reverse("upload_report_batch"), {"file": csv_file(content)})

    assert response.status_code == 400
    assert "micronaire" in response.json()["error"]
    assert not Bale.objects.exists()


@pytest.mark.django_db
def test_upload_batch_over_the_row_cap_persists_nothing(
    client, monkeypatch, django_capture_on_commit_callbacks
):
    """The cap has to roll back like any other refusal.

    Returning early from inside transaction.atomic() exits the block with no
    exception, which commits — so a rejected batch would answer 400 and still
    persist every row it had written up to the limit.
    """
    monkeypatch.setattr(views, "MAX_CSV_ROWS", 2)
    content = HEADER + "".join(
        f"BR202600{i:04d},2025/2026,Farm,218.00,2026-04-20,4.20,1.16,29.0,82.0\n"
        for i in range(3)
    )

    with django_capture_on_commit_callbacks() as callbacks:
        response = client.post(
            reverse("upload_report_batch"), {"file": csv_file(content)}
        )

    assert response.status_code == 400
    assert "row limit" in response.json()["error"]
    assert not Bale.objects.exists()
    assert not HVIReport.objects.exists()
    assert callbacks == []


@pytest.mark.django_db
def test_upload_batch_with_invalid_row_rolls_the_whole_batch_back(client):
    content = HEADER + (
        "BR2026001300,2025/2026,Bom Futuro Farm,218.00,2026-04-20,4.20,1.16,29.0,82.0\n"
        "BR2026001301,2025/2026,Bom Futuro Farm,221.00,not-a-date,4.20,1.16,29.0,82.0\n"
    )

    response = client.post(reverse("upload_report_batch"), {"file": csv_file(content)})

    assert response.status_code == 400
    assert "line 3" in response.json()["error"]
    # The good first row must not survive a failed batch.
    assert not Bale.objects.exists()
    assert not HVIReport.objects.exists()
