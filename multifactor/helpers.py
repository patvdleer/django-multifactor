from django.http import JsonResponse

from .views import authenticate
from .models import UserKey
from .factors import u2f, fido2, totp


def has_mfa(request):
    if UserKey.objects.filter(user=request.user, enabled=True).exists():
        return authenticate(request)
    return False


def has_mfa_keys(request):
    return UserKey.objects.filter(user=request.user, enabled=True).exists()


def is_mfa(request):
    return request.session.get("multifactor", {}).get("verified", False)


def recheck(request):
    method = request.session.get("multifactor", {}).get("method", None)
    if not method:
        return JsonResponse({"res": False})
    elif method == "U2F":
        return JsonResponse({"html": u2f.recheck(request).content})
    elif method == "FIDO2":
        return JsonResponse({"html": fido2.recheck(request).content})
    elif method == "TOTP":
        return JsonResponse({"html": totp.recheck(request).content})