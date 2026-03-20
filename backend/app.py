import os

from waitress import serve

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application  # noqa: E402


if __name__ == "__main__":
    serve(
        application,
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        threads=int(os.getenv("WAITRESS_THREADS", "32")),
        connection_limit=int(os.getenv("WAITRESS_CONNECTION_LIMIT", "1000")),
        cleanup_interval=30,
        channel_timeout=30,
    )
