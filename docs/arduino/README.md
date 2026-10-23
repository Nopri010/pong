# Firmware Arduino do Pongino

Abra `potenciometros/potenciometros.ino` no Arduino IDE, selecione **Arduino Uno**
e a porta USB da placa. A pasta e o arquivo possuem o mesmo nome, conforme o
formato de sketch do Arduino.

## Ligacao e protocolo

- Jogador 1: terminal central do potenciometro em **A0**, extremos em **5V** e
  **GND** do Arduino.
- No modo original, o segundo potenciometro usa **A1**, 5V e GND do Arduino.
- A serial usa **115200 baud** e envia um quadro a cada aproximadamente 100 ms:
  valor ADC de A0, uma linha contendo `;`, valor ADC de A1. Cada valor esta entre
  0 e 1023. Nao sao transmitidos textos de diagnostico.
- No modo hibrido previsto, A0 continua controlando o jogador 1. Os botoes da
  Raspberry controlam o jogador 2 (`PONG_BUTTON_PLAYER=2`). O segundo valor
  serial continua sendo transmitido para preservar o protocolo, e devera ser
  descartado pela fonte hibrida. A1 desconectado pode apresentar valores variaveis.
- Os botoes sao ligados a GPIO/GND da Raspberry, conforme a configuracao BCM.
  Os 5V do Arduino nao devem ser conectados aos GPIOs.

O firmware serve aos dois modos. A selecao de modo e o controle incremental dos
botoes pertencem a aplicacao Python, cuja implementacao hibrida ainda esta
pendente no checkout base.

## Validacao

Depois do upload, abra o Monitor Serial a **115200 baud**. Gire o potenciometro:
o primeiro valor de cada quadro deve acompanhar o movimento. O valor 0
corresponde a 0% e 1023 a 100% no parser do Pongino.

Feche o Monitor Serial antes de iniciar o diagnostico `uv run task cli` ou o
servidor `uv run task run`, pois ambos precisam abrir a porta USB.

Com Arduino CLI e o suporte `arduino:avr` instalados, a compilacao e a gravacao
podem ser feitas a partir da raiz do repositorio:

```text
arduino-cli compile --fqbn arduino:avr:uno docs/arduino/potenciometros
arduino-cli upload --fqbn arduino:avr:uno --port COM3 --verify docs/arduino/potenciometros
```

`COM3` foi a porta identificada neste computador durante o desenvolvimento.
Confira a porta da placa antes de repetir o upload em outro computador ou na
Raspberry. A gravacao substitui o programa anterior da placa.

## Evidencia de execucao em 2026-10-16

O sketch foi compilado para Arduino Uno com Arduino CLI 1.5.1 e core AVR 1.8.8:
2154 bytes de flash e 188 bytes de RAM. O upload na COM3 foi seguido de
verificacao; uma comparacao independente confirmou os 2154 bytes gravados.

Antes da substituicao do firmware SMARTPARK, o teste encontrou zero quadros
Pongino validos a 115200 baud. Depois do upload, foram capturados 198 quadros
validos em 20 segundos. O protocolo serial esta validado no Arduino real.

A0 ficou entre 280 e 283 nessa captura. Como o potenciometro foi girado durante
o teste, ainda e necessario conferir a montagem e comprovar a variacao da
leitura. Essa evidencia nao comprova o movimento da barra no jogo nem a
integracao com GPIOs da Raspberry.

Na verificacao manual posterior, apos selecionar 115200 baud no Monitor Serial,
foi informado funcionamento do potenciometro com minimo de 44–45 e maximo de
1009 ao girar. Isso valida a resposta de A0; a normalizacao atual corresponde
a aproximadamente 4,3–4,4% no minimo e 98,6% no maximo, sem calibracao adicional.
O movimento da barra na aplicacao e a integracao GPIO ainda precisam ser
validados.
