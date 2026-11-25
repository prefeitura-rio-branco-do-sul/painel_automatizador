# Painel de Chamamento - Inicializador Autônomo (IDS)

Aplicação desktop desenvolvida pelo **Departamento de Tecnologia da Informação (DETEC)** da **Prefeitura Municipal de Rio Branco do Sul - PR** para automação, autenticação, inicialização autônoma, exibição em monitor virtual dedicado e transmissão automática via Google Cast (Chromecast / Google TV) do painel eletrônico de atendimento do sistema **IDS Saúde**.

---

## Principais Recursos

- **Atualização Automática Silenciosa (GitHub Releases + Inno Setup)**:
  - **Detecção Inteligente de Versões**: Consulta assíncrona à API pública do GitHub Releases (`/releases/latest`) para identificar novas versões publicadas sem lentidão na inicialização.
  - **Atualização 100% Silenciosa (`--auto`)**: No modo autônomo, baixa o instalador em background e executa a atualização silenciosa (`/VERYSILENT`), preservando as credenciais e configurações e reiniciando a aplicação com a nova versão.
  - **Gestão Manual no Painel Admin (`--config`)**: Permite à equipe de TI verificar atualizações sob demanda e disparar a instalação diretamente pela interface.
- **Suporte a Extensões de Estilo do Chrome/Edge (Perfil Persistente + GPO)**:
  - **Perfil Compartilhado Persistente (`launch_persistent_context`)**: O navegador utiliza um perfil local fixo em `C:\ProgramData\PMRBS Inicializador do Painel IDS\chrome_profile`, permitindo que extensões institucionais, cache e dados permaneçam salvos sem necessidade de download assíncrono a cada inicialização.
  - **Instalação e Gestão via Políticas Corporativas**: Integração nativa com `ExtensionInstallForcelist` (Chrome e Edge) gravada pelo instalador e configurável via Painel Admin (`--config`), eliminando a necessidade de scripts `.reg` avulsos.
- **Transmissão Automática para TVs (Google Cast via CDP & mDNS)**:
  - **Descoberta Instantânea (mDNS)**: Escaneia todas as interfaces de rede locais via pacotes UDP mDNS (`_googlecast._tcp.local` na porta `5353`) para listar as TVs disponíveis em ~100ms na tela de login, sem precisar abrir o navegador.
  - **Espelhamento 100% Automatizado (`Cast.startDesktopMirroring`)**: Utiliza o domínio `Cast` do Chrome DevTools Protocol combinado com `--auto-select-desktop-capture-source` e relay mDNS em segundo plano para espelhar automaticamente o monitor virtual na TV escolhida assim que o login é iniciado.
- **Busca Ultra-Rápida de Unidades (HTTP Keep-Alive + Fallback Playwright)**: Extrai dinamicamente a lista de unidades diretamente do endpoint Ajax do sistema (`idspaiele.dll/HandleEvent`) em ~150ms, mantendo o Playwright em modo headless como fallback automático de contingência.
- **Persistência e Criptografia no Escopo da Máquina (`ProgramData` + DPAPI)**:
  - As credenciais, a unidade de atuação e a TV de transmissão são salvas globalmente para o computador em `C:\ProgramData\PMRBS Inicializador do Painel IDS\credentials\credentials.json`.
  - A senha é protegida pela DPAPI do Windows com a flag `CRYPTPROTECT_LOCAL_MACHINE`, permitindo que **qualquer usuário do Windows** naquela máquina (ou scripts de inicialização via GPO) utilize a configuração padrão salva.
- **Interface Gráfica Adaptável (WebView2)**: As telas de Login e de Administração se ajustam automaticamente à área útil do monitor (`SPI_GETWORKAREA`), contam com layout responsivo para resoluções menores (ex: `1366x768`) e barra de rolagem integrada.
- **Monitor Virtual Inteligente (VDD)**: Instalação automatizada de monitor auxiliar virtual fixado em 1920x1080 (via `MttVDD` / DevCon), com verificação via PowerShell no instalador para evitar a criação de monitores duplicados.
- **Logs Temporais e Rotativos**: Geração de arquivos de log na pasta `logs/` nomeados com data e hora, mantendo automaticamente os 10 registros mais recentes com fallback de permissões.
- **Compilação Nativa com Nuitka**: Empacotado em código de máquina nativo C via **Nuitka** e distribuído com **Inno Setup**, oferecendo inicialização rápida e integração nativa com o Edge WebView2.

---

## Estrutura do Repositório

