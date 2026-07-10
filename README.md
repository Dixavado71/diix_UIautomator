# diix_UIautomator

Framework Python modularizado para automação de dispositivos Android usando ADB e UIAutomator2.

## Estrutura do projeto

- `ui_automator/`
  - `adb_client.py`: gerenciamento de conexão com dispositivo Android via ADB/UIAutomator2
  - `dump_manager.py`: dump de UI em tempo real com hash e cache de página
  - `element_finder.py`: localização dinâmica de elementos por resourceId, classe, texto ou descrição
  - `flow_loader.py`: leitura de fluxo JSON e normalização de etapas
  - `action_runner.py`: execução do fluxo com ações de clique, digitação, espera e dump
  - `cli.py`: interface de linha de comando para executar fluxos
- `example_flow.json`: exemplo de fluxo de automação
- `pyproject.toml` e `setup.py`: configuração do pacote

## Instalação

Recomenda-se criar um ambiente virtual antes de instalar:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

O pacote instala a dependência principal:

- `uiautomator2`

## Uso CLI

Para executar um fluxo de automação JSON:

```bash
python -m ui_automator.cli --flow example_flow.json --debug
```

Ou, após a instalação do pacote:

```bash
diix-ui-automator --flow example_flow.json --debug
```

O resultado é salvo em um arquivo JSON com o mesmo nome da entrada, mas sufixado com `.result.json`.

## Formato do fluxo JSON

O arquivo de fluxo deve conter um objeto principal com a lista `steps`.
Cada passo pode ter as chaves:

- `action`: ação a executar (`wait_for`, `tap`, `set_text`, `dump`, `press_back`, `sleep`)
- `selector`: objeto de seleção do elemento (`resourceId`, `className`, `text`, `description`)
- `value`: valor para digitação ou tempo de espera
- `timeout`: tempo máximo de espera em segundos
- `description`: descrição opcional do passo

Exemplo:

```json
{
  "steps": [
    {
      "action": "wait_for",
      "selector": {
        "text": "Entrar"
      },
      "timeout": 20,
      "description": "Aguardar o botão Entrar aparecer"
    },
    {
      "action": "tap",
      "selector": {
        "text": "Entrar"
      },
      "description": "Clicar no botão Entrar"
    },
    {
      "action": "wait_for",
      "selector": {
        "resourceId": "com.example:id/password"
      },
      "description": "Aguardar o campo de senha"
    },
    {
      "action": "set_text",
      "selector": {
        "resourceId": "com.example:id/password"
      },
      "value": "minha_senha",
      "description": "Digitar senha"
    },
    {
      "action": "dump",
      "description": "Realizar dump da tela atual"
    }
  ]
}
```

## Observações

- O `DumpManager` detecta mudanças de página usando hash do dump XML e mantém cache para evitar leituras repetidas quando a tela não muda.
- O `ElementFinder` tenta localizar elementos por seletores exatos e usa XPath como fallback para buscas por texto ou descrição.
- O fluxo é facilmente estendido adicionando novas ações em `ui_automator/action_runner.py`.
