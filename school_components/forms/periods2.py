from django import forms
from django.forms import ModelForm, HiddenInput, DateInput, ModelMultipleChoiceField, BooleanField
from school_components.models import Period, School, Department, Class, Course
from accounts.models import TeacherUser

class PeriodForm(forms.ModelForm):
    user_school = None

    class Meta:
        model = Period
        school = forms.CharField(widget=forms.HiddenInput())
        fields = ['description','start_date', 'end_date', 'comments']
        widgets = {
			'comments': forms.Textarea(attrs={'rows': 5}),
			'start_date': DateInput(attrs={'class':'datepicker'}),
			'end_date': DateInput(attrs={'class':'datepicker'}),
		}

        def clean(self):
                cleaned_data = super(PeriodForm, self).clean() 
                sd = cleaned_data.get('start_date')
                ed = cleaned_data.get('end_date')

                if sd == None or ed == None:
                        raise forms.ValidationError("You must include both start and end dates.")

                #check that start_date <= end_date
                if sd > ed:
                        raise forms.ValidationError("Your period ends before it starts!")

                #check that the start_date and end_date don't overlap with other periods'
                if self.user_school != None:
                        periods = Period.objects.filter(school=self.user_school)
                        for p in periods:
                                psd = p.start_date
                                ped = p.end_date

                                if ((sd <= psd and psd <= ed) or (sd <= ped and ped <= ed) or
                                        (psd <= sd and sd <= ped) or (psd <= ed and ed <= ped)):
                                        raise forms.ValidationError("Your period is overlapping with " + str(p))

                return cleaned_data
                

        def __init__(self, *args, **kwargs):
                    super(PeriodForm, self).__init__(*args, **kwargs)
                    self.user_school = args[1]#kwargs.get('user_school')