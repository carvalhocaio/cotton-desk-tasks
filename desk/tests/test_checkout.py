from unittest.mock import patch

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_checkout_ingenuo_espera_enqueue_logo_apos_o_post(client, fardo):
    """Teste proposital 'ingênuo': espera que o enqueue já tenha
    acontecido assim que o POST retorna a resposta.
    """
    with patch("desk.views.confirmar_contrato.enqueue") as enqueue_mock:
        resposta = client.post(
            reverse("checkout"),
            {"fardo_id": fardo.id, "comprador": "Têxtil Boa Vista", "preco_por_kg": "6.85"},
        )

    assert resposta.status_code == 201
    enqueue_mock.assert_called_once()
