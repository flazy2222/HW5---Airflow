HW5 — Airflow retraining pipeline with conditional deploy and notifications

Домашнее задание №5 по курсу «Продвинутая оркестрация и инфраструктура как код».
Реализован автоматизированный ML-конвейер в Apache Airflow с условным деплоем модели и уведомлением о выводе новой версии в продакшен.

Цель работы

Освоить проектирование оркестрируемого ML-пайплайна, включающего:

переобучение модели,

проверку качества,

условное ветвление (деплой / пропуск),

уведомление о выводе новой модели,

использование переменных окружения для параметров пайплайна.

Архитектура DAG

DAG ml_retrain_pipeline состоит из следующих задач:

train_model — обучение модели.

evaluate_model — оценка качества модели (метрика сравнивается с порогом).

decide_deploy — ветвление на основе результата оценки:

если метрика ≥ порога → deploy_model,

иначе → skip_deploy.

deploy_model — деплой модели в продакшен.

notify_success — отправка уведомления в Telegram о деплое.

skip_deploy — логирование пропуска деплоя.

end — финальная точка DAG.

Схема:

train_model → evaluate_model → decide_deploy
                             ↳ deploy_model → notify_success → end
                             ↳ skip_deploy → end

⚙ Используемые технологии

Apache Airflow 2.x

PythonOperator, BranchPythonOperator

Переменные окружения для конфигурации

Telegram Bot API для уведомлений

Конфигурация через переменные окружения
Переменная	Назначение
MODEL_VERSION	Версия модели
METRIC_VALUE	Текущее значение метрики
METRIC_THRESHOLD	Порог качества
TG_TOKEN	Telegram bot token
TG_CHAT	Telegram chat id

Пример (PowerShell):

$env:MODEL_VERSION="hw5-model"
$env:METRIC_VALUE="0.9"
$env:METRIC_THRESHOLD="0.8"
$env:TG_TOKEN="..."
$env:TG_CHAT="..."

Логика деплоя

Если METRIC_VALUE >= METRIC_THRESHOLD → выполняется деплой.

Иначе деплой пропускается, уведомление не отправляется.

Уведомления

После успешного деплоя отправляется сообщение в Telegram:

Новая модель в продакшене: hw5-model
metric=0.9 threshold=0.8
deploy_status=success

Запуск

Поместить ml_retrain_pipeline.py в каталог dags/.

Установить переменные окружения.

Запустить Airflow.

Запустить DAG вручную или дождаться планового запуска.

Проверка через CLI:

airflow dags test ml_retrain_pipeline 2025-12-25
