from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.apps import apps
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from apps.credits.models import Loan
from apps.insurance.models import InsuranceSubscription
from apps.accounts.permissions import IsAdmin


class DashboardView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsAdmin)

    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        agent = request.query_params.get("agent")
        region = request.query_params.get("region")

        # -- Volume par statut (une seule requête) --
        loan_qs = Loan.objects.all()
        if date_from:
            loan_qs = loan_qs.filter(created_at__gte=date_from)
        if date_to:
            loan_qs = loan_qs.filter(created_at__lte=date_to)
        if agent:
            loan_qs = loan_qs.filter(analyzed_by_id=agent)
        if region:
            loan_qs = loan_qs.filter(client__region=region)

        volume_par_statut = dict(
            loan_qs.values("status").annotate(
                count=Count("id")
            ).values_list("status", "count")
        )

        # -- Taux de recouvrement --
        disbursed_qs = loan_qs.filter(status="decaissée")
        stats = disbursed_qs.aggregate(
            total_attendu=Sum("schedule__amount"),
            total_percu=Sum("schedule__paid_amount"),
        )
        total_attendu = stats["total_attendu"] or Decimal("0")
        total_percu = stats["total_percu"] or Decimal("0")
        taux_recouvrement = (
            float((total_percu / total_attendu) * 100)
            if total_attendu > 0 else 0.0
        )

        # -- Souscriptions actives --
        sub_qs = InsuranceSubscription.objects.filter(status="active")
        if region:
            sub_qs = sub_qs.filter(client__region=region)
        if date_from:
            sub_qs = sub_qs.filter(created_at__gte=date_from)
        if date_to:
            sub_qs = sub_qs.filter(created_at__lte=date_to)
        souscriptions_actives = sub_qs.count()

        # -- Conversations ouvertes (via apps registry, résilient) --
        conversations_ouvertes = 0
        try:
            ChatConversation = apps.get_model("chat", "Conversation")
            if ChatConversation:
                conv_qs = ChatConversation.objects.filter(status="open")
                if date_from:
                    conv_qs = conv_qs.filter(created_at__gte=date_from)
                if date_to:
                    conv_qs = conv_qs.filter(created_at__lte=date_to)
                if region:
                    conv_qs = conv_qs.filter(
                        Q(client__region=region) | Q(agent__region=region)
                    )
                conversations_ouvertes = conv_qs.count()
        except LookupError:
            pass

        return Response({
            "volume_par_statut": volume_par_statut,
            "taux_recouvrement": round(taux_recouvrement, 2),
            "souscriptions_actives": souscriptions_actives,
            "conversations_ouvertes": conversations_ouvertes,
        })
