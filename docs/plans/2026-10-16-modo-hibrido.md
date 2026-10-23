# Controle híbrido do Pongino

Objetivo: manter dois potenciômetros no modo `arduino`; no modo `arduino_rasp`,
usar A0 para jogador 1 e dois botões para jogador 2, com posição incremental.

## Mapa e sequência

1. `test/test_buttons.py`, `test/test_config.py`: verificar direção, tempo,
   limites, ambos pressionados e configuração inválida antes de implementar.
2. `pong/domain/`: leitura comum e controle puro, sem bibliotecas de hardware.
3. `pong/infra/input/serial/`: emitir frames; `arduino/`: preservar os dois canais.
4. `pong/infra/input/botoes/` e `arduino_rasp/`: GPIO com pull-up/debounce,
   composição e tarefas com limpeza inclusive em falhas parciais.
5. `pong/infra/input/factory.py`, CLI e servidor: selecionar modo e encerrar em
   falha; preservar mensagem WebSocket e frontend.
6. `.env.example`, documentação e dependências: valores numéricos válidos e
   instruções de montagem/configuração, sem presumir os pinos físicos do usuário.
7. Validar pytest com cobertura >=95%, Ruff, BasedPyright e testes JavaScript.

GPIOs confirmados pelo aluno: 27 e 22, GND físico 9, Raspberry Pi 4.
Definido 27 para subir e 22 para descer. Implementação e verificações locais
concluídas; evidências em `docs/validacao-hibrido.md`. Testes usam leitores falsos;
aceitação física exige executar na Raspberry e observar ambos os jogadores.
