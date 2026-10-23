# Validação local do modo híbrido — 16/10/2026

Implementação solicitada pelo aluno. Revisão local realizada sobre configuração,
contratos, mapeamento de canais, movimento e ciclo de vida dos recursos.

- `uv run task test`: 95 testes aprovados, 99,27% de cobertura com branches.
- `uv run task type-check`: zero erros e avisos.
- `uv run task lint`: verificação Ruff aprovada.
- `node --test pong/web/tests/*.test.js`: 8 testes aprovados.
- `git diff --check`: sem erros de whitespace.

Ambiente local: Windows, Python 3.14.0, GPIO e serial falsos nos testes.
O pytest usou uma pasta temporária dentro de `work/` porque a pasta temporária
padrão do Windows estava inacessível. Não foi necessário alterar os testes por isso.

Comportamentos verificados: subir/descer por tempo decorrido, segurar/soltar,
ambos pressionados, limites, rejeição de valores inválidos, canais A0/A1 no modo
original, seleção do canal complementar no híbrido, espera pelo primeiro frame,
ociosidade sem retransmissão GPIO, reconexão serial e EOF, limpeza após falha
parcial e encerramento de HTTP/WebSocket após falha GPIO.

Montagem informada: Raspberry Pi 4, GPIO 27 para subir, GPIO 22 para descer,
GND no pino físico 9. Ainda faltam execução com Python 3.13 na Raspberry,
validação elétrica dos botões e observação das barras no navegador. Não há
comprovação física de GPIO nesta validação local.
