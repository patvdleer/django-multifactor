from fido2 import cbor
from fido2.client import ClientData
from fido2.ctap2 import AttestedCredentialData, AttestationObject, AuthenticatorData
from fido2.server import Fido2Server
from fido2.utils import websafe_decode, websafe_encode
from fido2.webauthn import PublicKeyCredentialRpEntity
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from multifactor.app_settings import mf_settings
from multifactor.common import write_session
from multifactor.models import KEY_TYPE_FIDO2, UserKey

from .index import ListFactorAPIView
from .mixins import SpecificFactorMixIn
from ..messages import Success, Error
from ..serializers import FIDO2Serializer


def get_server():
    rp = PublicKeyCredentialRpEntity(
        mf_settings['FIDO_SERVER_ID'],
        mf_settings['FIDO_SERVER_NAME'],
        mf_settings['FIDO_SERVER_ICON']
    )
    return Fido2Server(rp)


class Fido2FactorApiView(SpecificFactorMixIn, mixins.CreateModelMixin, ListFactorAPIView):
    key_type = KEY_TYPE_FIDO2
    serializer_class = FIDO2Serializer

    def get_user_credentials(self, request):
        return [
            AttestedCredentialData(websafe_decode(uk.properties["device"]))
            for uk in self.get_queryset(
                properties__domain=request.get_host(),
                enabled=True,
            )
        ]

    @action(detail=False, methods=['GET'])
    def registration_data(self, request):
        server = get_server()
        registration_data, state = server.register_begin(
            {
                'id': request.user.get_username().encode("utf8"),
                'name': (request.user.get_full_name()),
                'displayName': request.user.get_username(),
            },
            self.get_user_credentials(request)
        )
        request.session['fido_state'] = state

        return Response(cbor.encode(registration_data), content_type='application/octet-stream')

    def create(self, request):
        try:
            data = cbor.decode(request.body)
            client_data = ClientData(data['clientDataJSON'])
            att_obj = AttestationObject((data['attestationObject']))
            server = get_server()
            auth_data = server.register_complete(
                request.session['fido_state'],
                client_data,
                att_obj
            )
            encoded = websafe_encode(auth_data.credential_data)
            key = UserKey.objects.create(
                user=request.user,
                properties={
                    "device": encoded,
                    "type": att_obj.fmt,
                    "domain": request.get_host(),
                },
                key_type=KEY_TYPE_FIDO2,
            )
            write_session(request, key)
            return Success('FIDO2 Token added!')
        except Exception as e:
            return Error("Error completing FIDO2 registration.")

    @action(detail=False, methods=['GET'], url_path="authenticate")
    def authenticate_get(self, request):
        server = get_server()
        auth_data, state = server.authenticate_begin(self.get_user_credentials(request))
        request.session['fido_state'] = state
        return Response(cbor.encode(auth_data), content_type="application/octet-stream")

    @action(detail=False, methods=['POST'], url_path="authenticate")
    def authenticate_post(self, request):
        server = get_server()
        data = cbor.decode(request.body)
        credential_id = data['credentialId']
        client_data = ClientData(data['clientDataJSON'])
        auth_data = AuthenticatorData(data['authenticatorData'])
        signature = data['signature']

        cred = server.authenticate_complete(
            request.session.pop('fido_state'),
            self.get_user_credentials(request),
            credential_id,
            client_data,
            auth_data,
            signature
        )

        keys = UserKey.objects.filter(
            user=request.user,
            key_type=KEY_TYPE_FIDO2,
            enabled=True,
        )

        for key in keys:
            if AttestedCredentialData(websafe_decode(key.properties["device"])).credential_id == cred.credential_id:
                write_session(request, key)
                return Success("")

        return Error("")