```text
painel_automatizador/
├── .github/
│   └── workflows/             # Workflows e pipelines de automação no GitHub Actions
├── bin/
│   └── vdd/                   # Binários e drivers do monitor virtual (DevCon, MttVDD, mttvdd.cat)
├── credentials/               # Armazenamento local de credenciais em ambiente dev (credentials.json)
├── installer/                 # Scripts de compilação e instalador Inno Setup
│   ├── build.ps1              # Script de automação unificada (Nuitka + Inno Setup)
│   ├── build.py               # Script orquestrador de build Nuitka standalone
│   ├── setup.iss              # Definições de release e variáveis da versão atual
│   └── setup_base.iss         # Script base do instalador Inno Setup e assistente
├── logs/                      # Histórico de logs rotativos da aplicação
├── releases/                  # Instaladores executáveis finais gerados por versão (.exe)
├── scripts/                   # Scripts de automação do projeto
│   └── release.py             # Orquestrador automatizado de releases e publicação
├── src/                       # Código-fonte da aplicação
│   ├── core/                  # Módulos centrais (Config, Logger, CredentialsRepository DPAPI)
│   ├── drivers/               # Gerenciador de hardware/display virtual (VirtualDisplayManager)
│   ├── services/              # Serviços de automação Playwright/Cast, auto-updater e busca mDNS/HTTP
│   ├── ui/                    # Interfaces gráficas Edge WebView2 (HTML, CSS responsivo, JS)
│   └── main.py                # Ponto de entrada e roteamento de argumentos da aplicação
├── .env                       # Configuração de ambiente local para desenvolvimento
├── .env.example               # Modelo de variáveis de ambiente do projeto
├── .gitattributes             # Normalização de finais de linha e arquivos binários
├── .gitignore                 # Arquivos e diretórios ignorados pelo controle de versão
├── CHANGELOG.md               # Histórico detalhado de alterações por versão
├── CONTRIBUTING.md            # Diretrizes de desenvolvimento para a equipe
├── LICENSE                    # Termos de uso e licença institucional
├── package.json               # Metadados e scripts de automação do projeto
├── README.md                  # Esta documentação
└── requirements.txt           # Dependências Python do projeto
```

---

## Modos de Execução

O sistema possui três rotas de execução acionadas por parâmetros de linha de comando:

### 1. Modo Padrão (Interface Gráfica de Login)
```bash
python -m src.main
# ou: npm start
```
Abre a interface gráfica (WebView2) carregando em paralelo e instantaneamente as **Unidades de Atuação** e as **TVs / Dispositivos Cast** disponíveis na rede. O operador pode marcar *"Manter estas credenciais como padrão"* para gravar o operador, senha, unidade e TV para todos os usuários do computador.

### 2. Modo Autônomo / Inicialização via GPO (`--auto`)
```bash
python -m src.main --auto
# ou: npm run auto
```
Ideal para inicialização automática no logon do Windows (via Registro `Run` ou GPO do Windows Server). Se houver credenciais salvas na máquina (`C:\ProgramData\PMRBS Inicializador do Painel IDS\credentials\credentials.json`), o sistema pula a tela de login, garante o monitor virtual ativo, faz login no painel e inicia a transmissão para a TV automaticamente. Caso não existam credenciais salvas, abre a tela de login normalmente.

### 3. Modo Administrativo / Configurações da TI (`--config`)
```bash
python -m src.main --config
# ou: npm run config
```
Também acessível dando um **duplo clique na logo** na tela de login. Solicita elevação de Administrador (UAC) e permite alterar a URL global do painel no Registro do Windows (`HKLM\SOFTWARE\PMRBS\InicializadorPainelIDS`), configurar a URL/ID de atualização da extensão corporativa e ativar/desativar manualmente o driver do monitor virtual.

---

## Scripts Disponíveis (npm / CLI)

No terminal, na raiz do projeto, você pode executar tanto via `npm` quanto chamando os comandos nativos:

| Comando | Equivalente CLI | Descrição |
|---|---|---|
| `npm start` | `python -m src.main` | Inicia o painel no modo interativo padrão (tela de login WebView2). |
| `npm run auto` | `python -m src.main --auto` | Executa no modo autônomo / logon silencioso via GPO. |
| `npm run config` | `python -m src.main --config` | Abre a janela administrativa com elevação de privilégios (UAC). |
| `npm run build` | `python installer/build.py` | Compila o executável standalone em código C nativo com Nuitka. |
| `npm run installer` | `iscc.exe installer/setup.iss` | Gera o instalador executável via Inno Setup 6. |
| `npm run pack` | `powershell ./installer/build.ps1` | Executa o build completo e a geração do instalador em um único comando. |
| `npm run release` | `python scripts/release.py` | Orquestra a release completa (versão, build, commit, tag e GitHub Release). |

---

## Como Compilar e Gerar o Instalador

1. Certifique-se de ter o Python, o **Nuitka** (com compilador C como MinGW64 ou MSVC) e o **Inno Setup 6** (`iscc.exe`) instalados.
2. Para compilar o executável e gerar o instalador completo em um único passo via PowerShell:

```powershell
./installer/build.ps1
# ou: npm run pack
```

Ou execute as etapas separadamente a partir da raiz do projeto:

```powershell
python installer/build.py
iscc.exe installer/setup.iss
```

O instalador final (`Instalador_InicializadorPainelIDS_v1.9.exe`) será gerado na pasta `releases/v1.9/`.

---

## Requisitos do Sistema

- **OS**: Windows 10 / 11 (x64)
- **Navegador**: Google Chrome (recomendado para suporte completo ao Media Router / Google Cast) ou Microsoft Edge
- **Python**: 3.10 ou superior (para desenvolvimento/build)
- **Bibliotecas Principais**: `playwright`, `pywebview`, `screeninfo`, `pywin32` (`win32crypt`), `clr_loader`, `pythonnet`

---

## Licença e Créditos

Desenvolvido pelo **Departamento de Tecnologia da Informação (DETEC)**  
Secretaria Municipal de Administração (SEMAD)  
**Prefeitura Municipal de Rio Branco do Sul - PR**
