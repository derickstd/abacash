from django.contrib import admin
from common.admin import CEOOnlyActionsAdminMixin
from .models import Company, Domain, CompanyRegistration


class DomainInline(CEOOnlyActionsAdminMixin, admin.TabularInline):
    model = Domain
    extra = 1


@admin.register(Company)
class CompanyAdmin(CEOOnlyActionsAdminMixin, admin.ModelAdmin):
    ceo_only_readonly_fields = ("is_active", "provisioning_status", "provisioning_step")
    list_display = ("name", "schema_name", "is_active", "created_on")
    inlines = [DomainInline]


@admin.register(CompanyRegistration)
class CompanyRegistrationAdmin(CEOOnlyActionsAdminMixin, admin.ModelAdmin):
    ceo_only_readonly_fields = ("status",)
    list_display  = ("company_name", "contact_name", "email", "phone", "plan", "status", "submitted_at")
    list_filter   = ("status", "plan", "country")
    search_fields = ("company_name", "contact_name", "email", "phone")
    list_editable = ("status",)
    readonly_fields = ("submitted_at",)
    ordering = ("-submitted_at",)

    def get_list_editable(self, request):
        return self.list_editable if self._is_ceo(request) else ()
