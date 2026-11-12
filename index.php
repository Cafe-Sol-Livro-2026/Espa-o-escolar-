<?php
require_once __DIR__ . '/config.php';

$page = $_GET['page'] ?? 'inicio';

$permitidas = [
    'inicio',
    'cadastro_doador',
    'cadastro_receptor',
    'cadastro_emissor',
    'projeto',
    'doacao',
    'solicitacao',
    'governo',
    'sair'
];

if (!in_array($page, $permitidas, true)) {
    $page = 'inicio';
}

try {

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {

        $acao = $_POST['acao'] ?? '';

        // CADASTRO DE DOADOR

        if ($acao === 'cadastro_doador') {

            $nome = trim($_POST['nome'] ?? '');
            $email = trim($_POST['email'] ?? '');
            $cpf = preg_replace('/\D/', '', $_POST['cpf'] ?? '');
            $celular = trim($_POST['celular'] ?? '');
            $senha = $_POST['senha'] ?? '';

            if (
                $nome === '' ||
                !filter_var($email, FILTER_VALIDATE_EMAIL) ||
                strlen($cpf) !== 11 ||
                $celular === '' ||
                strlen($senha) < 6
            ) {
                throw new RuntimeException(
                    'Confira os campos. CPF deve ter 11 números e a senha pelo menos 6 caracteres.'
                );
            }

            $q = db()->prepare(
                'INSERT INTO doadores
                (nome, email, senha_hash, cpf, celular)
                VALUES (?, ?, ?, ?, ?)'
            );

            $q->execute([
                $nome,
                $email,
                password_hash($senha, PASSWORD_DEFAULT),
                $cpf,
                $celular
            ]);

            $_SESSION['usuario'] = [
                'id' => (int) db()->lastInsertId(),
                'tipo' => 'doador',
                'nome' => $nome
            ];

            aviso('Cadastro realizado com sucesso!');

            go('projeto');
        }

        // CADASTRO DE RECEPTOR E EMISSOR

        if (
            $acao === 'cadastro_receptor' ||
            $acao === 'cadastro_emissor'
        ) {

            $tipo = $acao === 'cadastro_receptor'
                ? 'receptor'
                : 'emissor';

            $cnpj = preg_replace('/\D/', '', $_POST['cnpj'] ?? '');
            $razao = trim($_POST['razao_social'] ?? '');
            $email = trim($_POST['email'] ?? '');
            $senha = $_POST['senha'] ?? '';

            if (
                strlen($cnpj) !== 14 ||
                $razao === '' ||
                !filter_var($email, FILTER_VALIDATE_EMAIL) ||
                strlen($senha) < 6
            ) {
                throw new RuntimeException(
                    'Confira os dados. CNPJ deve ter 14 números e a senha pelo menos 6 caracteres.'
                );
            }

            if ($tipo === 'receptor') {

                $q = db()->prepare(
                    'INSERT INTO receptores
                    (cnpj, razao_social, email, senha_hash)
                    VALUES (?, ?, ?, ?)'
                );

            } else {

                $q = db()->prepare(
                    'INSERT INTO emissores
                    (cnpj, razao_social, email, senha_hash)
                    VALUES (?, ?, ?, ?)'
                );
            }

            $q->execute([
                $cnpj,
                $razao,
                $email,
                password_hash($senha, PASSWORD_DEFAULT)
            ]);

            $_SESSION['usuario'] = [
                'id' => (int) db()->lastInsertId(),
                'tipo' => $tipo,
                'nome' => $razao
            ];

            aviso('Cadastro realizado com sucesso!');

            go('solicitacao');
        }

        // ENVIO DE SOLICITAÇÃO PELO EMISSOR

        if ($acao === 'solicitacao') {

            exigir_tipo('emissor');

            $inicio = $_POST['data_inicio'] ?? '';
            $fim = $_POST['data_fim'] ?? '';

            if (
                $inicio === '' ||
                $fim === '' ||
                $fim < $inicio
            ) {
                throw new RuntimeException(
                    'Informe as duas datas. A data final não pode ser anterior à inicial.'
                );
            }

            $q = db()->prepare(
                'INSERT INTO solicitacoes
                (
                    problema_mostrado,
                    descricao_problema,
                    duracao_problema,
                    afetados,
                    projeto_solucao,
                    descricao_projeto,
                    data_prevista_inicio,
                    data_prevista_finalizacao,
                    id_emissor
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
            );

            $q->execute([
                trim($_POST['problema'] ?? ''),
                trim($_POST['descricao_problema'] ?? ''),
                trim($_POST['duracao'] ?? ''),
                trim($_POST['afetados'] ?? ''),
                trim($_POST['projeto'] ?? ''),
                trim($_POST['descricao_projeto'] ?? ''),
                $inicio,
                $fim,
                usuario()['id']
            ]);

            $sid = (int) db()->lastInsertId();

            // Relaciona a solicitação aos receptores cadastrados.

            db()->prepare(
                'INSERT IGNORE INTO solicitacao_receptores
                (id_solicitacao, id_receptor)
                SELECT ?, id_receptor FROM receptores'
            )->execute([$sid]);

            aviso('Solicitação enviada e salva com sucesso!');

            go('inicio');
        }

        // EMISSÃO GOVERNAMENTAL PELO RECEPTOR

        if ($acao === 'permissao') {

            exigir_tipo('receptor');

            $q = db()->prepare(
                'INSERT INTO permissoes
                (
                    orgao_governo,
                    descricao_necessidade,
                    escola_solicitante,
                    projeto,
                    status,
                    descricao_doacao,
                    id_receptor
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)'
            );

            $q->execute([
                trim($_POST['orgao'] ?? ''),
                trim($_POST['necessidade'] ?? ''),
                trim($_POST['escola'] ?? ''),
                trim($_POST['projeto'] ?? ''),
                'Pendente',
                trim($_POST['descricao_doacao'] ?? ''),
                usuario()['id']
            ]);

            aviso('Emissão governamental enviada com sucesso!');

            go('inicio');
        }

        // CADASTRO DE DOAÇÃO

        if ($acao === 'doacao') {

            exigir_tipo('doador');

            $receptor = (int) ($_POST['id_receptor'] ?? 0);

            $valor = (float) str_replace(
                ',',
                '.',
                $_POST['valor'] ?? '0'
            );

            if ($receptor < 1 || $valor < 0) {
                throw new RuntimeException(
                    'Selecione um receptor e informe um valor válido.'
                );
            }

            $q = db()->prepare(
                'INSERT INTO doacoes
                (
                    id_doador,
                    id_receptor,
                    tipo_doacao,
                    valor,
                    data_doacao,
                    local_recebimento
                )
                VALUES (?, ?, ?, ?, ?, ?)'
            );

            $q->execute([
                usuario()['id'],
                $receptor,
                trim($_POST['tipo'] ?? ''),
                $valor,
                $_POST['data_doacao'] ?? '',
                trim($_POST['local'] ?? '')
            ]);

            aviso('Doação registrada com sucesso! Obrigado por ajudar.');

            go('inicio');
        }
    }

} catch (PDOException $ex) {

    aviso(
        $ex->getCode() === '23000'
            ? 'Já existe cadastro com esse CPF, CNPJ ou e-mail.'
            : 'Erro ao salvar. Confira se o MySQL está ligado e execute banco.sql.',
        'erro'
    );

} catch (Throwable $ex) {

    aviso($ex->getMessage(), 'erro');
}


// BOTÃO SAIR

if ($page === 'sair') {

    unset($_SESSION['usuario']);

    aviso('Você saiu da sua conta.');

    go('inicio');
}


// BUSCAR SOLICITAÇÃO PARA O RECEPTOR

$solicitacao = null;

if (
    $page === 'solicitacao' &&
    (usuario()['tipo'] ?? '') === 'receptor'
) {

    $q = db()->query(
        'SELECT s.*, e.razao_social AS emissor_nome
        FROM solicitacoes s
        JOIN emissores e
        ON e.id_emissor = s.id_emissor
        ORDER BY s.id_solicitacao DESC
        LIMIT 1'
    );

    $solicitacao = $q->fetch() ?: null;
}


// BUSCAR RECEPTORES PARA DOAÇÃO

$receptores = [];

if ($page === 'doacao') {

    $receptores = db()->query(
        'SELECT id_receptor, razao_social
        FROM receptores
        ORDER BY razao_social'
    )->fetchAll();
}

?>

<!DOCTYPE html>
<html lang="pt-BR">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Gestão de Móveis Escolares</title>

    <link rel="stylesheet" href="style.css">

</head>

<body>

<main class="pagina">

<?= mostrar_aviso(); ?>


<?php if ($page === 'inicio'): ?>

    <h1>
        Escolha seu tipo<br>
        de cadastro
    </h1>

    <nav class="opcoes">

        <a class="opcao" href="?page=cadastro_doador">
            <span class="icone">🤲</span>
            Cadastro de Doadores
        </a>

        <a class="opcao" href="?page=cadastro_receptor">
            <span class="icone">🏫</span>
            Cadastro de Receptores
        </a>

        <a class="opcao" href="?page=cadastro_emissor">
            <span class="icone">📄</span>
            Cadastro de Emissores
        </a>

    </nav>

    <?php if (usuario()): ?>

        <p class="centro">
            Conectado: <?= e(usuario()['nome']) ?>

            ·

            <a href="?page=sair">Sair</a>
        </p>

    <?php endif; ?>


<?php elseif (
    in_array(
        $page,
        [
            'cadastro_doador',
            'cadastro_receptor',
            'cadastro_emissor'
        ],
        true
    )
): ?>

    <?php $doador = $page === 'cadastro_doador'; ?>

    <h1 class="menor">
        Vamos realizar seu cadastro!<br>
        precisaremos só de algumas informações
        para prosseguirmos.
    </h1>

    <form class="formulario" method="POST">

        <input
            type="hidden"
            name="acao"
            value="<?= $doador
                ? 'cadastro_doador'
                : ($page === 'cadastro_receptor'
                    ? 'cadastro_receptor'
                    : 'cadastro_emissor') ?>"
        >

        <?php if ($doador): ?>

            <label>
                Nome:
                <input
                    name="nome"
                    maxlength="150"
                    required
                >
            </label>

            <label>
                Email:
                <input
                    type="email"
                    name="email"
                    required
                >
            </label>

            <label>
                Senha:
                <input
                    type="password"
                    name="senha"
                    minlength="6"
                    required
                >
            </label>

            <label>
                CPF:
                <input
                    name="cpf"
                    maxlength="14"
                    placeholder="000.000.000-00"
                    required
                >
            </label>

            <label>
                Celular:
                <input
                    name="celular"
                    placeholder="(00) 00000-0000"
                    required
                >
            </label>

        <?php else: ?>

            <label>
                CNPJ:
                <input
                    name="cnpj"
                    maxlength="18"
                    placeholder="00.000.000/0000-00"
                    required
                >
            </label>

            <label>
                Razão Social:
                <input
                    name="razao_social"
                    maxlength="200"
                    required
                >
            </label>

            <label>
                Email:
                <input
                    type="email"
                    name="email"
                    required
                >
            </label>

            <label>
                Senha:
                <input
                    type="password"
                    name="senha"
                    minlength="6"
                    required
                >
            </label>

        <?php endif; ?>

        <button type="submit">
            Continuar
        </button>

    </form>


<?php elseif ($page === 'projeto'): ?>

    <?php exigir_tipo('doador'); ?>

    <h1>Projeto:</h1>

    <h2>
        Espaço Escolar / Cantina da Escola
    </h2>

    <div class="linha-tempo"></div>

    <p class="texto-projeto">

        Descrição: Um espaço escolar, que não havia sido
        utilizado, podendo se transformar em uma cantina.

        <br><br>

        Um lugar que abrigaria os alunos em suas refeições,
        sem precisarem se preocupar com chuva, frio ou calor,
        podendo desfrutar de uma boa refeição em segurança.

        <br><br>

        O projeto trata-se de uma série de tendas com
        estrutura de aço, com lonas de tecido impermeáveis
        e isotérmicas que cobrirão o teto e formarão as
        paredes, podendo ser recolhidas para dar aos alunos
        ar fresco/vento; também haverá mesas e bancos
        para os alunos.

    </p>

    <img
        class="foto-projeto"
        src="assets/projeto-escolar.jpg"
        alt="Espaço escolar do projeto"
    >

    <p class="centro">

        Juntos, cada contribuição transforma a nossa
        visão em realidade :) venha ajudar e fazer
        a diferença no nosso projeto!

    </p>

    <a class="botao-link" href="?page=doacao">
        Faça sua doação aqui!!!
    </a>


