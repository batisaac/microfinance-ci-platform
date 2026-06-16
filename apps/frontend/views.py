from django.views.generic import TemplateView


class LoginView(TemplateView):
    template_name = "login.html"


class DashboardView(TemplateView):
    template_name = "dashboard.html"


class LoanListView(TemplateView):
    template_name = "loans_list.html"


class LoanDetailView(TemplateView):
    template_name = "loan_detail.html"


class InsuranceListView(TemplateView):
    template_name = "insurance_list.html"


class NotificationListView(TemplateView):
    template_name = "notifications.html"


class ChatView(TemplateView):
    template_name = "chat.html"
