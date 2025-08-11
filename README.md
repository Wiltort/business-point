# Справочник организаций — REST API

## Описание

Это приложение реализует REST API для справочника организаций, зданий и видов деятельности.  
Стек: **FastAPI + SQLAlchemy + Alembic + PostgreSQL + Docker**.

---

## Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Wiltort/business-point.git
cd business-point
```
### 2. Настройте переменные окружения
Создайте файл .env в корне проекта и добавьте:
```bash
    POSTGRES_USER=<user>
    POSTGRES_PASSWORD=<password>
    POSTGRES_DB=<dbname>
    POSTGRES_HOST=<host> # для докера - postgres
    # SYNC_DATABASE_URL=<> для разработки (создания новых миграции)
    API_KEY=supersecretkey
```
### 3. Запустите приложение через Docker
```bash
docker-compose up --build
```
- FastAPI будет доступен на порту 8002 (Swagger UI: http://localhost:8002/docs)
- PostgreSQL — на порту 5432

## Авторизация
Все запросы к API требуют заголовок X-API-Key:
```
X-API-Key: supersecretkey
```
## Тестовые данные
При разворачивание в докер база данных каждый раз сбрасывается и заполняется тестовыми данными. Если это не требуется в файле src/entrypoint.sh нужно убрать строку 
```
python -m app.scripts.populate_db
```
## Примеры запросов
### Получить список организации
```
curl -H "X-API-Key: supersecretkey" http://localhost:8002/organizations/
```
### Поиск организаций по радиусу
```
curl -X POST -H "X-API-Key: supersecretkey" \
     -H "Content-Type: application/json" \
     -d '{"latitude":55.7558,"longitude":37.6173,"radius":1,"unit":"km"}' \
     http://localhost:8002/organizations/by_radius/
```
## Документация API

- Swagger UI: http://localhost:8002/docs
- Redoc: http://localhost:8002/redoc