<?php elseif ($page === 'doacao'): ?>

    <?php exigir_tipo('doador'); ?>

    <h1 class="menor">
        Formulário de Entrada de Doação
    </h1>

    <?php if (!$receptores): ?>

        <p class="aviso erro">
            Ainda não há receptores cadastrados.
            Um receptor precisa se cadastrar antes
            de receber doações.
        </p>

    <?php else: ?>

        <form class="formulario" method="POST">

            <input
                type="hidden"
                name="acao"
                value="doacao"
            >

            <label>
                Tipo de Doação:
                <input
                    name="tipo"
                    maxlength="100"
                    required
                >
            </label>

            <label>
                Valor da doação:
                <input
                    name="valor"
                    type="number"
                    min="0"
                    step="0.01"
                    required
                >
            </label>

            <label>
                Data da doação:
                <input
                    name="data_doacao"
                    type="date"
                    required
                >
            </label>

            <label>
                Local para receber doação:
                <input
                    name="local"
                    maxlength="255"
                    required
                >
            </label>

            <label>
                Receptor:

                <select name="id_receptor" required>

                    <option value="">
                        Selecione
                    </option>

                    <?php foreach ($receptores as $r): ?>

                        <option value="<?= $r['id_receptor'] ?>">
                            <?= e($r['razao_social']) ?>
                        </option>

                    <?php endforeach; ?>

                </select>

            </label>

            <button type="submit">
                Doar
            </button>

        </form>

    <?php endif; ?>


