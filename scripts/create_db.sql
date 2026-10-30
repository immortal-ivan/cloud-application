-- Создание пользователя и базы данных PostgreSQL для Cloud Application.
-- Выполнить в pgAdmin: правый клик по серверу -> Query Tool -> вставить -> F5.
-- (Подключение под суперпользователем postgres.)
-- Пароль должен совпадать с содержимым файла secrets/db_password.

CREATE ROLE cloud_user LOGIN PASSWORD 'cloud_pass_2026';

CREATE DATABASE cloud_app OWNER cloud_user;
