import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


def send_msg_by_redis(msg):
    if not msg:
        return

    return redis_client.rpush("notify_message", msg)