<?php elseif (
    $page === 'solicitacao' &&
    (usuario()['tipo'] ?? '') === 'receptor'
): ?>

    <?php exigir_tipo('receptor'); ?>

    <h1>
        Solicitação para<br>
        o Governo
    </h1>

    <?php if ($solicitacao): ?>

        <section class="dados-solicitacao">

            <p>
                <b>Problema Mostrado:</b>
                <?= e($solicitacao['problema_mostrado']) ?>
            </p>

            <p>
                <b>Descrição do problema:</b><br>
                <?= nl2br(e($solicitacao['descricao_problema'])) ?>
            </p>

            <p>
                <b>Duração do Problema:</b>
                <?= e($solicitacao['duracao_problema']) ?>
            </p>

            <p>
                <b>Afetados:</b>
                <?= e($solicitacao['afetados']) ?>
            </p>

            <p>
                <b>Projeto/Solução:</b>
                <?= e($solicitacao['projeto_solucao']) ?>
            </p>

            <p>
                <b>Descrição do Projeto:</b><br>
                <?= nl2br(e($solicitacao['descricao_projeto'])) ?>
            </p>

            <p>
                <b>Data prevista para inicialização:</b>
                <?= e($solicitacao['data_prevista_inicio']) ?>
            </p>

            <p>
                <b>Data prevista para finalização:</b>
                <?= e($solicitacao['data_prevista_finalizacao']) ?>
            </p>

        </section>

    <?php else: ?>

        <p class="aviso">
            Ainda não existe solicitação enviada por um emissor.
        </p>

    <?php endif; ?>

    <a class="botao-link" href="?page=governo">
        Ajudar
    </a>


