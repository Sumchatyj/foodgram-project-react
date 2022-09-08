## Foodgram

### Описание:
Веб-приложение для публикации рецептов, позволяет создавать свои рецепты из перечня ингредиентов, добавлять рецепты в избранное или список покупок, подписываться на других авторов и скачать свой списой покупок.

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Sumchatyj/foodgram-project-react
```

При необходимости создать файл infra/.env по следующему шаблону:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password> # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД
DJANGO_SECRET_KEY=<SECRET_KEY> # установите  секретный ключ для Django
DJANGO_DEBUG=False # при необходимости измените статус режима отладки
```

Собрать образ и запустить контейнер:

```
docker-compose up -d
```

Команда для заполнения базы данных ингредиентов из файла backend/foodgram/data/ingredients.json:

```
python manage.py fill_db
```

Веб-приложение будет доступно на localhost

адрес:
http://foodgram.zapto.org/

username:
admin
password:
adminyandex