from invoke import task
from datetime import datetime
import os
import zipfile
import shutil
from dotenv import load_dotenv


# ==========================================================
# GERENCIAMENTO DE AMBIENTE
# ==========================================================

def load_env(env: str):
    """
    Carrega o arquivo .env correspondente ao ambiente.
    Ex: dev, test, prod
    """
    env_file = f".env.{env}"

    if not os.path.exists(env_file):
        raise FileNotFoundError(
            f"Erro Crítico: O arquivo de ambiente '{env_file} não foi encontrado."
        )

    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
        print(f"[ENV] Carregado: {env_file}")
    else:
        raise FileNotFoundError(f"{env_file} não encontrado")


# ==========================================================
# INSTALACAO
# ==========================================================

@task
def install(c, dev=True):
    """
    Instala o projeto.
    """
    if dev:
        c.run('pip install -e ".[dev,test]"', echo=True)
    else:
        c.run("pip install .", echo=True)


@task
def uninstall(c):
    """
    Remove o pacote instalado.
    """
    c.run("pip uninstall -y delivery", echo=True)


# ==========================================================
# EXECUCAO
# ==========================================================

@task
def run(c):
    """
    Executa a aplicacao Flask em ambiente de desenvolvimento.
    """
    load_dotenv(".env.dev", override=True)

    env = os.environ.copy()

    c.run("flask --app tasty:create_app run --debug --reload", env=env, pty=False)


@task
def prod(c):
    """
    Executa a aplicacao em modo producao.
    """
    load_env("prod")
    c.run("flask run")


# ==========================================================
# TESTES
# ==========================================================

@task
def test(c):
    """
    Executa os testes automatizados.
    """
    load_env("test")
    c.run("pytest -v", env={"PYTHONPATH": "."})


# ==========================================================
# QUALIDADE DE CODIGO
# ==========================================================

@task
def lint(c):
    """
    Verifica qualidade de codigo.
    """
    c.run("flake8")


@task
def format(c):
    """
    Formata o codigo automaticamente.
    """
    c.run("black .")

@task
def create_db_dev(c):
    load_env("dev")

    c.run(
        "flask create-db",
        env=os.environ.copy(),
        pty=False
    )

@task
def seed_dev(c):
    """
    Executa o comando de seed garantindo o ambiente de desenvolvimento.
    """
    load_env("dev")
    os.system("flask seed-dev")


# ==========================================================
# LIMPEZA GITHUB
# ==========================================================

@task
def clean(c):
    """
    Exclui arquivos e pastas indesejadas a partir do diretório atual.
    """
    excludes = ["venv", "__pycache__", ".git", ".vscode", "tasty.egg-info"]

    print("→ Iniciando a exclusão dos arquivos e pastas...")

    for root, dirs, files in os.walk(".", topdown=True):

        for d in list(dirs):
            if d in excludes:
                dir_path = os.path.join(root, d)
                print(f"  Removendo pasta: {dir_path}")
                shutil.rmtree(dir_path, ignore_errors=True)
                dirs.remove(d)

        for file in files:
            if file.endswith((".pyc", ".pyo", ".pyd", ".log", ".db", ".sqlite3")):
                filepath = os.path.join(root, file)
                print(f"  Removendo arquivo: {filepath}")
                try:
                    os.remove(filepath)
                except OSError:
                    pass

    print("→ Limpeza concluída com sucesso!")