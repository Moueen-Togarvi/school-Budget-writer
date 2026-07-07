from django import forms
from .models import Entry

class EntryForm(forms.ModelForm):
    NAME_CHOICES = [
        ('', '--- Select Category/Name ---'),
        ('Standard Expenses', (
            ('Staff Payment', 'Staff Payment'),
            ('Other Expenses', 'Other Expenses'),
            ('Stationery', 'Stationery'),
            ('Internet Bill', 'Internet Bill'),
            ('Electricity Bill', 'Electricity Bill'),
            ('Petrol', 'Petrol'),
        )),
        ('Infrastructure & Maintenance', (
            ('Fans', 'Fans'),
            ('Fans Repair', 'Fans Repair'),
            ('Water Cooler', 'Water Cooler'),
            ('Doors', 'Doors'),
            ('Room Build', 'Room Build'),
        )),
        ('Other Options', (
            ('Other', 'Other (Type Custom Category)...'),
        ))
    ]

    name = forms.ChoiceField(
        choices=NAME_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-950 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-950 focus:ring-offset-2 form-select',
            'required': 'required'
        }),
        label="Name"
    )

    custom_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-950 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-950 focus:ring-offset-2',
            'placeholder': 'Enter custom category name...'
        }),
        label="Custom Category Name"
    )

    class Meta:
        model = Entry
        fields = ['name', 'money', 'income', 'date']
        widgets = {
            'money': forms.NumberInput(attrs={
                'class': 'w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-950 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-950 focus:ring-offset-2 pl-9', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            'income': forms.NumberInput(attrs={
                'class': 'w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-950 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-950 focus:ring-offset-2 pl-9', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            'date': forms.DateInput(attrs={
                'class': 'w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-950 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-950 focus:ring-offset-2', 
                'type': 'date',
                'required': 'required'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Extract flat list of predefined choice values
        predefined = []
        for group_name, group_choices in self.NAME_CHOICES:
            if isinstance(group_choices, (list, tuple)):
                for val, label in group_choices:
                    if val and val != 'Other':
                        predefined.append(val)
            else:
                if group_name and group_name != 'Other':
                    predefined.append(group_name)

        if self.instance and self.instance.pk:
            name_val = self.instance.name
            if name_val not in predefined:
                self.initial['name'] = 'Other'
                self.initial['custom_name'] = name_val

        if self.is_bound and self.data.get('name') == 'Other':
            self.initial['custom_name'] = self.data.get('custom_name')

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        custom_name = cleaned_data.get('custom_name')

        if name == 'Other':
            if custom_name and custom_name.strip():
                cleaned_data['name'] = custom_name.strip()
            else:
                self.add_error('custom_name', 'Please enter a custom category name.')

        money = cleaned_data.get('money') or 0
        income = cleaned_data.get('income') or 0

        # Ensure no negative values
        if money < 0:
            self.add_error('money', 'Money cannot be negative.')
        if income < 0:
            self.add_error('income', 'Income cannot be negative.')

        # Custom logic: Either Money or Income must have a value > 0
        if money == 0 and income == 0:
            raise forms.ValidationError('Either Money or Income must have a value greater than zero.')

        return cleaned_data
