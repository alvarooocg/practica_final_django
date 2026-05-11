from django import forms
from .models import CustomUser, Sala, Actividad


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            'nombre', 'tipo', 'horario', 'descripcion', 'duracion',
            'plazas_disponibles', 'monitor', 'sala_principal', 'salas_secundarias',
        ]
        widgets = {
            'horario': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['monitor'].queryset = CustomUser.objects.filter(rol='monitor')
        self.fields['sala_principal'].queryset = Sala.objects.all()
        self.fields['salas_secundarias'].queryset = Sala.objects.all()
        if self.instance.pk:
            self.fields['horario'].initial = self.instance.horario.strftime('%Y-%m-%dT%H:%M')


class SalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = ['nombre', 'capacidad', 'ubicacion', 'responsable']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = CustomUser.objects.filter(rol='responsable')


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'edad', 'telefono', 'especializacion']

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'edad', 'telefono']


class MonitorForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput, required=False,
        help_text='Dejar en blanco para no cambiar.'
    )
    password2 = forms.CharField(
        label='Confirmar contraseña', widget=forms.PasswordInput, required=False
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'especializacion']

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
