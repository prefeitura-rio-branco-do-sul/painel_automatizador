# Guia de Contribuição

Obrigado pelo interesse em contribuir com o **Painel de Chamamento - Inicializador Autônomo (IDS)** da Prefeitura Municipal de Rio Branco do Sul.

## Diretrizes de Desenvolvimento

1. **Separação Modular de Responsabilidades**:
   - Mantenha o isolamento nas pastas de domínio correspondentes:
     - `src/core/`: Configurações centrais do sistema (`Config`), persistência criptografada via DPAPI (`CredentialsRepository`) e rotinas de logging rotativo (`Logger`).
     - `src/drivers/`: Controle de hardware e monitores auxiliares virtuais (`VirtualDisplayManager`).
     - `src/services/`: Orquestração do navegador Chromium, transmissões Cast via CDP (`AutomationService`) e descoberta mDNS/extração HTTP (`ScraperService`).
     - `src/ui/`: Telas e APIs de interface com WebView2 (`view.py`, `config_view.py`), templates HTML desacoplados e arquivos estáticos.

2. **Gerenciamento de Configurações e Ambientes**:
   - Siga a hierarquia de configurações implementada na classe `Config`:
     1. Variáveis de ambiente (`.env`) para testes locais em desenvolvimento;
     2. Registro do Windows (`HKLM\SOFTWARE\PMRBS\InicializadorPainelIDS`) e políticas corporativas do navegador (`ExtensionInstallForcelist`);
     3. Fallback de contingência em arquivo `config.json` em `ProgramData` ou `LocalAppData`;
     4. Valores padrão do sistema.
   - **Atenção**: Nunca comite senhas ou credenciais reais no repositório.

3. **Perfil de Navegador e Extensões**:
   - As sessões do Chromium devem sempre utilizar `p.chromium.launch_persistent_context` com o diretório compartilhado fornecido por `Config.get_browser_profile_path()` para assegurar persistência de extensões, dados e cache.
   - Não reintroduza o uso de `p.chromium.launch()` ou de contextos efêmeros (`new_context()`), pois eles isolam o navegador em abas anônimas e impedem a execução de extensões corporativas.

4. **Fluxo de Trabalho e Scripts**:
   - Para executar em modo desenvolvimento:
     ```bash
     npm start
     # ou python -m src.main
     ```
   - Para compilar o executável com Nuitka:
     ```bash
     npm run build
     # ou python installer/build.py
     ```
   - Para gerar o instalador completo via Inno Setup:
     ```bash
     npm run pack
     # ou powershell ./installer/build.ps1
     ```
   - Antes de gerar uma nova versão para distribuição, certifique-se de atualizar a versão no `installer/setup.iss`, no `package.json` e registrar os detalhes no `CHANGELOG.md`.

5. **Driver do Monitor Virtual (VDD)**:
   - Os arquivos de driver residem em `bin/vdd/` (`MttVDD.inf`, `MttVDD.dll`, `mttvdd.cat`, `devcon.exe`).
   - Não remova as etapas de aprovação de certificados (`certutil`) e verificação via PowerShell no instalador (`setup_base.iss`) para evitar a criação de dispositivos virtuais duplicados.
