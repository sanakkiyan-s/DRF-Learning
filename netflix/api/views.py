from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
from rest_framework import viewsets
from .models import User
from .serializers import AccountSerializer

# views.py
import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# class CreateSubscriptionView(APIView):
#     def post(self, request, *args, **kwargs):
#         plan_id = request.data.get('plan_id')
#         customer_email = request.user.email # Assuming email is passed from frontend

#         try:
#             # Create the subscription in Razorpay
#             subscription_data = {
#                 'plan_id': plan_id,
#                 'customer_notify': 1, # Set to 1 to have Razorpay email the customer
#                 'quantity': 1,
#                 'total_count': 60, # Optional: number of billing cycles
#                 'start_at': None, # Optional: Unix timestamp for start time
#                 'notes': {
#                     'user_id': str(request.user.id), # Add internal notes
#                 }
#             }
#             subscription = client.subscription.create(data=subscription_data)

#             return Response({
#                 'subscription_id': subscription['id'],
#                 'razorpay_key': settings.RAZORPAY_KEY_ID
#             }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
# # views.py
# import hmac
# import hashlib

# @csrf_exempt # Use this decorator for CSRF exemption on this specific view
# class VerifySubscriptionView(APIView):
#     def post(self, request, *args, **kwargs):
#         # The data sent from the frontend/Razorpay
#         razorpay_payment_id = request.data.get('razorpay_payment_id')
#         razorpay_subscription_id = request.data.get('razorpay_subscription_id')
#         razorpay_signature = request.data.get('razorpay_signature')

#         # Create your own signature
#         generated_signature = hmac.new(
#             bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
#             bytes(f"{razorpay_payment_id}|{razorpay_subscription_id}", 'utf-8'),
#             hashlib.sha256
#         ).hexdigest()

#         if generated_signature == razorpay_signature:
#             # Payment is successful. Update your database (e.g., set user's subscription status to active)
#             # You can access notes data here to link to your user model
#             return Response({'status': 'success'}, status=status.HTTP_200_OK)
#         else:
#             return Response({'status': 'failure'}, status=status.HTTP_400_BAD_REQUEST)



class AccountView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AccountSerializer