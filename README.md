# Nobreak SMS (Serial UPS) — integração customizada para Home Assistant

[![Validate HACS](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/validate.yml/badge.svg)](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/validate.yml)
[![Hassfest](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/hassfest.yml/badge.svg)](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/hassfest.yml)

Substitui o fluxo Node-RED de monitoramento do nobreak SMS PRO 700VA (ligado
via USB serial) por uma integração nativa do Home Assistant, com detecção
automática das portas USB disponíveis na tela de configuração.

## Por que isso existe

Esse modelo de nobreak não fala o protocolo padrão de UPS Tools do HA — ele
usa uma variante binária do protocolo Megatec/Voltronic. O fluxo Node-RED
original enviava comandos hexadecimais fixos (`51 ff ff ff ff b3 0d` etc.) e
fazia o parse manual da resposta por posição de byte. Esta integração faz o
mesmo trabalho, mas:

- expõe a seleção da porta serial numa tela de configuração, com
  auto-detecção via `serial.tools.list_ports`;
- deixa capacidade (VA), fator de potência e intervalo de leitura
  configuráveis pela interface, sem precisar editar código;
- calcula o checksum genericamente (two's complement da soma dos bytes),
  em vez de comandos hardcoded — então adaptar para outro nobreak da mesma
  família de protocolo deve ser simples.

## Instalação

**Opção A — HACS (repositório customizado)**
1. HACS → Integrações → menu (⋮) → "Repositórios customizados".
2. URL: `https://github.com/andregoncalvespires/nobreak_ups_sms_ha`, categoria
   "Integration".
3. Instale "Nobreak SMS (Serial UPS)" e reinicie o Home Assistant.

Ou use o link direto (My Home Assistant):
`https://my.home-assistant.io/redirect/hacs_repository/?owner=andregoncalvespires&repository=nobreak_ups_sms_ha&category=integration`

**Opção B — manual**
1. Copie a pasta `custom_components/sms_nobreak` para
   `<config>/custom_components/sms_nobreak` na sua instalação.
2. Reinicie o Home Assistant.

## Configuração

1. Ajustes → Dispositivos e serviços → Adicionar integração → "Nobreak SMS".
2. A tela lista as portas seriais detectadas no momento (preferindo o
   caminho estável em `/dev/serial/by-id/...`, igual ao fluxo original, para
   sobreviver a reboots/trocas de porta USB). Se o nobreak não aparecer na
   lista, escolha "Digitar caminho manualmente…".
3. Informe também baud rate, capacidade nominal (VA) e fator de potência —
   o padrão (2400 bauds, 700 VA, 0.7) reflete os valores do flow original.
4. A integração abre a porta e confere se uma resposta de status válida
   volta antes de criar a entrada; se não vier nada compatível, ela avisa em
   vez de criar entidades quebradas.
5. Capacidade, fator de potência e intervalo de leitura podem ser
   reajustados depois em "Configurar" na própria integração (options flow).

## Entidades criadas

**Sensores:** última tensão de entrada, tensão de entrada, tensão de saída,
potência de saída (%), potência de saída (W, calculada), frequência de
saída, nível de bateria, temperatura.

**Binários:** operando na bateria, bateria fraca, bypass, boost, problema no
nobreak (inverso do flag "UPS OK"), teste em andamento, desligamento
agendado, alarme sonoro ativo.

**Botões:** iniciar teste de bateria (10s / 5min), testar até descarregar,
parar teste.

## Migrando do fluxo Node-RED

1. Instale e configure esta integração primeiro, com o Node-RED ainda
   rodando — como os dois processos vão disputar a porta serial, **pare o
   Node-RED (ou desabilite os nós `SMS IN`/`SMS OUT` e o inject `Request
   Data`) antes de abrir a porta pela integração**, senão um dos dois vai
   falhar ao conectar.
2. Confirme que os valores batem com o que o flow antigo mostrava.
3. As entidades novas nascem com `entity_id` diferentes das criadas pelos
   nós `ha-sensor`/`ha-binary-sensor`/`ha-button` do flow antigo (que usam os
   UUIDs do Node-RED). Se você tem automações, dashboards ou histórico
   presos aos `entity_id` antigos (`sensor.sms_input_voltage` etc.), o
   caminho mais simples é renomear o `entity_id` das novas entidades para
   igualar os antigos, em Configurações da entidade → Avançado.
4. Depois de validar tudo, exclua ou desabilite a aba "UPS SMS" no Node-RED
   e remova os nós `ha-entity-config` correspondentes para não deixar
   entidades órfãs.

## Adaptando para outro modelo

O protocolo (`protocol.py`) é genérico dentro da família Megatec/Voltronic:
byte de comando + 4 bytes de parâmetro + checksum (two's complement) + `0x0D`,
resposta iniciando em `0x3D` e terminando em `0x0D`. Para outro nobreak que
siga esse mesmo framing, normalmente basta ajustar em `const.py` os bytes de
comando e, se os campos do status vierem em outra ordem/tamanho, os offsets
em `parse_status()`.

Uma observação: o comando `I` (consulta de nome/identificação do nobreak,
`CMD_UPS_NAME`) existe no protocolo mas estava desabilitado no flow original
e por isso não foi conectado a nenhuma entidade aqui — o formato de resposta
dele não foi validado.
