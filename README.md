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

- `name`: nome descritivo do passo
- `action`: ação a executar (`launch_app`, `wait`, `click`, `type`, `extract`, `log`, `dump`, `press_back`, `sleep`)
- `target`: seletor do elemento a ser encontrado (`classe`, `resourceId`, `texto`, `texto_contem`, `descricao`, `descricao_contem`)
- `selector`: alternativa ao `target` para usar chaves de UIAutomator2 diretamente (`className`, `resourceId`, `text`, `description`)
- `value`: valor para digitação ou tempo de espera
- `message`: texto para `log`
- `save_as`: nome da variável a salvar com o texto extraído
- `timeout`: tempo máximo de espera em segundos
- `on_failure`: lista de ações de fallback, como `delay:2` ou `log:falha`
- `continue_on_failure`: `true` para seguir o fluxo após erro

A seguir está um fluxo de login realista para o app Inter (`br.com.intermedium`):

```json
{
  "package": "br.com.intermedium",
  "variables": {
    "senhas": ["minha_senha_inter"]
  },
  "steps": [
    {
      "name": "Abrir app Inter",
      "action": "launch_app",
      "package": "br.com.intermedium",
      "timeout": 15
    },
    {
      "name": "Aguardar campo de senha",
      "action": "wait",
      "target": {
        "classe": "android.widget.EditText"
      },
      "timeout": 20
    },
    {
      "name": "Digitar senha",
      "action": "type",
      "target": {
        "classe": "android.widget.EditText"
      },
      "value": "$senhas.0",
      "timeout": 10
    },
    {
      "name": "Clicar em Entrar",
      "action": "click",
      "target": {
        "texto_contem": "Entrar"
      },
      "timeout": 15,
      "on_failure": ["delay:2"]
    },
    {
      "name": "Aguardar saldo (R$)",
      "action": "wait",
      "target": {
        "texto_contem": "R$"
      },
      "timeout": 20
    },
    {
      "name": "Extrair saldo",
      "action": "extract",
      "target": {
        "texto_contem": "R$"
      },
      "save_as": "saldo",
      "timeout": 10
    },
    {
      "name": "Logar saldo",
      "action": "log",
      "message": "💰 Saldo extraído: $saldo"
    }
  ]
}
```

## Observações

- O `DumpManager` detecta mudanças de página usando hash do dump XML e mantém cache para evitar leituras repetidas quando a tela não muda.
- O `ElementFinder` tenta localizar elementos por seletores exatos e usa XPath como fallback para buscas por texto, descrição ou classes.
- O `FlowRunner` resolve variáveis em `value`, `message` e em seletores, permitindo usar `$saldo` e `$senhas.0` no fluxo.
- O fluxo suporta `continue_on_failure` para prosseguir após erro, e `on_failure` para ações como `delay:2` e `log:...`.

## Testes

Para executar testes com `pytest`:

```bash
pip install -r requirements-dev.txt
pytest
```
