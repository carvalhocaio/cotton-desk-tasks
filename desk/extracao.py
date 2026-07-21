from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent

load_dotenv()

class DadosConfirmacao(BaseModel):
    """Campos extraídos de um texto de confirmação de contrato."""

    fardo_codigo: str = Field(description="Código do fardo mencionado no texto")
    comprador: str = Field(description="Nome do comprador mencionado no texto")
    preco_por_kg: str = Field(
        description="Preço por kg como string decimal, ex.: '6.85'"
    )


agente_extracao = Agent(
    "google:gemini-2.5-flash",
    output_type=DadosConfirmacao,
    system_prompt=(
        "Você extrai dados estruturados de confirmações de contrato de venda de "
        "algodão. Leia o texto livre e devolva o código do fardo, o nome do "
        "comprador e o preço por kg, exatamente como aparecem no texto."
    ),
    defer_model_check=True,
)

def extrair_dados_confirmacao(texto: str) -> DadosConfirmacao:
    """Usa o agente PydanticAI para extrair campos estruturados de um texto livre."""
    resultado = agente_extracao.run_sync(texto)
    return resultado.output
