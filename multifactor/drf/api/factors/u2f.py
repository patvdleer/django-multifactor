import hashlib
import json

from rest_framework import mixins
from rest_framework.decorators import action
from u2flib_server import u2f
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding

from multifactor.app_settings import mf_settings
from multifactor.common import write_session
from multifactor.models import KEY_TYPE_U2F, UserKey

from .index import ListFactorAPIView
from .mixins import SpecificFactorMixIn
from ..messages import Error, Info, Success
from ..serializers import U2FSerializer


class U2FFactorApiView(SpecificFactorMixIn, mixins.CreateModelMixin, ListFactorAPIView):
    key_type = KEY_TYPE_U2F
    serializer_class = U2FSerializer
    token = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        enroll = u2f.begin_registration(mf_settings['U2F_APPID'], [])
        request.session['multifactor_u2f_enroll_'] = enroll.json
        self.token = json.dumps(enroll.data_for_client)

    def create(self, request, *args, **kwargs):
        if 'response' not in request.data:
            return Error("Missing U2F response, please try again.")

        response = request.data["response"]
        if any(x not in response for x in ['clientData', 'registrationData', 'version']):
            return Error("Invalid U2F response, please try again.")

        device, cert = u2f.complete_registration(
            request.session['multifactor_u2f_enroll_'],
            json.loads(response),
            [mf_settings['U2F_APPID']]
        )
        cert = x509.load_der_x509_certificate(cert, default_backend())
        cert_hash = hashlib.sha384(cert.public_bytes(Encoding.PEM)).hexdigest()

        if self.get_queryset(properties__domain=request.get_host(), properties__cert=cert_hash).exists():
            return Info("That key's already in your account.")

        key = UserKey.objects.create(
            user=request.user,
            key_type=KEY_TYPE_U2F,
            properties={
                "device": json.loads(device.json),
                "cert": cert_hash,
                "domain": request.get_host(),
            },
        )
        write_session(request, key)
        return Success("U2F key added to account.")

    @action(detail=False, methods=['POST'])
    def authenticate(self, request, *args, **kwargs):
        keys = self.get_queryset(
            properties__domain=request.get_host(),
            enabled=True
        )
        if not keys.exists():
            return Error('You have no U2F devices for this domain.')

        data = json.loads(request.data["response"])
        if data.get("errorCode", 0) != 0:
            return Error("Invalid security key response.")

        challenge = u2f.begin_authentication(
            mf_settings['U2F_APPID'],
            list(keys.values_list("properties__device", flat=True))
        )

        challenge = json.dumps(challenge.data_for_client)
        device, c, t = u2f.complete_authentication(challenge, data, [mf_settings['U2F_APPID']])

        key = keys.get(properties__device__publicKey=device["publicKey"])
        write_session(request, key)
        return Success("")
