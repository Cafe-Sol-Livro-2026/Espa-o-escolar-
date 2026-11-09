from functools import wraps

import mysql.connector
from flask import (
    Flask, flash, redirect, render_template,
    request, session, url_for
)
from werkzeug.security import generate_password_hash

from config import DB_CONFIG, SECRET_KEY


app = Flask(__name__)
app.secret_key = SECRET_KEY


def conectar():
    return mysql.connector.connect(**DB_CONFIG)


def exige_sessao(chave, rota_cadastro):
    """Impede acesso a uma página sem o cadastro correspondente."""
    def decorador(funcao):
        @wraps(funcao)
        def decorada(*args, **kwargs):
            if chave not in session:
                flash("Faça seu cadastro para continuar.")
                return redirect(url_for(rota_cadastro))
            return funcao(*args, **kwargs)
        return decorada
    return decorador


def fechar(conexao, cursor):
    if cursor:
        cursor.close()
    if conexao and conexao.is_connected():
        conexao.close()


@app.route("/")
def inicio():
    return render_template("inicio.html")


# ---------------------------------------------------------
# DOADOR
# ---------------------------------------------------------

@app.route("/cadastro/doador", methods=["GET", "POST"])
def cadastro_doador():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        cpf = (
            request.form.get("cpf", "")
            .replace(".", "")
            .replace("-", "")
            .strip()
        )
        celular = request.form.get("celular", "").strip()

        if not all([nome, email, senha, cpf, celular]):
            flash("Preencha todos os campos.")
            return render_template("cadastro_doador.html")

        if len(cpf) != 11 or not cpf.isdigit():
            flash("O CPF deve conter 11 números.")
            return render_template("cadastro_doador.html")

        conexao = cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO doadores
                    (nome, email, senha_hash, cpf, celular)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    nome,
                    email,
                    generate_password_hash(senha),
                    cpf,
                    celular,
                ),
            )
            conexao.commit()

            session.clear()
            session["id_doador"] = cursor.lastrowid
            session["nome_doador"] = nome

            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("projeto"))

        except mysql.connector.IntegrityError:
            if conexao:
                conexao.rollback()
            flash("Este e-mail ou CPF já está cadastrado.")
        except mysql.connector.Error:
            if conexao:
                conexao.rollback()
            app.logger.exception("Erro ao cadastrar doador")
            flash("Não foi possível salvar o cadastro. Confira o banco de dados.")
        finally:
            fechar(conexao, cursor)

    return render_template("cadastro_doador.html")


@app.route("/projeto")
@exige_sessao("id_doador", "cadastro_doador")
def projeto():
    return render_template("projeto.html")


@app.route("/doacao", methods=["GET", "POST"])
@exige_sessao("id_doador", "cadastro_doador")
def doacao():
    conexao = cursor = None
    receptores = []

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id_receptor, razao_social
            FROM receptores
            ORDER BY razao_social
            """
        )
        receptores = cursor.fetchall()
    except mysql.connector.Error:
        app.logger.exception("Erro ao carregar receptores")
        flash("Não foi possível carregar os receptores.")
    finally:
        fechar(conexao, cursor)

    if request.method == "POST":
        tipo_doacao = request.form.get("tipo_doacao", "").strip()
        valor_texto = request.form.get("valor", "").strip()
        data_doacao = request.form.get("data_doacao", "").strip()
        local_recebimento = request.form.get("local_recebimento", "").strip()
        id_receptor_texto = request.form.get("id_receptor", "").strip()

        if not all([
            tipo_doacao, valor_texto, data_doacao,
            local_recebimento, id_receptor_texto
        ]):
            flash("Preencha todos os campos da doação.")
            return render_template("doacao.html", receptores=receptores)

        try:
            valor = float(valor_texto)
            id_receptor = int(id_receptor_texto)
            if valor < 0:
                raise ValueError
        except ValueError:
            flash("Confira o valor e o receptor selecionado.")
            return render_template("doacao.html", receptores=receptores)

        conexao = cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO doacoes
                    (id_doador, id_receptor, tipo_doacao, valor,
                     data_doacao, local_recebimento, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'pendente')
                """,
                (
                    session["id_doador"],
                    id_receptor,
                    tipo_doacao,
                    valor,
                    data_doacao,
                    local_recebimento,
                ),
            )
            conexao.commit()
            flash("Doação cadastrada com sucesso!")
            return redirect(url_for("projeto"))

        except mysql.connector.Error:
            if conexao:
                conexao.rollback()
            app.logger.exception("Erro ao cadastrar doação")
            flash("Não foi possível salvar a doação.")
        finally:
            fechar(conexao, cursor)

    return render_template("doacao.html", receptores=receptores)


# ---------------------------------------------------------
# EMISSOR E SOLICITAÇÕES
# ---------------------------------------------------------

