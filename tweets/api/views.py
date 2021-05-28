from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from newsfeeds.services import NewsFeedService
from tweets.api.serializers import TweetCreateSerializer, TweetSerializer, TweetSerializerWithComments
from tweets.models import Tweet
from utils.decorators import required_params


class TweetViewSet(viewsets.GenericViewSet,
                   viewsets.mixins.CreateModelMixin,
                   viewsets.mixins.ListModelMixin):
    """
    API endpoint that allows users to create, list tweets
    """
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        reload create method, because need to use request.user as tweet user
        """
        print("creating a tweet... ")
        serializer = TweetCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(TweetSerializer(tweet).data, status=201)

    @required_params(params=['user_id'])
    def list(self, request, *args, **kwargs):
        """
        reload list method, must have user_id as filter condition
        """
        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(tweets, context={'request': request}, many=True)
        return Response({'tweets': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        if 'with_all_comments' in request.query_params:
            return Response(TweetSerializerWithComments(tweet).data)
        if 'with_preview_comments' in request.query_params:
            return Response(TweetSerializerWithComments(tweet))
        return Response(TweetSerializer(tweet, context={'request': request}).data)
