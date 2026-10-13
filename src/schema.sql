CREATE TABLE IF NOT EXISTS unidade (
    id INTEGER PRIMARY KEY,
    identificacao TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('morador', 'gestor')),
    unidade_id INTEGER REFERENCES unidade(id),
    ativo INTEGER NOT NULL DEFAULT 1  -- 1 = elegível ao rateio do custo fixo
);
CREATE TABLE IF NOT EXISTS veiculo (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    placa TEXT NOT NULL,
    modelo TEXT,
    rfid TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS sessao (
    id INTEGER PRIMARY KEY,
    veiculo_id INTEGER NOT NULL REFERENCES veiculo(id),
    rfid TEXT NOT NULL,
    inicio TEXT NOT NULL,              -- horário local, ISO 'YYYY-MM-DD HH:MM:SS'
    fim TEXT,
    kwh REAL NOT NULL DEFAULT 0,       -- energia reportada pelo medidor
    duracao_s INTEGER NOT NULL DEFAULT 0,
    potencia_max_w REAL,
    potencia_media_w REAL,
    curva_json TEXT,                   -- lista de potências (W) a cada 15 min
    status TEXT NOT NULL CHECK (status IN ('em_andamento', 'concluida', 'incompleta')),
    rotulo_sim TEXT                    -- só existe em dados simulados; a IA NÃO usa
);
CREATE INDEX IF NOT EXISTS idx_sessao_inicio ON sessao(inicio);
CREATE TABLE IF NOT EXISTS fatura (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    mes TEXT NOT NULL,                 -- 'YYYY-MM'
    kwh_total REAL NOT NULL,
    valor_variavel REAL NOT NULL,
    valor_fixo REAL NOT NULL,
    valor_total REAL NOT NULL,
    detalhe_json TEXT,
    UNIQUE (usuario_id, mes)
);
CREATE TABLE IF NOT EXISTS anomalia (
    id INTEGER PRIMARY KEY,
    sessao_id INTEGER NOT NULL UNIQUE REFERENCES sessao(id),
    score REAL NOT NULL,               -- quanto maior, mais anômala
    sinalizada INTEGER NOT NULL,
    motivo TEXT
);
CREATE TABLE IF NOT EXISTS previsao_demanda (
    dia_semana INTEGER NOT NULL,       -- 0 = segunda
    hora INTEGER NOT NULL,
    kwh_previsto REAL NOT NULL,
    modelo TEXT NOT NULL,
    PRIMARY KEY (dia_semana, hora)
);
CREATE TABLE IF NOT EXISTS parametro (
    chave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);
