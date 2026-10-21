# Events Aggregator

Backend-сервис-агрегатор на Python, который стоит между клиентами и внешним **Events Provider API**. Сервис регулярно синхронизирует события в собственную БД и поверх этого отдаёт удобный REST API: фильтрация по дате, постраничная пагинация, кэш мест, валидация данных при регистрации.

## Возможности

- Фоновая синхронизация событий раз в сутки (и при старте) с инкрементальной загрузкой по `changed_at`
- Ручной запуск синхронизации: `POST /api/sync/trigger`
- Список событий из локальной БД с фильтром `date_from` (на уровне SQL) и пагинацией `page` / `page_size`
- Детали события и список свободных мест (кэш в памяти на 30 секунд)
- Регистрация на событие и отмена регистрации с валидацией на стороне сервиса

## Стек

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- FastAPI, Pydantic
- PostgreSQL, SQLAlchemy 2.0 (async, asyncpg), Alembic
- httpx для клиента Events Provider API
- pytest, Ruff
- Docker, GitHub Actions

## API

Базовый префикс: `/api`. Интерактивная документация доступна на `/docs`.

| Метод | Путь | Описание | Ответ |
|-------|------|----------|-------|
| GET | `/api/health` | Проверка доступности | 200 `{"status": "ok"}` |
| POST | `/api/sync/trigger` | Запуск синхронизации в фоне | 200 `{"status": "started"}` или `{"status": "already_running"}` |
| GET | `/api/events` | Список событий. Параметры: `date_from` (YYYY-MM-DD), `page` (по умолчанию 1), `page_size` (по умолчанию 20, максимум 100) | 200 `count`, `next`, `previous`, `results` |
| GET | `/api/events/{event_id}` | Детали события | 200, 404 |
| GET | `/api/events/{event_id}/seats` | Свободные места (из провайдера, кэш 30 с) | 200 `event_id`, `available_seats`; 404; 400, если событие не опубликовано |
| POST | `/api/tickets` | Регистрация на событие | 201 `ticket_id`; 400, 404 |
| DELETE | `/api/tickets/{ticket_id}` | Отмена регистрации | 200 `{"success": true}`; 404 |

Тело `POST /api/tickets`:

```json
{
  "event_id": "event-uuid",
  "first_name": "Иван",
  "last_name": "Иванов",
  "email": "ivan@example.com",
  "seat": "A15"
}
```

Коды ошибок:

- **400**: некорректное тело или параметры запроса, либо нарушено бизнес-правило (событие не опубликовано, дедлайн регистрации прошёл, такого места нет на площадке, место уже занято)
- **404**: событие или билет не найдены
- **502**: Events Provider API недоступен или вернул ошибку

## Как это устроено

Код разделён на слои, каждый знает только о соседнем:

```
API (роуты) -> Usecases (бизнес-логика) -> Repositories / Clients -> БД / Events Provider API
```

```
src/
  api/            роуты FastAPI, схемы, зависимости
  usecases/       бизнес-логика, работает через Protocol-интерфейсы
  repositories/   работа с PostgreSQL (паттерн Repository)
  clients/        EventsProviderClient и EventsPaginator
  workers/        фоновая синхронизация (запуск при старте и раз в сутки)
  models/         SQLAlchemy-модели
  core/           конфиг, подключение к БД, кэш
  domain.py       доменные объекты и исключения
  main.py         приложение и lifespan
migrations/       миграции Alembic
tests/            тесты
```

### Синхронизация

- Первая синхронизация запрашивает события с `changed_at=2000-01-01`, следующие только с даты последнего полученного `changed_at`
- Страницы провайдера (cursor-пагинация) обходит `EventsPaginator`, события записываются в БД пачками через upsert
- Состояние (`last_sync_time`, `last_changed_at`, `sync_status`) хранится в таблице `sync_metadata`
- `last_changed_at` обновляется только после успешного завершения, поэтому при сбое следующий запуск ничего не потеряет
- Одновременно выполняется не более одной синхронизации (плановая и ручная не пересекаются)
- Ход синхронизации и ошибки пишутся в лог

### Регистрация и отмена

Перед запросом к провайдеру сервис проверяет, что событие существует и опубликовано, дедлайн не прошёл и место существует по схеме площадки (`seats_pattern`). Свободно ли место, определяет провайдер, его отказ возвращается клиенту как 400. Созданные билеты хранятся в локальной БД: по ним определяется событие при отмене. После регистрации и отмены кэш мест события сбрасывается.

## Конфигурация

Настройки читаются из переменных окружения (локально из файла `.env`, пример в `.env.example`):

| Переменная | Описание |
|------------|----------|
| `POSTGRES_HOST`, `POSTGRES_PORT` | Адрес PostgreSQL |
| `POSTGRES_DATABASE_NAME` | Имя базы |
| `POSTGRES_USERNAME`, `POSTGRES_PASSWORD` | Учётные данные БД |
| `EVENTS_PROVIDER_URL` | Адрес Events Provider API |
| `EVENTS_PROVIDER_API_KEY` | API-ключ провайдера |

## Локальный запуск

Нужны Docker и uv.

```bash
cp .env.example .env        # заполнить значения
docker compose up -d        # локальный PostgreSQL
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```

Сервис будет доступен на http://127.0.0.1:8000, документация на http://127.0.0.1:8000/docs.

## Тесты и линтер

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Клиент провайдера и пагинатор покрыты тестами с `unittest.mock`, бизнес-логика тестируется с подставными репозиториями.

## CI/CD

Workflow `.github/workflows/deploy.yml` запускается на push в `main`:

1. **lint**: Ruff (`check` и `format --check`) и pytest
2. **build**: сборка Docker-образа и публикация в GitHub Container Registry
3. **deploy**: отправка deploy request на платформу

Каждый следующий шаг выполняется только после успешного предыдущего, поэтому деплой без прохождения линтера невозможен. Для шага deploy нужен секрет репозитория `LMS_API_KEY`.

При старте контейнера применяются миграции (`alembic upgrade head`), затем запускается uvicorn.
