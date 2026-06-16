from django.urls import path

from apps.insurance.views import (
    PlanListView, SubscribeView, MyPoliciesView, PolicyDetailView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="insurance_plans"),
    path("subscribe/", SubscribeView.as_view(), name="insurance_subscribe"),
    path("my-policies/", MyPoliciesView.as_view(), name="insurance_my_policies"),
    path("my-policies/<int:pk>/", PolicyDetailView.as_view(), name="insurance_policy_detail"),
]
