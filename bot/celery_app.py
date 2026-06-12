import os
from celery.schedules import crontab
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://:vexaredis2024@localhost:6379/0")

app = Celery("vexa", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "update-stats-embed": {"task": "bot.tasks.update_stats_embed", "schedule": 60.0},
        "check-alerts": {"task": "bot.tasks.check_alerts", "schedule": 30.0},
        "flash-sales": {"task": "bot.tasks.update_flash_sales", "schedule": 14400.0},
        "update-leaderboard": {"task": "bot.tasks.update_leaderboard", "schedule": 60.0},
        "rotate-live-demo": {
            "task": "bot.tasks.rotate_live_demo",
            "schedule": crontab(hour="0,12", minute=0),
        },
        "check-expired-plans": {
            "task": "bot.tasks.check_expired_plans",
            "schedule": crontab(hour="6", minute=0),
        },
        "send-expiration-warnings": {
            "task": "bot.tasks.send_expiration_warning",
            "schedule": crontab(hour="12", minute=0),
        },
        "cleanup-inactive-ai-channels": {
            "task": "bot.tasks.cleanup_inactive_ai_channels",
            "schedule": crontab(hour="3", minute=0),
        },
    },
)
