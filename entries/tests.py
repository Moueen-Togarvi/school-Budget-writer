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
            name="Other Expenses",
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
            'name': 'Other Expenses',
            'money': 0,
            'income': 50000,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_both_can_be_positive(self):
        # Case 4: Both money and income > 0 (valid)
        form_data = {
            'name': 'Staff Payment',
            'money': 100,
            'income': 200,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_negative_values(self):
        # Case 5: Negative money (invalid)
        form_data = {
            'name': 'Staff Payment',
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
            'name': 'Staff Payment',
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

    def test_form_invalid_choice_name(self):
        # Invalid Choice name selection (invalid)
        form_data = {
            'name': 'Invalid School Category Name',
            'money': 25000,
            'income': 0,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_custom_category_name_valid(self):
        form_data = {
            'name': 'Other',
            'custom_name': 'Special School Trip',
            'money': 12000,
            'income': 0,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Special School Trip')

    def test_form_custom_category_name_invalid_if_empty(self):
        form_data = {
            'name': 'Other',
            'custom_name': '  ',
            'money': 12000,
            'income': 0,
            'date': '2026-07-07'
        }
        form = EntryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_name', form.errors)


class EntrySinglePageFlowTest(TestCase):
    def setUp(self):
        self.entry = Entry.objects.create(
            name="Electricity Bill",
            money=Decimal("8500.00"),
            income=Decimal("0.00"),
            date="2026-07-07"
        )

    def test_get_add_entry_redirects_to_list(self):
        url = reverse('entry_create')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('entry_list'))

    def test_get_edit_entry_redirects_to_list_with_query_param(self):
        url = reverse('entry_update', args=[self.entry.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('entry_list')}?edit={self.entry.pk}")

    def test_list_view_with_edit_query_param_renders_prepopulated_form(self):
        url = f"{reverse('entry_list')}?edit={self.entry.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_editing'])
        self.assertEqual(response.context['editing_entry'], self.entry)
        self.assertEqual(response.context['form'].instance, self.entry)


class EntryPDFExportTest(TestCase):
    def setUp(self):
        Entry.objects.create(
            name="Electricity Bill",
            money=Decimal("8500.00"),
            income=Decimal("0.00"),
            date="2026-07-07"
        )
        Entry.objects.create(
            name="Staff Payment",
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
        self.assertEqual(entries[0].name, "Staff Payment")
        self.assertEqual(entries[1].name, "Electricity Bill")
