from rest_framework.serializers import ModelSerializer

from ...models import UserKey


class UserKeySerializer(ModelSerializer):
    class Meta:
        model = UserKey
        fields = [
            "name",
            "key_type",
            "enabled",
            "added_on",
            "expires",
            "last_used",
        ]
        read_only_fields = [
            "key_type",
            "added_on",
            "expires",
            "last_used",
        ]


class FIDO2Serializer(UserKeySerializer):
    pass


class TOTPSerializer(UserKeySerializer):
    pass


class U2FSerializer(UserKeySerializer):
    pass
