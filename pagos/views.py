from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import stripe
from django.conf import settings

from .models import CarritoCompra, ItemCarrito, OrdenCompra
from .serializers import (
    CarritoCompraSerializer,
    OrdenCompraSerializer,
    AgregarAlCarritoSerializer,
    ActualizarCantidadSerializer,
    PreciosSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY


class CarritoViewSet(viewsets.ViewSet):
    """ViewSet para manejar el carrito de compras"""
    permission_classes = [permissions.IsAuthenticated]

    def get_carrito(self, usuario):
        """Obtener o crear carrito para el usuario"""
        carrito, created = CarritoCompra.objects.get_or_create(usuario=usuario)
        return carrito

    @action(detail=False, methods=['get'])
    def precios(self, request):
        """Obtener precios de las clases"""
        precios = {25: 6, 50: 12, 80: 16}
        serializer = PreciosSerializer({
            'duracion_25min': precios[25],
            'duracion_50min': precios[50],
            'duracion_80min': precios[80],
        })
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mi_carrito(self, request):
        """Obtener el carrito del usuario actual"""
        carrito = self.get_carrito(request.user)
        serializer = CarritoCompraSerializer(carrito)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def agregar_item(self, request):
        """Agregar item al carrito"""
        serializer = AgregarAlCarritoSerializer(data=request.data)
        if serializer.is_valid():
            carrito = self.get_carrito(request.user)
            duracion = serializer.validated_data['duracion_minutos']
            cantidad = serializer.validated_data['cantidad']

            item, created = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                duracion_minutos=duracion,
                defaults={'cantidad': cantidad}
            )

            if not created:
                item.cantidad += cantidad
                item.save()

            return Response(CarritoCompraSerializer(carrito).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def actualizar_cantidad(self, request):
        """Actualizar cantidad de un item en el carrito"""
        serializer = ActualizarCantidadSerializer(data=request.data)
        if serializer.is_valid():
            carrito = self.get_carrito(request.user)
            duracion = serializer.validated_data['duracion_minutos']
            
            item = get_object_or_404(
                ItemCarrito,
                carrito=carrito,
                duracion_minutos=duracion
            )
            
            item.cantidad = serializer.validated_data['cantidad']
            item.save()

            return Response(CarritoCompraSerializer(carrito).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def eliminar_item(self, request):
        """Eliminar item del carrito"""
        duracion = request.data.get('duracion_minutos')
        if not duracion:
            return Response(
                {"error": "Se requiere duracion_minutos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        carrito = self.get_carrito(request.user)
        item = get_object_or_404(
            ItemCarrito,
            carrito=carrito,
            duracion_minutos=duracion
        )
        item.delete()

        return Response(CarritoCompraSerializer(carrito).data)

    @action(detail=False, methods=['post'])
    def vaciar_carrito(self, request):
        """Vaciar todo el carrito"""
        carrito = self.get_carrito(request.user)
        carrito.items.all().delete()
        return Response(CarritoCompraSerializer(carrito).data)


class OrdenCompraViewSet(viewsets.ModelViewSet):
    """ViewSet para manejar órdenes de compra"""
    serializer_class = OrdenCompraSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrdenCompra.objects.filter(usuario=self.request.user)

    def crear_o_obtener_precios_stripe(self):
        """IDs de precios de Stripe Dashboard"""
        return {
            25: "price_1SZZFH2ev9LdxX5bMQ7BDq3G",
            50: "price_1SZZGn2ev9LdxX5bVuWOacH0",
            80: "price_1SZZIb2ev9LdxX5bShWQN2JD",
        }

    @action(detail=False, methods=['post'])
    def crear_orden_desde_carrito(self, request):
        """Crear orden desde los items del carrito"""
        carrito = CarritoCompra.objects.filter(usuario=request.user).first()
        
        if not carrito or not carrito.items.exists():
            return Response(
                {"error": "El carrito está vacío"},
                status=status.HTTP_400_BAD_REQUEST
            )

        items_orden = []
        total = 0

        for item in carrito.items.all():
            item_data = {
                'duracion_minutos': item.duracion_minutos,
                'cantidad': item.cantidad,
                'precio_unitario': float(item.precio_unitario)
            }
            items_orden.append(item_data)
            total += item.subtotal

        orden = OrdenCompra.objects.create(
            usuario=request.user,
            items=items_orden,
            total=total,
            estado='pendiente'
        )

        try:
            precios_stripe = self.crear_o_obtener_precios_stripe()
            line_items = []

            for item in carrito.items.all():
                if item.duracion_minutos in precios_stripe:
                    line_items.append({
                        'price': precios_stripe[item.duracion_minutos],
                        'quantity': item.cantidad,
                    })

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url='http://localhost:5173/succes',
                cancel_url='http://localhost:5173/failed',
                customer_email=request.user.email,
                metadata={
                    'orden_id': orden.id,
                    'user_id': request.user.id
                }
            )

            orden.stripe_session_id = checkout_session.id
            orden.save()

            carrito.items.all().delete()

            return Response({
                'session_id': checkout_session.id,
                'url_pago': checkout_session.url,
                'orden_id': orden.id
            })

        except Exception as e:
            orden.estado = 'fallida'
            orden.save()
            return Response(
                {'error': f'Error creando sesión de pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def crear_orden_directa(self, request):
        """Crear orden directamente sin usar carrito"""
        items_data = request.data.get('items')
        
        if items_data and isinstance(items_data, list) and len(items_data) > 0:
            item_data = items_data[0]
        else:
            item_data = request.data

        serializer = AgregarAlCarritoSerializer(data=item_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        duracion = serializer.validated_data['duracion_minutos']
        cantidad = serializer.validated_data['cantidad']

        precios = {25: 6, 50: 12, 80: 16}
        precio_unitario = precios.get(duracion, 0)

        item_orden = {
            'duracion_minutos': duracion,
            'cantidad': cantidad,
            'precio_unitario': float(precio_unitario)
        }
        total = precio_unitario * cantidad

        orden = OrdenCompra.objects.create(
            usuario=request.user,
            items=[item_orden],
            total=total,
            estado='pendiente'
        )

        try:
            precios_stripe = self.crear_o_obtener_precios_stripe()

            if duracion not in precios_stripe:
                return Response(
                    {'error': 'Precio no configurado para esta duración'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': precios_stripe[duracion],
                    'quantity': cantidad,
                }],
                mode='payment',
                success_url='http://localhost:5173/succes',
                cancel_url='fahttp://localhost:5173/failed',
                customer_email=request.user.email,
                metadata={
                    'orden_id': orden.id,
                    'user_id': request.user.id,
                    'tipo': 'compra_directa'
                }
            )

            orden.stripe_session_id = checkout_session.id
            orden.save()

            return Response({
                'session_id': checkout_session.id,
                'url_pago': checkout_session.url,
                'orden_id': orden.id
            })

        except Exception as e:
            orden.estado = 'fallida'
            orden.save()
            return Response(
                {'error': f'Error creando sesión de pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def verificar_pago(self, request):
        """Verificar el estado de un pago"""
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response(
                {"error": "Se requiere session_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            orden = get_object_or_404(OrdenCompra, stripe_session_id=session_id)

            if session.payment_status == 'paid' and orden.estado == 'pendiente':
                orden.marcar_como_completada()
                
                return Response({
                    'estado': 'completada',
                    'mensaje': '¡Pago completado! Las clases han sido añadidas a tu saldo.',
                    'orden': OrdenCompraSerializer(orden).data,
                    'nuevo_saldo': {
                        '25min': orden.usuario.saldo_clases_25min,
                        '50min': orden.usuario.saldo_clases_50min,
                        '80min': orden.usuario.saldo_clases_80min
                    }
                })
            elif session.payment_status == 'unpaid':
                return Response({
                    'estado': 'pendiente',
                    'mensaje': 'Pago aún no completado'
                })
            else:
                return Response({
                    'estado': orden.estado,
                    'mensaje': f'Estado actual: {orden.estado}'
                })

        except Exception as e:
            return Response(
                {'error': f'Error verificando pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
def stripe_webhook(request):
    """Webhook para recibir eventos de Stripe - VERSIÓN CORREGIDA"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    if not endpoint_secret:
        print("❌ Webhook secret not configured")
        return HttpResponse("Webhook secret not configured", status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        print(f"❌ Error in payload: {e}")
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Invalid signature: {e}")
        return HttpResponse("Invalid signature", status=400)

    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(f"✅ Webhook: checkout.session.completed - Session ID: {session.id}")
        print(f"   Payment status: {session.payment_status}")
        print(f"   Customer email: {session.customer_email}")
        print(f"   Metadata: {session.metadata}")
        
        try:
            order = OrdenCompra.objects.get(stripe_session_id=session.id)
            print(f"   Order found: #{order.id}, Current status: {order.estado}")
            
            if order.estado == 'pendiente':
                if session.payment_status == 'paid':
                    # Successful payment
                    order.marcar_como_completada()
                    print(f"   ✅ Order {order.id} marked as COMPLETED")
                    
                    # Send HTML confirmation email in English
                    try:
                        from django.core.mail import EmailMultiAlternatives
                        from django.template.loader import render_to_string
                        from django.utils.html import strip_tags
                        
                        # Create context with order data
                        context = {
                            'username': order.usuario.username,
                            'order_id': order.id,
                            'date': order.creada_en.strftime('%B %d, %Y at %H:%M'),
                            'total': f"€{order.total:.2f}",
                            'items': order.items,
                            'current_balance': {
                                '25min': order.usuario.saldo_clases_25min,
                                '50min': order.usuario.saldo_clases_50min,
                                '80min': order.usuario.saldo_clases_80min,
                            },
                            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
                            'calendar_url': f"{settings.FRONTEND_URL}/calendar",
                            'support_email': 'support@spanishclasses.com',
                            'website': settings.FRONTEND_URL,
                        }
                        
                        # Render HTML
                        html_content = render_to_string('emails/purchase_confirmation.html', context)
                        text_content = strip_tags(html_content)
                        
                        # Create email
                        email = EmailMultiAlternatives(
                            subject='Payment Successful!',
                            body=text_content,
                            from_email='Manel Teacher <noreply@manelteacher.com>',
                            to=[order.usuario.email],
                            reply_to=['info@manelteacher.com']
                        )
                        
                        email.attach_alternative(html_content, "text/html")
                        email.send()
                        
                        print(f"   📧 HTML email sent to {order.usuario.email}")
                        
                    except Exception as email_error:
                        print(f"   ⚠️ Error sending email: {email_error}")
                    
                else:
                    # Payment not completed
                    order.estado = 'fallida'
                    order.save()
                    print(f"   ⚠️ Order {order.id} marked as FAILED (payment_status: {session.payment_status})")
            else:
                print(f"   ℹ️ Order {order.id} already has status: {order.estado}")
                
        except OrdenCompra.DoesNotExist:
            print(f"❌ Order not found for session {session.id}")

    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        print(f"⚠️ Webhook: checkout.session.expired - Session ID: {session.id}")
        
        try:
            order = OrdenCompra.objects.get(stripe_session_id=session.id)
            if order.estado == 'pendiente':
                order.marcar_como_cancelada()
                print(f"   ⚠️ Order {order.id} marked as CANCELLED (expired)")
        except OrdenCompra.DoesNotExist:
            print(f"❌ Order not found for expired session {session.id}")

    elif event['type'] == 'checkout.session.async_payment_failed':
        session = event['data']['object']
        print(f"❌ Webhook: checkout.session.async_payment_failed - Session ID: {session.id}")
        
        try:
            order = OrdenCompra.objects.get(stripe_session_id=session.id)
            if order.estado == 'pendiente':
                order.estado = 'fallida'
                order.save()
                print(f"   ❌ Order {order.id} marked as FAILED (async payment failed)")
        except OrdenCompra.DoesNotExist:
            print(f"❌ Order not found for failed session {session.id}")

    return HttpResponse(status=200)