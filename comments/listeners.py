from utils.listeners import invalidate_object_cache
from utils.redis_helper import RedisHelper


def incr_comments_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    if not created:
        return

    Tweet.objects.filter(id=instance.tweet_id).update(comments_count = F('comments_count') + 1)
    # shouldn't invalidate tweet cache each time updating comment or like counts, otherwise defeats
    # the purpose of caching
    # invalidate_object_cache(sender=Tweet, instance=instance.tweet)
    RedisHelper.incr_count(instance.tweet, 'comments_count')

def decr_comments_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    Tweet.objects.filter(id=instance.tweet_id).update(comments_count = F('comments_count') - 1)
    # invalidate_object_cache(sender=Tweet, instance=instance.tweet)
    RedisHelper.decr_count(instance.tweet, 'comments_count')