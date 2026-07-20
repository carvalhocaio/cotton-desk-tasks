from django.db import models


class Fardo(models.Model):
    """Um fardo físico de algodão, identificado e rastreável desde o beneficiamento."""

    codigo = models.CharField(max_length=20, unique=True)
    safra = models.CharField(max_length=9)  # ex.: "2025/2026"
    produtor = models.CharField(max_length=120)
    peso_kg = models.DecimalField(max_digits=6, decimal_places=2)
    data_classificacao = models.DateField()

    def __str__(self) -> str:
        return f"Fardo {self.codigo} ({self.safra})"
