## Проект Foodgram

Cайт Foodgram «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

#Технологии: 

1.Python 3.7.9 

2.Django 2.2.16

#ПО: 

1.Docker 

2.Docker-compose

#Запуск на сервере: -Остановите службу nginx на сервере: 

```sudo systemctl stop nginx```

-Установите на свой сервер Docker:

``` sudo apt install docker.io ```

-Установите docker-compose на сервере: 
```sudo curl -L "https://github.com/docker/compose/releases/download/1.29.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose ```

-Проверте установку docker-compose: 

```sudo  docker-compose --version```

-Создайте папку nginx/ в директории home//

-Скопируйте файлы docker-compose.yaml и nginx/default.conf из вашего проекта на сервер в home/<ваш_username>/docker-compose.yaml и home/<ваш_username>/nginx/default.conf соответственно.

-После Deploy автоматический пройдут все миграции и подгрузится статика. Сайтом можно пользоваться.

