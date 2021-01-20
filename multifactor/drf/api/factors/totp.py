import pyotp

from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response


from multifactor.app_settings import mf_settings
from multifactor.common import write_session
from multifactor.factors.totp import WINDOW
from multifactor.models import KEY_TYPE_TOPT, UserKey

from .index import ListFactorAPIView
from .mixins import SpecificFactorMixIn
from ..messages import Error
from ..serializers import TOTPSerializer


class TOPTFactorApiView(SpecificFactorMixIn, mixins.CreateModelMixin, ListFactorAPIView):
    key_type = KEY_TYPE_TOPT
    serializer_class = TOTPSerializer

    secret_key = None
    totp = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.secret_key = request.POST.get("key", pyotp.random_base32())
        self.totp = pyotp.TOTP(self.secret_key)

    @action(detail=False, methods=['GET'])
    def qr(self, request):
        return Response({
            "qr": self.totp.provisioning_uri(
                request.user.get_username(),
                issuer_name=mf_settings['TOKEN_ISSUER_NAME']
            ),
            "secret_key": self.secret_key,
        })

    def create(self, request, *args, **kwargs):
        if self.totp.verify(request.data["answer"], valid_window=WINDOW):
            key = UserKey.objects.create(
                user=request.user,
                properties={"secret_key": self.secret_key},
                key_type=KEY_TYPE_TOPT
            )
            write_session(request, key)

            serializer = self.get_serializer(data=key)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
                headers=self.get_success_headers(serializer.data)
            )

        return Error('Could not validate key, please try again.')

    @action(detail=False, methods=['POST'])
    def authenticate(self, request):
        token = request.data['answer']
        for key in self.get_queryset().filter(enabled=True):
            if pyotp.TOTP(key.properties["secret_key"]).verify(token, valid_window=WINDOW):
                write_session(request, key)
                return Response(status=status.HTTP_200_OK)
        return Error('Could not validate key, please try again.')
