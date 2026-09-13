.PHONY: build up pull deploy down logs ps restart dash status health

# En el homelab la imagen se baja de GHCR (Docker Hub bloqueado en Cuba).
COMPOSE_SERVER := docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml

build:
	docker compose build

up:
	docker compose up -d --build

pull:
	$(COMPOSE_SERVER) pull

deploy:
	$(COMPOSE_SERVER) up -d

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