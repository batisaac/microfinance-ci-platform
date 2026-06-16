from django.contrib import admin

from apps.credits.models import Loan, LoanDocument, LoanSchedule


class LoanDocumentInline(admin.TabularInline):
    model = LoanDocument
    extra = 1


class LoanScheduleInline(admin.TabularInline):
    model = LoanSchedule
    extra = 0
    readonly_fields = ("installment_number", "due_date", "amount", "status")


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "amount", "status", "eligibility_score", "created_at")
    list_filter = ("status",)
    search_fields = ("client__email", "client__first_name", "client__last_name")
    readonly_fields = ("eligibility_score", "monthly_payment", "created_at", "updated_at")
    inlines = [LoanDocumentInline, LoanScheduleInline]
    fieldsets = (
        (None, {"fields": ("client", "analyzed_by", "status")}),
        ("Détails du prêt", {"fields": ("amount", "purpose", "duration_months", "interest_rate")}),
        ("Calculs", {"fields": ("eligibility_score", "monthly_payment")}),
        ("Notes", {"fields": ("agent_notes",)}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(LoanDocument)
class LoanDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "loan", "description", "uploaded_at")


@admin.register(LoanSchedule)
class LoanScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "loan", "installment_number", "due_date", "amount", "status")
    list_filter = ("status",)
