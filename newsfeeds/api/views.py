from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api.serializers import UserSerializer
from friendships.models import Friendship
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed


class NewsFeedViewSet(viewsets.GenericViewSet):
    # queryset = NewsFeed.objects.all()
    # serializer_class = NewsFeedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # print(self.request.user)
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        print(request.user)
        #followers = Friendship.objects.filter(to_user=request.user['id'])
        # newsfeeds = NewsFeed.objects.filter(user=request.user)
        serializer = NewsFeedSerializer(
            self.get_queryset(),
            context={'request': request},
            many=True)
        return Response(
            {
             'newsfeeds': serializer.data,
             }, status=status.HTTP_200_OK)
