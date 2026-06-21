# EV ChargeOps

**Equipe:** Equipe 16  
**Integrantes:**
- Yuri Eurich — RM 569285
- Eduardo Titato — RM 572776
- Camila Kato de Godoi — RM 570229

**Desafio:** Enterprise Challenge 2026 — GoodWe x FIAP  
**Sprint:** 01 — Pesquisa e Documentação  
**Prazo:** 21/06/2026

---

## O Problema

A GoodWe é uma das maiores fabricantes globais de inversores e sistemas de armazenamento de energia, com presença em mais de 100 países. No Brasil, a empresa mantém parceria com a FIAP por meio do Energy Innovation Lab — Unidade Aclimação — onde opera um carregador de veículos elétricos modelo HCA G2 instalado no estacionamento L1.

O crescimento acelerado de veículos elétricos impõe um problema operacional concreto: infraestruturas de recarga compartilhadas, em condomínios residenciais, edifícios corporativos e campus universitários, não dispõem de mecanismos integrados para estruturar sessões por usuário, calcular consumo individual, aplicar regras de rateio justas e oferecer uma experiência digital clara para moradores e gestores.

**Pergunta central do desafio:**  
*Como transformar sessões de recarga de veículos elétricos em uma infraestrutura compartilhada em dados estruturados, rateio justo e inteligência acionável?*

O EV ChargeOps responde a essa pergunta transformando cada sessão de recarga em um registro estruturado, vinculado a um usuário identificado, processado por regras de rateio transparentes e analisado por modelos de inteligência artificial que geram alertas e previsões operacionais.

---

## Frente 1 — Contexto e Problema

O avanço da eletromobilidade no Brasil traz um desafio de infraestrutura: a gestão de carregadores compartilhados em ambientes coletivos, como condomínios e edifícios corporativos. Quando um carregador como o GoodWe HCA G2 é instalado em um estacionamento coletivo, o maior gargalo não é a parte elétrica em si, mas a gestão. Não existem mecanismos integrados na grande maioria dos carregadores para separar quem usou o aparelho, quantos kWh foram consumidos por unidade, e como cobrar isso de forma automatizada e justa.

Sem esse controle, os gestores acabam em duas situações: deixam a recarga gratuita (jogando o custo na conta de luz do condomínio geral, o que gera conflitos entre moradores) ou adotam planilhas manuais propensas a erros. O EV ChargeOps foi pensado para resolver exatamente essa dor, criando uma camada de software inteligente sobre o hardware da GoodWe para monitorar, ratear custos e prever o uso da estação de recarga.

### Desafios Operacionais

Gestores enfrentam dois gargalos principais. O primeiro é a sobrecarga da rede elétrica local em horários de pico — se vários carros tentarem puxar a potência máxima ao mesmo tempo (como às 19h, na volta do trabalho), corre-se o risco de desarmar o disjuntor geral do prédio. O segundo é a disputa por vagas: o motorista deixa o carro carregando à noite e o veículo passa a manhã inteira bloqueando o ponto, impedindo que outros moradores utilizem a estação.

No cenário nacional, os modelos de cobrança variam entre cobrança direta por kWh consumido, tempo de ocupação da vaga ou rateio fixo condominial — este último injusto para quem não possui veículo elétrico. Mudar as regras de cobrança mensalmente com base em planilhas gera desconfiança e atrito na comunidade.

### Como Funciona uma Sessão de Recarga

Do momento em que o cabo é conectado ao veículo até a sua desconexão, o processo segue quatro etapas:

- **Conexão e Handshake:** o veículo e o carregador trocam sinais para verificar o isolamento elétrico e os limites de corrente suportados.
- **Autenticação:** o usuário aprova o início da sessão via cartão RFID ou aplicativo, vinculando aquela sessão à sua conta.
- **Telemetria Ativa:** durante a carga, o medidor interno do HCA G2 registra e envia dados contínuos de potência instantânea (kW), energia acumulada (kWh), tensão (V) e tempo decorrido.
- **Encerramento:** o fluxo de energia é interrompido quando a bateria atinge 100% ou por comando do usuário, gerando o fechamento do pacote de dados da sessão.

### Análise de Mercado — Opção A

Para entender o que o mercado já oferece e onde a solução pode se diferenciar, foram analisadas três plataformas existentes:

