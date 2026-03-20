import logging
import time
from contextlib import contextmanager
from uuid import uuid4

from django.conf import settings
from redis import Redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)

LOCK_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


class RedisLockBusy(Exception):
    pass


class RedisLockUnavailable(Exception):
    pass


def build_lock_key(name):
    return f"{settings.REDIS_KEY_PREFIX}:lock:{name}"


def get_redis_client():
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=0.5,
    )


def acquire_lock(client, key, ttl, wait_timeout):
    token = uuid4().hex
    deadline = time.monotonic() + wait_timeout

    while True:
        try:
            locked = client.set(key, token, nx=True, ex=ttl)
        except RedisError as exc:
            raise RedisLockUnavailable(str(exc)) from exc

        if locked:
            return token

        if time.monotonic() >= deadline:
            raise RedisLockBusy(f"Could not acquire lock: {key}")

        time.sleep(0.05)


def release_lock(client, key, token):
    try:
        client.eval(LOCK_RELEASE_SCRIPT, 1, key, token)
    except RedisError:
        logger.warning("释放 Redis 锁失败: %s", key, exc_info=True)


@contextmanager
def guarded_redis_locks(lock_names):
    client = get_redis_client()
    acquired = []
    keys = [build_lock_key(name) for name in sorted(set(lock_names))]

    try:
        for key in keys:
            token = acquire_lock(
                client=client,
                key=key,
                ttl=settings.ENROLLMENT_LOCK_TTL,
                wait_timeout=settings.ENROLLMENT_LOCK_WAIT_TIMEOUT,
            )
            acquired.append((key, token))
        yield
    except RedisLockUnavailable as exc:
        if settings.ENROLLMENT_REDIS_REQUIRED:
            raise
        logger.warning("Redis 不可用，当前选课请求降级为仅依赖数据库事务保护：%s", exc)
        yield
    finally:
        for key, token in reversed(acquired):
            release_lock(client, key, token)
