from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.credits.models import Loan
from apps.credits.serializers import (
    LoanCreateSerializer, LoanListSerializer,
    LoanDetailSerializer, LoanStatusSerializer,
)
from apps.accounts.permissions import IsAdminOrAgent


class LoanListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LoanCreateSerializer
        return LoanListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "agent"):
            return Loan.objects.all()
        return Loan.objects.filter(client=user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class LoanDetailView(generics.RetrieveAPIView):
    serializer_class = LoanDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "agent"):
            return Loan.objects.all()
        return Loan.objects.filter(client=user)


class LoanStatusUpdateView(generics.UpdateAPIView):
    serializer_class = LoanStatusSerializer
    permission_classes = (permissions.IsAuthenticated & IsAdminOrAgent,)

    def get_queryset(self):
        return Loan.objects.all()

    def update(self, request, *args, **kwargs):
        loan = self.get_object()
        new_status = request.data.get("status")
        allowed = {
            "soumise": ["en_analyse", "rejetee"],
            "en_analyse": ["approuvee", "rejetee"],
            "approuvee": ["decaissée"],
        }
        current = loan.status
        if current in allowed and new_status in allowed[current]:
            loan.status = new_status
            loan.analyzed_by = request.user
            if new_status == "approuvee":
                loan.generate_schedule()
            loan.save()
            return Response(LoanDetailSerializer(loan).data)
        return Response(
            {"detail": f"Transition {current} → {new_status} non autorisée."},
            status=status.HTTP_400_BAD_REQUEST,
        )
