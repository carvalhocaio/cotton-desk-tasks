from django.db import models

from desk.domain import HVIParameters


class Bale(models.Model):
    """A physical cotton bale, identified and traceable from ginning onward."""

    code = models.CharField(max_length=20, unique=True)
    season = models.CharField(max_length=9)  # e.g.: "2025/2026"
    producer = models.CharField(max_length=120)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    classification_date = models.DateField()

    def __str__(self) -> str:
        return f"Bale {self.code} ({self.season})"


class HVIReport(models.Model):
    """HVI classification report issued by the lab for a bale.

    The report is saved as the lab issued it, even if the values are
    outside the commercial range — business validation only happens when
    converting to `HVIParameters` via `to_domain()`.
    """

    bale = models.ForeignKey(Bale, on_delete=models.CASCADE, related_name="reports")
    micronaire = models.DecimalField(max_digits=3, decimal_places=2)
    length = models.DecimalField(max_digits=4, decimal_places=2)
    strength = models.DecimalField(max_digits=4, decimal_places=1)
    uniformity = models.DecimalField(max_digits=4, decimal_places=1)
    issue_date = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return f"HVI report for bale {self.bale.code}"

    def to_domain(self) -> HVIParameters:
        """Converts the raw database fields into the validated domain value object.

        The fields are already `Decimal`, so nothing is converted on the way
        in — the reading the lab issued is the reading the domain validates.
        """
        return HVIParameters(
            micronaire=self.micronaire,
            length=self.length,
            strength=self.strength,
            uniformity=self.uniformity,
        )


class Contract(models.Model):
    """Sale contract for a bale to a buyer."""

    bale = models.ForeignKey(Bale, on_delete=models.CASCADE, related_name="contracts")
    buyer = models.CharField(max_length=120)
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2)
    closing_date = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Contract for bale {self.bale.code} with {self.buyer}"


class PriceIndex(models.Model):
    """Daily reading of a cotton reference price index."""

    code = models.CharField(max_length=20)  # e.g.: "ICE-CT2", "CEPEA-8DAYS"
    value = models.DecimalField(max_digits=8, decimal_places=2)
    trading_date = models.DateField()

    class Meta:
        unique_together = ("code", "trading_date")

    def __str__(self) -> str:
        return f"{self.code} on {self.trading_date}: {self.value}"
