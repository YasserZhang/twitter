from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api.serializers import UserSerializer
from friendships.models import Friendship
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    # queryset = NewsFeed.objects.all()
    # serializer_class = NewsFeedSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination


    def get_queryset(self):
        # print(self.request.user)
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        #followers = Friendship.objects.filter(to_user=request.user['id'])
        # newsfeeds = NewsFeed.objects.filter(user=request.user)
        newsfeeds = self.get_queryset()
        newsfeeds = self.paginate_queryset(newsfeeds)
        serializer = NewsFeedSerializer(
            newsfeeds,
            context={'request': request},
            many=True)
        return self.get_paginated_response(serializer.data)
