from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from accounts.api.serializers import UserSerializer, SignupSerializer, LoginSerializer, UserProfileSerializerForUpdate, \
    UserSerializerWithProfile
from django.contrib.auth import (
    authenticate as django_authenticate,
    login as django_login,
    logout as django_logout,
)

from accounts.models import UserProfile
from comments.api.permissions import IsObjectOwner

"""
dir(request)

['DATA', 'FILES', 'POST', 'QUERY_PARAMS', '__class__', '__delattr__',
 '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', 
 '__getattr__', '__getattribute__', '__gt__', '__hash__', '__init__', 
 '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', 
 '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', 
 '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_auth', 
 '_authenticate', '_authenticator', '_content_type', '_data', 
 '_default_negotiator', '_files', '_full_data', '_load_data_and_files', 
 '_load_stream', '_not_authenticated', '_parse', '_request', '_stream', 
 '_supports_form_parsing', '_user', 'accepted_media_type', 'accepted_renderer', 
 'auth', 'authenticators', 'content_type', 'data', 'force_plaintext_errors', 
 'negotiator', 'parser_context', 'parsers', 'query_params', 'stream', 
 'successful_authenticator', 'user', 'version', 'versioning_scheme']



"""


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializerWithProfile
    permission_classes = (permissions.IsAdminUser, )


class AccountViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=400)
        user = serializer.save()
        # Create UserProfile object
        user.profile
        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(user).data,
        }, status=201)

    @action(methods=['GET'], detail=False)
    @method_decorator(ratelimit(key='user', rate='3/s', method='GET', block=True))
    def login_status(self, request):
        print(request)
        print(request.user)
        print(request.data)
        data = {'has_logged_in': request.user.is_authenticated}
        if request.user.is_authenticated:
            data['user'] = UserSerializer(request.user).data
        return Response(data)

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def logout(self, request):
        django_logout(request)
        return Response({'success': True})

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def login(self, request):
        # to validate user data
        print(dir(request))
        serializer = LoginSerializer(data=request.data)  # request.query_params for GET
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input.",
                "errors": serializer.errors,
            }, status=400)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        # check user's authentication
        user = django_authenticate(username=username,password=password)
        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "username and password does not match",
            }, status=400)
        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(instance=user).data
        }, status=200)


class UserProfileViewSet(viewsets.GenericViewSet, viewsets.mixins.UpdateModelMixin):
    queryset = UserProfile
    permission_classes = (IsAuthenticated, IsObjectOwner)
    serializer_class = UserProfileSerializerForUpdate
