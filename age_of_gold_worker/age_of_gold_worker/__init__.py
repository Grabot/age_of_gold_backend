from .tasks import (
    task_initialize,
    task_generate_avatar,
    task_send_email_delete_account,
    task_send_email_forgot_password,
)

__all__ = [
    "task_initialize",
    "task_send_email_delete_account",
    "task_send_email_forgot_password",
    "task_generate_avatar",
]