@app.route("/cadastro-emissor", methods=["GET", "POST"])
def cadastro_emissor():
    if request.method == "POST":
        cnpj = (
            request.form.get("cnpj", "")
            .replace(".", "")
            .replace("/", "")
            .replace("-", "")
            .strip()
        )
        razao_social = request.form.get("razao_social", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not all([cnpj, razao_social, email, senha]):
            flash("Preencha todos os campos.")
            return render_template("cadastro_emissor.html")

        if len(cnpj) != 14 or not cnpj.isdigit():
            flash("O CNPJ deve conter 14 números.")
            return render_template("cadastro_emissor.html")

        conexao = cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO emissores
                    (cnpj, razao_social, email, senha_hash)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    cnpj,
                    razao_social,
                    email,
                    generate_password_hash(senha),
                ),
            )
            conexao.commit()

            session.clear()
            session["id_emissor"] = cursor.lastrowid
            session["razao_social_emissor"] = razao_social

            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("nova_solicitacao"))

        except mysql.connector.IntegrityError:
            if conexao:
                conexao.rollback()
            flash("Esse CNPJ ou e-mail já está cadastrado.")
        except mysql.connector.Error:
            if conexao:
                conexao.rollback()
            app.logger.exception("Erro ao cadastrar emissor")
            flash("Não foi possível salvar o cadastro.")
        finally:
            fechar(conexao, cursor)

    return render_template("cadastro_emissor.html")


@app.route("/solicitacao", methods=["GET", "POST"])
@exige_sessao("id_emissor", "cadastro_emissor")
def nova_solicitacao():
    campos = [
        "problema_mostrado",
        "descricao_problema",
        "duracao_problema",
        "afetados",
        "projeto_solucao",
        "descricao_projeto",
        "data_prevista_inicio",
        "data_prevista_finalizacao",
    ]

    if request.method == "POST":
        dados = {
            campo: request.form.get(campo, "").strip()
            for campo in campos
        }

        if not all(dados.values()):
            flash("Preencha todos os campos.")
            return render_template("solicitacao.html", dados=dados)

        if dados["data_prevista_finalizacao"] < dados["data_prevista_inicio"]:
            flash("A data de finalização não pode ser anterior à data de início.")
            return render_template("solicitacao.html", dados=dados)

        conexao = cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO solicitacoes (
                    id_emissor, problema_mostrado, descricao_problema,
                    duracao_problema, afetados, projeto_solucao,
                    descricao_projeto, data_prevista_inicio,
                    data_prevista_finalizacao
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session["id_emissor"],
                    dados["problema_mostrado"],
                    dados["descricao_problema"],
                    dados["duracao_problema"],
                    dados["afetados"],
                    dados["projeto_solucao"],
                    dados["descricao_projeto"],
                    dados["data_prevista_inicio"],
                    dados["data_prevista_finalizacao"],
                ),
            )
            conexao.commit()
            flash("Solicitação salva com sucesso!")
            return redirect(url_for("nova_solicitacao"))

        except mysql.connector.Error:
            if conexao:
                conexao.rollback()
            app.logger.exception("Erro ao salvar solicitação")
            flash("Não foi possível salvar a solicitação.")
        finally:
            fechar(conexao, cursor)

    return render_template("solicitacao.html", dados={})


# ---------------------------------------------------------
# RECEPTOR E AJUDA
# ---------------------------------------------------------

@app.route("/cadastro-receptor", methods=["GET", "POST"])
def cadastro_receptor():
    if request.method == "POST":
        cnpj = (
            request.form.get("cnpj", "")
            .replace(".", "")
            .replace("/", "")
            .replace("-", "")
            .strip()
        )
        razao_social = request.form.get("razao_social", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not all([cnpj, razao_social, email, senha]):
            flash("Preencha todos os campos.")
            return render_template("cadastro_receptor.html")

        if len(cnpj) != 14 or not cnpj.isdigit():
            flash("O CNPJ deve conter 14 números.")
            return render_template("cadastro_receptor.html")

        conexao = cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO receptores
                    (cnpj, razao_social, email, senha_hash)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    cnpj,
                    razao_social,
                    email,
                    generate_password_hash(senha),
                ),
            )
            conexao.commit()

            session.clear()
            session["id_receptor"] = cursor.lastrowid
            session["razao_social_receptor"] = razao_social

            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("inicio"))

        except mysql.connector.IntegrityError:
            if conexao:
                conexao.rollback()
            flash("Esse CNPJ ou e-mail já está cadastrado.")
        except mysql.connector.Error:
            if conexao:
                conexao.rollback()
            app.logger.exception("Erro ao cadastrar receptor")
            flash("Não foi possível salvar o cadastro.")
        finally:
            fechar(conexao, cursor)

    return render_template("cadastro_receptor.html")