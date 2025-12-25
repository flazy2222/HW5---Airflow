import os
import requests
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT", "")

METRIC_THRESHOLD = float(os.getenv("METRIC_THRESHOLD", "0.8"))
METRIC_VALUE = float(os.getenv("METRIC_VALUE", "0.9"))


def train_model(**context):
    print("Модель обучена")
    return {"status": "trained", "model_version": MODEL_VERSION}


def evaluate_model(**context):
    metric = METRIC_VALUE
    ok = metric >= METRIC_THRESHOLD
    payload = {"metric": metric, "threshold": METRIC_THRESHOLD, "ok": ok}
    print(f"Оценка модели: {payload}")
    return payload


def decide_deploy(**context):
    eval_res = context["ti"].xcom_pull(task_ids="evaluate_model") or {}
    if eval_res.get("ok"):
        return "deploy_model"
    return "skip_deploy"


def deploy_model(**context):
    print(f"Модель {MODEL_VERSION} выведена в продакшен")
    return {"status": "deployed", "model_version": MODEL_VERSION}


def skip_deploy(**context):
    print("Деплой пропущен: метрика ниже порога")
    return {"status": "skipped", "model_version": MODEL_VERSION}


def notify_success(**context):
    deploy_res = context["ti"].xcom_pull(task_ids="deploy_model") or {}
    eval_res = context["ti"].xcom_pull(task_ids="evaluate_model") or {}

    if not deploy_res:
        print("notify_success: deploy_model не выполнялся, уведомление не отправляем")
        return

    text = (
        f"Новая модель в продакшене: {MODEL_VERSION}\n"
        f"metric={eval_res.get('metric')} threshold={eval_res.get('threshold')}\n"
        f"deploy_status=success"
    )
    if not TG_TOKEN or not TG_CHAT:
        print("TG_TOKEN/TG_CHAT не заданы, печатаю сообщение в лог:\n" + text)
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.get(url, params={"chat_id": TG_CHAT, "text": text}, timeout=10)
    r.raise_for_status()
    print(r.text)


with DAG(
    dag_id="ml_retrain_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["hw5", "mlops"],
) as dag:
    train = PythonOperator(task_id="train_model", python_callable=train_model)
    evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model)

    branch = BranchPythonOperator(task_id="decide_deploy", python_callable=decide_deploy)

    deploy = PythonOperator(task_id="deploy_model", python_callable=deploy_model)
    skip = PythonOperator(task_id="skip_deploy", python_callable=skip_deploy)

    notify = PythonOperator(task_id="notify_success", python_callable=notify_success)

    end = EmptyOperator(task_id="end", trigger_rule="none_failed_min_one_success")

    train >> evaluate >> branch
    branch >> deploy >> notify >> end
    branch >> skip >> end
