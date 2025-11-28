from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, MeView, CreateMechanicView, MechanicDetailView,RequestPasswordResetView, ResetPasswordConfirmView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),            # POST { identifier, password }
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("auth/me/", MeView.as_view(), name="me"),                     # GET con Bearer access
    path("mechanics/", CreateMechanicView.as_view(), name="create-mechanic"),
    path("mechanics/<int:pk>/", MechanicDetailView.as_view(), name="mechanic-detail"),
    path("auth/password-reset/", RequestPasswordResetView.as_view(), name="password-reset-request"),
    path("auth/password-reset/confirm/", ResetPasswordConfirmView.as_view(), name="password-reset-confirm"),
]
