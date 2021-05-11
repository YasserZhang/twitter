from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from friendships.api.serializers import FollowingSerializer, FriendshipSerializerForCreate
from friendships.models import Friendship


class FriendshipViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    # serializer_class = FriendshipSerializerForCreate
    # authentication_classes = [IsAuthenticated()]

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        print(Friendship.objects.filter(to_user_id=pk).order_by('-created_at').query)
        friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')
        serializer = FollowingSerializer(friendships, many=True)
        return Response({
            'followings': serializer.data,
        })

    # @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    # def follow(self, request, pk):
    #     print(Friendship.objects.filter(from_user=request.user, to_user_id=pk).query)
    #     if Friendship.objects.filter(from_user=request.user, to_user_id=pk).exists():
    #         return Response({
    #             'success': True,
    #             'duplicate': True,
    #         })
    #     serializer = FriendshipSerializerForCreate(
    #         data={
    #             'from_user': request.user,
    #             'to_user_id': pk}
    #     )
    #     if not serializer.is_valid():
    #         return Response({
    #             'success': False,
    #             'message': 'check out the error.',
    #             'errors': serializer.errors,
    #         }, 400)
    #     serializer.save()
    #     return Response({
    #         'success': True
    #     }, status=200)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        # 特殊判断重复 follow 的情况（比如前端猛点好多少次 follow)
        # 静默处理，不报错，因为这类重复操作因为网络延迟的原因会比较多，没必要当做错误处理
        if Friendship.objects.filter(from_user=request.user, to_user=pk).exists():
            return Response({
                'success': True,
                'duplicate': True,
            }, status=status.HTTP_201_CREATED)
        serializer = FriendshipSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': pk,
        })
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'success': True}, status=status.HTTP_201_CREATED)



