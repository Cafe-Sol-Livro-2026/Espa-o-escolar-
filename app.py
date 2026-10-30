from flask import Flask, request, redirect, url_for, render_template, render_template_string
import mysql.connector
from config import DB_CONFIG

app = Flask(__name__)

def conectar():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/")
def index():
    return render_template("index.html")

# Campos exibidos em cada formulário.
# Para campos relacionados, informe a tabela, a chave e o texto do menu.
TABELAS = {
    "usuario": {
        "titulo": "Usuários",
        "campos": {
            "nome": ("Nome", "texto"),
            "email": ("E-mail", "email"),
            "senha": ("Senha", "senha"),
            "perfil": ("Perfil", "opcoes", [
                "Diretora", "Pedagoga",
                "Administrador_Estoque", "Representante_Governo"
            ]),
            "status": ("Status", "opcoes", ["Ativo", "Inativo"]),
        },
    },
    "item": {
        "titulo": "Itens do estoque",
        "campos": {
            "nome_item": ("Nome do item", "texto"),
            "tipo": ("Tipo", "texto"),
            "quantidade_total": ("Quantidade total", "numero"),
            "quantidade_disponivel": ("Quantidade disponível", "numero"),
            "status": ("Status", "opcoes", ["Disponível", "Indisponível"]),
        },
    },
    "doador": {
        "titulo": "Doadores",
        "campos": {
            "nome_doador": ("Nome / razão social", "texto"),
            "tipo_doador": ("Tipo", "opcoes", ["PF", "PJ", "ONG"]),
            "documento": ("CPF/CNPJ", "texto"),
            "contato": ("Contato", "texto"),
            "email": ("E-mail", "email"),
        },
    },
    "escola_emissora": {
        "titulo": "Escolas",
        "campos": {
            "nome_escola": ("Nome da escola", "texto"),
            "codigo_inep": ("Código INEP", "texto"),
            "endereco": ("Endereço", "texto"),
            "telefone": ("Telefone", "texto"),
        },
    },
    "governo_receptor": {
        "titulo": "Órgãos do governo",
        "campos": {
            "orgao_secretaria": ("Órgão / secretaria", "texto"),
            "esfera": ("Esfera", "opcoes", ["Municipal", "Estadual", "Federal"]),
            "responsavel_legal": ("Responsável legal", "texto"),
        },
    },
    "doacao": {
        "titulo": "Doações",
        "campos": {
            "id_doador": ("Doador", "relacao", "doador", "id_doador", "nome_doador"),
            "id_escola_destino": ("Escola de destino", "relacao", "escola_emissora", "id_escola", "nome_escola"),
            "status_doacao": ("Status", "opcoes", ["Oferecida", "Em Trânsito", "Recebida", "Recusada"]),
        },
    },
    "item_doacao": {
        "titulo": "Itens das doações",
        "campos": {
            "id_doacao": ("Doação", "relacao", "doacao", "id_doacao", "id_doacao"),
            "descricao_item": ("Descrição do item", "texto"),
            "quantidade": ("Quantidade", "numero"),
            "estado_conservacao": ("Estado de conservação", "opcoes", ["Novo", "Bom", "Regular"]),
        },
    },
    "solicitacao_ajuda_governo": {
        "titulo": "Solicitações de ajuda ao governo",
        "campos": {
            "numero_oficio": ("Número do ofício", "texto"),
            "id_escola": ("Escola", "relacao", "escola_emissora", "id_escola", "nome_escola"),
            "id_governo": ("Órgão do governo", "relacao", "governo_receptor", "id_governo", "orgao_secretaria"),
            "descricao_necessidade": ("Descrição da necessidade", "area"),
            "urgencia": ("Urgência", "opcoes", ["Baixa", "Média", "Alta"]),
            "status_solicitacao": ("Status", "opcoes", ["Tramitando", "Em Análise", "Aprovada", "Rejeitada"]),
        },
    },
    "permissao_ajuda_governo": {
        "titulo": "Permissões de ajuda do governo",
        "campos": {
            "id_solicitacao_governo": ("Solicitação", "relacao", "solicitacao_ajuda_governo", "id_solicitacao_governo", "numero_oficio", True),
            "id_governo_emissor": ("Governo emissor", "relacao", "governo_receptor", "id_governo", "orgao_secretaria"),
            "id_escola_beneficiada": ("Escola beneficiada", "relacao", "escola_emissora", "id_escola", "nome_escola"),
            "numero_portaria_autorizacao": ("Número da portaria", "texto"),
            "tipo_ajuda": ("Tipo de ajuda", "opcoes", ["Cessão de Imóvel/Móvel", "Verba Direta", "Autorização de Expansão"]),
            "valor_verba_liberada": ("Valor liberado", "decimal"),
            "detalhes_ajuda": ("Detalhes da ajuda", "area"),
        },
    },
    "solicitacao": {
        "titulo": "Solicitações internas",
        "campos": {
            "numero_protocolo": ("Número do protocolo", "texto_opcional"),
            "id_solicitante": ("Solicitante", "relacao", "usuario", "id_usuario", "nome"),
            "id_analista": ("Analista", "relacao", "usuario", "id_usuario", "nome", True),
            "data_uso": ("Data de uso", "data"),
            "periodo": ("Período", "texto"),
            "motivo_justificativa": ("Motivo / justificativa", "area"),
            "status": ("Status", "opcoes", ["Pendente", "Aprovado", "Recusado", "Entregue", "Cancelado"]),
        },
    },
    "item_solicitacao": {
        "titulo": "Itens das solicitações",
        "campos": {
            "id_solicitacao": ("Solicitação", "relacao", "solicitacao", "id_solicitacao", "numero_protocolo"),
            "id_item": ("Item", "relacao", "item", "id_item", "nome_item"),
            "quantidade_solicitada": ("Quantidade solicitada", "numero"),
        },
    },
}

