def push_tweet_to_cache(sender, instance, created, **kwargs):
    if not created:
        return

    from tweets.services import TweetService
    print("\nlistener triggering caching.\n")
    TweetService.push_tweet_to_cache(instance)