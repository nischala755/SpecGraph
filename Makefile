up:
	docker compose up -d
backend:
	cd backend && uv run uvicorn app.main:app --reload
frontend:
	cd frontend && npm run dev
test:
	cd backend && uv run pytest && python -m app.check_boundaries
	cd frontend && npm test
