from flask import (
    Blueprint, render_template, flash, redirect, url_for, request, session, current_app
)
import tasty.services.user_service as service
from tasty.utils.forms import LoginForm, RegisterForm

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")

@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    """Gerencia o processo de login, incluindo validação de formulário e autenticação."""
    if "user_id" in session:
        role = session.get("user_role", "client")
        current_app.logger.info(f"Usuário já logado (ID: {session['user_id']}, Role: {role}). Redirecionando para o dashboard.")
        return redirect(url_for(f"{role}.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        success, msg, code, user = service.login(
            email=form.email.data, 
            password=form.password.data
        )
        
        if success and user:
            session.clear()
            session.permanent = True 
            
            user_role = user.role.name.lower()
            
            session["user_id"] = user.id
            session["user_role"] = user_role
            session["user_name"] = user.name
            
            flash(f"Bem-vindo de volta, {user.name}!", "success")
            
            next_page = request.args.get("next")
            current_app.logger.info(f"Login bem-sucedido para usuário ID {user.id} com role '{user_role}'. Redirecionando para: {next_page or url_for(f'{user_role}.dashboard')}")
            return redirect(next_page or url_for(f"{user_role}.dashboard"))
            
        else:
            flash(msg, "danger")
    current_app.logger.info("Tentativa de login falhou.")
    return render_template("auth/login.html", form=form)

@bp_auth.route("/register", methods=["GET", "POST"])
def register():
    """Gerencia o processo de registro, incluindo validação de formulário e criação de conta."""
    if "user_id" in session:
        flash("Você já está conectado. Saia da sua conta atual para criar uma nova.", "info")
        role = session.get("user_role", "client")
        current_app.logger.info(f"Usuário já logado (ID: {session['user_id']}, Role: {role}). Redirecionando para o dashboard.")
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
            current_app.logger.info(f"Registro bem-sucedido para email: {data['email']}. Redirecionando para login.")
            return redirect(url_for("auth.login"))
        else:
            flash(msg, "danger")
    current_app.logger.info("Tentativa de registro falhou.")
    return render_template("auth/register.html", form=form)


@bp_auth.route("/logout")
def logout():
    """Destrói ativamente a sessão do usuário."""
    session.clear()
    current_app.logger.info(f"Usuário desconectado (ID: {session.get('user_id')}).")
    flash("Sessão encerrada com segurança.", "info")
    return redirect(url_for("main.index"))