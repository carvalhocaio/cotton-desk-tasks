import time
from decimal import Decimal

from django.tasks import task

from desk.domain import InvalidHVIParameter
from desk.extraction import extract_confirmation_data
from desk.models import Bale, Contract, HVIReport, PriceIndex


@task(queue_name="hvi_reports", priority=50)
def summarize_report(report_id: int) -> str:
    """Summarizes an HVI report from its validated domain parameters."""
    report = HVIReport.objects.get(pk=report_id)
    parameters = report.to_domain()
    return (
        f"Bale {report.bale.code}: micronaire {parameters.micronaire}, "
        f'length {parameters.length}", '
        f"strength {parameters.strength} gf/tex, "
        f"uniformity {parameters.uniformity}%"
    )


@task(queue_name="season_reports", priority=-10)
def generate_season_report(season: str) -> str:
    """Consolidates how many reports from a season are commercially valid."""
    reports = HVIReport.objects.filter(bale__season=season)
    total = reports.count()
    valid = 0
    invalid = 0
    for report in reports:
        try:
            report.to_domain()
            valid += 1
        except InvalidHVIParameter:
            invalid += 1
    return f"Season {season}: {total} report(s), {valid} valid, {invalid} invalid"


@task(queue_name="confirmations", priority=50)
def confirm_contract(contract_id: int) -> str:
    """Generates the textual confirmation of a newly closed contract."""
    contract = Contract.objects.select_related("bale").get(pk=contract_id)
    return (
        f"Contract for bale {contract.bale.code} confirmed with "
        f"{contract.buyer} at R$ {contract.price_per_kg}/kg"
    )


@task(queue_name="prices", priority=0)
def record_index_reading(code: str, value: str, trading_date: str) -> str:
    """Persists a price index reading.

    `value` arrives as a string, not Decimal: task arguments go through
    JSON serialization in `.enqueue()`, and Decimal doesn't survive that
    round-trip — the caller needs to convert it before calling this task.
    """
    reading, _created = PriceIndex.objects.update_or_create(
        code=code,
        trading_date=trading_date,
        defaults={"value": Decimal(value)},
    )
    return f"{reading.code} on {reading.trading_date}: R$ {reading.value}"


@task(queue_name="confirmations", priority=30)
def extract_confirmation(text: str) -> str:
    """Extracts data from free text, creates the Contract, and schedules the formal confirmation.

    If the bale mentioned in the text doesn't exist, the task fails with
    `Bale.DoesNotExist` — an LLM can hallucinate or get the code wrong, and
    this must show up as a real failure, not be swallowed silently.
    """
    data = extract_confirmation_data(text)
    bale = Bale.objects.get(code=data.bale_code)
    contract = Contract.objects.create(
        bale=bale,
        buyer=data.buyer,
        price_per_kg=Decimal(data.price_per_kg),
    )
    confirm_contract.enqueue(contract.id)
    return f"Contract {contract.id} created: bale {bale.code}, buyer {contract.buyer}"


@task(queue_name="demo", priority=0)
def demo_task() -> str:
    """Artificially slow task, just so the dashboard can show the 'running' state.

    The `sleep` here is intentional and honest: simulating latency IS this
    task's purpose. It plays no business role — it exists only to make the
    READY → RUNNING → SUCCESSFUL transition visible on the dashboard, which
    happens too fast to see with the real (fast) tasks.
    """
    time.sleep(4)
    return "demo completed after 4s of simulated execution"