**Wallbox Pulsar Plus**
Carregador com bom controle de potência local e aplicativo próprio. No entanto, o aplicativo nativo deixa a desejar no faturamento multifamiliar complexo e automatizado para o cenário de condomínios brasileiros. O foco principal está no gerenciamento físico de carga, com limitações em relatórios de rateio para múltiplas unidades.

**ChargePoint**
Uma das maiores redes de recarga do mundo, com plataforma de software robusta e completa. O problema é o custo: a implementação e as taxas de licença em dólar tornam o projeto inviável para condomínios residenciais de médio padrão no Brasil.

**Neocharge**
Plataforma nacional focada na gestão de frotas. Carece de algoritmos preditivos baseados em IA para otimização de demanda residencial, como antecipação de picos de consumo ou organização inteligente de filas de espera entre moradores.

O EV ChargeOps se diferencia das três ao combinar gestão de sessão por usuário, rateio automatizado e inteligência artificial aplicada à previsão de demanda — com foco no mercado nacional e no modelo condominial.

---

## Frente 2 — Base Regulatória e Técnica

### 2.1 Resolução Normativa ANEEL nº 1.000/2021

A RN 1.000/2021 é o principal marco regulatório do setor elétrico brasileiro para consumidores, publicada em 7 de dezembro de 2021. Ela consolida o conteúdo de 61 normas anteriores em um único documento, incluindo a antiga RN 819/2018, que regulava especificamente a recarga de veículos elétricos.

As regras sobre recarga estão no Capítulo V da resolução, dividido em quatro seções: Instalação de Estação de Recarga, Equipamentos Utilizados para a Recarga, Funcionamento da Estação de Recarga e Prestação de Atividade de Recarga pela Distribuidora.

**Pontos centrais que impactam o EV ChargeOps:**

**Exploração comercial liberada.** É permitida a qualquer interessado a realização de atividades de recarga de veículos elétricos, inclusive para fins de exploração comercial com preços livremente negociados — a chamada recarga pública. Isso significa que a plataforma pode cobrar por sessão, por kWh ou por rateio condominial sem necessidade de autorização específica da ANEEL.

**Atividade acessória, não regulada.** O artigo 554 da Resolução 1.000/2021 caracteriza as estações de recarga exploradas por terceiros como atividades acessórias complementares — uma atividade não regulada cuja prestação está relacionada com a utilização do serviço público de distribuição de energia elétrica e que pode ser prestada tanto pela distribuidora quanto por terceiros.

**Vedação à injeção na rede.** É vedada a injeção de energia elétrica na rede de distribuição a partir dos veículos. A plataforma deve garantir que nenhuma sessão opere em modo de exportação de energia para a rede.

**Transparência tarifária obrigatória.** Os prestadores de serviços de recarga devem informar claramente as tarifas aplicáveis, evitando práticas abusivas, em conformidade com o Código de Defesa do Consumidor. O EV ChargeOps exibe o custo estimado antes de cada sessão e o custo final ao encerramento.

**Regulamentação mínima intencional.** A ANEEL optou por uma regulamentação mínima do tema, com o objetivo de evitar interferências na operação da rede elétrica e garantir que as tarifas dos demais consumidores não sejam impactadas pela prestação do serviço de recarga por terceiros.

---

### 2.2 Carregador GoodWe HCA G2 — Interfaces de Comunicação

O HCA G2 é o carregador instalado no estacionamento L1 da FIAP Aclimação. Ele oferece cinco interfaces de comunicação, cada uma com um papel distinto na arquitetura do EV ChargeOps.

**RS-485**  
A porta RS-485 é destinada à comunicação com inversores fotovoltaicos ou medidores MID. No contexto do EV ChargeOps, essa interface permite que o carregador receba comandos de controle de potência vindos do inversor — por exemplo, limitar a corrente de recarga quando a geração solar é baixa. É a interface mais adequada para controle de carga dinâmico e automação local.

**LAN (Ethernet)**  
A porta LAN é usada para comunicação com o roteador local. É a conexão mais estável para transmissão de dados de sessão em tempo real para o back-end da plataforma. Recomendada como interface primária de comunicação no campus da FIAP, onde há infraestrutura de rede cabeada disponível.

