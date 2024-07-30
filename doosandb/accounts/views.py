from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from .models import CustomUser
from .serializers import CustomUserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        return Response({'status': 'error', 'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
