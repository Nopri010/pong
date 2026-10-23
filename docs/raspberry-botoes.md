# Executar com A0 e dois botões

Configuração desta montagem: Raspberry Pi 4 informada pelo aluno, potenciômetro
no Arduino (A0, 5V e GND), Arduino ligado por USB à Raspberry.

| Controle | BCM | Pino físico |
| --- | --- | --- |
| Subir jogador 2 | GPIO 27 | 13 |
| Descer jogador 2 | GPIO 22 | 15 |
| GND comum aos dois botões | — | 9 |

Cada botão fecha o contato entre seu GPIO e o GND. O programa ativa pull-up
interno e debounce de 50 ms. Não conecte o 5V do Arduino aos GPIOs da Raspberry.
Em botões de quatro pernas, use contatos de lados que só se conectam ao apertar.
Desligue a alimentação antes de mudar os fios.

## Atualizar a cópia na Raspberry

Copie os arquivos atualizados do projeto para a Raspberry, incluindo `pong/`,
`pyproject.toml`, `uv.lock` e os arquivos `.env.*.example`. Preserve seu `.env`
e não copie a pasta `.venv` do Windows. A cópia antiga na Raspberry não recebe
automaticamente as alterações feitas no PC.

No terminal da Raspberry:

```bash
cd /home/henrique/Desktop/Pongino/pongino-rasp
uv sync
nano .env
```

No `.env`, mantenha a porta serial que já funciona e coloque estas configurações
(substitua as linhas existentes; evite duplicá-las):

```dotenv
PONG_INPUT_MODE=arduino_rasp
PONG_SERIAL_BAUDRATE=115200
PONG_SERIAL_TIMEOUT_SECONDS=1
PONG_SERIAL_STARTUP_DELAY_SECONDS=2
PONG_SERIAL_RECONNECT_DELAY_SECONDS=2
PONG_BUTTON_PLAYER=2
PONG_BUTTON_UP_PIN=27
PONG_BUTTON_DOWN_PIN=22
PONG_BUTTON_POLL_INTERVAL_SECONDS=0.02
PONG_BUTTON_SPEED_PERCENT_PER_SECOND=160
PONG_BUTTON_DEBOUNCE_SECONDS=0.05
PONG_BUTTON_INITIAL_PERCENTAGE=50
```

O arquivo `.env.raspberry.example` é um exemplo completo dessa montagem; a porta
`/dev/ttyACM0` nele é apenas exemplo. Para identificar a porta real:

```bash
ls -l /dev/serial/by-id/
```

`uv sync` instala gpiozero e, no Linux, lgpio. Se o instalador precisar compilar
lgpio e informar ausência de SWIG/compilador/headers Python, instale somente os
pré-requisitos indicados (por exemplo, `sudo apt install swig build-essential
python3-dev`) e execute `uv sync` novamente. Use o Python 3.13 do Raspberry Pi OS.

## Diagnóstico e jogo

Feche o monitor serial da Arduino IDE. Rode primeiro:

```bash
uv run task cli
```

O diagnóstico informa os pinos, a conexão serial, as posições e os estados dos
botões. Antes do primeiro frame do Arduino, aparece "Aguardando leitura".
Gire o potenciômetro: jogador 1 deve mudar. Segure GPIO 27: jogador 2 deve subir.
Segure GPIO 22: deve descer. Solte: deve parar. Ambos pressionados: deve parar.
Nos extremos, a posição deve permanecer entre 0% e 100%.

Encerre o diagnóstico com Ctrl+C antes de iniciar o servidor (ambos usam a mesma
porta serial):

```bash
uv run task run
```

Abra <http://localhost:8888> no navegador da Raspberry. Se a barra estiver rápida
demais, reduza `PONG_BUTTON_SPEED_PERCENT_PER_SECOND` (por exemplo, para 80).

O firmware continua enviando A0 e A1 para preservar o protocolo. No modo híbrido
com jogador 2 nos botões, A1 é consumido e ignorado; pode ficar sem potenciômetro.
Para voltar ao modo original, reconecte o segundo potenciômetro e defina
`PONG_INPUT_MODE=arduino`.

## Evidências e limites

O aluno informou leitura do potenciômetro de aproximadamente 44 a 1009. Não foi
aplicada calibração: a conversão continua usando ADC 0–1023.
Os testes locais usam leitores falsos e verificam movimento, limites, seleção
de canais, reconexão e liberação dos recursos. A montagem GPIO precisa ser
validada na Raspberry; não foi acessada remotamente nesta implementação.

Referências: [GPIO Zero — botões](https://gpiozero.readthedocs.io/en/stable/api_input.html#button),
[GPIO Zero — backend lgpio](https://gpiozero.readthedocs.io/en/stable/api_pins.html#lgpio).
