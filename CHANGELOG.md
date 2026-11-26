# Registro de Alterações (Changelog)

Todas as modificações notáveis neste projeto são documentadas neste arquivo.

## [1.9.1] - 2026-11-26

### Corrigido
- Removida a flag não suportada `--no-sandbox` do Chromium em `automation.py` e `scraper.py`, eliminando a barra de aviso persistente ao iniciar o navegador.
- Corrigido erro de inicialização do Microsoft Edge WebView2 (`EBWebView`) ao abrir a interface de administração (`--config`) a partir de usuários não-administradores via elevação UAC.
- Isolados os diretórios de dados do WebView2 (`webview2_user` no perfil local e `webview2_admin` em ProgramData) e configurado `WEBVIEW2_USER_DATA_FOLDER` explicitamente.
- Sanitização das variáveis de ambiente (`TEMP` e `TMP`) no modo administrativo para prevenir bloqueios de ACL em perfis de outros usuários.
- Atualizado o script do Inno Setup (`setup_base.iss`) com permissões explícitas (`users-modify`) para as novas pastas de cache e arquivos temporários.

---

## [1.9.0] - 2026-11-25

### Adicionado
- Serviço nativo de Auto-Atualização (`UpdaterService`) integrado ao GitHub Releases e Inno Setup, com download assíncrono e aplicação silenciosa (`/VERYSILENT`).
- Verificação e aplicação automática de updates antes da inicialização do painel no modo autônomo (`--auto`).
- Painel Administrativo (`--config`) com verificação manual de atualizações e botão de instalação com um clique.
- Script automatizado de criação de releases (`scripts/release.py`) com sincronização de versão, compilação Nuitka/Inno Setup e publicação via GitHub CLI.

---

## [1.8.0] - 2026-11-18

### Adicionado
- Suporte a extensões de customização de estilo do Google Chrome e Microsoft Edge via políticas corporativas (`ExtensionInstallForcelist`).
- Configuração de perfil persistente compartilhado (`launch_persistent_context`) em `C:\ProgramData\PMRBS Inicializador do Painel IDS\chrome_profile`, eliminando o download assíncrono repetitivo da extensão e mantendo dados e cache salvos em disco.
- Gerenciamento de extensões integrado ao assistente do Instalador Inno Setup (`setup_base.iss`) com parâmetros pré-configurados para a URL de atualização (`updates.xml`) e ID da extensão.
- Painel Administrativo da TI (`--config`) atualizado para exibir e salvar as URLs e IDs de extensões diretamente no Registro do Windows com elevação de Administrador.
- Suporte a variáveis de ambiente `.env` para testes em ambiente de desenvolvimento (`PAINEL_EXTENSION_URL` e `PAINEL_EXTENSION_ID`).
- Tratamento resiliente de permissões para arquivos de log rotativos em ambientes restritos.

---

## [1.7.0] - 2026-11-05

### Adicionado
- Transmissão automática de tela para TVs via Google Cast utilizando o domínio `Cast` do Chrome DevTools Protocol (CDP `Cast.startDesktopMirroring`).
- Descoberta instantânea de dispositivos Google Cast na rede local via pacotes UDP mDNS (`_googlecast._tcp.local` na porta 5353) em ~100ms, sem necessidade de abrir o navegador.
- Busca ultra-rápida de unidades de atuação via requisição direta HTTP Keep-Alive ao endpoint do UniGUI (`idspaiele.dll/HandleEvent`) em ~150ms.
- Fallback automático com Playwright em modo headless caso a estrutura da requisição HTTP mude.
- Armazenamento global de credenciais criptografadas por computador em `C:\ProgramData` via DPAPI com a flag `CRYPTPROTECT_LOCAL_MACHINE`, viabilizando auto-inicialização multiusuário e via GPO.
- Interface gráfica adaptável baseada na área útil do monitor (`SPI_GETWORKAREA`) e layout responsivo.

---

## [1.6.0] - 2026-11-04

### Adicionado
- Extração dinâmica de unidades disponíveis via web scraping no momento do login.
- Configuração automatizada do monitor virtual auxiliar (VDD) via DevCon e driver `MttVDD`, com verificação PowerShell no instalador para impedir duplicação de dispositivos.
- Sistema de logs rotativos na pasta `logs/` com retenção automática dos 10 registros mais recentes.

---

## [1.5.0] - 2026-11-03

### Modificado
- Migração completa do processo de compilação do PyInstaller para código nativo C via **Nuitka** standalone.
- Reestruturação da arquitetura interna do projeto em módulos dedicados (`core`, `drivers`, `services`, `ui`).
- Suporte ao runtime Microsoft Edge WebView2 nativo no Windows 10 e 11.

---

## [1.4.0] - 2026-10-30

### Adicionado
- Suporte nativo à arquitetura 64-bit no instalador Inno Setup.
- Integração da interface de login com o WebView2.
- Correção no posicionamento e dimensionamento da janela do navegador no monitor virtual.

---

## [1.0.0] - 2026-10-25

### Adicionado
- Versão inicial funcional do automatizador de login e exibição do painel eletrônico IDS Saúde.
- Automação de navegação e autenticação com Playwright no navegador Chromium.
- Isolamento da exibição do painel em monitor virtual dedicado.
