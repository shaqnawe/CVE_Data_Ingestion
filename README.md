---

## Common Commands

- **Check Celery workers:**  
  `docker-compose exec backend celery -A backend.celery_app.celery_app status`
- **Check Redis cache:**  
  `docker-compose exec redis redis-cli ping`
- **Create DB tables manually:**  
  `docker-compose run --rm backend python backend/create_tables.py`

---

## CI/CD

- Automated tests and linting run on every pull request via GitHub Actions.
- See `.github/workflows/` for workflow configuration.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryq.dev/)
- [Elasticsearch](https://www.elastic.co/elasticsearch/)
- [React](https://react.dev/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)