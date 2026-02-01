from app.workers.celery_app import celery_app

@celery_app.task
def generate_documentation(repository_id: int):
    # Task logic here
    pass

@celery_app.task
def index_code(repository_id: int):
    # Task logic here
    pass
