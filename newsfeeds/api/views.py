from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
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
        newsfeeds = NewsFeedService.get_cached_newsfeeds(request.user.id)
        newsfeeds = self.paginate_queryset(newsfeeds)
        serializer = NewsFeedSerializer(
            newsfeeds,
            context={'request': request},
            many=True)
        return self.get_paginated_response(serializer.data)
