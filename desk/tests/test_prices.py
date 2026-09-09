from decimal import Decimal

import pytest
from django.tasks import TaskResultStatus

from desk.models import PriceIndex
from desk.tasks import record_index_reading


def test_enqueue_with_raw_decimal_fails_serialization():
    """Documents the gotcha: Decimal doesn't survive enqueue's JSON serialization."""
    with pytest.raises(TypeError):
        record_index_reading.enqueue("ICE-CT2", Decimal("82.35"), "2026-04-10")


@pytest.mark.django_db
def test_record_index_reading_with_value_as_string_persists_as_decimal():
    result = record_index_reading.enqueue("ICE-CT2", "82.35", "2026-04-10")

    assert result.status == TaskResultStatus.SUCCESSFUL
    reading = PriceIndex.objects.get(code="ICE-CT2")
    assert reading.value == Decimal("82.35")
