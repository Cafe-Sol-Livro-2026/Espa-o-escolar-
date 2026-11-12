<?php
declare(strict_types=1);

if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}

const DB_HOST = 'localhost';
const DB_NAME = 'gestao_moveis_escolar';
const DB_USER = 'espaco_escolar';
const DB_PASS = 'escola';

function db(): PDO {
    static $pdo = null;

    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $dsn = 'mysql:host=' . DB_HOST .
           ';dbname=' . DB_NAME . ';charset=utf8mb4';

    $pdo = new PDO($dsn, DB_USER, DB_PASS, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false
    ]);

    return $pdo;
}

function e($valor): string {
    return htmlspecialchars(
        (string)$valor,
        ENT_QUOTES,
        'UTF-8'
    );
}

function go(string $pagina): never {
    header('Location: index.php?page=' . urlencode($pagina));
    exit;
}

function usuario(): ?array {
    return $_SESSION['usuario'] ?? null;
}

function exigir_tipo(string $tipo): void {
    if (!usuario() || usuario()['tipo'] !== $tipo) {
        aviso('Faça o cadastro correspondente para continuar.', 'erro');
        go('inicio');
    }
}

function aviso(string $mensagem, string $tipo = 'sucesso'): void {
    $_SESSION['aviso'] = [
        'mensagem' => $mensagem,
        'tipo' => $tipo
    ];
}

function mostrar_aviso(): string {
    if (empty($_SESSION['aviso'])) {
        return '';
    }

    $a = $_SESSION['aviso'];
    unset($_SESSION['aviso']);

    return '<div class="aviso ' . e($a['tipo']) . '">' .
        e($a['mensagem']) .
        '</div>';
}