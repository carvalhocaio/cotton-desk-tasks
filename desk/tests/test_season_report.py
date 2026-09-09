import pytest
from django.tasks import TaskResultStatus

from desk.models import Bale, HVIReport
from desk.tasks import generate_season_report


@pytest.mark.django_db
def test_generate_season_report_counts_valid_and_invalid_reports():
    valid_bale = Bale.objects.create(
        code="BR2026000600",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="220.00",
        classification_date="2026-04-01",
    )
    invalid_bale = Bale.objects.create(
        code="BR2026000601",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="215.00",
        classification_date="2026-04-01",
    )
    HVIReport.objects.create(
        bale=valid_bale,
        micronaire="4.20",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )
    HVIReport.objects.create(
        bale=invalid_bale,
        micronaire="2.00",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    result = generate_season_report.enqueue("2025/2026")

    assert result.status == TaskResultStatus.SUCCESSFUL
    assert result.return_value == "Season 2025/2026: 2 report(s), 1 valid, 1 invalid"
