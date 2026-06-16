from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.insurance.models import InsurancePlan, InsuranceSubscription
from apps.insurance.serializers import (
    InsurancePlanListSerializer, SubscribeSerializer,
    PolicyListSerializer, PolicyDetailSerializer,
)
from apps.accounts.permissions import IsAdminOrAgent


class PlanListView(generics.ListAPIView):
    queryset = InsurancePlan.objects.filter(is_active=True)
    serializer_class = InsurancePlanListSerializer
    permission_classes = (permissions.IsAuthenticated,)


class SubscribeView(generics.CreateAPIView):
    serializer_class = SubscribeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class MyPoliciesView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return SubscribeSerializer
        return PolicyListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = InsuranceSubscription.objects.select_related("client", "plan")
        if user.role in ("admin", "agent"):
            return qs
        return qs.filter(client=user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class PolicyDetailView(generics.RetrieveAPIView):
    serializer_class = PolicyDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = InsuranceSubscription.objects.select_related("client", "plan")
        if user.role in ("admin", "agent"):
            return qs
        return qs.filter(client=user)
