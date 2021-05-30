from friendships.api.serializers import FollowerSerializer
from friendships.models import Friendship
from newsfeeds.models import NewsFeed


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        followers = Friendship.objects.filter(to_user=tweet.user)
        newsfeeds = [NewsFeed(user_id=follower.from_user_id, tweet=tweet) for follower in followers]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)
