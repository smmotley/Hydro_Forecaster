from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput
from django import forms
from .models import DateRange


class DateRangeForm(forms.ModelForm):
    class Meta:
        model = DateRange
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': DatePickerInput(options={
                "format": "YYYY-MM-DD",  # moment date-time format
                "showClose": True,
                "showClear": True,
                "showTodayButton": True,
            }
            ),
            'end_date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",  # moment date-time format
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
        }
