class CEOOnlyActionsAdminMixin:
    ceo_only_readonly_fields = ()

    @staticmethod
    def _is_ceo(request):
        return getattr(request.user, "role", None) == "CEO"

    def has_delete_permission(self, request, obj=None):
        return self._is_ceo(request) and super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if self._is_ceo(request):
            return readonly_fields
        return tuple(dict.fromkeys((*readonly_fields, *self.ceo_only_readonly_fields)))
