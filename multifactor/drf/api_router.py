from django.conf import settings
from rest_framework import routers

from .api import factors as factor_views

if settings.DEBUG:
    router = routers.DefaultRouter()
else:
    router = routers.SimpleRouter()

router.register("fido2", factor_views.Fido2FactorApiView, basename="multifactor-drf-fido2")
router.register("totp", factor_views.TOPTFactorApiView, basename="multifactor-drf-totp")
router.register("u2f", factor_views.U2FFactorApiView, basename="multifactor-drf-u2f")
router.register("", factor_views.ListFactorAPIView, basename="multifactor-drf-index")

urlpatterns = router.urls
