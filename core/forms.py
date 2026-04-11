from django import forms
from .models import PedidoAfiliacaoAtleta, PedidoAfiliacaoAcademia, Atleta
import re

def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', str(cpf))
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True

class FormAfiliacaoAtleta(forms.ModelForm):
    class Meta:
        model = PedidoAfiliacaoAtleta
        fields = ['nome', 'cpf', 'email', 'whatsapp', 'academia_desejada', 'modalidade', 'termo_lgpd', 'foto']

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if not validar_cpf(cpf):
            raise forms.ValidationError("CPF inválido. Verifique os números.")
        return cpf

class FormAfiliacaoAcademia(forms.ModelForm):
    class Meta:
        model = PedidoAfiliacaoAcademia
        fields = ['nome_academia', 'nome_responsavel', 'cpf_responsavel', 'email', 'whatsapp', 'endereco', 'termo_lgpd']

    def clean_cpf_responsavel(self):
        cpf = self.cleaned_data.get('cpf_responsavel')
        if not validar_cpf(cpf):
            raise forms.ValidationError("CPF do responsável é inválido.")
        return cpf

class FormAtualizarPerfil(forms.ModelForm):
    # O email não existe no modelo Atleta, então declaramos manualmente
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full bg-gray-700 text-white border border-gray-600 rounded py-2 px-3 focus:outline-none focus:border-brasilAmarelo'
    }))

    class Meta:
        model = Atleta
        fields = ['foto']
        widgets = {
            'foto': forms.FileInput(attrs={
                'class': 'w-full bg-gray-700 text-white border border-gray-600 rounded py-2 px-3 focus:outline-none focus:border-brasilAmarelo file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-brasilVerde file:text-white hover:file:bg-green-600 cursor-pointer'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        atleta = super().save(commit=False)
        # Salva o email na tabela User
        if self.user:
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            atleta.save()
        return atleta