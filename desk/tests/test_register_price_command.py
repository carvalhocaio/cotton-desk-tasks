from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from desk.models import PriceIndex


@pytest.mark.django_db
def test_register_price_command_enqueues_and_persists_the_reading():
    output = StringIO()

    call_command("register_price", "ICE-CT2", "82.35", "2026-04-15", stdout=output)

    assert "Enqueued" in output.getvalue()
    reading = PriceIndex.objects.get(code="ICE-CT2")
    assert reading.value == Decimal("82.35")
