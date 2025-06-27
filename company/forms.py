from django import forms
from core.models import ComapnyDocument

class CompanyDocumentForm(forms.ModelForm):
    class Meta:
        model = ComapnyDocument
        fields = ['document', 'category', 'description']
