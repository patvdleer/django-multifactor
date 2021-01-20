
class SpecificFactorMixIn:
    key_type = None

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(key_type=self.key_type)