**Wi-Fi**  
Permite conexão sem fio à rede local. O aplicativo SolarGo oferece opção de configuração de Wi-Fi diretamente no carregador HCA G2. Útil para instalações onde o cabeamento não é viável, mas com menor estabilidade para transmissão contínua de dados de sessão em comparação com a LAN.

**Bluetooth**  
Funciona como canal de configuração inicial e diagnóstico local. O smartphone precisa suportar Bluetooth para comunicação via aplicativo SolarGo. Não é adequado para integração contínua com o back-end da plataforma por limitação de alcance.

**RFID**  
O carregador suporta inicialização por cartão RFID, por aplicativo e de forma automática ao conectar o cabo. Para o EV ChargeOps, o RFID é o mecanismo principal de autenticação do usuário: cada morador ou colaborador recebe um cartão vinculado ao seu cadastro na plataforma, permitindo associar cada sessão a um usuário específico sem login manual.

---

### 2.3 API GoodWe SEMS — Estrutura e Dados Disponíveis

O SEMS (Smart Energy Management System) é a plataforma de monitoramento da GoodWe. Os dados do sistema são atualizados a cada 10 segundos, cobrindo inversores, carregadores de veículos elétricos e outros dispositivos conectados.

**Tipos de acesso disponíveis**

A GoodWe disponibiliza três tipos de API:

- **OpenAPI:** exclusiva para usuários com conta organizacional no SEMS. Fornece acesso completo a todos os dispositivos da organização, incluindo dados e controle remoto.
- **Real-time Data Monitoring API:** permite que fornecedores terceiros obtenham dados em tempo real de inversores autorizados via whitelist.
- **Batch Remote Control Interface:** permite controle remoto de dispositivos previamente autorizados, utilizada principalmente para gerenciamento dinâmico de carga por concessionárias.

**Autenticação**

O acesso à API SEMS se dá pela obtenção de um token via endpoint CrossLogin, utilizado em todas as requisições subsequentes:

```
POST https://www.semsportal.com/api/v1/Common/CrossLogin
Header: Token: {"version":"v2.1.0","client":"ios","language":"en"}
Body: {"account": "<email>", "pwd": "<senha>"}
```

**Endpoints relevantes para o EV ChargeOps**

```
GET /api/v4/EvCharger/GetEvChargerMoreView
GET /api/v3/EvCharger/GetCurrentChargeinfo
GET /powerstation/EvChargerDetail?stationId={station_id}
```

**Estrutura JSON de uma sessão de recarga**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "stationId": "a1b2c3d4-xxxx-xxxx-xxxx-e5f6a7b8c9d0",
    "evChargerStatus": 2,
    "chargingStatus": "Charging",
    "power": 7400,
    "energy": 12.85,
    "sessionStartTime": "2026-06-21T08:14:00Z",
    "sessionEndTime": null,
    "duration": 6240,
    "rfidCard": "UID-00A3F7C2",
    "userId": "usr_yuri_569285",
    "currentL1": 32.1,
    "currentL2": 0.0,
    "currentL3": 0.0,
    "voltage": 231.4,
    "totalEnergyDelivered": 248.6,
    "maxPower": 7400,
    "temperature": 38.2
  }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `evChargerStatus` | int | 0=Inativo, 1=Conectado, 2=Carregando, 3=Erro |
| `power` | int (W) | Potência instantânea entregue ao veículo |
| `energy` | float (kWh) | Energia entregue na sessão atual |
| `sessionStartTime` | datetime | Início da sessão (UTC) |
| `duration` | int (s) | Duração acumulada em segundos |
| `rfidCard` | string | UID do cartão RFID que iniciou a sessão |
| `totalEnergyDelivered` | float (kWh) | Energia total histórica entregue pelo equipamento |
| `temperature` | float (°C) | Temperatura interna do carregador |

**Como esses dados alimentam o EV ChargeOps**

O back-end realiza polling periódico (a cada 30–60 segundos) nos endpoints da API SEMS. A cada resposta, os dados são persistidos no banco com referência ao `rfidCard` — chave de vínculo entre a sessão física e o usuário cadastrado. Ao encerramento da sessão (quando `evChargerStatus` retorna a 0 ou 1), a plataforma calcula o consumo da sessão via campo `energy` e registra o evento na tabela de sessões, alimentando o motor de rateio.

---

