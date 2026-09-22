from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_calcular_soma(mocker):
    mocker_somar_delay = mocker.patch("app.tasks.somar.delay")
    mocker_redis_lpush = mocker.patch("app.main.redis_client.lpush")
    mocker_redis_ltrim = mocker.patch("app.main.redis_client.ltrim")
    
    mocker_somar_delay.return_value.id = "fake-task-id"
    response = client.post("/calcular/soma", params={"a":1, "b":2})
    
    assert response.status_code == 200
    assert response.json() == {
        "task_id": "fake-task-id",
        "message": "Tarefa de soma enviada para execução!"
    }
    
    mocker_redis_lpush.assert_called_once()
    mocker_redis_ltrim.assert_called_once()

def test_calcular_fatorial(mocker):
    mocker_fatorial_delay = mocker.patch("app.tasks.fatorial.delay")
    mocker_redis_lpush = mocker.patch("app.main.redis_client.lpush")
    mocker_redis_ltrim = mocker.patch("app.main.redis_client.ltrim")
        
    mocker_fatorial_delay.return_value.id = "fake-task-id"
    response = client.post("/calcular/fatorial", params={"n":5})
        
    assert response.status_code == 200
    assert response.json() == {
        "task_id": "fake-task-id",
        "message": "Tarefa de fatorial enviada para execução!"
    }
        
    mocker_redis_lpush.assert_called_once()
    mocker_redis_ltrim.assert_called_once()