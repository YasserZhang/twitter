from twitter import settings
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, key, objects):
        conn = RedisClient.get_connection()

        serialized_list = []
        for obj in objects:
            serialized_data = DjangoModelSerializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, key, queryset):
        conn = RedisClient.get_connection()
        if conn.exists(key):
            print("loading from cache...")
            return cls.load_objects_from_cache(conn, key)
        cls._load_objects_to_cache(key, queryset)
        return list(queryset)

    @classmethod
    def load_objects_from_cache(cls, conn, key):
        serialized_list = conn.lrange(key, 0, -1)
        objects = []
        for serialized_data in serialized_list:
            deserialized_obj = DjangoModelSerializer.deserialize(serialized_data)
            objects.append(deserialized_obj)
        return objects


    @classmethod
    def push_object(cls, key, obj, queryset):
        conn = RedisClient.get_connection()
        if not conn.exists(key):
            cls._load_objects_to_cache(key, queryset)
            return
        serialized_data = DjangoModelSerializer.serialize(obj)
        conn.lpush(key, serialized_data)