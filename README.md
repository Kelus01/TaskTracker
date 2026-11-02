# Task Tracker

Базовий каркас системи керування проєктами та задачами на Django і Django REST Framework.
## Запуск локально

Потрібен Python 3.12 або новіший.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Службова перевірка доступна за адресою `GET http://127.0.0.1:8000/health` і повертає:

```json
{"status": "ok"}
```

Для створення адміністратора виконайте `python manage.py createsuperuser`. Локальне значення секретного ключа призначене лише для розробки; перед розгортанням задайте змінну середовища `DJANGO_SECRET_KEY` і вимкніть режим налагодження через `DJANGO_DEBUG=false`.

## Структура

- `config/` — налаштування Django, маршрути та endpoint перевірки стану.
- `accounts/` — користувачі та їхні ролі.
- `projects/` — моделі проєктів і задач, репозиторний та сервісний шари.

## Модель даних

```mermaid
erDiagram
    USER ||--o{ PROJECT : manages
    PROJECT ||--o{ TASK : contains
    USER o|--o{ TASK : assigned_to

    USER {
        int id
        string username
        string role
    }
    PROJECT {
        int id
        string name
        text description
        int manager_id
        datetime created_at
    }
    TASK {
        int id
        string title
        text description
        string status
        string priority
        int project_id
        int assignee_id
        date due_date
    }
```

## REST API

Колекції та деталі проєктів і задач доступні за адресами:

- `/api/projects/` і `/api/projects/{id}/`
- `/api/tasks/` і `/api/tasks/{id}/`

Для обох ресурсів доступні `GET`, `POST`, `PUT`, `PATCH` і `DELETE`. Щоб створити проєкт, передайте `manager_id`; для задачі — `project_id` і за потреби `assignee_id`. Відповіді містять вкладені дані менеджера, проєкту та виконавця.

Списки повертаються сторінками по 20 записів. Номер сторінки задається параметром `page`. Фільтри:

- Проєкти: `name`, `manager`, `created_after`, `created_before`.
- Задачі: `project`, `status`, `priority`, `assignee`, `due_after`, `due_before`.

Сортування задається параметром `ordering`; префікс `-` сортує у зворотному порядку. Наприклад: `/api/tasks/?status=in_progress&ordering=-due_date&page=2`.

Помилки API повертаються у форматі `application/problem+json` за RFC 7807. Колекції використовують `select_related` для завантаження пов'язаних даних без N+1-запитів.

## Перевірки коду

```bash
ruff check .
ruff format --check .
```
