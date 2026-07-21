import io

import pytest
from django.urls import reverse

from desk.models import LaudoHVI


@pytest.mark.django_db
def test_upload_lote_cria_fardos_laudos_e_enfileira_uma_task_por_linha(client):
    csv_conteudo = (
        "codigo,safra,produtor,peso_kg,data_classificacao,"
        "micronaire,comprimento,resistencia,uniformidade\n"
        "BR2026001100,2025/2026,Fazenda Bom Futuro,218.00,2026-04-20,4.20,1.16,29.0,82.0\n"
        "BR2026001101,2025/2026,Fazenda Bom Futuro,221.00,2026-04-20,2.00,1.16,29.0,82.0\n"
    )
    arquivo = io.BytesIO(csv_conteudo.encode("utf-8"))
    arquivo.name = "laudos.csv"

    resposta = client.post(reverse("upload_lote_laudos"), {"arquivo": arquivo})
    corpo = resposta.json()

    assert resposta.status_code == 202
    assert corpo["criados"] == 2
    assert len(corpo["task_ids"]) == 2
    assert LaudoHVI.objects.filter(fardo__codigo="BR2026001100").exists()
    assert LaudoHVI.objects.filter(fardo__codigo="BR2026001101").exists()
