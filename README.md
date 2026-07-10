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
- `action`: ação a executar (`launch_app`, `wait`, `click`, `type`, `extract`, `log`, `dump`, `press_back`, `sleep`, `find_all`, `tap_all`, `return`, `if`, `loop`)
- `target`: seletor do elemento a ser encontrado (`classe`, `resourceId`, `texto`, `texto_contem`, `descricao`, `descricao_contem`)
- `selector`: alternativa ao `target` para usar chaves de UIAutomator2 diretamente (`className`, `resourceId`, `text`, `description`)
- `value`: valor para digitação ou tempo de espera
- `message`: texto para `log`
- `save_as`: nome da variável a salvar com o texto extraído
- `timeout`: tempo máximo de espera em segundos
- `on_failure`: lista de ações de fallback, como `delay:2` ou `log:falha`
- `continue_on_failure`: `true` para seguir o fluxo após erro
- `over`: lista ou variável de lista para `loop`
- `var_name`: nome da variável de loop para `loop`
- `then` / `else`: blocos de passos condicionais para `if`

### Novas capacidades do fluxo
- `find_all`: retorna todos os elementos que correspondem ao seletor
- `tap_all`: clica em todos os elementos encontrados
- `return`: encerra o fluxo imediatamente com um valor retornado
- `if` e `loop`: estruturas condicionais e repetição para fluxos mais inteligentes

O projeto também inclui um exemplo de fluxo Pix em `example_pix_flow.json` para automação de Pix no app Inter.

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

## Publicação do pacote

O projeto está configurado como pacote Python via `pyproject.toml`. Para publicar uma nova versão no PyPI:

1. Gere os artefatos de distribuição:

```bash
python -m pip install --upgrade build twine
python -m build
```

2. Faça upload para o PyPI ou Test PyPI:

```bash
python -m twine upload dist/*
```

Se você quiser criar um novo release no GitHub, use o GitHub CLI:

```bash
gh release create v0.1.1 --title "v0.1.1" --notes "Atualizações do framework e novo fluxo Pix"
```

## Uso do fluxo Pix

O exemplo `example_pix_flow.json` mostra um fluxo completo para o app Inter com validação de chaves Pix.

### Passo a passo básico

1. Crie um ambiente virtual e instale o pacote:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Prepare um arquivo de chaves Pix chamado `chaves_pix.txt` no mesmo diretório do fluxo. Cada linha desse arquivo deve conter uma chave Pix válida. Um exemplo já está disponível no repositório em `chaves_pix.txt`:

```text
usuario1@example.com
usuario2@example.com
00000000000
```

3. Execute o fluxo Pix:

```bash
python -m ui_automator.cli --flow example_pix_flow.json --debug
```

ou

```bash
diix-ui-automator --flow example_pix_flow.json --debug
```

### Variáveis usadas no fluxo Pix

- `senhas`: lista de senhas para autenticar no app Inter
- `chaves_pix_file`: caminho para o arquivo de chaves Pix
- `saldo`: saldo extraído da conta Inter
- `valor_pagar`: valor identificado para pagamento Pix
- `erro_msg`: mensagem de erro capturada quando a chave é inválida

### O que o fluxo faz

### Exemplo: usar `wait_any` / `wait_for` + `find_all`

Para lidar com mudanças de tela e múltiplos elementos que podem aparecer em diferentes variantes, você pode usar `wait` (que faz fallback para `find_all`) ou `wait_any` que retorna todos os elementos correspondentes assim que aparecem.

Exemplo prático no fluxo Pix:

```json
{
  "name": "Aguardar e pegar botões Pagar",
  "action": "wait",
  "selector": {"texto_contem": "Pagar R$"},
  "timeout": 20
},
{
  "name": "Capturar todos os botões Pagar visíveis",
  "action": "find_all",
  "selector": {"texto_contem": "Pagar R$"}
},
{
  "name": "Clicar em todos os botões Pagar",
  "action": "tap_all",
  "selector": {"texto_contem": "Pagar R$"}
}
```

Ou, para obter diretamente todos os elementos assim que qualquer um aparecer, use `wait_any`:

```json
{
  "name": "Aguardar qualquer botão Pagar",
  "action": "wait_any",
  "selector": {"texto_contem": "Pagar R$"},
  "timeout": 20
}
```

Esses padrões ajudam quando o app muda a tela ou os elementos aparecem de forma assíncrona: `wait` tentará usar o método nativo `wait` do seletor quando disponível e fará fallback para polling com `find_all` caso contrário.


- Abre o app Inter
- Faz login usando a senha armazenada
- Navega até a tela de Pix
- Itera sobre todas as chaves no arquivo `chaves_pix.txt`
- Tenta enviar um Pix para cada chave
- Registra sucesso ou falha para cada tentativa

### Resultado

O fluxo salva resultados em um arquivo `.result.json` ao terminar. Use o modo `--debug` para ver logs detalhados no console.
