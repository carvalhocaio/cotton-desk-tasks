import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_checkout_registra_confirmacao_para_rodar_apos_commit(
    client, fardo, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks() as callbacks:
        resposta = client.post(
            reverse("checkout"),
            {
                "fardo_id": fardo.id,
                "comprador": "Têxtil Boa Vista",
                "preco_por_kg": "6.85",
            },
        )

    assert resposta.status_code == 201
    assert len(callbacks) == 1
