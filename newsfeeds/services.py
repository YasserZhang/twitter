from newsfeeds.models import NewsFeed
from twitter.cache_constants import USER_NEWSFEED_PATTERN
from utils.redis_helper import RedisHelper
from newsfeeds.tasks import fanout_newsfeeds_task

class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        fanout_newsfeeds_task.delay(tweet.id)
        # followers = Friendship.objects.filter(to_user=tweet.user)
        # newsfeeds = [NewsFeed(user_id=follower.from_user_id, tweet=tweet) for follower in followers]
        # newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        # NewsFeed.objects.bulk_create(newsfeeds)
        #
        # # bulk create wont trigger post_sava signal, need to manually put newsfeeds into cache
        # for newsfeed in newsfeeds:
        #     cls.push_newsfeed_to_cache(newsfeed)


    """
    another way to implement
    """

    # @classmethod
    # def fanout_to_followers(cls, tweet):
    #     # 错误的方法
    #     # 不可以将数据库操作放在 for 循环里面，效率会非常低
    #     # for follower in FriendshipService.get_followers(tweet.user):
    #     #     NewsFeed.objects.create(
    #     #         user=follower,
    #     #         tweet=tweet,
    #     #     )
    #
    #     # 正确的方法：使用 bulk_create，会把 insert 语句合成一条
    #     newsfeeds = [
    #         NewsFeed(user=follower, tweet=tweet)
    #         for follower in FriendshipService.get_followers(tweet.user)
    #     ]
    #     newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
    #     NewsFeed.objects.bulk_create(newsfeeds)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        queryset = NewsFeed.objects.filter(user_id = user_id).order_by("-created_at")
        key = USER_NEWSFEED_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by("-created_at")
        key = USER_NEWSFEED_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, queryset)

