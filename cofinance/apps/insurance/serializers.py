from datetime import date

from rest_framework import serializers

from apps.insurance.models import InsurancePlan, InsuranceSubscription


class InsurancePlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePlan
        fields = (
            "id", "name", "description",
            "coverage_amount", "monthly_premium", "is_active",
        )


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceSubscription
        fields = (
            "id", "plan", "loan", "start_date", "end_date",
            "duration_months", "premium", "status", "created_at",
        )
        read_only_fields = (
            "id", "client", "end_date", "premium", "status", "created_at",
        )

    def validate_plan(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Ce produit d'assurance n'est plus disponible.")
        return value

    def validate_start_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("La date de début ne peut pas être dans le passé.")
        return value

    def validate_duration_months(self, value):
        if value < 1:
            raise serializers.ValidationError("La durée doit être d'au moins 1 mois.")
        return value

    def create(self, validated_data):
        plan = validated_data["plan"]
        start = validated_data["start_date"]
        duration = validated_data["duration_months"]

        def add_months(source, months):
            month = source.month - 1 + months
            year = source.year + month // 12
            month = month % 12 + 1
            day = min(source.day, [31, 29 if year % 4 == 0 and (
                year % 100 != 0 or year % 400 == 0
            ) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            return date(year, month, day)

        end = add_months(start, duration)
        validated_data["end_date"] = end
        return super().create(validated_data)


class PolicyListSerializer(serializers.ModelSerializer):
    plan_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceSubscription
        fields = (
            "id", "plan_name", "client_name",
            "start_date", "end_date", "duration_months",
            "premium", "status", "created_at",
        )

    def get_plan_name(self, obj):
        return obj.plan.name

    def get_client_name(self, obj):
        return obj.client.get_full_name()


class PolicyDetailSerializer(serializers.ModelSerializer):
    plan_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    coverage_amount = serializers.SerializerMethodField()
    expires_soon = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceSubscription
        fields = (
            "id", "plan_name", "client_name", "coverage_amount",
            "start_date", "end_date", "duration_months",
            "premium", "status", "expires_soon", "created_at",
        )
        read_only_fields = fields

    def get_plan_name(self, obj):
        return obj.plan.name

    def get_client_name(self, obj):
        return obj.client.get_full_name()

    def get_coverage_amount(self, obj):
        return str(obj.plan.coverage_amount)

    def get_expires_soon(self, obj):
        return obj.is_expiring_soon()