## Frente 3 — Arquitetura e IA

> Stack de desenvolvimento (Sprint 2): **Python** (back-end, API e camada de IA/Data Science), **SQL** (persistência relacional) e **Flutter** (aplicativo mobile multiplataforma).

### 3.1 As Camadas da Plataforma EV ChargeOps

A solução foi projetada em arquitetura de quatro camadas, garantindo separação de responsabilidades, escalabilidade e manutenibilidade. Cada camada se comunica apenas com a camada adjacente, reduzindo acoplamento e facilitando a evolução independente de cada componente.

**Camada Física**
Componente central: carregador inteligente GoodWe HCA G2. Converte e entrega energia elétrica ao veículo, ao mesmo tempo em que atua como medidor inteligente (smart meter), capturando em tempo real grandezas elétricas como tensão (V), corrente (A), potência (kW) e energia acumulada (kWh). Realiza autenticação do usuário no início da sessão (via RFID ou aplicativo), controle do relé de carga e geração do dado bruto de telemetria. É a camada que materializa o evento de negócio "sessão de recarga", origem de toda a cadeia de rateio.

**Camada de Conectividade**
Transporta de forma segura e confiável os dados gerados pelo carregador até a nuvem, e os comandos da nuvem até o carregador. A conexão se dá via Wi-Fi ou LAN do condomínio, com o protocolo OCPP (Open Charge Point Protocol) trafegado sobre WebSocket. As mensagens-chave utilizadas são `Authorize`, `StartTransaction`, `MeterValues` e `StopTransaction`. A camada prevê store-and-forward (armazenamento local temporário no carregador) em caso de queda de conectividade, reenviando os dados assim que o link for restabelecido — requisito crítico para a integridade do rateio.

**Camada de Aplicação**
Núcleo de negócio e inteligência do sistema, hospedado em nuvem. Composta por três módulos em Python: o back-end (API REST via FastAPI/Django) que recebe, valida e persiste a telemetria em banco SQL; o módulo de regras de negócio que implementa o motor de rateio e a geração de faturas; e o módulo de Inteligência Artificial que roda como serviço assíncrono consumindo os dados persistidos para detecção de anomalias e previsão de demanda. Por compartilharem a mesma linguagem, o pipeline de dados ganha simplicidade: bibliotecas como `pandas` e `scikit-learn` podem ser chamadas diretamente pelo módulo de faturamento quando necessário.

**Camada de Apresentação**
Entrega a informação processada ao usuário final. O aplicativo mobile em Flutter é voltado ao morador — consulta de consumo individual em kWh, histórico de sessões, fatura do mês e sugestões de horários de recarga otimizados. O dashboard web é voltado ao gestor/síndico — visão consolidada do condomínio, alertas de anomalias, gestão de usuários e emissão do fechamento mensal. Ambas as interfaces consomem exclusivamente a API da camada de aplicação.

---

### 3.2 Fluxo de Dados — Do Hardware à Fatura

O pipeline foi desenhado como um fluxo unidirecional e auditável:

1. **Autenticação e início da sessão:** o morador identifica-se no HCA G2 via RFID ou app. O carregador emite `StartTransaction`, vinculando a sessão ao `usuario_id` e ao `veiculo_id`.
2. **Geração da telemetria bruta:** durante a recarga, o firmware amostra continuamente corrente, tensão e energia acumulada, consolidando leituras periódicas via `MeterValues` a cada 5–15 minutos.
3. **Transporte via rede:** as mensagens trafegam via Wi-Fi/LAN, empacotadas no protocolo OCPP sobre WebSocket, até o back-end na nuvem.
4. **Ingestão e persistência:** a API valida o payload e grava cada leitura no banco relacional, associada a `sessao_id`, `timestamp` e `kWh_acumulado`.
5. **Encerramento da sessão:** ao final da recarga, o carregador envia `StopTransaction` com o valor final de energia consumida, fechando a sessão com status `concluída`.
6. **Interceptação pela IA:** de forma assíncrona (batch noturno ou near real-time), o módulo de IA lê as sessões fechadas e executa detecção de anomalias e modelagem preditiva. Os resultados são gravados de volta no banco, vinculados às sessões ou usuários correspondentes.
7. **Fechamento de fatura:** em rotina mensal, o back-end agrega todas as sessões válidas por usuário/unidade, aplica a fórmula de rateio e gera os registros de fatura.
8. **Disponibilização ao usuário:** a fatura é exposta via API ao app Flutter (visão do morador) e ao dashboard web (visão do síndico), podendo ser exportada para fechamento contábil.

