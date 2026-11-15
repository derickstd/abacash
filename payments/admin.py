from django.contrib import admin
from common.admin import CEOOnlyActionsAdminMixin
from .models import Payment, Receipt


@admin.register(Payment)
class PaymentAdmin(CEOOnlyActionsAdminMixin, admin.ModelAdmin):
    ceo_only_readonly_fields = (
        "status",
        "reversal_reason",
        "reversal_date",
        "reversed_by",
    )


@admin.register(Receipt)
class ReceiptAdmin(CEOOnlyActionsAdminMixin, admin.ModelAdmin):
    pass
