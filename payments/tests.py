from types import SimpleNamespace
from decimal import Decimal
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from accounts.templatetags.aba_filters import amount_in_words
from payments import views as payment_views
from payments.admin import PaymentAdmin
from payments.models import Payment
from payments.views import _receipt_document_basename


class AmountInWordsTests(SimpleTestCase):
    def test_formats_amount_in_words(self):
        self.assertEqual(
            amount_in_words(Decimal("1234567")),
            "one million two hundred thirty-four thousand five hundred sixty-seven Uganda shillings only",
        )

    def test_matches_receipt_display_for_fractional_amounts(self):
        self.assertEqual(
            amount_in_words(Decimal("100.99")),
            "one hundred Uganda shillings only",
        )

    def test_formats_zero_and_negative_amounts(self):
        self.assertEqual(amount_in_words(Decimal("0")), "zero Uganda shillings only")
        self.assertEqual(
            amount_in_words(Decimal("-5")),
            "minus five Uganda shillings only",
        )


class ReceiptDocumentNameTests(SimpleTestCase):
    def test_filename_includes_company_client_and_tenant_slug(self):
        self.assertEqual(
            _receipt_document_basename(
                "Acme Finance Ltd",
                "Amina N. Kato",
                "acme_finance",
            ),
            "acme-finance-ltd-amina-n-kato-acme-finance",
        )

    def test_filename_removes_path_characters(self):
        self.assertEqual(
            _receipt_document_basename("Acme/Finance", "Amina Kato", "acme"),
            "acme-finance-amina-kato-acme",
        )


class CreditRefundRoleTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client_pk = "12345678-1234-5678-1234-567812345678"

    @patch("payments.views.messages.error")
    def test_non_ceo_cannot_open_refund_form(self, show_error):
        request = self.factory.get("/")
        request.user = SimpleNamespace(role="MANAGER", is_authenticated=True)

        response = payment_views.credit_refund(request, client_pk=self.client_pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("clients:detail", kwargs={"pk": self.client_pk}),
        )
        show_error.assert_called_once()

    @patch("payments.views.render", return_value=HttpResponse())
    @patch("payments.views.can_access_branch_object", return_value=True)
    @patch("payments.views.get_object_or_404")
    def test_ceo_can_open_refund_form(self, get_object, _branch_access, render):
        request = self.factory.get("/")
        request.user = SimpleNamespace(role="CEO", is_authenticated=True)
        client = SimpleNamespace()
        get_object.return_value = client

        response = payment_views.credit_refund(request, client_pk=self.client_pk)

        self.assertEqual(response.status_code, 200)
        render.assert_called_once_with(
            request,
            "payments/credit_refund.html",
            {"client": client},
        )


class PaymentAdminRoleTests(SimpleTestCase):
    def setUp(self):
        self.payment_admin = PaymentAdmin(Payment, AdminSite())

    def test_non_ceo_cannot_delete_or_reverse_payment_in_admin(self):
        request = SimpleNamespace(
            user=SimpleNamespace(
                role="MANAGER",
                has_perm=lambda _permission: True,
            )
        )

        self.assertFalse(self.payment_admin.has_delete_permission(request))
        readonly_fields = self.payment_admin.get_readonly_fields(request)
        self.assertTrue(
            {"status", "reversal_reason", "reversal_date", "reversed_by"}.issubset(
                readonly_fields
            )
        )

    def test_ceo_can_delete_payment_when_django_permission_is_granted(self):
        request = SimpleNamespace(
            user=SimpleNamespace(
                role="CEO",
                has_perm=lambda _permission: True,
            )
        )

        self.assertTrue(self.payment_admin.has_delete_permission(request))
