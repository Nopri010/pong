# 03 — Arquitetura real do Pongino

## Fluxo principal

```text
Settings
  → make_input_source
    → ArduinoInputSource ou ArduinoRaspInputSource
      → SerialInputSource
        → SerialPotentiometerFrame (dois canais)
      → mapeamento do modo
        → PotenciometroReading e/ou LeituraJogadorBotoes
          → PongState (duas posições, LeituraJogador)
            → ConnectionManager
              → WebSocket
                → módulos JavaScript do jogo
```

## Camadas existentes

- `pong/config.py`: configurações `PONG_*`, incluindo `input_mode`, representado
  pelo `InputMode(StrEnum)` com os membros `ARDUINO` e `ARDUINO_RASP`.
- `pong/domain/`: posições de jogador, leituras heterogêneas e regras puras,
  sem dependência de hardware. `PongState` sempre contém duas posições que
  implementam `LeituraJogador`.
- `pong/domain/botoes/`: entidade `ControleBotoes`, leitura da posição do jogador
  (incluindo os estados lógicos de subir/descer) e regra de movimento; não
  conhece GPIO, pinos ou `gpiozero`.
- `pong/domain/normalizacao.py`: normalização numérica genérica compartilhada
  entre os domínios de potenciômetro e botões.
- `pong/infra/input/serial/`: parser e reconexão assíncrona; emite um
  `SerialPotentiometerFrame` com os dois canais e timestamp, sem compor
  diretamente o estado do jogo.
- `pong/infra/input/arduino/`: mapeia os dois canais seriais para os dois
  jogadores no modo `arduino`.
- `pong/infra/input/botoes/`: adaptador GPIO baseado em `gpiozero`.
- Use os nomes atuais em português: o contrato fica em
  `pong/protocols/leitor_botoes.py` e o adaptador em `pong/infra/input/botoes/`.
  Ao conduzir a refatoração, atualize imports e testes para esses caminhos em vez
  de manter módulos paralelos `button_reader`/`buttons`.
- `pong/infra/input/arduino_rasp/`: coordena um canal serial ativo com a posição
  do jogador controlado pelos dois botões. O modo híbrido é um objetivo atual do
  projeto; não reduza a implementação ao comportamento legado da branch `main`.
- `pong/infra/input/arduino_rasp/mapeamento.py`: resolve jogador, canal/pino
  serial e pinos GPIO conforme `Settings` e `PONG_BUTTON_PLAYER`.
- `pong/infra/input/arduino_rasp/composicao.py`: combina o frame serial e a
  leitura dos botões em um `PongState` com as duas posições.
- `pong/infra/input/arduino_rasp/monitor_botoes.py`: gerencia o ciclo de vida dos
  leitores GPIO, amostra os botões e avança a posição com base no tempo decorrido.
- `pong/infra/input/arduino_rasp/source.py`: coordena serial, monitor e
  compositor; publica o estado combinado depois de receber dados seriais.
- `pong/infra/input/factory.py`: seleciona uma única fonte de entrada.
- `pong/protocols/`: contratos para fonte de entrada e `LeitorBotoesProtocol`.
- `pong/cli/server.py`: bootstrap do servidor, sem conhecer detalhes GPIO.
- `pong/cli/input_diagnostics.py`: diagnóstico das entradas por modo.
- `pong/api/`: HTTP, WebSocket e transmissão do estado.
- `pong/web/`: interface e controles locais por teclado.

## Modos de entrada

### `arduino`

O Arduino envia dois valores no formato existente `valor1`, `;`, `valor2`. Os
dois valores formam o `PongState`.

### `arduino_rasp`

O Arduino continua enviando os dois valores. O parser consome ambos para manter
o sincronismo, mas a fonte utiliza somente o jogador do potenciômetro que
permaneceu no Arduino. O jogador configurado em `PONG_BUTTON_PLAYER` é produzido
pelos dois botões GPIO. A fábrica cria somente o potenciômetro do jogador
complementar aos botões.

No `PongState`, cada jogador pode ter uma `PotenciometroReading` ou uma
`LeituraJogadorBotoes`. A leitura de botões contém a posição efetiva e os estados
lógicos de subir/descer. A fonte híbrida compõe o estado completo; a CLI não
mantém uma segunda fonte de estado para os botões.

O servidor não deve instanciar GPIO diretamente. A fábrica seleciona a fonte e
a própria fonte cria os leitores durante `start()`.

O sketch serial fica em `docs/arduino/potenciometros/potenciometros.ino`. Ele lê
`A0` e `A1` a 115200 baud; veja `04_raspberry_hardware.md` para gravar o sketch
e confirmar o protocolo antes de iniciar o servidor.

