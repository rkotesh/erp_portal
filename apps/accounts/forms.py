from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.accounts.models import User
from apps.academics.models import Department
from django.contrib.auth.password_validation import validate_password

class RoleAuthenticationForm(AuthenticationForm):
    role = forms.ChoiceField(choices=User.Role.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('code'), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Your Department"
    )

    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        role = cleaned_data.get('role')
        department = cleaned_data.get('department')
        
        if user:
            if user.role != role:
                raise forms.ValidationError(f"This account is registered as {user.role}, not {role}.")
            
            # Roles that MUST specify a department
            dept_roles = ['Faculty', 'HOD', 'Mentor', 'Student']
            if role in dept_roles:
                if not department:
                    raise forms.ValidationError("Please select your department.")
                if user.department != department:
                    raise forms.ValidationError(f"Incorrect department for this user.")
        
        return cleaned_data

class VerifyOTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6, 
        min_length=6, 
        widget=forms.TextInput(attrs={
            'class': 'input-glass text-center', 
            'placeholder': '000000',
            'style': 'font-size: 2rem; letter-spacing: 0.5rem; font-weight: bold;',
            'pattern': '[0-9]*',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code'
        })
    )
