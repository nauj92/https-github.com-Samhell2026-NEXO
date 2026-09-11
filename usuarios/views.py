from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import PerfilSerializer, CambiarPasswordSerializer, UsuarioSimpleSerializer

Usuario = get_user_model()


class PerfilView(APIView):
    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = PerfilSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CambiarPasswordView(APIView):
    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = request.user
        password_actual = serializer.validated_data["password_actual"]
        password_nueva = serializer.validated_data["password_nueva"]

        if not usuario.check_password(password_actual):
            return Response({"detail": "La contraseña actual no es correcta."}, status=status.HTTP_400_BAD_REQUEST)

        usuario.set_password(password_nueva)
        usuario.save()
        return Response({"detail": "Contraseña actualizada correctamente."})


class UsuarioListView(APIView):
    def get(self, request):
        usuarios = Usuario.objects.filter(rol__in=["abogado", "socio_director", "administrador"])
        serializer = UsuarioSimpleSerializer(usuarios, many=True)
        return Response(serializer.data)