## Contratos e dados

- `InputSourceProtocol` define `start()`, `stop()` e `is_connected()`. O servidor
  depende desse contrato, não de uma classe serial ou GPIO concreta.
- `LeitorBotoesProtocol` expõe `esta_pressionado` e `fechar()`. O adaptador
  `LeitorBotoesGPIO` usa `gpiozero.Button` com pull-up e debounce.
- `LeituraJogador` exige `player`, `percentage`, `timestamp` e `tipo_entrada`.
  `PotenciometroReading` e `LeituraJogadorBotoes` implementam o contrato.
  `TipoEntradaJogador` identifica as origens com `POTENCIOMETRO` e `BOTOES`.
- `PongState` sempre contém as leituras dos dois jogadores e aceita tipos
  diferentes em cada posição. Seu timestamp de composição não substitui o
  timestamp original de cada leitura.
- Preserve as propriedades `player1_pos`, `player2_pos`, `player1_pct` e
  `player2_pct`; os consumidores e o serializador dependem dessa interface.
- `SerialPotentiometerFrame` contém `channel_1_percentage`,
  `channel_2_percentage` e `timestamp`; os canais já estão normalizados entre
  0% e 100%.
- `serialize_paddle_update` mantém a mensagem WebSocket pública:
  `type=paddle_update`, `player1_pct`, `player2_pct` e `timestamp`. A origem
  diferente de cada leitura não deve mudar esse contrato externo.

## Normalização numérica

`normalize_raw_value(raw_value, raw_min, raw_max)` rejeita uma faixa em que
`raw_min >= raw_max` e também rejeita leituras fora dos limites recebidos. Para
valores válidos, converte linearmente para percentual com
`(raw_value - raw_min) * 100 / (raw_max - raw_min)` e limita o resultado ao
intervalo 0–100. `adc_to_percent` usa os limites 0 e 1023. Não confunda essa
validação — que rejeita entrada ADC inválida — com `limitar_valor`, usado para
conter o movimento incremental dos botões nos limites do jogo.

O protocolo físico permanece compatível com o sketch: uma linha com o valor ADC
de `A0`, uma linha com `;` e uma linha com o valor ADC de `A1`, repetindo o par.
O parser aceita somente inteiros de 0 a 1023. Uma linha não numérica, um valor
fora da faixa, um separador sem valor pendente ou um separador duplicado limpa o
estado parcial. Um segundo número antes do separador substitui o valor pendente;
ele não completa um frame. Não altere esse protocolo para implementar o modo
híbrido.

## Configuração e validação

`Settings` carrega variáveis com prefixo `PONG_` do ambiente e de `.env`. Os
padrões e limites relevantes são:

| Variável | Padrão/limite | Regra |
| --- | --- | --- |
| `PONG_INPUT_MODE` | `arduino` | Valores suportados: `arduino` e `arduino_rasp`. |
| `PONG_SERIAL_PORT` | não definido | Deve identificar a porta USB do Arduino para execução física. |
| `PONG_SERIAL_BAUDRATE` | `115200`, maior que zero | Deve coincidir com o sketch. |
| `PONG_SERIAL_TIMEOUT_SECONDS` | `1.0`, maior que zero | Timeout por linha lida. |
| `PONG_SERIAL_STARTUP_DELAY_SECONDS` | `2.0`, maior ou igual a zero | Aguarda a inicialização do Arduino. |
| `PONG_SERIAL_RECONNECT_DELAY_SECONDS` | `2.0`, maior ou igual a zero | Intervalo entre tentativas de reconexão. |
| `PONG_POT1_PIN` / `PONG_POT2_PIN` | `A0` / `A1` | Identificadores dos canais Arduino. |
| `PONG_BUTTON_PLAYER` | `1`, inteiro entre 1 e 2 | Jogador controlado pelos botões no modo híbrido. |
| `PONG_BUTTON_UP_PIN` / `PONG_BUTTON_DOWN_PIN` | sem padrão, BCM 0–27 | Obrigatórios e diferentes no modo híbrido. |
| `PONG_BUTTON_POLL_INTERVAL_SECONDS` | `0.02`, maior que zero | Intervalo de amostragem GPIO. |
| `PONG_BUTTON_SPEED_PERCENT_PER_SECOND` | `160.0`, maior que zero | Velocidade incremental dos botões. |
| `PONG_BUTTON_DEBOUNCE_SECONDS` | `0.05`, maior ou igual a zero | Debounce passado ao leitor GPIO. |
| `PONG_BUTTON_INITIAL_PERCENTAGE` | `50.0`, entre 0 e 100 | Posição inicial do jogador dos botões. |
| `PONG_SERVER_HOST` / `PONG_SERVER_PORT` | `0.0.0.0` / `8888` | Host não vazio; porta entre 1 e 65535. |

