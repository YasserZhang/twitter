from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from inbox.api.serializers import NotificationSerializer


class NotificationViewSet(
        viewsets.GenricViewSet,
        viewsets.mixins.ListModeMixin,
    ):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fileds = ('unread',)

    def get_queryset(self):
        return self.request.user.notifications.all()


    def unread_count(self, request, *args, **kwargs):
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)