document.getElementById('btnSalvar').addEventListener('click', function() {
    const u = document.getElementById('url').value;
    const extUrl = document.getElementById('extension_url').value;
    const extId = document.getElementById('extension_id').value;
    
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.save_settings(u, extUrl, extId);
    } else {
        alert("Erro de comunicação com o sistema.");
    }
});

document.getElementById('btnLigarDriver').addEventListener('click', function() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.toggle_virtual_monitor("LIGAR");
    }
});

document.getElementById('btnDesligarDriver').addEventListener('click', function() {
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.toggle_virtual_monitor("DESLIGAR");
    }
});

const btnVerificarUpdate = document.getElementById('btnVerificarUpdate');
const btnInstalarUpdate = document.getElementById('btnInstalarUpdate');
const updateContainer = document.getElementById('updateContainer');
const updateMsg = document.getElementById('updateMsg');
const updateStatusText = document.getElementById('updateStatusText');

if (btnVerificarUpdate) {
    btnVerificarUpdate.addEventListener('click', async function() {
        btnVerificarUpdate.disabled = true;
        btnVerificarUpdate.textContent = 'Verificando...';
        updateContainer.style.display = 'none';
        updateStatusText.style.display = 'block';
        updateStatusText.textContent = 'Consultando o GitHub Releases...';

        try {
            if (window.pywebview && window.pywebview.api) {
                const res = await window.pywebview.api.check_for_updates();
                if (res && res.available) {
                    updateStatusText.style.display = 'none';
                    updateContainer.style.display = 'block';
                    updateMsg.textContent = `Nova versão ${res.version} disponível (${res.size_mb} MB)!`;
                } else {
                    updateStatusText.style.display = 'block';
                    updateStatusText.textContent = 'O sistema já está na versão mais recente.';
                }
            }
        } catch (e) {
            updateStatusText.style.display = 'block';
            updateStatusText.textContent = 'Erro ao verificar atualizações: ' + e;
        } finally {
            btnVerificarUpdate.disabled = false;
            btnVerificarUpdate.textContent = 'Verificar Atualizações';
        }
    });
}

if (btnInstalarUpdate) {
    btnInstalarUpdate.addEventListener('click', function() {
        btnInstalarUpdate.disabled = true;
        btnInstalarUpdate.textContent = 'Baixando atualização...';
        updateStatusText.style.display = 'block';
        updateStatusText.textContent = 'O instalador está sendo baixado em segundo plano. O sistema será reiniciado em instantes.';
        
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.apply_update_now();
        }
    });
}