from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .api import EuView, ReservaViewSet, VeiculoViewSet

router = DefaultRouter()
router.register("veiculos", VeiculoViewSet, basename="veiculo")
router.register("reservas", ReservaViewSet, basename="reserva")

urlpatterns = [
    path("login/", TokenObtainPairView.as_view()),
    path("login/renovar/", TokenRefreshView.as_view()),
    path("eu/", EuView.as_view()),
    path("", include(router.urls)),
]
