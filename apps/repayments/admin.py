from django.contrib import admin

from apps.repayments.models import Repayment


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "loan", "amount", "principal_paid", "interest_paid", "penalty_paid", "payment_date", "method")
    list_filter = ("method", "payment_date")
    search_fields = ("loan__id", "reference", "agent__email")
    readonly_fields = ("principal_paid", "interest_paid", "penalty_paid", "created_at")