def buscar_opcoes(tabela, chave, descricao):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(f"SELECT {chave}, {descricao} FROM {tabela} ORDER BY {chave}")
    resultado = cursor.fetchall()
    cursor.close()
    conexao.close()
    return resultado

@app.route("/")
def inicio():
    links = "".join(
        f'<li><a href="/{tabela}">{config["titulo"]}</a></li>'
        for tabela, config in TABELAS.items()
    )
    return f"<h1>Gestão de Móveis Escolares</h1><ul>{links}</ul>"

@app.route("/<tabela>", methods=["GET", "POST"])
def gerenciar(tabela):
    if tabela not in TABELAS:
        return "Tabela não encontrada.", 404

    config = TABELAS[tabela]
    campos = config["campos"]

    if request.method == "POST":
        colunas = []
        valores = []

        for campo, definicao in campos.items():
            tipo = definicao[1]
            valor = request.form.get(campo)

            if tipo == "relacao" and not valor and len(definicao) > 6 and definicao[6]:
                valor = None

            if tipo == "texto_opcional" and not valor:
                valor = None

            colunas.append(campo)
            valores.append(valor)

        nomes = ", ".join(colunas)
        marcadores = ", ".join(["%s"] * len(valores))
        sql = f"INSERT INTO {tabela} ({nomes}) VALUES ({marcadores})"

        conexao = conectar()
        cursor = conexao.cursor()
        try:
            cursor.execute(sql, valores)
            conexao.commit()
        except mysql.connector.Error as erro:
            conexao.rollback()
            return f"Erro ao cadastrar: {erro}", 400
        finally:
            cursor.close()
            conexao.close()

        return redirect(url_for("gerenciar", tabela=tabela))

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {tabela}")
    registros = cursor.fetchall()
    cursor.close()
    conexao.close()

    formulario = ""

    for campo, definicao in campos.items():
        rotulo, tipo = definicao[0], definicao[1]
        obrigatorio = not (tipo == "texto_opcional" or (tipo == "relacao" and len(definicao) > 6 and definicao[6]))
        required = "required" if obrigatorio else ""

        if tipo == "opcoes":
            opcoes = "".join(
                f'<option value="{opcao}">{opcao}</option>'
                for opcao in definicao[2]
            )
            entrada = f'<select name="{campo}" {required}>{opcoes}</select>'
        elif tipo == "relacao":
            _, _, tabela_ref, chave_ref, descricao_ref, *opcional = definicao
            opcoes = buscar_opcoes(tabela_ref, chave_ref, descricao_ref)
            entrada = f'<select name="{campo}" {required}>'
            if opcional and opcional[0]:
                entrada += '<option value="">Não informado</option>'
            for id_ref, texto in opcoes:
                entrada += f'<option value="{id_ref}">{texto} (ID {id_ref})</option>'
            entrada += "</select>"
        elif tipo == "area":
            entrada = f'<textarea name="{campo}" required></textarea>'
        else:
            tipo_html = {
                "texto": "text",
                "texto_opcional": "text",
                "email": "email",
                "senha": "password",
                "numero": "number",
                "decimal": "number",
                "data": "date",
            }.get(tipo, "text")
            extra = 'step="0.01"' if tipo == "decimal" else ""
            entrada = f'<input type="{tipo_html}" name="{campo}" {required} {extra}>'

        formulario += f"<label>{rotulo}</label><br>{entrada}<br><br>"

    tabela_html = "<table border='1' cellpadding='6'><tr>"
    if registros:
        for coluna in registros[0].keys():
            tabela_html += f"<th>{coluna}</th>"
        tabela_html += "</tr>"
        for registro in registros:
            tabela_html += "<tr>"
            for valor in registro.values():
                tabela_html += f"<td>{valor if valor is not None else ''}</td>"
            tabela_html += "</tr>"
    tabela_html += "</table>"

    return render_template_string("""
        <p><a href="/">Voltar ao menu</a></p>
        <h2>{{ titulo }}</h2>
        <form method="POST">{{ formulario|safe }}<button type="submit">Cadastrar</button></form>
        <hr><h3>Registros cadastrados</h3>
        {{ tabela_html|safe }}
    """, titulo=config["titulo"], formulario=formulario, tabela_html=tabela_html)

if __name__ == "__main__":
    app.run(debug=True)