def incr_likes_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from comments.models import Comment
    from django.db.models import F

    if not created:
        return

    model_class = instance.content_type.model_class()
    if model_class == Comment:
        comment = instance.content_object
        f = F('likes_count') + 1
        print("F('likes_count') + 1: ", f)
        Comment.objects.filter(id=comment.id).update(likes_count=f)
        return
    if model_class == Tweet:
        tweet = instance.content_object
        f = F('likes_count') + 1
        print("F('likes_count') + 1: ", f)
        Tweet.objects.filter(id=tweet.id).update(likes_count=f)

def decr_likes_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from comments.models import Comment
    from django.db.models import F

    model_class = instance.content_type.model_class()
    if model_class == Comment:
        comment = instance.content_object
        f = F('likes_count') - 1
        print("F('likes_count') - 1: ", f)
        Comment.objects.filter(id=comment.id).update(likes_count=f)
        return
    if model_class == Tweet:
        tweet = instance.content_object
        f = F('likes_count') - 1
        print("F('likes_count') - 1: ", f)
        Tweet.objects.filter(id=tweet.id).update(likes_count=f)