from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .api import EuView, ReservaViewSet, VeiculoViewSet
from .google_login import GoogleLoginView

router = DefaultRouter()
router.register("veiculos", VeiculoViewSet, basename="veiculo")
router.register("reservas", ReservaViewSet, basename="reserva")

urlpatterns = [
    path("login/google/", GoogleLoginView.as_view()),
    path("login/renovar/", TokenRefreshView.as_view()),
    path("eu/", EuView.as_view()),
    path("", include(router.urls)),
]