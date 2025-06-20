# config.py
DEMO_MODE = {
    "30_MIN": {
        "crises_count": 3,
        "news_items": 5,
        "news_interval": 300,  # 5 minutes
        "auto_advance": False,
        "crisis_delay": 8  # minutes between crises
    },
    "90_MIN": {
        "crises_count": 12,
        "news_items": 36,
        "news_interval": 60,  # 1 minute
        "auto_advance": True,
        "crisis_delay": 5
    }
}
