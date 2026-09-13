.PHONY: build up down logs ps restart dash status health

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail 100

ps:
	docker compose ps

status:
	./deploy/status.sh

dash:
	./deploy/dashboard.sh

health:
	docker inspect --format '{{json .State.Health}}' nauta-monitor