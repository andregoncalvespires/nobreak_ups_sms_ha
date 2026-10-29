# Nobreak SMS (Serial UPS) — integração customizada para Home Assistant

[![Validate HACS](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/validate.yml/badge.svg)](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/validate.yml)
[![Hassfest](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/hassfest.yml/badge.svg)](https://github.com/andregoncalvespires/nobreak_ups_sms_ha/actions/workflows/hassfest.yml)

Integração de monitoramento do nobreak SMS PRO (ligado
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


## Versões

As tags e releases do GitHub são criadas automaticamente pelo workflow
`.github/workflows/release.yml`. A versão da integração é o campo `version`
de `custom_components/sms_nobreak/manifest.json`.

Para publicar uma nova versão:

1. Suba o campo `version` no `manifest.json` (por exemplo, de `0.1.1` para `0.1.2`).
2. Faça o commit e o push (ou o merge de um PR) na branch `main`.
3. O workflow lê a versão, e, se a release `v<versão>` ainda não existir, cria a
   tag e a release apontando para esse commit, com notas geradas a partir dos
   commits e PRs desde a release anterior.

O workflow só roda quando o `manifest.json` muda na `main`, e é idempotente: se a
release já existir, nada é feito. Também pode ser executado manualmente em
Actions → Release → "Run workflow". O HACS usa a tag da release mais recente
para oferecer a atualização aos usuários.