---

### 3.3 Modelo de Rateio

O rateio é baseado no consumo real medido em kWh por usuário, evitando a divisão igualitária tradicional que penaliza quem recarrega pouco. A fatura individual é composta por duas parcelas: uma variável, proporcional ao consumo efetivo, e uma fixa, referente ao custo de manutenção e disponibilidade do equipamento, rateada entre os usuários ativos cadastrados.

**Fórmula:**

```
Fatura_usuario = (kWh_usuario × Tarifa_energia) + (Custo_fixo_manutencao / N_usuarios_ativos)
```

Onde:
- `kWh_usuario`: energia total consumida pelo usuário no período, medida pelo HCA G2
- `Tarifa_energia`: tarifa de energia vigente (R$/kWh), repassada pela concessionária
- `Custo_fixo_manutencao`: custo fixo mensal de manutenção, conectividade e operação do(s) carregador(es)
- `N_usuarios_ativos`: número de usuários elegíveis ao rateio do custo fixo no período

**Tratamento de exceções:**

**Sessão interrompida abruptamente:** o sistema considera válido o último checkpoint de `MeterValues` recebido antes da interrupção. A sessão é marcada com status `incompleta`, mas o consumo parcial é faturado normalmente. Sessões incompletas são sinalizadas no dashboard para auditoria e avaliadas pelo módulo de IA.

**Usuário sem recarga no mês:** a parcela variável é zerada naturalmente. A parcela fixa de manutenção continua sendo cobrada, pois o usuário permanece com acesso disponível ao equipamento — mesmo princípio de taxas condominiais de áreas comuns não utilizadas. Essa regra pode ser parametrizada pela administração.

**Unidade com dois veículos elétricos:** cada veículo possui identificação própria (RFID ou perfil no app), permitindo rastreamento de consumo por veículo de forma independente. No fechamento, o back-end agrega os kWh dos dois veículos da mesma unidade, gerando uma fatura consolidada por apartamento com detalhamento individual por veículo para transparência.

---

### 3.4 O Papel da Inteligência Artificial

A IA atua na camada de aplicação como módulo analítico complementar ao motor de regras de negócio, processando dados históricos de telemetria para gerar valor que regras determinísticas simples não conseguem capturar. Foram definidas duas abordagens, ambas implementadas em Python.

**Abordagem 1 — Detecção de Anomalias**

Problema que resolve: identificar fraudes (uso indevido de tag de terceiros), furto de energia e falhas físicas (degradação de bateria ou mau funcionamento do HCA G2) que não seriam percebidos por checagem de limites fixos.

Técnica: Isolation Forest, algoritmo de detecção de anomalias não supervisionada. Adequado pois não exige dataset rotulado de fraudes conhecidas — isola observações que se comportam de forma estatisticamente diferente da maioria das sessões legítimas, atribuindo um anomaly score a cada sessão.

Dados necessários: duração da sessão, curva de potência ao longo da sessão, energia total consumida versus duração, horário e dia da semana, e histórico de sessões anteriores do mesmo usuário/veículo para comparação de padrão individual.

Impacto esperado: redução de perdas financeiras por uso indevido, manutenção preventiva do carregador e aumento da confiança dos condôminos no modelo de rateio, por ser auditável e capaz de sinalizar inconsistências automaticamente.

**Abordagem 2 — Regressão para Previsão de Demanda**

Problema que resolve: antecipar os horários de pico de utilização do carregador compartilhado, permitindo sugerir aos moradores janelas de recarga otimizadas — reduzindo filas e, potencialmente, custos de energia em horários de tarifa mais alta.

Técnica: regressão para séries temporais em duas etapas conforme a maturidade dos dados — Regressão Linear como baseline simples e interpretável, evoluindo para XGBoost (Gradient Boosting) para capturar relações não lineares e interações mais complexas à medida que o volume histórico cresce.

Dados necessários: série histórica de sessões (timestamp, kWh), variáveis temporais (dia da semana, horário, feriados), número de unidades ativas e veículos cadastrados, e eventualmente tarifa de energia por faixa horária quando disponível.

