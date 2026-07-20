from django.db import models

from desk.domain import HVIParametros


class Fardo(models.Model):
    """Um fardo físico de algodão, identificado e rastreável desde o beneficiamento."""

    codigo = models.CharField(max_length=20, unique=True)
    safra = models.CharField(max_length=9)  # ex.: "2025/2026"
    produtor = models.CharField(max_length=120)
    peso_kg = models.DecimalField(max_digits=6, decimal_places=2)
    data_classificacao = models.DateField()

    def __str__(self) -> str:
        return f"Fardo {self.codigo} ({self.safra})"


class LaudoHVI(models.Model):
    """Laudo de classificação HVI emitido pelo laboratório para um fardo.

    O laudo é salvo como o laboratório o emitiu, mesmo que os valores
    estejam fora da faixa comercial — a validação de negócio só acontece
    ao converter para `HVIParametros` via `to_dominio()`.
    """

    fardo = models.ForeignKey(Fardo, on_delete=models.CASCADE, related_name="laudos")
    micronaire = models.DecimalField(max_digits=3, decimal_places=2)
    comprimento = models.DecimalField(max_digits=4, decimal_places=2)
    resistencia = models.DecimalField(max_digits=4, decimal_places=1)
    uniformidade = models.DecimalField(max_digits=4, decimal_places=1)
    data_emissao = models.DateField(auto_now_add=True)

    def to_dominio(self) -> HVIParametros:
        """Converte os campos brutos do banco no value object de domínio validado."""
        return HVIParametros(
            micronaire=float(self.micronaire),
            comprimento=float(self.comprimento),
            resistencia=float(self.resistencia),
            uniformidade=float(self.uniformidade),
        )

    def __str__(self) -> str:
        return f"Laudo HVI do fardo {self.fardo.codigo}"


class Contrato(models.Model):
    """Contrato de venda de um fardo para um comprador."""

    fardo = models.ForeignKey(Fardo, on_delete=models.CASCADE, related_name="contratos")
    comprador = models.CharField(max_length=120)
    preco_por_kg = models.DecimalField(max_digits=6, decimal_places=2)
    data_fechamento = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Contrato do fardo {self.fardo.codigo} com {self.comprador}"


class IndicePreco(models.Model):
    """Leitura diária de um índice de preço de referência do algodão."""

    codigo = models.CharField(max_length=20) # ex.: "ICE-CT2", "CEPEA-8DIAS"
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    data_pregao = models.DateField()

    class Meta:
        unique_together = ("codigo", "data_pregao")

    def __str__(self) -> str:
        return f"{self.codigo} em {self.data_pregao}: {self.valor}"
