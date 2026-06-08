from flask import (
    Blueprint, render_template, flash, redirect, url_for, request, session
)
import tasty.services.user_service as service

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")

@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    # Se já estiver logado, redireciona para o painel correto da sua role
    if "user_id" in session:
        role = session.get("user_role", "client")
        return redirect(url_for(f"{role}.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Espera-se que o formulário de login possua um select/hidden para o tipo de acesso
        role = request.form.get("role", "client") 

        success, msg, code, user = service.login(email, password, role)
        
        if success and user:
            session.clear() # Prevenção contra fixação de sessão
            session["user_id"] = user.id
            session["user_role"] = role
            session["user_name"] = user.name
            
            flash(f"Bem-vindo, {user.name}!", "success")
            
            # Redirecionamento dinâmico seguro pós-login
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for(f"{role}.dashboard"))
            
        else:
            flash(msg, "danger")

    return render_template("auth/login.html")


@bp_auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
            "cpf": request.form.get("cpf"),
            "phone": request.form.get("phone")
        }
        
        # Define se está criando um cliente ou um dono de negócio
        role_choice = request.form.get("role", "client")
        
        if role_choice == "owner":
            success, msg, code = service.create_business_owner(data)
        else:
            success, msg, code = service.create_client(data)

        if success:
            flash("Conta criada com sucesso! Faça seu login.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(msg, "danger")

    return render_template("auth/register.html")


@bp_auth.route("/logout")
def logout():
    session.clear()
    flash("Você saiu com sucesso.", "info")
    return redirect(url_for("auth.login"))