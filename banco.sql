CREATE DATABASE IF NOT EXISTS gestao_moveis_escolar
CHARACTER SET utf8mb4;

USE gestao_moveis_escolar;

CREATE USER IF NOT EXISTS 'espaco_escolar'@'localhost'
IDENTIFIED BY 'escola';

ALTER USER 'espaco_escolar'@'localhost'
IDENTIFIED BY 'escola';

GRANT ALL PRIVILEGES ON gestao_moveis_escolar.*
TO 'espaco_escolar'@'localhost';

FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS doadores (
    id_doador INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    cpf CHAR(11) NOT NULL UNIQUE,
    celular VARCHAR(20) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS receptores (
    id_receptor INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    cnpj CHAR(14) NOT NULL UNIQUE,
    razao_social VARCHAR(200) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS emissores (
    id_emissor INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    cnpj CHAR(14) NOT NULL UNIQUE,
    razao_social VARCHAR(200) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doacoes (
    id_doacao INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_doador INT UNSIGNED NOT NULL,
    id_receptor INT UNSIGNED NOT NULL,
    id_emissor INT UNSIGNED NULL,
    tipo_doacao VARCHAR(100) NOT NULL,
    valor DECIMAL(12,2) NOT NULL,
    data_doacao DATE NOT NULL,
    local_recebimento VARCHAR(255) NOT NULL,
    status ENUM(
        'pendente',
        'confirmada',
        'cancelada'
    ) DEFAULT 'pendente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_doador)
        REFERENCES doadores(id_doador),

    FOREIGN KEY (id_receptor)
        REFERENCES receptores(id_receptor),

    FOREIGN KEY (id_emissor)
        REFERENCES emissores(id_emissor),

    CHECK (valor >= 0)
);

CREATE TABLE IF NOT EXISTS permissoes (
    id_permissao INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    orgao_governo VARCHAR(150) NOT NULL,
    descricao_necessidade TEXT NOT NULL,
    escola_solicitante VARCHAR(150) NOT NULL,
    projeto VARCHAR(150) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pendente',
    descricao_doacao TEXT NOT NULL,
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    id_receptor INT UNSIGNED NULL,

    FOREIGN KEY (id_receptor)
        REFERENCES receptores(id_receptor)
);

CREATE TABLE IF NOT EXISTS solicitacoes (
    id_solicitacao INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    problema_mostrado VARCHAR(255) NOT NULL,
    descricao_problema TEXT NOT NULL,
    duracao_problema VARCHAR(100) NOT NULL,
    afetados VARCHAR(255) NOT NULL,
    projeto_solucao VARCHAR(150) NOT NULL,
    descricao_projeto TEXT NOT NULL,
    data_prevista_inicio DATE NOT NULL,
    data_prevista_finalizacao DATE NOT NULL,
    data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    id_emissor INT UNSIGNED NOT NULL,

    FOREIGN KEY (id_emissor)
        REFERENCES emissores(id_emissor),

    CHECK (
        data_prevista_finalizacao >= data_prevista_inicio
    )
);

CREATE TABLE IF NOT EXISTS solicitacao_receptores (
    id_solicitacao INT UNSIGNED NOT NULL,
    id_receptor INT UNSIGNED NOT NULL,

    PRIMARY KEY (id_solicitacao, id_receptor),

    FOREIGN KEY (id_solicitacao)
        REFERENCES solicitacoes(id_solicitacao)
        ON DELETE CASCADE,

    FOREIGN KEY (id_receptor)
        REFERENCES receptores(id_receptor)
        ON DELETE CASCADE
);