# DoubleSequenceIA 🎯

Sistema de análise de padrões de sequência para o Blaze Double.
Identifica padrões de 4, 5 e 6 cores e gera estratégias com base em probabilidade real.

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Edite `config.py`:
- `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` para notificações
- `MIN_CONFIDENCE` para ajustar sensibilidade (padrão: 70%)
- `MIN_OCCURRENCES` para ajustar raridade mínima (padrão: 5x)

## Uso

```bash
# 1. Coleta dados em tempo real
python main.py collect

# 2. Analisa DB e gera estratégias
python main.py analyze

# 3. Monitora em tempo real e dispara alertas
python main.py monitor

# 4. Relatório no terminal
python main.py report
```

## Dashboard

Abra `dashboard/index.html` no navegador.
Os arquivos `data/strategies.json` e `data/signals_log.json` são atualizados automaticamente.

## Estrutura

```
DoubleSequenceIA/
├── core/               # Engine de análise
├── monitor/            # Monitoramento em tempo real
├── strategies/         # Gerenciamento de estratégias
├── notifier/           # Alertas Telegram
├── coletor/            # Coleta WebSocket Blaze
├── dashboard/          # Interface web
├── data/               # Banco de dados e JSONs
├── config.py           # Configurações centralizadas
└── main.py             # Entry point
```
