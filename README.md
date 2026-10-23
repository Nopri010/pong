# 🏓 Pongino

## Montagem com um potenciômetro e dois botões

Este checkout implementa os modos `arduino` (dois potenciômetros) e
`arduino_rasp` (um potenciômetro e dois botões). Para a montagem atual, A0 controla
o jogador 1; GPIO 27 sobe e GPIO 22 desce o jogador 2, com GND no pino físico 9.
Manter pressionado move continuamente; soltar ou pressionar ambos para a barra.

Veja o [guia de configuração e execução na Raspberry](docs/raspberry-botoes.md)
e o exemplo completo [`.env.raspberry.example`](.env.raspberry.example).

## Conceito

O projeto demonstra a comunicação entre potenciômetros conectados a um Arduino, ou entre um potenciômetro no Arduino e dois botões na Raspberry Pi, com uma interface Pong distribuída por HTTP e WebSocket. A aplicação normaliza as entradas para percentuais, cria um estado de domínio para as duas raquetes e publica atualizações em tempo real para os navegadores conectados.

A fonte serial usa streams assíncronos e tenta reconectar à porta configurada após falhas. O servidor Tornado e a leitura serial compartilham o mesmo event loop do `asyncio`, iniciado por `asyncio.run()`.

## Desenvolvimento orientado por IA

Este repositório contém um condutor técnico configurado em [`AGENTS.md`](AGENTS.md) e na pasta [`.ai-instructions/`](.ai-instructions/). O objetivo do trabalho é orientar o aluno a desenvolver o modo híbrido `arduino_rasp`: servidor Python na Raspberry Pi, um potenciômetro no Arduino e dois botões nos GPIOs da Raspberry. A implementação da branch `main` é a base legada com dois potenciômetros no Arduino; o modo híbrido é o resultado esperado deste trabalho.

Ao iniciar uma atividade, leia primeiro `AGENTS.md` e todos os arquivos existentes em `.ai-instructions/`. Use o checkout atual, `pong/`, `test/`, `pyproject.toml`, `uv.lock` e este README como fonte de verdade. O agente conduz o raciocínio, a implementação e a validação sem inventar hardware, credenciais ou resultados; o aluno edita o código e apresenta evidências.

As principais pastas de `pong/` e `test/` também possuem um `AGENTS.md` local
com regras específicas para aquela camada. Ao trabalhar em uma pasta, consulte
as instruções da raiz e o arquivo mais específico do caminho.

O fluxo recomendado é:

1. validar o modo original com dois potenciômetros no Arduino;
2. revisar os protocolos, a configuração e os testes;
3. preparar a Raspberry Pi e o circuito dos botões;
4. copiar este checkout para a Raspberry via SSH;
5. configurar a porta serial, os GPIOs e o modo `arduino_rasp`;
6. executar os testes e validar o comportamento no hardware.

## Demonstração

Confira uma demonstração de aproximadamente 40 segundos do projeto:

https://github.com/user-attachments/assets/ace504d5-78aa-4ed2-83e9-9f8730d2ba52

## Componentes Físicos

![Componentes Físicos](docs/componentes-fisicos.png)

O circuito é composto por um Arduino Uno conectado a dois potenciômetros montados em uma protoboard:

- **Potenciômetro 1 (Jogador 1 - Esquerda):** conectado ao pino analógico `A0`
- **Potenciômetro 2 (Jogador 2 - Direita):** conectado ao pino analógico `A1`
- **Alimentação:** pinos `5V` e `GND` do Arduino distribuídos para os barramentos da protoboard

O firmware está em [`docs/arduino/potenciometros/potenciometros.ino`](docs/arduino/potenciometros/potenciometros.ino).
As instruções de gravação e validação estão em [`docs/arduino/README.md`](docs/arduino/README.md).

No modo `arduino_rasp`, um dos potenciômetros é substituído por dois botões conectados aos GPIOs da Raspberry Pi. Cada botão deve ser ligado entre o GPIO configurado e o GND. O projeto usa pull-up interno, portanto o botão pressionado corresponde a nível lógico baixo. Os pinos são configurados pela numeração BCM e os sinais devem permanecer em 3,3 V.

