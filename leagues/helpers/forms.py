from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    username = UsernameField(max_length=254, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username', 'autofocus': True,}))
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.', widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'first_name', 'placeholder': 'first name',}))
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.', widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'last_name', 'placeholder': 'last name',}))
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.', widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'email', 'placeholder': 'email',}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'password',}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'confirm password',}))
    link_yahoo = forms.BooleanField(widget=forms.CheckboxInput(attrs={'name': 'link_yahoo', 'checked': True}))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'link_yahoo')


