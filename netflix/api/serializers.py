from rest_framework import serializers
from .models import User, SubscriptionPlan, BillingHistory, UserSubscription, Profile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'country_code', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'avatar_url', 'language_code', 'is_kid_profile', 'age']



class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class BillingHistorySerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    
    class Meta:
        model = BillingHistory
        fields = [
            'id', 'billing_cycle_start', 'billing_cycle_end', 'amount', 
            'currency', 'payment_status', 'invoice_number', 'plan_name', 'created_at'
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    max_streams = serializers.IntegerField(source='subscription_plan.max_concurrent_streams', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'status', 'plan_name', 'current_period_start', 'current_period_end',
            'trial_end', 'cancel_at_period_end', 'max_streams', 'created_at'
        ]