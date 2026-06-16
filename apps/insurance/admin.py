from django.contrib import admin

from apps.insurance.models import InsurancePlan, InsuranceSubscription


@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    list_display = ("name", "monthly_premium", "coverage_amount", "is_active")
    list_filter = ("is_active",)


@admin.register(InsuranceSubscription)
class InsuranceSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("client", "plan", "start_date", "end_date", "status")
    list_filter = ("status", "plan")
    search_fields = ("client__email", "client__first_name", "client__last_name")
    readonly_fields = ("premium", "created_at")
