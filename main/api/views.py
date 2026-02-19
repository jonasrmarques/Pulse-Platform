from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer
from django.contrib.auth import login, logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from groq import Groq
from registro_ponto.models import RegistroPonto



class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        
        login(request, user)
        
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
            }
        }, status=status.HTTP_200_OK)
        
class LogoutAPIView(APIView):
    authentication_classes = [
        SessionAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    print("caiu nela")
    
    def post(self, request):
        print("caiu no post")
        refresh_token = request.data.get("refresh")

        # Invalida JWT
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        # 🔥 REMOVE A SESSION DE VERDADE
        logout(request)

        return Response(
            {"detail": "Logout realizado com sucesso"},
            status=status.HTTP_200_OK
        )
    
class PulseChatbotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get("message")

        if not message:
            return Response(
                {"error": "Mensagem é obrigatória."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # 🔹 Busca SOMENTE os pontos do usuário logado
        registros = RegistroPonto.objects.filter(usuario=user).order_by("-data")[:30]

        if not registros.exists():
            contexto_pontos = "O usuário ainda não possui registros de ponto."
        else:
            contexto_pontos = "\n".join([
                (
                    f"Data: {r.data} | "
                    f"Entrada: {r.horario_entrada or '---'} | "
                    f"Saída: {r.horario_saida or '---'} | "
                    f"Status: {r.get_status_display()}"
                )
                for r in registros
            ])

        # 🔒 Prompt com regras fortes
        system_prompt = f"""
Você é o assistente da plataforma Pulse.

REGRAS OBRIGATÓRIAS:
- Responda SOMENTE com base nos registros de ponto fornecidos.
- NÃO invente dados.
- NÃO responda perguntas fora do contexto de ponto.
- Se a pergunta não tiver relação com ponto, diga:
  "Só posso responder perguntas sobre seus registros de ponto."

REGISTROS DE PONTO DO USUÁRIO:
{contexto_pontos}
"""

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.2
            )

            reply = completion.choices[0].message.content

            return Response({"reply": reply})

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        