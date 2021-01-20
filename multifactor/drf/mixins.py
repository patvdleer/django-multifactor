from multifactor.common import active_factors
from multifactor.models import UserKey


class DrfMultiFactorMixin:
    """Verify that the current user is multifactor-authenticated or has no factors yet."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        self.active_factors = active_factors(request)
        self.factors = UserKey.objects.filter(user=request.user)
        self.has_multifactor = self.factors.filter(enabled=True).exists()


class DrfRequireDrfMultiAuthMixin(DrfMultiFactorMixin):
    """Require Multifactor, force user to add factors if none on account."""

    def dispatch(self, request, *args, **kwargs):
        if not self.active_factors:
            request.session['multifactor-next'] = request.get_full_path()
            if self.has_multifactor:
                # todo: redirect('multifactor:authenticate')
                pass
            # todo: redirect('multifactor:add')

        return super().dispatch(request, *args, **kwargs)


class DrfPreferDrfMultiAuthMixin(DrfMultiFactorMixin):
    """Use Multifactor if user has active factors."""

    def dispatch(self, request, *args, **kwargs):
        if not self.active_factors and self.has_multifactor:
            request.session['multifactor-next'] = request.get_full_path()
            # ToDo: redirect('multifactor:authenticate')

        return super().dispatch(request, *args, **kwargs)