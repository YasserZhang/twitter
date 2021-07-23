from celery import shared_task

from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from tweets.models import Tweet

ONE_HOUR = 60 * 60

@shared_task(time_limit=ONE_HOUR)
def fanout_newsfeeds_task(tweet_id):
    from newsfeeds.services import NewsFeedService
    tweet = Tweet.objects.get(id=tweet_id)
    newsfeeds = [
        NewsFeed(user=follower, tweet=tweet)
        for follower in FriendshipService.get_followers(tweet.user)
    ]
    newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
    NewsFeed.objects.bulk_create(newsfeeds)

    # bulk create 不会触发 post_save 的 signal，所以需要手动 push 到 cache 里
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)