from flask import (
    Blueprint, render_template, flash, redirect, url_for, request, session
)
import tasty.services.user_service as service
from tasty.forms import LoginForm, RegisterForm

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")

@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        role = session.get("user_role", "client")
        return redirect(url_for(f"{role}.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        # Passamos apenas e-mail e senha para o serviço unificado
        success, msg, code, user = service.login(
            email=form.email.data, 
            password=form.password.data
        )
        
        if success and user:
            session.clear()
            session.permanent = True 
            
            # Captura a role real que está gravada no banco de dados do usuário
            user_role = user.role.name.lower()
            
            session["user_id"] = user.id
            session["user_role"] = user_role
            session["user_name"] = user.name
            
            flash(f"Bem-vindo de volta, {user.name}!", "success")
            
            next_page = request.args.get("next")
            return redirect(next_page or url_for(f"{user_role}.dashboard"))
            
        else:
            # Renderiza os erros consistentes ('Usuário não encontrado', 'Senha incorreta') na div flash
            flash(msg, "danger")

    return render_template("auth/login.html", form=form)

@bp_auth.route("/register", methods=["GET", "POST"])
def register():
    # 1. Trava de Segurança: Usuário já logado não pode criar conta
    if "user_id" in session:
        flash("Você já está conectado. Saia da sua conta atual para criar uma nova.", "info")
        role = session.get("user_role", "client")
        return redirect(url_for(f"{role}.dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():
        data = {
            "name": form.name.data,
            "email": form.email.data,
            "password": form.password.data,
            "cpf": form.cpf.data,
            "phone": form.phone.data
        }
        
        if form.role.data == "owner":
            success, msg, code = service.create_business_owner(data)
        else:
            success, msg, code = service.create_client(data)

        if success:
            flash("Conta criada com sucesso! Faça seu login para continuar.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(msg, "danger")

    return render_template("auth/register.html", form=form)


@bp_auth.route("/logout")
def logout():
    """Destrói ativamente a sessão do usuário."""
    session.clear()
    flash("Sessão encerrada com segurança.", "info")
    return redirect(url_for("main.index"))