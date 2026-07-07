from django import forms
from .models import Entry

class EntryForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-950 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-950 focus:ring-offset-2',
            'placeholder': 'Enter entry name...',
            'list': 'name-choices',
            'required': 'required'
        }),
        label="Name"
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
                'type': 'date'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
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
