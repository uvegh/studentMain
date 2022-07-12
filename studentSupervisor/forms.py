import imp
from .models import ProjectComment, MeetingComment, Supervisor
from django.forms import ModelForm
from django.core.exceptions import ValidationError

# model forms

class CommentForm(ModelForm):
    class Meta:
        model = ProjectComment
        fields = [ 'comment']

    # def __init__(self, *args, **kwargs):
    #     """Save the request with the form so it can be accessed in clean_*()"""
    #     self.request = kwargs.pop('request', None)
    #     super(CommentForm, self).__init__(*args, **kwargs)

    # def clean_name(self):
    #     """Make sure people don't use my name"""
    #     data = self.cleaned_data['name']
    #     if not self.request.user.is_authenticated and data.lower().strip() == 'samuel':
    #         raise ValidationError("Sorry, you cannot use this name.")
    #     return data

class MeetingCommentForm(ModelForm):
    class Meta:
        model = MeetingComment
        fields = [ 'comment']

from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django import forms
from .models import User, Student

class StudentSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    
   

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 
        'department', 'institution', 'profile_pix', 'state_of_origin'
        )
    #     date_of_birth=forms.DateTimeField(
    #     input_formats=['%d/%m/%Y %H:%M'],
    #     widget=forms.DateTimeInput(attrs={
    #         'class': 'form-control datetimepicker-input',
    #         'data-target': '#datetimepicker1'
    #     })
    # )
    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        student = Student.objects.create(user=user)        
        return user


class SupervisorSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    
   

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 
        'department', 'institution', 'profile_pix', 'state_of_origin'
        )
    #     date_of_birth=forms.DateTimeField(
    #     input_formats=['%d/%m/%Y %H:%M'],
    #     widget=forms.DateTimeInput(attrs={
    #         'class': 'form-control datetimepicker-input',
    #         'data-target': '#datetimepicker1'
    #     })
    # )
    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_supervisor = True
        user.save()
        supervisor = Supervisor.objects.create(user=user)        
        return user
