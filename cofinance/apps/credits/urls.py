from django.urls import path

from apps.credits.views import LoanListCreateView, LoanDetailView, LoanStatusUpdateView

urlpatterns = [
    path("", LoanListCreateView.as_view(), name="loan_list_create"),
    path("<int:pk>/", LoanDetailView.as_view(), name="loan_detail"),
    path("<int:pk>/status/", LoanStatusUpdateView.as_view(), name="loan_status"),
]
