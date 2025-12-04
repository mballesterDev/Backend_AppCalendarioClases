# django_tests_backend/middleware.py
from django.http import HttpResponse

class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Manejar preflight requests (OPTIONS)
        if request.method == "OPTIONS":
            response = HttpResponse()
            response['Content-Type'] = 'text/plain'
            response.status_code = 200
        else:
            response = self.get_response(request)
        
        # Añadir headers CORS a TODAS las respuestas
        origin = request.headers.get('Origin', '')
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://963c42e2b322.ngrok-free.app",
        ]
        
        if origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
        else:
            # Permitir solo localhost para desarrollo
            response["Access-Control-Allow-Origin"] = "http://localhost:5173"
        
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, ngrok-skip-browser-warning, Accept, Accept-Encoding, Origin, User-Agent"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Expose-Headers"] = "Content-Type, X-CSRFToken, Authorization"
        response["Access-Control-Max-Age"] = "86400"  # 24 horas
        
        return response