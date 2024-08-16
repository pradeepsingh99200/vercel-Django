from django import forms

class BlinkForm(forms.Form):
    name = forms.CharField(max_length=100, label='Your Name')
    camera_access = forms.BooleanField(required=True, label='Grant Camera Access')
