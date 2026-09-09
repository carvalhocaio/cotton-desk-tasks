import pytest

from desk.domain import HVIParameters, MicronaireOutOfRange
from desk.models import Bale, HVIReport


@pytest.mark.django_db
def test_valid_hvi_report_converts_to_hviparameters():
    bale = Bale.objects.create(
        code="BR2026000123",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="220.50",
        classification_date="2026-03-15",
    )
    report = HVIReport.objects.create(
        bale=bale,
        micronaire="4.20",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    parameters = report.to_domain()

    assert parameters == HVIParameters(
        micronaire=4.2, length=1.16, strength=29.0, uniformity=82.0
    )


@pytest.mark.django_db
def test_hvi_report_with_invalid_micronaire_saves_but_raises_error_on_convert():
    bale = Bale.objects.create(
        code="BR2026000124",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="215.00",
        classification_date="2026-03-15",
    )
    report = HVIReport.objects.create(
        bale=bale,
        micronaire="2.00",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    with pytest.raises(MicronaireOutOfRange):
        report.to_domain()
