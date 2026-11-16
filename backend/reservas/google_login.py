from django.conf import settings
from django.contrib.auth import get_user_model
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _validar_credencial(credencial):
    """Valida o ID token do Google (assinatura, expiração e audience)."""
    if not settings.GOOGLE_CLIENT_ID:
        raise serializers.ValidationError(
            {"detail": "Login com Google não configurado (GOOGLE_CLIENT_ID)."})
    try:
        dados = id_token.verify_oauth2_token(
            credencial, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError:
        raise AuthenticationFailed("Credencial do Google inválida ou expirada.")

    if dados.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise AuthenticationFailed("Emissor inválido.")
    if not dados.get("email") or not dados.get("email_verified"):
        raise AuthenticationFailed("E-mail da conta Google não verificado.")

    permitidos = settings.GOOGLE_ALLOWED_DOMAINS
    if permitidos:
        dominio = dados["email"].rsplit("@", 1)[-1].lower()
        if dominio not in permitidos:
            raise PermissionDenied("Use sua conta institucional para entrar.")
    return dados


def _usuario_do_google(dados):
    email = dados["email"].lower()
    usuario = User.objects.filter(email__iexact=email).first() \
        or User.objects.filter(username__iexact=email).first()

    if usuario is None:
        if not settings.GOOGLE_CRIAR_USUARIOS:
            raise PermissionDenied("Seu e-mail não está cadastrado no sistema.")
        usuario = User(
            username=email,
            email=email,
            first_name=(dados.get("given_name") or "")[:150],
            last_name=(dados.get("family_name") or "")[:150],
        )
        usuario.set_unusable_password()
        usuario.save()
    elif not usuario.is_active:
        raise PermissionDenied("Usuário inativo.")
    return usuario


class GoogleLoginView(APIView):
    """Recebe o ID token do Google e devolve o par de tokens JWT do sistema."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        credencial = request.data.get("credential")
        if not credencial:
            raise serializers.ValidationError({"credential": "Obrigatório."})
        usuario = _usuario_do_google(_validar_credencial(credencial))
        refresh = RefreshToken.for_user(usuario)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})