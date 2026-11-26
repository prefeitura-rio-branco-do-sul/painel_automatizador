import clr_loader
import clr
import pythonnet
import webview
import sys
import os

if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

if getattr(sys, 'frozen', False) or '__compiled__' in globals():
    import importlib.machinery
    # Habilitar carregamento de pacotes crus (.py) no Nuitka standalone
    sys.path_hooks.insert(0, importlib.machinery.FileFinder.path_hook((importlib.machinery.SourceFileLoader, ['.py'])))
    
    # Adicionar o diretorio do executavel no path para achar a pasta do Playwright
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

def main():
    # 1. Rota de Administração da TI
    from src.core.logger import log

    if "--config" in sys.argv:
        log.info("=== INICIANDO MODO DE CONFIGURAÇÃO ADMINISTRATIVA ===")
        from src.core.config import Config
        admin_data_dir = Config.get_webview_data_dir(admin=True)
        os.environ["WEBVIEW2_USER_DATA_FOLDER"] = admin_data_dir

        # Sanitizar TEMP e TMP herdados de elevação UAC sobre usuário comum
        if os.environ.get("PROGRAMDATA"):
            temp_admin_dir = os.path.join(os.environ["PROGRAMDATA"], Config.APP_DATA_FOLDER_NAME, "temp")
            try:
                os.makedirs(temp_admin_dir, exist_ok=True)
                os.environ["TEMP"] = temp_admin_dir
                os.environ["TMP"] = temp_admin_dir
            except Exception:
                pass

        from src.ui.config_view import AdminWindowManager
        AdminWindowManager.open()
        sys.exit(0)

    log.info("=== INICIALIZANDO ORQUESTRADOR DO PAINEL ===")

    try:
        # 2. Rota de Auto-Inicialização (GPO/Startup)
        if "--auto" in sys.argv:
            log.info("Flag --auto detectada. Tentando inicialização silenciosa...")

            # Verificação prévia de auto-update antes de iniciar o painel
            try:
                from src.services.updater import UpdaterService
                if UpdaterService.run_auto_update_flow(restart_args=["--auto"]):
                    sys.exit(0)
            except Exception as update_err:
                log.warning(f"Não foi possível verificar auto-update: {update_err}")

            from src.core.credentials_repo import CredentialsRepository, SecureCredentials
            loaded_data = CredentialsRepository.load()
            
            if loaded_data.get("usuario") and loaded_data.get("senha") and loaded_data.get("unidade"):
                log.info("Credenciais completas encontradas. Pulando interface gráfica.")
                
                secure_credentials = SecureCredentials(loaded_data)
                
                from src.drivers.virtual_display import VirtualDisplayManager
                VirtualDisplayManager.ensure_virtual_display()

                from src.services.automation import AutomationService
                AutomationService.run_panel(secure_credentials)
                sys.exit(0)
            else:
                log.warning("Modo --auto invocado, mas as credenciais estão ausentes ou incompletas. Recuando para a interface gráfica.")

        # 3. Rota Padrão (Interface Gráfica)
        from src.core.config import Config
        user_data_dir = Config.get_webview_data_dir(admin=False)
        os.environ["WEBVIEW2_USER_DATA_FOLDER"] = user_data_dir

        try:
            import threading
            from src.services.updater import UpdaterService
            threading.Thread(target=UpdaterService.check_for_updates, daemon=True).start()
        except Exception:
            pass

        from src.ui.view import DesktopWindowManager
        credentials = DesktopWindowManager.capture_credentials()
        
        if not credentials:
            log.warning("Execução abortada pelo operador na tela de login.")
            sys.exit(0)
            
        from src.drivers.virtual_display import VirtualDisplayManager
        VirtualDisplayManager.ensure_virtual_display()

        from src.services.automation import AutomationService
        AutomationService.run_panel(credentials)
    except Exception as e:
        log.exception(f"Erro fatal na aplicação: {e}")
        import traceback
        log.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()