from django.forms import *
from django import forms
from school_components.models import *
from accounts.models import TeacherUser
from django.forms.models import BaseModelFormSet

class AttendanceDateForm(ModelForm):
    start_date = forms.DateField(widget=DateInput(attrs={'class':'datepicker'}), required=True)
    end_date = forms.DateField(widget=DateInput(attrs={'class':'datepicker'}), required=True)
    
    class Meta:
        model = Period
        fields = ['start_date', 'end_date']
        # widgets = {
        # 	'start_date': DateInput(attrs={'class':'datepicker'}),
        # 	'end_date': DateInput(attrs={'class':'datepicker'}),
        # }