A validação cruzada de configuração exige ambos os GPIOs no modo híbrido e
rejeita pinos de subir/descer iguais. Testes de configuração também devem cobrir
defaults, leitura do prefixo `PONG_`, limites e valores inválidos. O modo
`arduino` não deve exigir GPIO.

## Mapeamento e comportamento híbrido

O jogador dos botões é `PONG_BUTTON_PLAYER`; o jogador serial é seu oponente.
O mapeamento deve selecionar somente o potenciômetro complementar:

| `PONG_BUTTON_PLAYER` | Botões GPIO | Jogador serial | Canal/pino serial |
| --- | --- | --- | --- |
| `1` | jogador 1 | jogador 2 | canal 2 / `PONG_POT2_PIN` (padrão `A1`) |
| `2` | jogador 2 | jogador 1 | canal 1 / `PONG_POT1_PIN` (padrão `A0`) |

Embora só um canal serial seja usado no estado híbrido, o parser deve consumir
os dois para preservar o alinhamento. O compositor seleciona o canal mapeado,
converte-o em leitura de potenciômetro e combina a leitura dos botões na posição
correta do `PongState`. Rejeite uma composição se o potenciômetro ou a leitura de
botões pertencer ao jogador errado.

`ControleBotoes` é lógica de domínio pura: percentual e velocidade precisam ser
finitos; a posição inicial fica entre 0% e 100%; a velocidade deve ser positiva;
tempo decorrido inválido é rejeitado. Subir reduz o percentual, descer aumenta,
ambos pressionados ou ambos soltos não movem a raquete, e a posição fica limitada
entre 0% e 100%. O movimento usa segundos decorridos, não a quantidade de
iterações do loop.

## Ciclo de vida, falhas e diagnóstico

- A fábrica cria somente a fonte correspondente a `PONG_INPUT_MODE`. No modo
  `arduino`, são criados dois potenciômetros e nenhum leitor GPIO. No híbrido, é
  criado apenas o potenciômetro do jogador complementar.
- A fonte híbrida prepara os dois leitores GPIO durante `start()`, inicia a fonte
  serial e depois o monitor periódico. Se qualquer etapa de inicialização falhar,
  libere os leitores e pare a fonte serial. `stop()` cancela/aguarda a tarefa do
  monitor e fecha GPIO e serial; chamar `stop()` antes de `start()` deve ser
  seguro.
- Não emita `PongState` antes do primeiro frame serial. Depois dele, emita estado
  quando houver atualização serial, mudança de estado dos botões ou movimento da
  posição; não retransmita continuamente um estado ocioso sem mudanças.
- A fonte serial mantém reconexão após `SerialException`/`OSError`, aplica o
  atraso de início, limpa o buffer e usa timeout por linha. Cancelar e parar a
  fonte deve encerrar a tarefa e fechar o writer.
- Falhas da tarefa GPIO são comunicadas pelo callback de falha. O servidor usa
  esse callback para encerrar o event loop de execução e, no `finally`, parar a
  fonte, fechar o HTTP server e encerrar conexões WebSocket. `SIGINT` e `SIGTERM`
  também sinalizam a parada; remova os handlers instalados durante a limpeza.
- `pong/cli/input_diagnostics.py` substitui o antigo diagnóstico exclusivo de
  potenciômetros. No modo `arduino`, mostra os dois potenciômetros; no híbrido,
  mostra o jogador serial, o jogador dos botões, estados/direções GPIO,
  conectividade e frescor da leitura serial. O diagnóstico e o servidor não
  devem disputar a mesma porta serial.

O projeto exige Python 3.12+. `gpiozero` é dependência de execução; `rich` é
usada pelo diagnóstico e fica no grupo de desenvolvimento. Alterações de
dependências devem atualizar `pyproject.toml` e `uv.lock` pelo fluxo `uv`.

## Regras de dependência

- O domínio não importa `gpiozero`, `serial_asyncio`, Tornado ou código de CLI.
- O código Python deve comparar modos usando `InputMode.ARDUINO` ou
  `InputMode.ARDUINO_RASP`; os textos `arduino` e `arduino_rasp` ficam reservados
  para `.env`, CLI/documentação e fronteiras externas.
- O servidor depende do contrato de fonte, não de um dispositivo específico.
- `gpiozero` é uma dependência normal e é importada no módulo do adaptador; a
  criação dos objetos GPIO deve ocorrer somente no modo `arduino_rasp`, durante
  o `start()` da fonte.
- Fakes e testes não devem exigir uma Raspberry conectada.
