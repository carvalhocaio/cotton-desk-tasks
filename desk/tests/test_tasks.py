import pytest
from django.tasks import TaskResultStatus

from desk.models import Bale, Contract, HVIReport
from desk.tasks import confirm_contract, summarize_report


@pytest.mark.django_db
def test_summarize_report_with_valid_report_returns_summary_and_successful_status():
    bale = Bale.objects.create(
        code="BR2026000200",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="218.00",
        classification_date="2026-03-20",
    )
    report = HVIReport.objects.create(
        bale=bale,
        micronaire="4.20",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    result = summarize_report.enqueue(report.id)

    assert result.status == TaskResultStatus.SUCCESSFUL
    assert "BR2026000200" in result.return_value


@pytest.mark.django_db
def test_confirm_contract_with_valid_contract_returns_confirmation_and_successful_status():
    bale = Bale.objects.create(
        code="BR2026000800",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="219.00",
        classification_date="2026-04-10",
    )
    contract = Contract.objects.create(
        bale=bale,
        buyer="Boa Vista Textile",
        price_per_kg="6.85",
    )

    result = confirm_contract.enqueue(contract.id)

    assert result.status == TaskResultStatus.SUCCESSFUL
    assert "BR2026000800" in result.return_value
    assert "Boa Vista Textile" in result.return_value
