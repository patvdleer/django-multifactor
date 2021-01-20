from rest_framework.decorators import action

from multifactor.app_settings import mf_settings
from multifactor.models import DisabledFallback

from . import ListFactorAPIView
from ..messages import Info, Error


class FallbackFactorApiView(ListFactorAPIView):

    @action(detail=True, methods=["GET"])
    def toggle(self, request, ident):
        if not (ident and ident in mf_settings['FALLBACKS']):
            return Error('Invalid fallback.')

        n, _ = DisabledFallback.objects.filter(user=request.user, fallback=ident).delete()
        if n:  # managed to delete something
            return Info(f"{ident} fallback factor has been re-enabled.")

        DisabledFallback(user=request.user, fallback=ident).save()
        return Info(f"{ident} fallback factor has been disabled.")
