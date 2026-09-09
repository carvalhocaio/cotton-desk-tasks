import io

import pytest
from django.urls import reverse

from desk.models import HVIReport


@pytest.mark.django_db
def test_upload_batch_creates_bales_reports_and_enqueues_one_task_per_row(client):
    csv_content = (
        "code,season,producer,weight_kg,classification_date,"
        "micronaire,length,strength,uniformity\n"
        "BR2026001100,2025/2026,Bom Futuro Farm,218.00,2026-04-20,4.20,1.16,29.0,82.0\n"
        "BR2026001101,2025/2026,Bom Futuro Farm,221.00,2026-04-20,2.00,1.16,29.0,82.0\n"
    )
    file = io.BytesIO(csv_content.encode("utf-8"))
    file.name = "reports.csv"

    response = client.post(reverse("upload_report_batch"), {"file": file})
    body = response.json()

    assert response.status_code == 202
    assert body["created"] == 2
    assert len(body["task_ids"]) == 2
    assert HVIReport.objects.filter(bale__code="BR2026001100").exists()
    assert HVIReport.objects.filter(bale__code="BR2026001101").exists()
