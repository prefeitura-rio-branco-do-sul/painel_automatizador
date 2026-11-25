import os
import sys
import shutil
import json
import ctypes
from ctypes import wintypes
import winreg
from dotenv import load_dotenv
from src.core.logger import log

# Carrega as variáveis do .env se o arquivo existir na raiz
load_dotenv()

class Config:
    TITULO_APP = "Painel de Chamamento - Inicializador Autônomo"
    APP_VERSION = "1.9.0"
    REGISTRY_PATH = r"SOFTWARE\PMRBS\InicializadorPainelIDS"
    APP_DATA_FOLDER_NAME = "PMRBS Inicializador do Painel IDS"

    DEFAULT_PANEL_URL = "https://riobrancodosul-saude.ids.inf.br/riobrancodosul/painel/idspaiele.dll"
    DEFAULT_EXTENSION_ID = "gclbcjhjbpibjakacaakcgdomkkefmaj"
    DEFAULT_EXTENSION_URL = "https://raw.githubusercontent.com/prefeitura-rio-branco-do-sul/extensao_painel_ids_estilo/main/updates.xml"
    DEFAULT_GITHUB_REPO = "prefeitura-rio-branco-do-sul/painel_automatizador"

    CHROME_FORCELIST_PATH = r"SOFTWARE\Policies\Google\Chrome\ExtensionInstallForcelist"
    EDGE_FORCELIST_PATH = r"SOFTWARE\Policies\Microsoft\Edge\ExtensionInstallForcelist"

    @staticmethod
    def is_compiled() -> bool:
        """
        Verifica se a aplicação está empacotada/compilada (PyInstaller ou Nuitka).
        """
        return getattr(sys, 'frozen', False) or '__compiled__' in globals()

    @staticmethod
    def _ui_base_path() -> str:
        """
        Retorna o caminho base para os arquivos de UI (templates e estáticos).
        Se o aplicativo estiver empacotado, retorna o diretório apropriado.
        Caso contrário, retorna o diretório raiz do projeto.

        Returns:
            str: Caminho absoluto para a pasta base de UI.
        """
        if Config.is_compiled():
            if hasattr(sys, '_MEIPASS'):
                return sys._MEIPASS
            else:
                return os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    @staticmethod
    def get_app_config() -> dict:
        """
        Retorna as configurações seguindo a hierarquia de prioridades.
        1. Variáveis de Ambiente (.env)
        2. Registro do Windows (HKLM da aplicação ou políticas corporativas do navegador)
        3. Fallback (Arquivo local config.json em ProgramData ou LocalAppData)
        4. Valores padrão do sistema

        Returns:
            dict: Dicionário contendo 'url', 'extension_url' e 'extension_id'.
        """
        # 1. Variáveis de Ambiente (.env) - Prioridade Máxima
        env_url = os.getenv("PAINEL_URL")
        env_ext_url = os.getenv("PAINEL_EXTENSION_URL")
        env_ext_id = os.getenv("PAINEL_EXTENSION_ID")
        env_repo = os.getenv("GITHUB_REPO")
        env_auto_update = os.getenv("AUTO_UPDATE_ENABLED")

        # 2. Registro do Windows
        reg_url = None
        reg_ext_url = None
        reg_ext_id = None
        reg_repo = None
        reg_auto_update = None
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, Config.REGISTRY_PATH) as key:
                try:
                    reg_url, _ = winreg.QueryValueEx(key, "UrlPainel")
                except WindowsError:
                    pass
                try:
                    reg_ext_url, _ = winreg.QueryValueEx(key, "UrlExtensao")
                except WindowsError:
                    pass
                try:
                    reg_ext_id, _ = winreg.QueryValueEx(key, "IdExtensao")
                except WindowsError:
                    pass
                try:
                    reg_repo, _ = winreg.QueryValueEx(key, "UpdateRepo")
                except WindowsError:
                    pass
                try:
                    reg_auto_update, _ = winreg.QueryValueEx(key, "AutoUpdateEnabled")
                except WindowsError:
                    pass
        except WindowsError:
            pass

        # Se a extensão não foi encontrada na chave da aplicação, consulta a política oficial do Chrome/Edge
        if not reg_ext_url:
            for pol_path in [Config.CHROME_FORCELIST_PATH, Config.EDGE_FORCELIST_PATH]:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, pol_path) as pol_key:
                        val, _ = winreg.QueryValueEx(pol_key, "1")
                        if ";" in val:
                            parts = val.split(";", 1)
                            if not reg_ext_id:
                                reg_ext_id = parts[0].strip()
                            reg_ext_url = parts[1].strip()
                            break
                except WindowsError:
                    pass

        # 3. Fallback (Arquivo config.json global da máquina ou por usuário)
        fallback_url = None
        fallback_ext_url = None
        fallback_ext_id = None
        fallback_repo = None
        fallback_auto_update = None
        fallback_paths = [
            os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), Config.APP_DATA_FOLDER_NAME, "config.json"),
            os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), Config.APP_DATA_FOLDER_NAME, "config.json"),
        ]
        for fallback_path in fallback_paths:
            if os.path.exists(fallback_path):
                try:
                    with open(fallback_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        fallback_url = data.get("url")
                        fallback_ext_url = data.get("extension_url")
                        fallback_ext_id = data.get("extension_id")
                        fallback_repo = data.get("github_repo")
                        fallback_auto_update = data.get("auto_update")
                        break
                except Exception:
                    pass
        
        final_url = env_url or reg_url or fallback_url or Config.DEFAULT_PANEL_URL
        final_ext_url = env_ext_url if env_ext_url is not None else (reg_ext_url or fallback_ext_url or Config.DEFAULT_EXTENSION_URL)
        final_ext_id = env_ext_id if env_ext_id is not None else (reg_ext_id or fallback_ext_id or Config.DEFAULT_EXTENSION_ID)
        final_repo = env_repo or reg_repo or fallback_repo or Config.DEFAULT_GITHUB_REPO

        if env_auto_update is not None:
            final_auto_update = env_auto_update.strip().lower() not in ("0", "false", "no", "disabled")
        elif reg_auto_update is not None:
            final_auto_update = bool(reg_auto_update)
        elif fallback_auto_update is not None:
            final_auto_update = bool(fallback_auto_update)
        else:
            final_auto_update = True

        return {
            "url": final_url.strip() if final_url else "",
            "extension_url": final_ext_url.strip() if final_ext_url else "",
            "extension_id": final_ext_id.strip() if final_ext_id else Config.DEFAULT_EXTENSION_ID,
            "github_repo": final_repo.strip() if final_repo else Config.DEFAULT_GITHUB_REPO,
            "auto_update": final_auto_update
        }
    
    @staticmethod
    def save_app_config(url: str, extension_url: str = None, extension_id: str = None, github_repo: str = None) -> bool:
        """
        Salva as configurações de volta no Registro do Windows (HKLM) da aplicação e
        sincroniza a política corporativa de extensões do Chrome e Edge.
        Requer que o script esteja rodando com privilégios de Administrador.

        Args:
            url (str): URL do painel.
            extension_url (str, optional): URL de atualização (updates.xml) da extensão.
            extension_id (str, optional): ID da extensão no Chrome.
            github_repo (str, optional): Repositório GitHub para atualizações (owner/repo).
        Returns:
            bool: True se salvou com sucesso, False caso contrário.
        """
        try:
            # 1. Grava no registro do próprio aplicativo
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, Config.REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
                winreg.SetValueEx(key, "UrlPainel", 0, winreg.REG_SZ, url.strip())
                if extension_url is not None:
                    winreg.SetValueEx(key, "UrlExtensao", 0, winreg.REG_SZ, extension_url.strip())
                if extension_id is not None:
                    winreg.SetValueEx(key, "IdExtensao", 0, winreg.REG_SZ, extension_id.strip())
                if github_repo is not None:
                    winreg.SetValueEx(key, "UpdateRepo", 0, winreg.REG_SZ, github_repo.strip())

            # 2. Sincroniza com as políticas corporativas do Chrome e Edge
            ext_url = (extension_url if extension_url is not None else Config.DEFAULT_EXTENSION_URL).strip()
            ext_id = (extension_id if extension_id is not None and extension_id.strip() else Config.DEFAULT_EXTENSION_ID).strip()

            target_policies = [
                Config.CHROME_FORCELIST_PATH,
                Config.EDGE_FORCELIST_PATH,
            ]

            for pol_path in target_policies:
                try:
                    if ext_url:
                        entry_value = f"{ext_id};{ext_url}"
                        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, pol_path, 0, winreg.KEY_ALL_ACCESS) as pol_key:
                            winreg.SetValueEx(pol_key, "1", 0, winreg.REG_SZ, entry_value)
                    else:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, pol_path, 0, winreg.KEY_ALL_ACCESS) as pol_key:
                            try:
                                winreg.DeleteValue(pol_key, "1")
                            except FileNotFoundError:
                                pass
                except Exception as pol_err:
                    log.warning(f"Não foi possível atualizar a política em '{pol_path}': {pol_err}")

            return True
        except PermissionError:
            log.error("Permissão negada. O aplicativo não foi executado como Administrador.")
            return False
        except Exception as e:
            log.error(f"Falha ao gravar no registro: {e}")
            return False

    @staticmethod
    def get_template_path(filename: str) -> str:
        """
        Obtém o caminho absoluto para um arquivo de template.

        Args:
            filename (str): Nome do arquivo de template.

        Returns:
            str: Caminho absoluto para o arquivo de template.
        """
        base_path = Config._ui_base_path()
        if Config.is_compiled():
            return os.path.join(base_path, "templates", filename)
        return os.path.join(base_path, "ui", "templates", filename)

    @staticmethod
    def get_static_path(filename: str) -> str:
        """
        Obtém o caminho absoluto para o arquivo estático.

        Args:
            filename (str): Nome do arquivo estático.

        Returns:
            str: Caminho absoluto para o arquivo estático.
        """
        base_path = Config._ui_base_path()
        if Config.is_compiled():
            return os.path.join(base_path, "static", filename)
        return os.path.join(base_path, "ui", "static", filename)
    
    @staticmethod
    def get_browser_profile_path() -> str:
        """
        Retorna o caminho do perfil de navegador persistente compartilhado na máquina,
        permitindo que extensões instaladas via políticas, cache e preferências locais permaneçam salvos.

        Returns:
            str: Caminho absoluto para a pasta de perfil do navegador.
        """
        if Config.is_compiled():
            base_dir = os.path.join(
                os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                Config.APP_DATA_FOLDER_NAME
            )
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        profile_dir = os.path.join(base_dir, "chrome_profile")
        try:
            os.makedirs(profile_dir, exist_ok=True)
        except OSError:
            pass
        return profile_dir

    @staticmethod
    def get_updates_dir() -> str:
        r"""
        Retorna o caminho absoluto para o diretório de download de atualizações
        (em C:\ProgramData quando compilado, ou na pasta do projeto em modo dev).

        Returns:
            str: Caminho absoluto para a pasta de atualizações.
        """
        if Config.is_compiled():
            base_dir = os.path.join(
                os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                Config.APP_DATA_FOLDER_NAME
            )
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        updates_dir = os.path.join(base_dir, "updates")
        try:
            os.makedirs(updates_dir, exist_ok=True)
        except OSError:
            pass
        return updates_dir

    @staticmethod
    def get_storage_path() -> str:
        """
        Obtém o caminho absoluto para o arquivo de armazenamento de credenciais compartilhado na máquina
        (em C:\\ProgramData quando compilado, ou na pasta do projeto em modo dev), garantindo que as
        credenciais valham para o computador inteiro e não apenas para o usuário logado.

        Returns:
            str: Caminho absoluto para o arquivo de credenciais.
        """
        if Config.is_compiled():
            base_dir = os.path.join(
                os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                Config.APP_DATA_FOLDER_NAME
            )
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        credentials_dir = os.path.join(base_dir, "credentials")
        os.makedirs(credentials_dir, exist_ok=True)
        return os.path.join(credentials_dir, "credentials.json")

    @staticmethod
    def get_legacy_storage_path() -> str:
        """
        Retorna o caminho antigo principal de credenciais (mantido por compatibilidade).
        """
        return Config.get_legacy_storage_paths()[0]

    @staticmethod
    def get_legacy_storage_paths() -> list[str]:
        """
        Retorna todos os possíveis caminhos antigos de credenciais (por usuário em LOCALAPPDATA
        ou na raiz antiga) para migração automática para o armazenamento global da máquina.
        """
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

        return [
            os.path.join(local_app_data, Config.APP_DATA_FOLDER_NAME, "credentials", "credentials.json"),
            os.path.join(local_app_data, Config.APP_DATA_FOLDER_NAME, "credentials.json"),
            os.path.join(program_data, Config.APP_DATA_FOLDER_NAME, "credentials.json"),
            os.path.join(project_root, "credentials.json"),
        ]

    @staticmethod
    def get_adaptive_window_size(ideal_width: int, ideal_height: int) -> tuple[int, int]:
        """
        Calcula o tamanho ideal da janela limitando-o à área útil do monitor principal
        (descontando a barra de tarefas e respeitando a escala de DPI do Windows).

        Args:
            ideal_width (int): Largura desejada em telas grandes.
            ideal_height (int): Altura desejada em telas grandes.

        Returns:
            tuple[int, int]: (largura, altura) ajustadas para caber perfeitamente na tela.
        """
        try:
            rect = wintypes.RECT()
            # SPI_GETWORKAREA = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                work_w = max(400, rect.right - rect.left)
                work_h = max(400, rect.bottom - rect.top)
                width = min(ideal_width, int(work_w * 0.92))
                height = min(ideal_height, int(work_h * 0.88))
                return width, height
        except Exception:
            pass
        return ideal_width, ideal_height

    @staticmethod
    def get_browser_executable_path() -> str | None:
        """
        Retorna o caminho do executável do navegador (Chrome ou Edge) instalado no sistema.

        Returns:
            str | None: Caminho absoluto para o executável do navegador, ou None se não encontrado.
        """
        candidate_paths = [
            os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local"), "Microsoft", "Edge", "Application", "msedge.exe"),
        ]

        for path in candidate_paths:
            if path and os.path.exists(path):
                return path

        return shutil.which("chrome") or shutil.which("msedge")

    @staticmethod
    def get_cast_ignore_default_args() -> list[str]:
        """
        Retorna a lista de argumentos padrão do Playwright que devem ser ignorados
        para permitir que o Media Router e a descoberta de dispositivos Cast (mDNS/DIAL) funcionem.
        """
        return [
            "--disable-background-networking",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--mute-audio",
            "--disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,BlockOriginHeaderModificationOnRedirect,Translate,AutoDeElevate,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion",
        ]

    @staticmethod
    def get_cast_browser_args() -> list[str]:
        """
        Retorna as flags do Chrome necessárias para habilitar o domínio Cast via CDP.
        """
        return [
            "--enable-features=MediaRouter,DialMediaRouteProvider,CastMediaRouteProvider,CastAllowAllIPs",
            "--allow-running-insecure-content",
            "--lang=pt-BR",
        ]
