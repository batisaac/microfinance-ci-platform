from rest_framework import generics, permissions

from apps.repayments.models import Repayment
from apps.repayments.serializers import (
    RepaymentCreateSerializer, RepaymentListSerializer,
    RepaymentDetailSerializer,
)
from apps.accounts.permissions import IsAdminOrAgent


class RepaymentListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsAdminOrAgent()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RepaymentCreateSerializer
        return RepaymentListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Repayment.objects.select_related("loan__client", "agent")
        if user.role in ("admin", "agent"):
            return qs
        return qs.filter(loan__client=user)

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)


class RepaymentDetailView(generics.RetrieveAPIView):
    serializer_class = RepaymentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Repayment.objects.select_related("loan__client", "agent")
        if user.role in ("admin", "agent"):
            return qs
        return qs.filter(loan__client=user)
