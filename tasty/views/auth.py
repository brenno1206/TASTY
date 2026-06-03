from functools import wraps
from flask import (
    Blueprint, render_template, current_app, 
    flash, redirect, url_for, request, session
)
import tasty.services.user_service as service

# ==========================================================
# 1. DECORADORES AUXILIARES (PROTEÇÃO DE ROTAS)
# ==========================================================

def login_required(f):
    """Garante que o usuário está logado antes de acessar a rota."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """Garante que o usuário logado tem o papel (role) correto."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("user_role") != role_name:
                flash("Você não tem permissão para acessar esta área.", "danger")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==========================================================
# 2. AUTENTICAÇÃO (LOGIN, REGISTRO, LOGOUT)
# ==========================================================
bp_auth = Blueprint("auth", __name__, url_prefix="/auth")

@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    # Se já estiver logado, redireciona para o painel correto
    if "user_id" in session:
        role = session.get("user_role")
        return redirect(url_for(f"main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role") # Espera-se que o formulário envie 'admin', 'client' ou 'owner'

        success, msg, code, user = service.login(email, password, role)
        
        if success:
            session.clear() # Limpa sessões antigas por segurança
            session["user_id"] = user.id
            session["user_role"] = role
            session["user_name"] = user.name
            
            flash(f"Bem-vindo, {user.name}!", "success")
            return redirect(url_for(f"main.home"))
        else:
            flash(msg, "danger")

    return render_template("auth/login.html")


@bp_auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Monta o dicionário de dados a partir do formulário
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


# ==========================================================
# 3. CRUD DE ADMINISTRADORES
# ==========================================================
bp_admin = Blueprint("admin", __name__, url_prefix="/admin")

@bp_admin.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    return render_template("admin/dashboard.html")

@bp_admin.route("/users", methods=["GET"])
@login_required
@role_required("admin")
def list_admins():
    # Opcional: filtrar por level via query string (?level=max)
    level = request.args.get("level")
    if level:
        admins = service.get_admins_by_level(level)
    else:
        admins = service.get_all_admins()
    return render_template("admin/index.html", users=admins)

@bp_admin.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_admin():
    if request.method == "POST":
        data = dict(request.form) # Converte ImmutableMultiDict para dict
        success, msg, code = service.create_admin(data)
        if success:
            flash(msg, "success")
            return redirect(url_for("admin.list_admins"))
        flash(msg, "danger")
    
    return render_template("admin/form.html", action="Criar")

@bp_admin.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_admin(id):
    admin_user = service.get_admin(id)
    if not admin_user:
        flash("Administrador não encontrado.", "warning")
        return redirect(url_for("admin.list_admins"))

    if request.method == "POST":
        data = dict(request.form)
        # Se a senha estiver em branco no form, remove do dicionário para não atualizar
        if not data.get("password"):
            data.pop("password", None)
            
        success, msg, code = service.update_admin(id, data)
        if success:
            flash(msg, "success")
            return redirect(url_for("admin.list_admins"))
        flash(msg, "danger")

    return render_template("admin/form.html", user=admin_user, action="Editar")

@bp_admin.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_admin(id):
    success, msg, code = service.delete_admin(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.list_admins"))


# ==========================================================
# 4. CRUD DE CLIENTES
# ==========================================================
bp_client = Blueprint("client", __name__, url_prefix="/client")

@bp_client.route("/dashboard")
@login_required
@role_required("client")
def dashboard():
    return render_template("client/dashboard.html")

# Visão do admin gerenciando clientes (pode ficar no bp_admin também, mas agrupado aqui por entidade)
@bp_client.route("/list", methods=["GET"])
@login_required
@role_required("admin") 
def list_clients():
    clients = service.get_all_clients()
    return render_template("client/index.html", users=clients)

@bp_client.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(id):
    # Proteção: Apenas o próprio cliente ou um admin podem editar
    if session.get("user_role") != "admin" and session.get("user_id") != id:
        flash("Acesso negado.", "danger")
        return redirect(url_for("client.dashboard"))

    client_user = service.get_client(id)
    if request.method == "POST":
        data = dict(request.form)
        if not data.get("password"): data.pop("password", None)
            
        success, msg, code = service.update_client(id, data)
        if success:
            flash(msg, "success")
            return redirect(request.referrer or url_for("client.dashboard"))
        flash(msg, "danger")

    return render_template("client/form.html", user=client_user)

@bp_client.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_client(id):
    success, msg, code = service.delete_client(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("client.list_clients"))


# ==========================================================
# 5. CRUD DE DONOS DE NEGÓCIO (OWNERS)
# ==========================================================
bp_owner = Blueprint("owner", __name__, url_prefix="/owner")

@bp_owner.route("/dashboard")
@login_required
@role_required("owner")
def dashboard():
    return render_template("owner/dashboard.html")

@bp_owner.route("/list", methods=["GET"])
@login_required
@role_required("admin")
def list_owners():
    owners = service.get_all_business_owners()
    return render_template("owner/index.html", users=owners)

@bp_owner.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_owner(id):
    # Proteção: Apenas o próprio dono ou um admin podem editar
    if session.get("user_role") != "admin" and session.get("user_id") != id:
        flash("Acesso negado.", "danger")
        return redirect(url_for("owner.dashboard"))

    owner_user = service.get_business_owner(id)
    if request.method == "POST":
        data = dict(request.form)
        if not data.get("password"): data.pop("password", None)
            
        success, msg, code = service.update_business_owner(id, data)
        if success:
            flash(msg, "success")
            return redirect(request.referrer or url_for("owner.dashboard"))
        flash(msg, "danger")

    return render_template("owner/form.html", user=owner_user)

@bp_owner.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_owner(id):
    success, msg, code = service.delete_business_owner(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("owner.list_owners"))