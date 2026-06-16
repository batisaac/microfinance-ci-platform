from rest_framework import serializers
from apps.credits.models import Loan, LoanDocument, LoanSchedule


class LoanDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanDocument
        fields = ("id", "file", "description", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")


class LoanScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanSchedule
        fields = (
            "id", "installment_number", "due_date",
            "amount", "paid_amount", "status", "paid_date",
        )
        read_only_fields = (
            "id", "installment_number", "due_date",
            "amount", "status",
        )


class LoanListSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = (
            "id", "client_name", "amount", "status",
            "eligibility_score", "duration_months",
            "monthly_payment", "created_at",
        )

    def get_client_name(self, obj):
        return obj.client.get_full_name()


class LoanCreateSerializer(serializers.ModelSerializer):
    documents = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = Loan
        fields = ("amount", "purpose", "duration_months", "status", "documents")
        read_only_fields = ("status",)

    def create(self, validated_data):
        docs = validated_data.pop("documents", [])
        loan = Loan.objects.create(**validated_data)
        for f in docs:
            LoanDocument.objects.create(loan=loan, file=f)
        return loan


class LoanDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    documents = LoanDocumentSerializer(many=True, read_only=True)
    schedule = LoanScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = (
            "id", "client_name", "amount", "purpose", "status",
            "eligibility_score", "duration_months", "interest_rate",
            "monthly_payment", "agent_notes", "documents",
            "schedule", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "client", "eligibility_score",
            "monthly_payment", "created_at", "updated_at",
        )

    def get_client_name(self, obj):
        return obj.client.get_full_name()


class LoanStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ("status", "agent_notes")
