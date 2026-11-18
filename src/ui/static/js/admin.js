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