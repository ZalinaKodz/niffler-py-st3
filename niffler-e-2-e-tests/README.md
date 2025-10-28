
<img src="/niffler-ng-client/src/assets/images/niffler-with-a-coin.png" width="250">

# 🧪 Niffler Test Automation Framework
Автотесты по проекту Niffler на Python.

## 🛠 Технологический стек

- **Python 3.9+** - Основной язык программирования
- **Playwright** - Автоматизация браузера
- **Pytest** - Фреймворк для тестирования
- **Allure Framework** - Генерация отчетов
- **Docker** - Контейнеризация
- **Pydantic** - Валидация данных


## 🚀 Быстрый старт


### Установка и настройка

```bash
# 1. Клонирование репозитория
git clone https://github.com/ZalinaKodz/niffler-py-st3.git
cd niffler-py-st3

# 2. Установка зависимостей через Poetry
poetry install

# 3. Установка браузера для Playwright
poetry run playwright install chromium

# 4. Настройка окружения
Создайте файл .env в корне проекта (см .env.sample)

# 5. Запуск инфраструктуры
bash docker-compose-dev.sh

# 6. Создать пользователя 
qwerty/12345
```
## 🏗 Архитектура

### Структура проекта

````
niffler-py-st3/
├── tests/                          # 🧪 Тестовые сценарии
│   ├── ui/                        # 🎨 UI тесты (Playwright)
│   │   ├── test_authorization.py
│   │   ├── main_functional.py
│   │   └── test_registration.py
│   ├── api/                       # 🌐 REST API тесты
│   │   ├── test_category_api.py
│   │   ├── test_spend_api.py
│   │   └── test_api_with_db.py
│   ├── grpc/                      # 🔷 gRPC тесты
│   │   └── test_currency_service.py
│   ├── kafka/                     # 📨 Kafka тесты
│   │   └── test_auth_kafka.py
│   ├── soap/                      # 🧩 SOAP тесты
│   │   └── test_soap_users.py
│   └── integration/               # 🔗 Интеграционные тесты
│       └── test_main_functional.py
├── internal/                      # 🔧 Внутренние модули
│   ├── grpc/
│   │   ├── interceptors/
│   │   │   ├── allure.py         # Allure интерцепторы
│   │   │   └── logging.py        # Логирование gRPC
│   │   └── pb/                   # Protobuf файлы
│   └── models/                   # 📊 Pydantic модели
├── pages/                         # 🏗 Page Object Model
├── clients/                       # 🔌 Клиенты для сервисов
├── fixtures/                      # 🎭 pytest фикстуры
├── databases/                     # 💾 DAO слои
└── config/                       # ⚙️ Конфигурация
    ├── conftest.py
    ├── settings.py
    └── marks.py                  # 📝 Маркеры тестов
````
## 🎯 Запуск тестов
### Группировка тестов для параллельного запуска
````
poetry run pytest -m "api or grpc or soap" -n auto    # Быстрые тесты
poetry run pytest -m "ui" -n 2                         # Медленные UI тесты  
poetry run pytest -m "kafka" -n 1                      # Kafka тесты последовательно
````
### Визуализация результатов тестирования:
```bash
allure serve allure-results
```