## Tecnologias

### Execução

- [Python 3.12+](https://docs.python.org/3.12/)
- [Tornado 6.4+](https://www.tornadoweb.org/en/stable/)
- [pyserial](https://pyserial.readthedocs.io/en/latest/)
- [pyserial-asyncio](https://pyserial-asyncio.readthedocs.io/en/latest/)
- [GPIO Zero](https://gpiozero.readthedocs.io/en/stable/)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [HTML Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [JavaScript ES Modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [Tailwind CSS Play CDN](https://tailwindcss.com/docs/installation/play-cdn)
- [Arduino IDE](https://docs.arduino.cc/software/ide-v2)
- [Arduino Language Reference](https://docs.arduino.cc/language-reference/)

### Desenvolvimento

- [uv](https://docs.astral.sh/uv/)
- [pytest](https://docs.pytest.org/en/stable/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/stable/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Based Pyright](https://docs.basedpyright.com/latest/)
- [Taskipy](https://github.com/taskipy/taskipy)
- [Rich](https://rich.readthedocs.io/en/stable/)

## Como executar

Instale o `uv`, copie `.env.example` para `.env` e substitua todos os placeholders descritivos por valores válidos para o ambiente e o dispositivo utilizado.

```bash
uv sync
cp .env.example .env
```

Mantenha o `.env` diretamente na raiz do projeto, ao lado de `pyproject.toml`.
O servidor e o `launch.json` carregam especificamente `${workspaceFolder}/.env`.
O `uv sync` instala o pacote local no ambiente virtual, portanto não é necessário
definir `PYTHONPATH`. Os comandos Python da aplicação são executados como
módulos, preservando a raiz do projeto no caminho de importação.

Para usar o Arduino, configure `PONG_SERIAL_PORT`. Exemplos de portas seriais:

- macOS: `/dev/cu.usbmodemXXXX` ou `/dev/cu.usbserial-XXXX`;
- Linux: `/dev/ttyACM0` ou `/dev/ttyUSB0`;
- Windows: `COM3`.

Um `.env` mínimo pode conter:

```dotenv
PONG_INPUT_MODE=arduino
PONG_SERIAL_PORT=/dev/cu.usbmodemXXXX
PONG_SERIAL_BAUDRATE=115200
PONG_SERIAL_TIMEOUT_SECONDS=1
PONG_SERIAL_STARTUP_DELAY_SECONDS=2
PONG_SERIAL_RECONNECT_DELAY_SECONDS=2
PONG_POT1_PIN=A0
PONG_POT2_PIN=A1
PONG_BUTTON_PLAYER=1
PONG_BUTTON_UP_PIN=17
PONG_BUTTON_DOWN_PIN=27
PONG_BUTTON_POLL_INTERVAL_SECONDS=0.02
PONG_BUTTON_SPEED_PERCENT_PER_SECOND=160.0
PONG_BUTTON_DEBOUNCE_SECONDS=0.05
PONG_BUTTON_INITIAL_PERCENTAGE=50.0
PONG_SERVER_HOST=0.0.0.0
PONG_SERVER_PORT=8888
```

`PONG_INPUT_MODE=arduino` mantém o comportamento original: os dois valores do Arduino controlam os dois jogadores. Para usar um potenciômetro no Arduino e botões na Raspberry, configure `PONG_INPUT_MODE=arduino_rasp`. Nesse modo, `PONG_BUTTON_PLAYER` define qual jogador é controlado pelos botões; o outro valor do par serial é aproveitado e o canal serial correspondente aos botões é descartado.

Os botões têm comportamento incremental: o botão configurado em `PONG_BUTTON_UP_PIN` reduz o percentual da raquete e o botão em `PONG_BUTTON_DOWN_PIN` aumenta o percentual enquanto permanecer pressionado. `PONG_BUTTON_SPEED_PERCENT_PER_SECOND` controla a velocidade, `PONG_BUTTON_DEBOUNCE_SECONDS` filtra oscilações elétricas e `PONG_BUTTON_INITIAL_PERCENTAGE` define a posição inicial.

A fonte serial usa `PONG_SERIAL_TIMEOUT_SECONDS` para limitar a espera de cada linha, `PONG_SERIAL_STARTUP_DELAY_SECONDS` para aguardar a inicialização do Arduino e `PONG_SERIAL_RECONNECT_DELAY_SECONDS` para controlar o intervalo entre tentativas.

O parser espera os valores do Arduino na sequência `valor1`, `;`, `valor2`,
com cada item em uma linha. Os valores analógicos devem estar entre `0` e
`1023`, por exemplo:

```text
512
;
768
```

O formato serial permanece igual nos dois modos. No modo `arduino_rasp`, os dois valores continuam sendo consumidos para manter o sincronismo do stream, mas somente o valor do jogador que permanece no Arduino é usado no estado final.

Inicie o servidor:

```bash
uv run task run
```

Acesse `http://localhost:8888` no navegador.

### Debug no VS Code

1. Execute `uv sync` para criar ou atualizar o ambiente virtual.
2. Selecione o interpretador `.venv` no VS Code.
3. Abra **Run and Debug**.
4. Selecione **Python: servidor Pongino** e pressione `F5`.

A configuração em `.vscode/launch.json` executa o módulo `pong.cli.server`, usa
a raiz do projeto como diretório de trabalho e carrega as variáveis de `.env`.
Os logs de inicialização ficam visíveis no terminal integrado.

Para acompanhar os potenciômetros no terminal:

O diagnóstico usa Rich com tabela e barras atualizadas em tempo real. Rich pertence ao grupo `dev`, instalado por `uv sync`; *esse comando deve ser executado sem o servidor principal, pois a porta serial normalmente não pode ser aberta por dois processos ao mesmo tempo*.

```bash
uv run task cli
```

### Executar na Raspberry Pi via SSH

Na máquina de desenvolvimento, conecte-se usando o endereço e o usuário reais da Raspberry:

```bash
ssh <usuario>@<ip-da-raspberry>
```

Se o checkout ainda não estiver na Raspberry, copie o estado atual do projeto por `rsync` ou `scp`. Não copie `.env`, `.venv`, caches, chaves ou credenciais. Na Raspberry, instale as dependências e configure o ambiente:

```bash
cd ~/pongino-rasp
uv sync
cp .env.example .env
```

Para o modo com um potenciômetro no Arduino e dois botões na Raspberry, use no `.env`:

```dotenv
PONG_INPUT_MODE=arduino_rasp
PONG_SERIAL_PORT=/dev/ttyACM0
PONG_BUTTON_PLAYER=1
PONG_BUTTON_UP_PIN=17
PONG_BUTTON_DOWN_PIN=27
PONG_SERVER_HOST=0.0.0.0
PONG_SERVER_PORT=8888
```

Valide a instalação antes de iniciar o jogo:

```bash
uv run task test
uv run task lint
uv run task type-check
uv run task run
```

Depois, acesse `http://<ip-da-raspberry>:8888`. Os GPIOs usam numeração BCM; cada botão deve ser conectado entre o GPIO configurado e o GND. Não aplique 5 V aos GPIOs. O Arduino continua enviando os dois valores seriais, mas o modo híbrido consome ambos para manter o sincronismo e utiliza apenas o canal do potenciômetro que não foi substituído pelos botões.

Os comandos de qualidade são:

```bash
uv run task test
uv run task lint
uv run task format
uv run task type-check
```

O comando `test` executa os testes Python da pasta `test/` com pytest e exige
cobertura mínima de 95% (linhas e branches). Os testes assíncronos usam
pytest-asyncio e não dependem de um Arduino conectado. O comando `type-check`
executa o Based Pyright. O lint e a formatação são executados pelo Ruff.

## Observabilidade

O servidor configura o logging no entrypoint e registra a inicialização e a
finalização da fonte de entrada, tentativas de conexão serial, falhas de
leitura e conexões WebSocket. O cliente WebSocket atualiza o indicador da
interface e tenta reconectar com intervalo progressivo quando a conexão é
encerrada.

As rotas principais são:

- `GET /`: página do jogo;
- `GET /static/...`: arquivos JavaScript e recursos estáticos;
- `WebSocket /ws`: conexão em tempo real com o estado das raquetes.

Uma mensagem de atualização de raquete tem este formato:

```json
{
  "type": "paddle_update",
  "player1_pct": 50.0,
  "player2_pct": 75.0,
  "timestamp": 1710000000.0
}
```

## Estrutura

```text
├── .gitignore
├── .env.example
├── .vscode/
│   └── launch.json
├── .ai-instructions/
│   ├── 01_role_and_policy.md
│   ├── 02_cognitive_framework.md
│   ├── 03_project_architecture.md
│   ├── 04_raspberry_hardware.md
│   ├── 05_ssh_and_operations.md
│   └── 06_missions_and_assessment.md
├── AGENTS.md
├── README.md
├── docs/
│   ├── componentes-fisicos.png
│   └── demo-pongio.mp4
├── test/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_connection_manager.py
│   ├── test_domain.py
│   ├── test_parser.py
│   ├── test_serial_source.py
│   ├── test_serialization.py
│   └── test_server.py
├── pong/
│   ├── __init__.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── http/
│   │   │   ├── __init__.py
│   │   │   └── index_handler.py
│   │   └── websocket/
│   │       ├── __init__.py
│   │       ├── connection_manager.py
│   │       ├── handler.py
│   │       └── serializer.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── input_diagnostics.py
│   │   └── server.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── potenciometro/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py
│   │   │   ├── normalization.py
│   │   │   └── reading.py
│   │   └── pong/
│   │       ├── __init__.py
│   │       └── state.py
│   ├── infra/
│   │   ├── __init__.py
│   │   └── input/
│   │       ├── __init__.py
│   │       ├── arduino_rasp/
│   │       │   ├── __init__.py
│   │       │   └── source.py
│   │       ├── botoes/
│   │       │   ├── __init__.py
│   │       │   └── gpio.py
│   │       ├── factory.py
│   │       └── serial/
│   │           ├── __init__.py
│   │           ├── parser.py
│   │           └── source.py
│   ├── protocols/
│   │   ├── __init__.py
│   │   ├── leitor_botoes.py
│   │   └── input_source.py
│   └── web/
│       ├── index.html
│       ├── static/
│       │   ├── favicon.svg
│       │   └── js/
│       │       ├── app.js
│       │       ├── dom.js
│       │       ├── game.js
│       │       ├── ui.js
│       │       └── websocket.js
│       └── tests/
│           ├── game.test.js
│           ├── ui.test.js
│           └── websocket.test.js
├── pyproject.toml
└── uv.lock
```

Arquivos locais como `.env` e diretórios gerados como `.venv/`, `__pycache__/`
e `.ruff_cache/` não aparecem nessa árvore porque não fazem parte do código
versionado.

O fluxo da aplicação é:

1. `Settings` carrega as variáveis de ambiente com o prefixo `PONG_`.
2. A fábrica seleciona exclusivamente `SerialInputSource` ou `ArduinoRaspInputSource` conforme `PONG_INPUT_MODE`.
3. `PotStreamParser` valida a sequência serial e transforma valores ADC em percentuais.
4. No modo `arduino_rasp`, a fonte combina o jogador serial com o movimento incremental dos botões GPIO.
5. O domínio cria um `PongState` para os dois jogadores.
6. `ConnectionManager` transmite o estado para cada WebSocket conectado.
7. Os módulos JavaScript atualizam as raquetes e os indicadores da interface.

## Frontend e Tailwind

A interface fica em `pong/web/`. O Tornado entrega `web/index.html` em `/` e os módulos JavaScript de `web/static/` em `/static/`.

> Este projeto usa o Tailwind Play CDN para simplificar o desenvolvimento e as demonstrações. Os estilos são gerados no navegador e dependem de acesso à internet. Essa abordagem é destinada ao desenvolvimento; para produção, utilize CSS compilado localmente.

O script do [Tailwind Play CDN](https://tailwindcss.com/docs/installation/play-cdn) é carregado diretamente pelo HTML. Não é necessário instalar dependências npm nem executar build ou watch. Para iniciar toda a aplicação:

```bash
uv run task run
```
