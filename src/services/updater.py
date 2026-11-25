import os
import sys
import json
import re
import urllib.request
import urllib.error
import subprocess
from src.core.config import Config
from src.core.logger import log

class UpdaterService:
    @staticmethod
    def parse_version(v_str: str) -> tuple[int, ...]:
        """
        Normaliza strings de versão como 'v1.8.0', '1.9' ou 'v1.8' em uma tupla comparável: (1, 8, 0).
        """
        clean = re.sub(r'^[^\d]*', '', str(v_str).strip())
        parts = []
        for p in clean.split('.'):
            match = re.match(r'^\d+', p)
            if match:
                parts.append(int(match.group(0)))
            else:
                break
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)

    @staticmethod
    def check_for_updates(repo: str = None) -> dict | None:
        """
        Consulta a API do GitHub Releases para verificar se há uma versão mais recente disponível.

        Args:
            repo (str, optional): Repositório no formato 'owner/repo'. Padrão obtido via Config.

        Returns:
            dict | None: Dados da release com URL do instalador se houver atualização, ou None.
        """
        app_config = Config.get_app_config()
        if not app_config.get("auto_update", True):
            log.info("Verificação de atualizações desabilitada nas configurações.")
            return None

        target_repo = (repo or app_config.get("github_repo") or Config.DEFAULT_GITHUB_REPO).strip()
        current_version_str = Config.APP_VERSION
        current_version = UpdaterService.parse_version(current_version_str)

        api_url = f"https://api.github.com/repos/{target_repo}/releases/latest"
        log.info(f"Verificando atualizações em '{api_url}' (Versão atual: v{current_version_str})...")

        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": "PMRBS-InicializadorPainelIDS-Updater",
                "Accept": "application/vnd.github.v3+json",
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status != 200:
                    log.warning(f"Resposta inesperada da API do GitHub: HTTP {resp.status}")
                    return None
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log.info(f"Nenhuma release publicada encontrada no repositório '{target_repo}' (HTTP 404).")
            else:
                log.warning(f"Erro HTTP ao consultar GitHub Releases: {e.code} {e.reason}")
            return None
        except urllib.error.URLError as e:
            log.warning(f"Não foi possível conectar ao GitHub: {e.reason}")
            return None
        except Exception as e:
            log.warning(f"Falha ao processar resposta do GitHub Releases: {e}")
            return None

        tag_name = data.get("tag_name", "").strip()
        remote_version = UpdaterService.parse_version(tag_name)

        if remote_version <= current_version:
            log.info(f"O aplicativo já está na versão mais recente ({tag_name} <= v{current_version_str}).")
            return None

        log.info(f"Nova versão identificada: {tag_name} (superior à atual v{current_version_str})!")

        # Procura o executável do instalador nos assets da release
        assets = data.get("assets", [])
        installer_asset = None

        # Prioriza arquivos que começam com 'Instalador' e terminam com '.exe'
        for asset in assets:
            name = asset.get("name", "")
            if name.lower().startswith("instalador") and name.lower().endswith(".exe"):
                installer_asset = asset
                break

        # Fallback: qualquer .exe nos assets
        if not installer_asset:
            for asset in assets:
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    installer_asset = asset
                    break

        if not installer_asset:
            log.warning(f"A release {tag_name} foi encontrada, mas nenhum instalador .exe está anexado.")
            return None

        return {
            "version": tag_name,
            "version_tuple": remote_version,
            "name": data.get("name") or tag_name,
            "notes": data.get("body", ""),
            "published_at": data.get("published_at", ""),
            "asset_name": installer_asset.get("name"),
            "download_url": installer_asset.get("browser_download_url"),
            "size": installer_asset.get("size", 0),
        }

    @staticmethod
    def download_installer(download_url: str, filename: str, progress_callback=None) -> str | None:
        """
        Baixa o executável do instalador para o diretório de updates local com suporte a streaming.

        Args:
            download_url (str): URL de download do executável no GitHub.
            filename (str): Nome do arquivo de destino.
            progress_callback (callable, optional): Função chamada com (bytes_baixados, total_bytes).

        Returns:
            str | None: Caminho do arquivo baixado em disco, ou None em caso de falha.
        """
        updates_dir = Config.get_updates_dir()
        dest_path = os.path.join(updates_dir, filename)
        temp_path = dest_path + ".part"

        log.info(f"Iniciando download do instalador: {filename} a partir de {download_url}...")

        req = urllib.request.Request(
            download_url,
            headers={
                "User-Agent": "PMRBS-InicializadorPainelIDS-Updater",
                "Accept": "application/octet-stream"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024  # 64 KB

                with open(temp_path, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            try:
                                progress_callback(downloaded, total_size)
                            except Exception:
                                pass

            # Substitui arquivo definitivo após download bem-sucedido
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except OSError:
                    pass
            os.rename(temp_path, dest_path)
            log.info(f"Download do instalador concluído com sucesso: '{dest_path}' ({downloaded} bytes).")
            return dest_path

        except Exception as e:
            log.error(f"Falha durante o download da atualização: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            return None

    @staticmethod
    def apply_update(installer_path: str, restart_args: list[str] = None):
        """
        Executa o instalador em segundo plano de forma silenciosa e encerra o processo atual,
        reiniciando a aplicação com a nova versão após a conclusão do instalador.

        Args:
            installer_path (str): Caminho absoluto do instalador baixado.
            restart_args (list[str], optional): Argumentos a repassar na reinicialização (ex: ['--auto']).
        """
        if not installer_path or not os.path.exists(installer_path):
            log.error(f"Arquivo de instalador não encontrado para aplicação: {installer_path}")
            return

        if Config.is_compiled():
            app_exe = sys.executable
        else:
            app_exe = sys.executable
            log.info(f"[MODO DEV] Executável do instalador pronto em: {installer_path}")

        args_str = " ".join(restart_args) if restart_args else ""
        log.info(f"Disparando instalação silenciosa via Inno Setup: '{installer_path}'...")

        # Script PowerShell que aguarda 1s para o processo atual liberar as travas de arquivo,
        # executa o instalador silenciosamente (/VERYSILENT /SUPPRESSMSGBOXES /NORESTART),
        # aguarda o término e reabre a aplicação.
        ps_command = (
            f'Start-Sleep -Seconds 1; '
            f'Start-Process -FilePath "{installer_path}" -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" -Wait; '
            f'if (Test-Path "{app_exe}") {{ Start-Process -FilePath "{app_exe}" -ArgumentList "{args_str}".Trim() }}'
        )

        try:
            # 0x08000000 = CREATE_NO_WINDOW
            # 0x00000008 = DETACHED_PROCESS
            creation_flags = 0x08000000 | 0x00000008
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_command],
                creationflags=creation_flags,
                close_fds=True
            )
            log.info("Processo de atualização despachado em background. Encerrando instância atual...")
            sys.exit(0)
        except Exception as e:
            log.error(f"Falha ao disparar o instalador da atualização: {e}")

    @staticmethod
    def run_auto_update_flow(restart_args: list[str] = None) -> bool:
        """
        Executa o fluxo completo e silencioso de verificação, download e aplicação do update.
        Projetado para rodar no modo autônomo (--auto).

        Returns:
            bool: True se uma atualização foi disparada (o processo irá fechar), False caso contrário.
        """
        try:
            update_info = UpdaterService.check_for_updates()
            if not update_info:
                return False

            installer_path = UpdaterService.download_installer(
                download_url=update_info["download_url"],
                filename=update_info["asset_name"]
            )

            if installer_path:
                log.info(f"Aplicando atualização para {update_info['version']}...")
                UpdaterService.apply_update(installer_path, restart_args=restart_args)
                return True
        except Exception as e:
            log.error(f"Erro no fluxo de auto-atualização: {e}")
        return False