<?php elseif ($page === 'solicitacao'): ?>

    <?php exigir_tipo('emissor'); ?>

    <h1 class="menor">
        Solicitação para o Governo
    </h1>

    <form class="formulario" method="POST">

        <input
            type="hidden"
            name="acao"
            value="solicitacao"
        >

        <label>
            Problema Mostrado:
            <input
                name="problema"
                maxlength="255"
                required
            >
        </label>

        <label>
            Descrição do problema:
            <textarea
                name="descricao_problema"
                required
            ></textarea>
        </label>

        <label>
            Duração do Problema:
            <input
                name="duracao"
                maxlength="100"
                required
            >
        </label>

        <label>
            Afetados:
            <input
                name="afetados"
                maxlength="255"
                required
            >
        </label>

        <label>
            Projeto/Solução:
            <input
                name="projeto"
                maxlength="150"
                required
            >
        </label>

        <label>
            Descrição do Projeto:
            <textarea
                name="descricao_projeto"
                required
            ></textarea>
        </label>

        <label>
            Data prevista para inicialização:
            <input
                type="date"
                name="data_inicio"
                required
            >
        </label>

        <label>
            Data prevista para finalização:
            <input
                type="date"
                name="data_fim"
                required
            >
        </label>

        <button type="submit">
            Enviar Solicitação
        </button>

    </form>


<?php elseif ($page === 'governo'): ?>

    <?php exigir_tipo('receptor'); ?>

    <h1>
        Emissão Governamental
    </h1>

    <form class="formulario" method="POST">

        <input
            type="hidden"
            name="acao"
            value="permissao"
        >

        <label>
            Órgão/Governo Ciente:
            <input
                name="orgao"
                maxlength="150"
                required
            >
        </label>

        <label>
            Descrição de Necessidade:
            <textarea
                name="necessidade"
                required
            ></textarea>
        </label>

        <label>
            Escola Solicitante:
            <input
                name="escola"
                maxlength="150"
                required
            >
        </label>

        <label>
            Projeto:
            <input
                name="projeto"
                maxlength="150"
                required
            >
        </label>

        <label>
            Status:
            <input
                value="Pendente"
                disabled
            >
        </label>

        <label>
            Descrição da Doação:
            <textarea
                name="descricao_doacao"
                required
            ></textarea>
        </label>

        <button type="submit">
            Enviar solicitação
        </button>

    </form>

<?php endif; ?>

</main>

</body>
</html>