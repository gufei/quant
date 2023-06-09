import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


def send_msg_by_redis(typename, msg):
    if not msg:
        return
    if not typename:
        typename = "msg"

    notify_dict = dict(typename=typename, msg=msg)

    notify = json.dumps(notify_dict)

    return redis_client.rpush("notify_message", notify)
