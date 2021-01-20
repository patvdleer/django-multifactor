from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from multifactor.models import UserKey
from ..messages import Info
from ..serializers import UserKeySerializer


class ListFactorAPIView(mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.ListModelMixin,
                        GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserKeySerializer
    queryset = UserKey.objects.all()

    def get_queryset(self, *args, **kwargs):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=["GET"])
    def toggle(self, request, *args, **kwargs):
        factor = self.get_object()
        factor.enabled = not factor.enabled
        factor.save()
        return Info(f'{factor.get_key_type_display()} has been {"enabled" if factor.enabled else "disabled"}.')
