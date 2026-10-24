export

.PHONY: build up down restart logs ssh test clean

build:
	docker compose build

up: build
	docker compose up -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f

ssh:
	ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null builtin@127.0.0.1

test:
	docker compose ps
	@ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
	  -o BatchMode=no builtin@127.0.0.1 true 2>&1 | head -n 3 || true

#push: build
#	docker push $(REGISTRY)/builtin:latest

clean:
	docker compose down --rmi local -v
