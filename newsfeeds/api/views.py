from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
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

    @method_decorator(ratelimit(key='user', rate='5/s', method='GET', block=True))
    def list(self, request):
        #followers = Friendship.objects.filter(to_user=request.user['id'])
        # newsfeeds = NewsFeed.objects.filter(user=request.user)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(request.user.id)
        page = self.paginator.paginate_cached_list(newsfeeds, request)
        if page is None:
            newsfeeds = NewsFeed.objects.filter(user=request.user)
            page = self.paginate_queryset(newsfeeds)
        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True)
        return self.get_paginated_response(serializer.data)
