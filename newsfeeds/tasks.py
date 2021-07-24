from celery import shared_task

from newsfeeds.models import NewsFeed
from twitter import settings

ONE_HOUR = 60 * 60
FANOUT_BATCH_SIZE = 1000 if not settings.TESTING else 3


@shared_task(routing_key='newsfeeds', time_limit=ONE_HOUR)
def fanout_newsfeeds_batch_task(tweet_id, follower_ids):
    from newsfeeds.services import NewsFeedService

    newsfeeds = [NewsFeed(user_id=follower_id, tweet_id=tweet_id) for follower_id in follower_ids]
    NewsFeed.objects.bulk_create(newsfeeds)
    # bulk create 不会触发 post_save 的 signal，所以需要手动 push 到 cache 里
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)
    return "{} newsfeeds created".format(len(newsfeeds))

@shared_task(routing_key='default', time_limit=ONE_HOUR)
def fanout_newsfeeds_main_task(tweet_id, tweet_user_id):
    from friendships.models import Friendship
    NewsFeed.objects.create(user_id=tweet_user_id, tweet_id=tweet_id)

    followers = Friendship.objects.filter(to_user_id=tweet_user_id)
    follower_ids = [follower.from_user_id for follower in followers]
    for index in range(0, len(follower_ids), FANOUT_BATCH_SIZE):
        batch_ids = follower_ids[index:index + FANOUT_BATCH_SIZE]
        fanout_newsfeeds_batch_task.delay(tweet_id, batch_ids)

    return '{} newsfeeds going to fanout, {} batches created.'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1,
    )