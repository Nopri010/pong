# 04 — Integração com Raspberry Pi

## Arduino e potenciômetros

- O sketch do projeto está em `docs/arduino/potenciometros/potenciometros.ino`. Abra esse
  arquivo diretamente no Arduino IDE.
- Em Arduino Uno/Nano clássico, ligue cada potenciômetro (preferencialmente
  10 kΩ) entre `5V` e `GND`, com o terminal central em `A0` (jogador 1) ou
  `A1` (jogador 2). Desconecte do `A0` qualquer divisor NTC antes de conectar o
  potenciômetro.
- No Arduino IDE, abra o sketch, selecione a placa e a porta USB corretas e use
  **Upload**. No Monitor Serial a `115200 baud`, confirme a sequência `valor A0`,
  `;`, `valor A1`, cada item em uma linha e repetida a cada 100 ms.
- Feche o Monitor Serial antes de executar `uv run task cli` ou
  `uv run task run`: normalmente só um processo pode abrir a porta serial por vez.
- O modo `arduino_rasp` usa o mesmo firmware e protocolo. Com
  `PONG_BUTTON_PLAYER=1`, os botões controlam o jogador 1 e o potenciômetro em
  `A1` controla o jogador 2; com `PONG_BUTTON_PLAYER=2`, o potenciômetro em `A0`
  controla o jogador 1. O Arduino continua enviando os dois canais.

## Ligações

- Use numeração BCM nos pinos configurados.
- Cada botão deve ligar um GPIO ao GND.
- O código usa pull-up interno; pressionado significa nível lógico baixo.
- Não aplique 5 V a um GPIO da Raspberry.
- Configure os números BCM fisicamente conectados em `PONG_BUTTON_UP_PIN` e
  `PONG_BUTTON_DOWN_PIN`; não presuma que a disposição física esquerda/direita
  corresponde a subir/descer.
- `PONG_BUTTON_PLAYER=1` seleciona o jogador 1; `=2` seleciona o jogador 2.
  Essa opção escolhe a raquete controlada pelos botões, não a direção deles.

## Configuração

No modo físico, revisar:

- `PONG_INPUT_MODE=arduino_rasp`;
- `PONG_SERIAL_PORT=/dev/ttyACM0` ou `/dev/ttyUSB0` conforme o Arduino;
- `PONG_BUTTON_PLAYER=1` ou `2`;
- `PONG_BUTTON_UP_PIN` e `PONG_BUTTON_DOWN_PIN`;
- `PONG_BUTTON_SPEED_PERCENT_PER_SECOND`,
  `PONG_BUTTON_POLL_INTERVAL_SECONDS`, `PONG_BUTTON_DEBOUNCE_SECONDS` e
  `PONG_BUTTON_INITIAL_PERCENTAGE` conforme necessário.

Não usar ADC para os botões. O Arduino continua responsável pelo potenciômetro.
`gpiozero` é uma dependência normal do projeto e deve ser importada no módulo,
não carregada dinamicamente dentro do construtor do leitor.

## Comportamento esperado

- botão de subir reduz o percentual;
- botão de descer aumenta o percentual;
- percentuais menores movem a raquete para o topo da tela; percentuais maiores,
  para baixo;
- manter pressionado gera movimento incremental baseado em tempo;
- soltar interrompe o movimento;
- ambos pressionados resultam em direção neutra;
- a posição é limitada entre 0% e 100%.

## Diagnóstico

Antes de iniciar o servidor, execute `uv run task cli` sozinho, sem outro
processo usando a porta serial. Confirme no diagnóstico a origem de cada
jogador, pressione e solte os dois botões e verifique o percentual e o estado
pressionado/solto. O servidor registra o backend de pinos selecionado pelo GPIO
Zero; confirme que ele não é um backend simulado e que o usuário tem acesso aos
GPIOs.

Ao pressionar o GPIO ligado a `PONG_BUTTON_UP_PIN`, a tabela deve indicar
"Botão subir" e o percentual deve diminuir; em `PONG_BUTTON_DOWN_PIN`, deve
indicar "Botão descer" e o percentual deve aumentar. Se a tabela indicar o outro
botão, confira a correspondência entre os pinos BCM configurados e a fiação antes
de alterar a regra de movimento.

Se o diagnóstico mostrar pinos diferentes dos declarados no `.env`, verifique
as variáveis `PONG_BUTTON_*` exportadas no shell: variáveis de ambiente têm
precedência sobre os valores do arquivo `.env`. Para testar usando os pinos do
`.env` no Raspberry Pi OS, remova possíveis overrides dos pinos ao invocar:

```bash
env -u PONG_BUTTON_UP_PIN -u PONG_BUTTON_DOWN_PIN uv run task cli
```

No `uv run task cli`, a barra progride horizontalmente para representar o valor
percentual: diminuir o percentual encurta a barra à esquerda e aumentá-lo a
preenche à direita. Essa barra não representa o lado físico do botão nem a
posição horizontal da raquete. Se os controles estiverem fisicamente à esquerda
e à direita, associe cada BCM à ação lógica desejada por `PONG_BUTTON_UP_PIN` e
`PONG_BUTTON_DOWN_PIN`.

Antes de culpar o código, verificar se a sessão está em uma Raspberry Pi com
Raspberry Pi OS, além de alimentação, GND comum, numeração BCM, porta serial e
permissões do usuário no grupo `dialout`. Um teste com fake valida a lógica, mas
não prova que a montagem física está correta.

Se o ambiente não for uma Raspberry Pi com Raspberry Pi OS, interrompa a
validação física e informe ao aluno que não é possível prosseguir com a etapa de
GPIO naquele ambiente. Não crie importações dinâmicas ou um fallback para
simular a plataforma.
