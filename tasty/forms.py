from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Length, Optional

class LoginForm(FlaskForm):
    email = EmailField('E-mail', validators=[
        DataRequired(message="O e-mail é obrigatório."), 
        Email(message="Digite um e-mail válido.")
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória.")
    ])
    submit = SubmitField('Entrar')


class RegisterForm(FlaskForm):
    name = StringField('Nome Completo', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(min=3, max=100, message="O nome deve ter entre 3 e 100 caracteres.")
    ])
    cpf = StringField('CPF', validators=[
        DataRequired(message="O CPF é obrigatório."),
        Length(min=11, max=14, message="Formato de CPF inválido.")
    ])
    email = EmailField('E-mail', validators=[
        DataRequired(message="O e-mail é obrigatório."), 
        Email(message="Digite um e-mail válido.")
    ])
    phone = StringField('Telefone', validators=[
        Optional(),
        Length(min=10, max=15, message="Telefone inválido.")
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória."),
        Length(min=6, message="A senha deve ter no mínimo 6 caracteres.")
    ])
    role = SelectField('Tipo de Conta', choices=[
        ('client', 'Quero Comer'),
        ('owner', 'Tenho um Negócio')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Criar Conta')