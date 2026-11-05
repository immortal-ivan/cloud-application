"""HTTP-клиент Cloud Application для Notification Service.

ЛР №29: асинхронный вызов по HTTP.
ЛР №30: явный timeout, ограниченные retry с exponential backoff только для ошибок
установления соединения, собственные исключения интеграционного слоя.
Доп. задание ЛР №30: идемпотентность через request_id - один и тот же request_id
передаётся во всех попытках одной операции, сервис не создаёт дубликат.
"""
import asyncio
from uuid import uuid4

import httpx

from app.config import settings


class NotificationServiceError(Exception):
    pass


class NotificationServiceUnavailable(NotificationServiceError):
    pass


class NotificationServiceTimeout(NotificationServiceError):
    pass


class NotificationServiceBadResponse(NotificationServiceError):
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"Notification service returned HTTP {status_code}")


async def send_notification(recipient: str, message: str) -> dict:
    url = f"{settings.notification_service_url}/notifications"
    payload = {
        "recipient": recipient,
        "message": message,
        # Один ключ идемпотентности на всю пользовательскую операцию (все попытки).
        "request_id": uuid4().hex,
    }
    timeout = httpx.Timeout(settings.notification_timeout_seconds)
    max_attempts = settings.notification_max_attempts

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            # Соединение не установлено - запрос точно не обработан, повтор безопасен.
            if attempt == max_attempts:
                raise NotificationServiceUnavailable() from exc
            delay = settings.notification_retry_delay_seconds * (2 ** (attempt - 1))
            await asyncio.sleep(delay)
        except httpx.TimeoutException as exc:
            # Запрос мог быть уже обработан - POST автоматически не повторяем.
            raise NotificationServiceTimeout() from exc
        except httpx.HTTPStatusError as exc:
            raise NotificationServiceBadResponse(exc.response.status_code) from exc
        except httpx.RequestError as exc:
            raise NotificationServiceUnavailable() from exc

    raise NotificationServiceUnavailable()


async def get_notification(notification_id: int) -> dict | None:
    """Чтение уведомления. None - если сервис ответил 404."""
    url = f"{settings.notification_service_url}/notifications/{notification_id}"
    timeout = httpx.Timeout(settings.notification_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        raise NotificationServiceUnavailable() from exc
    except httpx.TimeoutException as exc:
        raise NotificationServiceTimeout() from exc
    except httpx.HTTPStatusError as exc:
        raise NotificationServiceBadResponse(exc.response.status_code) from exc
    except httpx.RequestError as exc:
        raise NotificationServiceUnavailable() from exc
