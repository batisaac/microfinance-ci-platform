from rest_framework import serializers
from apps.repayments.models import Repayment


class RepaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repayment
        fields = (
            "id", "loan", "amount", "interest_paid",
            "penalty_paid", "principal_paid",
            "payment_date", "method", "reference", "notes",
            "created_at",
        )
        read_only_fields = (
            "id", "interest_paid", "penalty_paid",
            "principal_paid", "created_at",
        )


class RepaymentListSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = Repayment
        fields = (
            "id", "loan", "client_name", "agent_name",
            "amount", "interest_paid", "penalty_paid",
            "principal_paid", "payment_date", "method",
        )

    def get_client_name(self, obj):
        return obj.loan.client.get_full_name()

    def get_agent_name(self, obj):
        if obj.agent:
            return obj.agent.get_full_name()
        return None


class RepaymentDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    loan_amount = serializers.SerializerMethodField()
    loan_purpose = serializers.SerializerMethodField()

    class Meta:
        model = Repayment
        fields = (
            "id", "loan", "loan_amount", "loan_purpose",
            "client_name", "agent_name",
            "amount", "interest_paid", "penalty_paid",
            "principal_paid", "payment_date", "method",
            "reference", "notes", "created_at",
        )
        read_only_fields = (
            "id", "interest_paid", "penalty_paid",
            "principal_paid", "created_at",
        )

    def get_client_name(self, obj):
        return obj.loan.client.get_full_name()

    def get_agent_name(self, obj):
        return obj.agent.get_full_name() if obj.agent else None

    def get_loan_amount(self, obj):
        return str(obj.loan.amount)

    def get_loan_purpose(self, obj):
        return obj.loan.purpose
