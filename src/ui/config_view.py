import webview
from src.core.config import Config
from src.ui.base_api import BaseWebviewAPI
from src.utils.template_engine import TemplateEngine
from src.drivers.virtual_display import VirtualDisplayManager

class ConfigAdminAPI(BaseWebviewAPI):
    def save_settings(self, url: str, extension_url: str = "", extension_id: str = ""):
        """
        Recebe os dados da interface HTML e salva no registro do Windows.
        
        Args:
            url (str): A URL do sistema alvo.
            extension_url (str): A URL de atualização (updates.xml) da extensão.
            extension_id (str): O ID da extensão no Chrome.
        """
        success = Config.save_app_config(url, extension_url, extension_id)
        if success:
            self.show_alert("Configurações salvas no Registro do Windows com sucesso! Reinicie o aplicativo.")
            self.close_window()
        else:
            self.show_alert("Erro de Permissão. Verifique se você está rodando como Administrador.")

    def toggle_virtual_monitor(self, action: str):
        """
        Recebe o comando da interface HTML para ligar/desligar o driver.
        
        Args:
            action (str): "LIGAR" para ativar o driver, "DESLIGAR" para desativar.
        """
        sucesso = False
        if action == "LIGAR":
            sucesso = VirtualDisplayManager.enable_driver()
        elif action == "DESLIGAR":
            sucesso = VirtualDisplayManager.disable_driver()
            
        if sucesso:
            self.show_alert(f"Comando executado! O monitor virtual foi {action.lower()} com sucesso. Reinicie a aplicação para visualizar.")
        else:
            self.show_alert("Erro. Verifique se o driver já foi instalado na máquina e se possui permissão de Administrador.")

    def check_for_updates(self):
        """
        Verifica se há atualizações disponíveis no GitHub e retorna o status.
        """
        from src.services.updater import UpdaterService
        info = UpdaterService.check_for_updates()
        if info:
            return {
                "available": True,
                "version": info["version"],
                "name": info["name"],
                "notes": info["notes"],
                "size_mb": round(info["size"] / (1024 * 1024), 1) if info.get("size") else 0
            }
        return {"available": False, "version": Config.APP_VERSION}

    def apply_update_now(self):
        """
        Dispara o download e a instalação silenciosa da nova versão.
        """
        import threading
        from src.services.updater import UpdaterService
        def _bg():
            UpdaterService.run_auto_update_flow(restart_args=["--config"])
        threading.Thread(target=_bg, daemon=True).start()
        return True

class AdminWindowManager:
    @staticmethod
    def open():
        """
        Abre a janela de configuração avançada para o usuário.
        """
        api = ConfigAdminAPI()
        current_config = Config.get_app_config()
        status_driver = VirtualDisplayManager.status_driver()
        
        html_content = TemplateEngine.render(
            "admin.html", 
            "base.css",
            "admin.js",
            {
                "CURRENT_URL": current_config.get("url", ""),
                "CURRENT_EXTENSION_URL": current_config.get("extension_url", ""),
                "CURRENT_EXTENSION_ID": current_config.get("extension_id", ""),
                "STATUS_DRIVER": status_driver,
                "APP_VERSION": Config.APP_VERSION
            }
        )

        win_w, win_h = Config.get_adaptive_window_size(650, 780)
        webview.create_window(
            title="Configuração Avançada - TI",
            html=html_content,
            js_api=api,
            width=win_w,
            height=win_h,
            resizable=True,
            min_size=(380, 500)
        )
        webview.start()
