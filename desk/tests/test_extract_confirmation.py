from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.tasks import TaskResultStatus

from desk.extraction import ConfirmationData
from desk.models import Contract
from desk.tasks import extract_confirmation


@pytest.mark.django_db
def test_extract_confirmation_creates_contract_and_schedules_confirmation(bale):
    fake_data = ConfirmationData(
        bale_code=bale.code,
        buyer="Boa Vista Textile",
        price_per_kg="6.85",
    )
    confirm_contract_mock = MagicMock()

    with (
        patch("desk.tasks.extract_confirmation_data", return_value=fake_data),
        patch("desk.tasks.confirm_contract", confirm_contract_mock),
    ):
        result = extract_confirmation.enqueue("any text")

    assert result.status == TaskResultStatus.SUCCESSFUL
    contract = Contract.objects.get(bale=bale)
    assert contract.buyer == "Boa Vista Textile"
    assert contract.price_per_kg == Decimal("6.85")
    confirm_contract_mock.enqueue.assert_called_once_with(contract.id)


@pytest.mark.django_db
def test_extract_confirmation_with_nonexistent_bale_fails():
    fake_data = ConfirmationData(
        bale_code="BR-NONEXISTENT-CODE",
        buyer="Boa Vista Textile",
        price_per_kg="6.85",
    )

    with patch("desk.tasks.extract_confirmation_data", return_value=fake_data):
        result = extract_confirmation.enqueue("any text")

    assert result.status == TaskResultStatus.FAILED
    assert result.errors[0].exception_class_path == "desk.models.Bale.DoesNotExist"
