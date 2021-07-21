from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from likes.services import LikeService
from tweets.constants import TWEET_PHOTOS_UPLOAD_LIMIT
from tweets.models import Tweet
from tweets.services import TweetService
from utils.redis_helper import RedisHelper


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()
    has_liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = ('id',
                  'user',
                  'created_at',
                  'content',
                  'has_liked',
                  'likes_count',
                  'comments_count',
                  'photo_urls',
                  )

    def get_likes_count(self, obj):
        return RedisHelper.get_count(obj, 'likes_count')

    def get_comments_count(self, obj):
        return RedisHelper.get_count(obj, 'comments_count')

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_photo_urls(self, obj):
        photo_urls = []
        for photo in obj.tweetphoto_set.all().order_by('order'):
            photo_urls.append(photo.file.url)
        return photo_urls


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files')

    def validate(self, data):
        if len(data.get('files', [])) > TWEET_PHOTOS_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'You can upload {TWEET_PHOTOS_UPLOAD_LIMIT} photos '
                           'at most'
            })
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        if validated_data.get('files'):
            TweetService.create_photos_from_files(
                tweet,
                validated_data['files'],
            )
        return tweet


class TweetSerializerForDetail(TweetSerializer):
    user = UserSerializerForTweet()
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        # fields = ('id', 'user', 'comments', 'content', 'created_at')
        fields = (
            'id',
            'user',
            'comments',
            'content',
            'likes',
            'comments',
            'likes_count',
            'comments_count',
            'has_liked',
            'created_at',
            'photo_urls',
        )
