from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
import requests

User = get_user_model()

@api_view(['POST'])
def google_login(request):
    google_token = request.data.get("token")
    if not google_token:
        return Response({"error": "No token provided"}, status=400)

    google_response = requests.get(
        f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={google_token}"
    ).json()

    email = google_response.get("email")
    name = google_response.get("name")

    if not email:
        return Response({"error": "Invalid Google token"}, status=400)

    # Usamos email como username para este caso
    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": name},
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        "token": token.key,
        "email": email,
        "name": name,
    })
