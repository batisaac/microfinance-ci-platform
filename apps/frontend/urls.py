from django.urls import path
from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("loans/", views.LoanListView.as_view(), name="loans_list"),
    path("loans/<int:pk>/", views.LoanDetailView.as_view(), name="loan_detail"),
    path("insurance/", views.InsuranceListView.as_view(), name="insurance_list"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("chat/", views.ChatView.as_view(), name="chat"),
]
