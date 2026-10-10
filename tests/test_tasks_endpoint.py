import os

# Mesmo motivo do test_auth.py: o app/auth.py exige essas variáveis no import.
os.environ.setdefault("MEU_USUARIO", "admin")
os.environ.setdefault("MINHA_SENHA", "admin")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_calcular_soma(mocker):
    mocker_somar_delay = mocker.patch("app.tasks.somar.delay")
    # new_callable=AsyncMock: no main.py essas chamadas usam "await redis_client.lpush(...)".
    # Um MagicMock comum não pode ser awaitado e dava TypeError.
    mocker_redis_lpush = mocker.patch("app.main.redis_client.lpush", new_callable=mocker.AsyncMock)
    mocker_redis_ltrim = mocker.patch("app.main.redis_client.ltrim", new_callable=mocker.AsyncMock)

    mocker_somar_delay.return_value.id = "fake-task-id"
    response = client.post("/calcular/soma", params={"a": 1, "b": 2})

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "fake-task-id",
        "message": "Tarefa de soma enviada para execução!"
    }

    mocker_redis_lpush.assert_awaited_once()
    mocker_redis_ltrim.assert_awaited_once()


def test_calcular_fatorial(mocker):
    mocker_fatorial_delay = mocker.patch("app.tasks.fatorial.delay")
    mocker_redis_lpush = mocker.patch("app.main.redis_client.lpush", new_callable=mocker.AsyncMock)
    mocker_redis_ltrim = mocker.patch("app.main.redis_client.ltrim", new_callable=mocker.AsyncMock)

    mocker_fatorial_delay.return_value.id = "fake-task-id"
    response = client.post("/calcular/fatorial", params={"n": 5})

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "fake-task-id",
        "message": "Tarefa de fatorial enviada para execução!"
    }

    mocker_redis_lpush.assert_awaited_once()
    mocker_redis_ltrim.assert_awaited_once()
