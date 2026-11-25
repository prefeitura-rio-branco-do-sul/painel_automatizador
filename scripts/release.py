#!/usr/bin/env python3
"""
Orquestrador de Releases para o Painel Automatizador IDS.

Uso:
    python scripts/release.py [patch|minor|major|VERSAO] [-m "Descricao da release"] [opcoes]

Exemplos:
    python scripts/release.py minor -m "servico de auto-atualizacao integrado ao github releases"
    python scripts/release.py 1.9.0 -m "release v1.9.0 oficial"
    python scripts/release.py patch --skip-build
"""

import os
import sys
import re
import json
import shutil
import argparse
import subprocess
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def log_info(msg: str):
    print(f"\033[94m[*] {msg}\033[0m")

def log_success(msg: str):
    print(f"\033[92m[✓] {msg}\033[0m")

def log_warning(msg: str):
    print(f"\033[93m[!] {msg}\033[0m")

def log_error(msg: str):
    print(f"\033[91m[✗] {msg}\033[0m")

def get_current_version() -> tuple[int, int, int]:
    pkg_path = os.path.join(ROOT_DIR, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            v_str = data.get("version", "1.8.0")
            parts = [int(p) for p in re.findall(r"\d+", v_str)]
            while len(parts) < 3:
                parts.append(0)
            return (parts[0], parts[1], parts[2])
    return (1, 8, 0)

def calculate_next_version(current: tuple[int, int, int], bump: str) -> tuple[int, int, int]:
    major, minor, patch = current
    bump_lower = bump.lower().strip()
    if bump_lower == "patch":
        return (major, minor, patch + 1)
    elif bump_lower == "minor":
        return (major, minor + 1, 0)
    elif bump_lower == "major":
        return (major + 1, 0, 0)
    else:
        # Versão explícita (ex: '1.9.0' ou 'v1.9.0')
        parts = [int(p) for p in re.findall(r"\d+", bump)]
        while len(parts) < 3:
            parts.append(0)
        return (parts[0], parts[1], parts[2])

def update_package_json(new_semver: str, dry_run: bool = False):
    pkg_path = os.path.join(ROOT_DIR, "package.json")
    if not os.path.exists(pkg_path):
        return
    log_info(f"Atualizando package.json -> version: {new_semver}")
    if dry_run:
        return
    with open(pkg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = new_semver
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def update_config_py(new_semver: str, dry_run: bool = False):
    cfg_path = os.path.join(ROOT_DIR, "src", "core", "config.py")
    if not os.path.exists(cfg_path):
        return
    log_info(f"Atualizando src/core/config.py -> APP_VERSION = '{new_semver}'")
    if dry_run:
        return
    with open(cfg_path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(r'APP_VERSION\s*=\s*["\'][^"\']+["\']', f'APP_VERSION = "{new_semver}"', content)
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def update_setup_iss(short_ver: str, dry_run: bool = False):
    iss_path = os.path.join(ROOT_DIR, "installer", "setup.iss")
    if not os.path.exists(iss_path):
        return
    log_info(f"Atualizando installer/setup.iss -> #define Versao '{short_ver}'")
    if dry_run:
        return
    with open(iss_path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(r'#define\s+Versao\s+["\'][^"\']+["\']', f'#define Versao "{short_ver}"', content)
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def update_readme_md(short_ver: str, dry_run: bool = False):
    readme_path = os.path.join(ROOT_DIR, "README.md")
    if not os.path.exists(readme_path):
        return
    log_info(f"Atualizando README.md -> referências de release v{short_ver}")
    if dry_run:
        return
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'releases/v[\d\.]+/Instalador_[^.]+\.exe',
        f'releases/v{short_ver}/Instalador_InicializadorPainelIDS_v{short_ver}.exe',
        content
    )
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def update_changelog_md(new_semver: str, message: str, dry_run: bool = False) -> str:
    changelog_path = os.path.join(ROOT_DIR, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        return message
    header = f"## [{new_semver}]"
    today = datetime.now().strftime("%Y-%m-%d")
    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if header in content:
        log_info(f"CHANGELOG.md já contém seção para [{new_semver}].")
        # Extrai o bloco de notas para a release
        match = re.search(rf'## \[{re.escape(new_semver)}\][^\n]*\n(.*?)(?=\n## \[|\Z)', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return message

    log_info(f"Inserindo nova entrada no CHANGELOG.md para [{new_semver}] - {today}...")
    if dry_run:
        return message

    new_section = (
        f"## [{new_semver}] - {today}\n\n"
        f"### Adicionado\n"
        f"- {message}\n\n"
        f"---\n\n"
    )

    # Insere antes da primeira seção existente de versão
    first_version_match = re.search(r'\n## \[', content)
    if first_version_match:
        pos = first_version_match.start() + 1
        new_content = content[:pos] + new_section + content[pos:]
    else:
        new_content = content + "\n\n" + new_section

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return f"- {message}"

def run_build(short_ver: str, dry_run: bool = False) -> str | None:
    log_info("Iniciando compilação do executável com Nuitka...")
    build_py = os.path.join(ROOT_DIR, "installer", "build.py")
    if not dry_run:
        res = subprocess.run([sys.executable, build_py], cwd=ROOT_DIR)
        if res.returncode != 0:
            log_error(f"Compilação Nuitka falhou com código {res.returncode}.")
            return None

    log_info("Gerando pacote instalador com Inno Setup 6 (iscc)...")
    setup_iss = os.path.join(ROOT_DIR, "installer", "setup.iss")
    iscc_cmd = shutil.which("iscc") or r"C:\Users\luis.castro\AppData\Local\Programs\Inno Setup 6\iscc.exe"
    if not dry_run:
        res = subprocess.run([iscc_cmd, setup_iss], cwd=ROOT_DIR)
        if res.returncode != 0:
            log_error(f"Inno Setup falhou com código {res.returncode}.")
            return None

    installer_name = f"Instalador_InicializadorPainelIDS_v{short_ver}.exe"
    expected_path = os.path.join(ROOT_DIR, "releases", f"v{short_ver}", installer_name)
    if os.path.exists(expected_path) or dry_run:
        log_success(f"Instalador gerado com sucesso: '{expected_path}'")
        return expected_path
    else:
        log_warning(f"Instalador não encontrado no caminho esperado: '{expected_path}'")
        return None

def git_commit_and_tag(short_ver: str, new_semver: str, message: str, dry_run: bool = False) -> bool:
    log_info("Preparando commit Git e tag de release...")
    commit_msg = f"feat: versao {short_ver} - {message}"
    tag_name = f"v{new_semver}"

    if dry_run:
        log_info(f"[DRY-RUN] Executaria: git commit -m \"{commit_msg}\" e git tag {tag_name}")
        return True

    files_to_add = [
        "package.json",
        "src/core/config.py",
        "installer/setup.iss",
        "README.md",
        "CHANGELOG.md",
        "scripts/release.py"
    ]
    existing_files = [f for f in files_to_add if os.path.exists(os.path.join(ROOT_DIR, f))]
    subprocess.run(["git", "add"] + existing_files, cwd=ROOT_DIR)

    res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=ROOT_DIR)
    if res.returncode != 0:
        log_warning("Nenhuma alteração para comitar ou commit falhou.")

    tag_res = subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], cwd=ROOT_DIR)
    if tag_res.returncode != 0:
        # Fallback para tag simples
        subprocess.run(["git", "tag", tag_name], cwd=ROOT_DIR)
    
    log_success(f"Commit e Tag '{tag_name}' criados com sucesso!")
    return True

def publish_github_release(tag_name: str, installer_path: str, message: str, notes: str, dry_run: bool = False):
    gh_cmd = shutil.which("gh")
    if not gh_cmd:
        log_warning("GitHub CLI (gh) não encontrado no PATH. Pulando publicação remota da release.")
        return

    log_info(f"Publicando Release '{tag_name}' no GitHub com anexo do instalador...")
    if dry_run:
        log_info(f"[DRY-RUN] Executaria: gh release create {tag_name} {installer_path} --title 'Versão {tag_name} - {message}'")
        return

    cmd = [
        gh_cmd,
        "release",
        "create",
        tag_name,
        installer_path,
        "--title", f"Versão {tag_name} - {message}",
        "--notes", notes or f"Release oficial {tag_name}"
    ]

    res = subprocess.run(cmd, cwd=ROOT_DIR)
    if res.returncode == 0:
        log_success(f"Release '{tag_name}' publicada com sucesso no GitHub!")
    else:
        log_warning(f"gh release create retornou código {res.returncode}. Verifique a autenticação ou se a tag já foi enviada.")

def main():
    parser = argparse.ArgumentParser(description="Automação de Release para o Painel Automatizador.")
    parser.add_argument("bump", nargs="?", default="minor", help="Tipo de incremento ('patch', 'minor', 'major') ou versão explícita (ex: '1.9.0').")
    parser.add_argument("-m", "--message", default="nova versao de release", help="Descrição sucinta das novidades desta release.")
    parser.add_argument("--skip-build", action="store_true", help="Pula a compilação no Nuitka e Inno Setup.")
    parser.add_argument("--skip-git", action="store_true", help="Pula o commit e a criação de tag no Git.")
    parser.add_argument("--skip-publish", action="store_true", help="Pula a publicação no GitHub Releases.")
    parser.add_argument("--dry-run", action="store_true", help="Simula as ações sem alterar arquivos nem executar comandos.")

    args = parser.parse_args()

    curr_tuple = get_current_version()
    curr_str = f"{curr_tuple[0]}.{curr_tuple[1]}.{curr_tuple[2]}"
    next_tuple = calculate_next_version(curr_tuple, args.bump)
    new_semver = f"{next_tuple[0]}.{next_tuple[1]}.{next_tuple[2]}"
    
    # Versão curta usada no setup.iss e instalador (ex: '1.9' se patch == 0, '1.9.1' se patch > 0)
    short_ver = f"{next_tuple[0]}.{next_tuple[1]}" if next_tuple[2] == 0 else new_semver
    tag_name = f"v{new_semver}"

    print("=" * 60)
    print(f"🚀 INICIANDO PROCESSO DE RELEASE")
    print(f"   Versão Atual:   v{curr_str}")
    print(f"   Nova Versão:    v{new_semver} (Instalador: v{short_ver})")
    print(f"   Tag de Release: {tag_name}")
    print(f"   Mensagem:       {args.message}")
    if args.dry_run:
        print("   [MODO DRY-RUN ATIVADO - NENHUMA ALTERAÇÃO REAL SERÁ FEITA]")
    print("=" * 60)

    # 1. Sincroniza metadados e arquivos de configuração
    update_package_json(new_semver, dry_run=args.dry_run)
    update_config_py(new_semver, dry_run=args.dry_run)
    update_setup_iss(short_ver, dry_run=args.dry_run)
    update_readme_md(short_ver, dry_run=args.dry_run)
    release_notes = update_changelog_md(new_semver, args.message, dry_run=args.dry_run)

    # 2. Compilação
    installer_path = None
    if not args.skip_build:
        installer_path = run_build(short_ver, dry_run=args.dry_run)
    else:
        log_info("Compilação pulada (--skip-build).")
        expected = os.path.join(ROOT_DIR, "releases", f"v{short_ver}", f"Instalador_InicializadorPainelIDS_v{short_ver}.exe")
        if os.path.exists(expected):
            installer_path = expected

    # 3. Git commit e Tag
    if not args.skip_git:
        git_commit_and_tag(short_ver, new_semver, args.message, dry_run=args.dry_run)
    else:
        log_info("Operações do Git puladas (--skip-git).")

    # 4. GitHub Releases
    if not args.skip_publish and installer_path:
        publish_github_release(tag_name, installer_path, args.message, release_notes, dry_run=args.dry_run)
    elif not installer_path:
        log_warning("Instalador não disponível. Publicação no GitHub Releases pulada.")
    else:
        log_info("Publicação no GitHub Releases pulada (--skip-publish).")

    print("=" * 60)
    log_success(f"Release {tag_name} concluída!")
    print("=" * 60)

if __name__ == "__main__":
    main()
