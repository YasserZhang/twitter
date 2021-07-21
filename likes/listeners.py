from utils.redis_helper import RedisHelper


def incr_likes_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from comments.models import Comment
    from django.db.models import F

    if not created:
        return

    model_class = instance.content_type.model_class()
    if model_class == Comment:
        f = F('likes_count') + 1
        Comment.objects.filter(id=instance.object_id).update(likes_count=f)
        comment = instance.content_object
        RedisHelper.incr_count(comment, 'likes_count')
        return
    if model_class == Tweet:
        f = F('likes_count') + 1
        # when put this line here, tweet's likes_count will be always zero, as caching kicks in
        # tweet = instance.content_object
        Tweet.objects.filter(id=instance.object_id).update(likes_count=f)
        tweet = instance.content_object
        RedisHelper.incr_count(tweet, 'likes_count')

def decr_likes_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from comments.models import Comment
    from django.db.models import F

    model_class = instance.content_type.model_class()
    if model_class == Comment:
        f = F('likes_count') - 1
        Comment.objects.filter(id=instance.object_id).update(likes_count=f)
        comment = instance.content_object
        RedisHelper.decr_count(comment, 'likes_count')
        return
    if model_class == Tweet:
        tweet = instance.content_object
        f = F('likes_count') - 1
        Tweet.objects.filter(id=tweet.id).update(likes_count=f)
        RedisHelper.decr_count(tweet, 'likes_count')