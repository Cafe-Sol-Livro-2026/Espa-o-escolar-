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


def exige_login(funcao):
    @wraps(funcao)
    def decorada(*args, **kwargs):
        if "id_doador" not in session:
            flash("Faça seu cadastro para continuar.")
            return redirect(url_for("cadastro_doador"))
        return funcao(*args, **kwargs)
    return decorada


@app.route("/")
def inicio():
    return render_template("inicio.html")


@app.route("/cadastro/doador", methods=["GET", "POST"])
def cadastro_doador():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        cpf = request.form.get("cpf", "").replace(".", "").replace("-", "").strip()
        celular = request.form.get("celular", "").strip()

        if not all([nome, email, senha, cpf, celular]):
            flash("Preencha todos os campos.")
            return render_template("cadastro_doador.html")

        if len(cpf) != 11 or not cpf.isdigit():
            flash("Informe um CPF válido com 11 números, sem pontos ou traços.")
            return render_template("cadastro_doador.html")

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            senha_hash = generate_password_hash(senha)

            cursor.execute(
                """
                INSERT INTO doadores (nome, email, senha_hash, cpf, celular)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nome, email, senha_hash, cpf, celular)
            )
            conexao.commit()

            # Entra automaticamente após o cadastro
            session["id_doador"] = cursor.lastrowid
            session["nome_doador"] = nome

            return redirect(url_for("projeto"))

        except mysql.connector.IntegrityError:
            if conexao:
                conexao.rollback()
            flash("Este e-mail ou CPF já está cadastrado.")
        except mysql.connector.Error as erro:
            if conexao:
                conexao.rollback()
            app.logger.exception("Erro ao cadastrar doador")
            flash("Não foi possível concluir o cadastro. Verifique a conexão com o banco.")
        finally:
            if cursor:
                cursor.close()
            if conexao and conexao.is_connected():
                conexao.close()

    return render_template("cadastro_doador.html")


@app.route("/projeto")
@exige_login
def projeto():
    return render_template("projeto.html")


@app.route("/doacao", methods=["GET", "POST"])
@exige_login
def doacao():
    conexao = None
    cursor = None
    receptores = []

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_receptor, razao_social FROM receptores ORDER BY razao_social"
        )
        receptores = cursor.fetchall()
    except mysql.connector.Error:
        app.logger.exception("Erro ao carregar receptores")
        flash("Não foi possível carregar a lista de receptores.")
    finally:
        if cursor:
            cursor.close()
        if conexao and conexao.is_connected():
            conexao.close()

    if request.method == "POST":
        tipo_doacao = request.form.get("tipo_doacao", "").strip()
        valor = request.form.get("valor", "").strip()
        data_doacao = request.form.get("data_doacao", "").strip()
        local_recebimento = request.form.get("local_recebimento", "").strip()
        id_receptor = request.form.get("id_receptor", "").strip()

        if not all([tipo_doacao, valor, data_doacao, local_recebimento, id_receptor]):
            flash("Preencha todos os campos da doação.")
            return render_template("doacao.html", receptores=receptores)

        try:
            valor = float(valor)
            id_receptor = int(id_receptor)
            if valor < 0:
                raise ValueError
        except ValueError:
            flash("Confira o valor e o receptor selecionado.")
            return render_template("doacao.html", receptores=receptores)

        conexao = None
        cursor = None

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
                    local_recebimento
                )
            )
            conexao.commit()
            flash("Doação cadastrada com sucesso!")
            return redirect(url_for("projeto"))

        except mysql.connector.Error:
            if conexao:
                conexao.rollback()
            app.logger.exception("Erro ao cadastrar doação")
            flash("Não foi possível salvar a doação. Confira os dados e tente novamente.")
        finally:
            if cursor:
                cursor.close()
            if conexao and conexao.is_connected():
                conexao.close()

    return render_template("doacao.html", receptores=receptores)


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)