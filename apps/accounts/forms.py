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

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}), validators=[validate_password])
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}))
    
    # Exclude admin-managed roles from self-registration
    EXCLUDED_ROLES = ['HR', 'Chairman', 'Director', 'Principal']
    REGISTRATION_ROLES = [(k, v) for k, v in User.Role.choices if k not in EXCLUDED_ROLES]
    role = forms.ChoiceField(choices=REGISTRATION_ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'role', 'department']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@college.edu'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all().order_by('code')
        self.fields['department'].required = False
        self.fields['department'].empty_label = 'Select Your Department'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