Impacto esperado: melhor distribuição da demanda ao longo do dia, suporte à decisão do síndico sobre expansão da infraestrutura e recomendações proativas ao morador via app sobre o melhor horário para iniciar a sessão.

---

## Diagrama de Arquitetura

> *Diagrama a ser inserido como imagem após conclusão da Frente 3.*

---

## Plano para a Sprint 02

O desenvolvimento seguirá a mesma arquitetura de quatro camadas definida na Sprint 01, com as seguintes tecnologias: **Python** (back-end e IA), **SQL** (banco de dados relacional), **Flutter** (aplicativo mobile) e a **API SEMS da GoodWe** como fonte de dados do carregador HCA G2.

A ordem de desenvolvimento será:

1. **Banco de dados e modelagem relacional:** criação do esquema SQL com as entidades usuário, unidade, veículo, sessão e fatura, com registros simulados para validação das regras de negócio.
2. **Integração com a API SEMS:** implementação do polling periódico nos endpoints do SEMS Portal, ingestão dos dados JSON e persistência no banco, com vínculo por `rfidCard`.
3. **Motor de rateio:** implementação da fórmula de faturamento em Python, incluindo o tratamento das três exceções definidas (sessão interrompida, usuário sem recarga e unidade com dois veículos).
4. **Módulo de IA:** treinamento e integração do Isolation Forest para detecção de anomalias e do modelo de regressão para previsão de demanda, ambos consumindo os dados persistidos no banco.
5. **API REST:** exposição dos endpoints autenticados (JWT) para consumo pelo aplicativo e pelo dashboard.
6. **Aplicativo Flutter:** telas de histórico de sessões, fatura do mês e sugestão de horário de recarga para o morador.
7. **Dashboard web:** visão consolidada para o síndico com alertas de anomalias e fechamento mensal.

---

## Fontes Consultadas

- ANEEL. Resolução Normativa nº 1.000, de 7 de dezembro de 2021. Disponível em: https://www2.aneel.gov.br/cedoc/ren20211000.html
- ANEEL. Página institucional sobre veículos elétricos. Disponível em: https://www.gov.br/aneel/pt-br/assuntos/veiculos-eletricos
- GoodWe. HCA G2 Series EV Charger — Página do produto. Disponível em: https://en.goodwe.com/hca-g2
- GoodWe. User Manual AC Charger HCA Series G2 V1.3-2025. Disponível em: https://pvhurt.com.ua/wp-content/uploads/2025/10/GW_HCA-G2_User-Manual-EN.pdf
- GoodWe. SEMS+ Smart Energy Management System. Disponível em: https://en.goodwe.com/semsplus-series-smart-energy-management-system
- GoodWe Community. API Technical Document. Disponível em: https://community.goodwe.com/static/images/2024-08-20597794.pdf
- Karunanayake, B. Accessing GoodWe Sems Portal API: A Comprehensive Guide. Medium, 2024. Disponível em: https://binodmx.medium.com/accessing-the-goodwe-sems-portal-api
- Voltbras. Legislação Brasileira sobre eletropostos. 2026. Disponível em: https://voltbras.com/legislacao-brasileira-sobre-eletropostos-o-que-saber-antes-de-investir/
- Canal Solar. O futuro da mobilidade e os desafios tributários no Brasil. 2023. Disponível em: https://canalsolar.com.br/o-futuro-da-mobilidade-e-os-desafios-tributarios-no-brasil/
- TimSoethout. goodwe-sems-home-assistant. GitHub. Disponível em: https://github.com/TimSoethout/goodwe-sems-home-assistant
- ABVE — Associação Brasileira do Veículo Elétrico. Dados de Emplacamentos e Evolução da Frota no Brasil (2024-2026). Disponível em: http://www.abve.org.br
- Wallbox. Visão Geral do Produto: Pulsar Plus. Disponível em: https://support.wallbox.com/pt-pt/knowledge-base/visao-geral-do-produto-pulsar-plus/
- ChargePoint. Plataforma de Hardware e Software para Redes de Recarga. Disponível em: https://www.chargepoint.com/
- Neocharge. Soluções em Infraestrutura e Gestão de Recarga para Veículos Elétricos. Disponível em: https://www.neocharge.com.br/loja
