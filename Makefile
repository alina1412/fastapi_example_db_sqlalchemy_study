run:
	poetry run python -m service
	

ifdef OS
	docker_up = docker compose up -d
	docker_down = docker compose down --volumes
else
	docker_up = sudo docker compose up -d
	docker_down = sudo docker compose down
endif



renew:
	poetry run alembic -c alembic.ini downgrade -1
	poetry run alembic -c alembic.ini upgrade head

test:
	poetry run pytest -vsx

async-alembic-init:
	poetry run alembic init -t async migration
	poetry run alembic -c alembic.ini revision --autogenerate -m "initial"

alembic:
	poetry run alembic -c alembic.ini upgrade head

lint:
	poetry run black service
	poetry run pylint service

isort:
	poetry run isort service

req:
	poetry export -f requirements.txt --without-hashes --output ./requirements.txt
