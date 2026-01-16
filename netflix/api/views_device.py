"""
Custom authentication views with device tracking.
"""
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.utils import timezone
from .models import Device, DeviceLogin, Profile, UserSubscription
from .device_utils import get_device_info, get_client_ip


class DeviceTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer that includes device_id in the token."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get device info from request (set by the view)
        device_info = getattr(self, 'device_info', None)
        device = getattr(self, 'device', None)
        
        if device:
            # Add device_id to token response
            data['device_id'] = str(device.id)
        
        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Can add custom claims here
        return token


class DeviceTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that:
    1. Parses device info from User-Agent header
    2. Creates/updates Device record for the user
    3. Returns device_id along with tokens
    """
    serializer_class = DeviceTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # First, let the parent validate credentials
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Now we have the authenticated user
        user = serializer.user
        
        # Parse device info
        device_info = get_device_info(request)
        
        # Create or update Device record
        device, created = Device.objects.update_or_create(
            user=user,
            device_name=device_info['device_name'],
            defaults={
                'device_type': device_info['device_type'],
                'device_model': device_info['device_model'],
                'os_version': device_info['os_version'],
                'last_login_at': timezone.now(),
                'is_active': True
            }
        )
        
        # Store device on serializer for token response
        serializer.device = device
        serializer.device_info = device_info
        
        # Get the response data
        response_data = serializer.validated_data
        response_data['device_id'] = str(device.id)
        
        from rest_framework.response import Response
        return Response(response_data)


# ==================== PROFILE SELECT & STREAM LIMITING ====================
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


class ProfileSelectView(APIView):
    """
    Select a profile to start streaming.
    Checks concurrent stream limit before allowing.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        profile_id = request.data.get('profile_id')
        device_id = request.headers.get('X-Device-ID')
        
        if not profile_id:
            return Response(
                {'error': 'profile_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not device_id:
            return Response(
                {'error': 'X-Device-ID header is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate profile belongs to user
        try:
            profile = Profile.objects.get(id=profile_id, user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {'error': 'Invalid profile'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate device belongs to user
        try:
            device = Device.objects.get(id=device_id, user=request.user)
        except Device.DoesNotExist:
            return Response(
                {'error': 'Invalid device'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's active subscription
        try:
            subscription = request.user.subscriptions.get(
                status=UserSubscription.SubscriptionStatus.ACTIVE,
                current_period_end__gt=timezone.now()
            )
        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'Active subscription required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        max_streams = subscription.subscription_plan.max_concurrent_streams
        
        # Count active streams (DeviceLogins where logout_at is NULL)
        active_streams = DeviceLogin.objects.filter(
            device__user=request.user,
            logout_at__isnull=True
        ).count()
        
        # Check if this device already has an active session
        existing_session = DeviceLogin.objects.filter(
            device=device,
            profile=profile,
            logout_at__isnull=True
        ).first()
        
        if existing_session:
            # Already streaming on this device/profile, just return success
            return Response({
                'message': 'Session already active',
                'session_id': str(existing_session.id)
            })
        
        # Check stream limit
        if active_streams >= max_streams:
            return Response(
                {
                    'error': 'Too many concurrent streams',
                    'max_streams': max_streams,
                    'active_streams': active_streams
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create new DeviceLogin session
        session = DeviceLogin.objects.create(
            device=device,
            profile=profile,
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'message': 'Stream started',
            'session_id': str(session.id)
        })


class StreamLogoutView(APIView):
    """End a streaming session to free up a slot."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        device_id = request.headers.get('X-Device-ID')
        
        if session_id:
            # Logout specific session
            try:
                session = DeviceLogin.objects.get(
                    id=session_id,
                    device__user=request.user,
                    logout_at__isnull=True
                )
                session.logout_at = timezone.now()
                session.save()
                return Response({'message': 'Session ended'})
            except DeviceLogin.DoesNotExist:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif device_id:
            # Logout all sessions on this device
            updated = DeviceLogin.objects.filter(
                device_id=device_id,
                device__user=request.user,
                logout_at__isnull=True
            ).update(logout_at=timezone.now())
            
            return Response({
                'message': f'{updated} session(s) ended'
            })
        
        return Response(
            {'error': 'session_id or X-Device-ID header required'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ActiveStreamsView(APIView):
    """List all active streaming sessions for the user."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        active_sessions = DeviceLogin.objects.filter(
            device__user=request.user,
            logout_at__isnull=True
        ).select_related('device', 'profile')
        
        sessions_data = [
            {
                'session_id': str(s.id),
                'device_name': s.device.device_name,
                'device_type': s.device.device_type,
                'profile_name': s.profile.name,
                'login_at': s.login_at.isoformat(),
                'ip_address': s.ip_address
            }
            for s in active_sessions
        ]
        
        # Get max streams from subscription
        try:
            subscription = request.user.subscriptions.get(
                status=UserSubscription.SubscriptionStatus.ACTIVE,
                current_period_end__gt=timezone.now()
            )
            max_streams = subscription.subscription_plan.max_concurrent_streams
        except UserSubscription.DoesNotExist:
            max_streams = 0
        
        return Response({
            'max_streams': max_streams,
            'active_count': len(sessions_data),
            'sessions': sessions_data
        })
