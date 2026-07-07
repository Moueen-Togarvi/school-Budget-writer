from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from .models import Entry
from .forms import EntryForm

class EntryModelTest(TestCase):
    def setUp(self):
        self.entry = Entry.objects.create(
            name="Staff Payment",
            money=Decimal("25000.00"),
            income=Decimal("0.00"),
            date=timezone.now().date()
        )

    def test_entry_string_representation(self):
        self.assertEqual(str(self.entry), "Staff Payment")

    def test_entry_default_values(self):
        entry_default = Entry.objects.create(
            name="Default Test",
            date=timezone.now().date()
        )
        self.assertEqual(entry_default.money, Decimal("0.00"))
        self.assertEqual(entry_default.income, Decimal("0.00"))


class EntryFormTest(TestCase):
    def test_form_validation_either_money_or_income_required(self):
        # Case 1: Both money and income are 0 (invalid)
        form_data = {
            'name': 'Electricity Bill',
            'money': 0,
            'income': 0,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Either Money or Income must have a value greater than zero.', form.non_field_errors())

        # Case 2: Only money is entered (valid)
        form_data = {
            'name': 'Electricity Bill',
            'money': 8500,
            'income': 0,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Case 3: Only income is entered (valid)
        form_data = {
            'name': 'Customer Payment',
            'money': 0,
            'income': 50000,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_both_can_be_positive(self):
        # Case 4: Both money and income > 0 (valid)
        form_data = {
            'name': 'Mixed Entry',
            'money': 100,
            'income': 200,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_negative_values(self):
        # Case 5: Negative money (invalid)
        form_data = {
            'name': 'Negative Money',
            'money': -50,
            'income': 0,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('money', form.errors)
        self.assertEqual(form.errors['money'], ['Money cannot be negative.'])

        # Case 6: Negative income (invalid)
        form_data = {
            'name': 'Negative Income',
            'money': 0,
            'income': -50,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('income', form.errors)
        self.assertEqual(form.errors['income'], ['Income cannot be negative.'])

    def test_form_validation_date_required(self):
        # Case 7: Date omitted (invalid)
        form_data = {
            'name': 'Staff Payment',
            'money': 25000,
            'income': 0,
            'date': ''
        }
        form = EntryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)


class EntryPDFExportTest(TestCase):
    def setUp(self):
        Entry.objects.create(
            name="Electricity Bill",
            money=Decimal("8500.00"),
            income=Decimal("0.00"),
            date="2026-07-07"
        )
        Entry.objects.create(
            name="Customer Payment",
            money=Decimal("0.00"),
            income=Decimal("50000.00"),
            date="2026-07-07"
        )

    def test_pdf_export_status_and_content_type(self):
        url = reverse('entry_pdf')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(b"".join(response.streaming_content)) > 0)

    def test_pdf_export_with_custom_headers(self):
        url = reverse('entry_pdf') + "?school_name=Beaconhouse&budget_period=July+2025"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_entry_list_ordering(self):
        url = reverse('entry_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        entries = list(response.context['entries'])
        self.assertEqual(entries[0].name, "Customer Payment")
        self.assertEqual(entries[1].name, "Electricity Bill")
