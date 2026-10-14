import pytest
from app.tasks import somar, fatorial

# Mocks não foram usados porque as tasks são funções puras, sem
# dependências externas a isolar. Eles fariam sentido ao testar os
# endpoints que disparam as tasks com .delay().

def test_somar_inteiros_positivos():
    resultado = somar(2, 3)
    assert resultado == 5, f"somar(2, 3) deveria retornar 5, mas retornou {resultado}"

def test_somar_com_negativo():
    resultado = somar(-4, 10)
    assert resultado == 6, f"somar(-4, 10) deveria retornar 6, mas retornou {resultado}"

def test_somar_decimais():
    resultado = somar(0.1, 0.2)
    assert resultado == pytest.approx(0.3), (
        f"somar(0.1, 0.2) deveria ser aproximadamente 0.3, mas retornou {resultado}"
    )

def test_fatorial_de_zero():
    resultado = fatorial(0)
    assert resultado == 1, f"fatorial(0) deveria retornar 1 (caso base), mas retornou {resultado}"

def test_fatorial_de_um():
    resultado = fatorial(1)
    assert resultado == 1, f"fatorial(1) deveria retornar 1, mas retornou {resultado}"

def test_fatorial_de_cinco():
    resultado = fatorial(5)
    assert resultado == 120, f"fatorial(5) deveria retornar 120, mas retornou {resultado}"

def test_fatorial_negativo_levanta_erro():
    # pytest.raises não aceita mensagem personalizada: se o ValueError não for
    # levantado, o próprio pytest falha com "DID NOT RAISE ValueError", e o
    # match garante que a mensagem do erro é a esperada.
    with pytest.raises(ValueError, match="Número negativo"):
        fatorial(-3)