from django.urls import path

from apps.repayments.views import RepaymentListCreateView, RepaymentDetailView

urlpatterns = [
    path("", RepaymentListCreateView.as_view(), name="repayment_list_create"),
    path("<int:pk>/", RepaymentDetailView.as_view(), name="repayment_detail"),
]
