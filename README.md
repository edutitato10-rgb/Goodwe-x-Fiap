# EV ChargeOps — Sprint 02: protótipo funcional

Enterprise Challenge 2026 — GoodWe x FIAP | Equipe 16

Integrantes: Yuri Eurich (RM 569285), Eduardo Titato (RM 572776), Camila Kato de Godoi (RM 570229)

## O que foi implementado

O protótipo cobre o fluxo central definido na Sprint 01, do dado de telemetria até a fatura e os alertas:

| Etapa (plano da Sprint 01)      | Arquivo               | Situação                                   |
|---------------------------------|-----------------------|--------------------------------------------|
| 1. Banco de dados e modelagem   | `src/schema.sql`, `src/db.py`, `src/seed.py` | Implementado (SQLite) |
| 2. Integração com a API SEMS    | `src/sems_client.py`  | Implementado; testado com respostas simuladas |
| 3. Motor de rateio              | `src/rateio.py`       | Implementado, com as três exceções         |
| 4. Módulo de IA                 | `src/ia.py`           | Implementado (anomalias e demanda)         |
| 5. API REST com JWT             | `src/api.py`          | Implementado                               |
| 6. Aplicativo Flutter           | —                     | Não implementado nesta entrega             |
| 7. Dashboard web                | —                     | Não implementado nesta entrega             |

## Como a solução funciona

1. **Sessões.** Cada leitura do carregador (formato JSON do SEMS) é aplicada ao banco por `processar_payload`.
   O `rfidCard` liga a leitura a um veículo e a um usuário cadastrado. Quando o status volta a 0 ou 1, a sessão
   é fechada como `concluida`; quando o carregador reporta erro (status 3), fecha como `incompleta`, mantendo
   o último valor de energia lido. Cartões não cadastrados não geram sessão.
2. **Rateio.** Implementa a fórmula da Sprint 01:
   `Fatura = (kWh_usuario x Tarifa) + (Custo_fixo / N_usuarios_ativos)`.
   - Sessão interrompida: o consumo parcial é faturado e a sessão fica sinalizada.
   - Usuário sem recarga: paga apenas a parcela fixa (parâmetro `cobrar_fixo_sem_recarga`).
   - Unidade com dois veículos: os kWh são somados em uma fatura, com detalhamento por veículo.
3. **IA, anomalias.** Um Isolation Forest analisa cada sessão fechada usando duração, energia, potência média e
   máxima, estabilidade da curva de potência, razão entre energia reportada e energia esperada pela curva,
   horário e dia da semana, e o desvio em relação ao histórico do próprio veículo. Cada sessão sinalizada
   recebe um motivo legível (a variável mais distante do padrão) e aparece para auditoria.
4. **IA, demanda.** A carga horária (kWh por hora) é calculada **apenas com sessões não sinalizadas**, ou seja,
   a saída do detector de anomalias alimenta o modelo de previsão. Compara-se média por hora da semana
   (referência), Regressão Linear e XGBoost em um teste com as últimas 3 semanas; o de menor erro é usado
   para preencher a tabela `previsao_demanda`, que gera a sugestão de horários de menor demanda.
5. **API.** Login com JWT, perfis `morador` e `gestor`. O morador vê suas sessões, sua fatura e sugestões
   de horário; o gestor vê faturas do mês e anomalias.

## Como executar

Requer Python 3.11 ou superior.

```bash
pip install -r requirements.txt
python -m src.main          # cria o banco, simula dados, roda rateio e IA, gera evidencias/
python -m pytest            # testes automatizados
uvicorn src.api:app         # API em http://127.0.0.1:8000/docs (após rodar src.main)
```

Usuários de demonstração (senha `senha123`): `sindico@condominio.test` (gestor) e
`morador1@condominio.test` até `morador12@condominio.test`.

Para usar a API real do SEMS, instancie `SemsClient(email, senha)` e chame `consultar(station_id)` em
laço de 30 a 60 segundos, repassando cada resposta a `processar_payload`. Isso exige uma conta SEMS e
não foi exercitado nesta entrega.

## Evidências de funcionamento

Na pasta `evidencias/`:

- `execucao.txt`: saída completa de `python -m src.main`.
- `anomalias.png`: sessões sinalizadas pelo Isolation Forest.
- `previsao_demanda.png`: curva de demanda prevista por hora.
- `faturas_2026-09.csv`: faturas de setembro/2026 do condomínio simulado.

Resultados da execução (dados simulados, semente fixa):

- Anomalias injetadas detectadas: 19 de 19 (8 fraudes, 6 falhas do carregador, 5 erros de medidor), com
  1 falso positivo entre 516 sessões normais. Das 10 sessões interrompidas, 1 foi sinalizada, o que é
  esperado: interrupção por si só não é anomalia.
- Erro médio absoluto da previsão (kWh por hora): média por hora da semana 2,79; Regressão Linear 3,02;
  XGBoost 2,77.
- Setembro/2026: 12 faturas, 2.208,7 kWh medidos, parcela fixa de R$ 25,00 por usuário (R$ 300,00 / 12).
- 5 testes automatizados passando (rateio e exceções, ingestão, cartão desconhecido, autenticação e perfis).

## Decisões técnicas e desvios em relação à Sprint 01

- **Dados simulados.** Não havia acesso ao carregador nem a credenciais do SEMS durante o desenvolvimento.
  O gerador `src/seed.py` cria 3 meses de uso de 12 moradores e injeta anomalias rotuladas. Os rótulos
  ficam na coluna `rotulo_sim` e só são usados para avaliar a IA, nunca para treiná-la. As métricas acima
  valem para esses dados sintéticos e não devem ser lidas como desempenho em produção.
- **Ingestão por polling do SEMS, sem OCPP.** A Sprint 01 descrevia OCPP sobre WebSocket na camada de
  conectividade e, no plano da Sprint 02, a integração via API SEMS. Foi seguido o plano da Sprint 02
  (polling), que dispensa configurar um servidor OCPP central. OCPP continua como evolução possível.
- **SQLite no lugar de um SQL de servidor.** A Sprint 01 especificava SQL relacional sem definir o SGBD.
  O SQLite mantém o protótipo executável sem instalação; o esquema usa SQL padrão e migra para PostgreSQL
  com ajustes pequenos.
- **Previsão de demanda.** A Regressão Linear foi pior que a média histórica por hora da semana, e o
  XGBoost ficou praticamente empatado com ela. Com apenas 3 meses simulados isso é plausível; o ganho
  do XGBoost deve aparecer com mais histórico. A média por hora da semana foi mantida como referência
  de comparação.
- **Fuso horário.** Os horários do SEMS vêm em UTC e são convertidos para UTC-3 antes de gravar.
- **Pendências.** Aplicativo Flutter e dashboard web (itens 6 e 7 do plano) não foram implementados;
  a API já expõe os dados que eles consumiriam. O segredo JWT deve ser definido pela variável
  `EVCHARGEOPS_JWT_SECRET` fora do ambiente de demonstração.

## Estrutura do repositório

```
src/        código-fonte (schema.sql, db, seed, sems_client, rateio, ia, api, main)
tests/      testes automatizados
evidencias/ saída da execução, gráficos e CSV
```

## Uso de ferramentas de IA

Partes do código foram escritas com apoio de um assistente de IA e revisadas pela equipe. A equipe deve
conseguir explicar cada módulo, em especial a fórmula de rateio (`src/rateio.py`), as variáveis usadas
pelo Isolation Forest (`src/ia.py`) e o fechamento de sessões (`src/sems_client.py`).
