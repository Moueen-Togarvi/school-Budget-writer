from django import forms
from .models import Entry

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['name', 'money', 'income', 'date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter entry name...',
                'required': 'required'
            }),
            'money': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            'income': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'required': 'required'
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
