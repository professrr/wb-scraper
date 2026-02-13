# WB Scraper

Два микросервиса для получения и парсинга товаров Wildberries по категориям через мобильное API (iOS).

## Запуск

```bash
docker compose up -d --build
```

- Worker API — http://localhost:8000/docs
- Kafka UI — http://localhost:8080

## Категории для скрапинга

[Список всех категорий Wildberries (Gist)](categories.json)

## Флоу

**1. Отправить категорию на скрапинг**

Воспользоваться [Swagger](http://localhost:8000/docs#/scrape/start_scrape_api_v1_scrape_post), либо:

```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"category_url": "https://www.wildberries.ru/catalog/elektronika/razvlecheniya-i-gadzhety/igrovye-konsoli"}'
```

**2. Проверить статус**

Воспользоваться [Swagger](http://localhost:8000/docs#/scrape/get_job_status_api_v1_scrape__job_id__get), либо:

```bash
curl http://localhost:8000/api/v1/scrape/{job_id}
```

**3. Посмотреть результат в [Kafka UI](http://localhost:8080)**

- `wb-category` — сырые JSON-ответы WB API (сообщение на страницу)
- `wb-products` — распарсенные товары (сообщение на товар)

## Сервисы

### Worker (REST API)

Принимает URL категории, получает товары с первых 5 страниц через мобильное API, отправляет каждый raw JSON в Kafka-топик `wb-category`.

- `POST /api/v1/scrape` — запуск скрапинга категории
- `GET /api/v1/scrape/{job_id}` — статус задачи
- `GET /docs` — Swagger UI

### Parser (Kafka Consumer)

Микросервис, 3 реплики. Читает из `wb-category`, парсит товары, отправляет в `wb-products`.

3 партиции / 3 реплики = 1:1 — исключает повторную обработку.

## Технологии

- Python 3.14, FastAPI, Pydantic v2
- confluent-kafka — producer / consumer
- curl_cffi — HTTP-клиент с неопределяемым TLS
- uv — пакетный менеджер, workspace
- Ruff — линтер + форматтер
- Pyright — статический анализ типов (strict)
- Docker, Confluent Kafka, Kafka UI
- semantic-release

## Примечания

### Ценовая политика товаров

API отдаёт базовую цену и цену со скидкой. Цена с ВБ-кошельком ~2–3% ниже. СПП через публичное API недоступна:

- **Базовая цена** — без скидок
- **Цена со скидкой** — скидка продавца
- **Цена с ВБ-кошельком** — доп. скидка ~2–3%
- **СПП** — персональная цена для авторизованных пользователей
