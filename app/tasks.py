from app.celery_app import celery_app

@celery_app.task(bind=True)
def somar(self, a, b):
    return a + b

@celery_app.task(bind=True)
def fatorial(self, n):
    if n < 0:
        raise ValueError("Número negativo não permitido!")
    
    resultado = 1
    
    for i in range(2, n + 1):
        resultado *= i
    
    return resultado