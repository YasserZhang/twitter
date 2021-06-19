from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from friendships.api.paginations import FriendshipPagination
from friendships.api.serializers import FollowingSerializer, FriendshipSerializerForCreate, FollowerSerializer
from friendships.models import Friendship
from friendships.services import FriendshipService


class FriendshipViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = FriendshipSerializerForCreate
    # authentication_classes = [IsAuthenticated()]
    pagination_class = FriendshipPagination

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        print(Friendship.objects.filter(from_user_id=pk).order_by('-created_at').query)
        friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowingSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
        page = self.paginate_queryset(friendships)
        serializer = FollowerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        print(Friendship.objects.filter(from_user=request.user, to_user_id=pk).query)
        if Friendship.objects.filter(from_user=request.user, to_user_id=pk).exists():
            return Response({
                'success': True,
                'duplicate': True,
            }, status=201)
        serializer = FriendshipSerializerForCreate(
            data={
                'from_user_id': request.user.id,
                'to_user_id': pk
            }
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'check out the error.',
                'errors': serializer.errors,
            }, 400)
        serializer.save()
        FriendshipService.invalidate_following_cache(request.user.id)
        return Response({
            'success': True
        }, status=201)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'message': 'You can\'t unfollow yourself.'
            }, 400)
        deleted, _ = Friendship.objects.filter(from_user=request.user, to_user_id=pk).delete()
        FriendshipService.invalidate_following_cache(request.user.id)
        return Response({
            'success': True,
            'deleted': deleted,
        })
