from django import forms

class UploadImageForm(forms.Form):
    locationName = forms.CharField(max_length=255, required=False)
    image = forms.ImageField()