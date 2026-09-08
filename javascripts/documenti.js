// ============================================================
// DOCUMENTI - Funzionalità delle schede singole
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    var baseUrl = (document.querySelector('meta[name="ami-base-url"]')?.content || '').replace(/\/$/, '');

    // ============================================================
    // 1. ARGOMENTI: split di serie multiple in link separati
    // ============================================================
    document.querySelectorAll('.metadata-item').forEach(function(item) {
        var label = item.querySelector('.metadata-label');
        var value = item.querySelector('.metadata-value');
        if (!label || !value) return;
        if (label.textContent.trim() !== 'Argomenti') return;
        var link = value.querySelector('a');
        if (!link) return;
        var tags = link.textContent.split(';').map(function(t) { return t.trim(); }).filter(Boolean);
        if (tags.length < 2) return;
        var fragment = document.createDocumentFragment();
        tags.forEach(function(tag, index) {
            if (index > 0) fragment.append(' , ');
            var a = document.createElement('a');
            a.href = baseUrl + '/documenti/?serie=' + encodeURIComponent(tag);
            a.textContent = tag;
            fragment.append(a);
        });
        value.replaceChildren(fragment);
    });

    // ============================================================
    // 2. FULLSCREEN per iframe
    // ============================================================
    document.querySelectorAll('.fullscreen-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            var iframe = document.getElementById(this.dataset.target);
            if (!iframe) return;
            var requestFullscreen = iframe.requestFullscreen ||
                iframe.webkitRequestFullscreen ||
                iframe.msRequestFullscreen;
            if (requestFullscreen) requestFullscreen.call(iframe);
        });
    });

    // ============================================================
    // 3. TOGGLE BILINGUE
    // ============================================================
    document.querySelectorAll('.text-bilingue').forEach(function(section) {
        var buttons = section.querySelectorAll('.lingua-btn');
        var contents = section.querySelectorAll('[data-lingua-content]');
        if (!buttons.length || !contents.length) return;
        buttons.forEach(function(button) {
            button.addEventListener('click', function() {
                var lingua = this.dataset.lingua;
                buttons.forEach(function(b) {
                    b.classList.toggle('lingua-btn--active', b === button);
                });
                contents.forEach(function(content) {
                    content.style.display = content.dataset.linguaContent === lingua ? '' : 'none';
                });
            });
        });
    });

    // ============================================================
    // 4. CITAZIONI
    // ============================================================
    document.querySelectorAll('.citazione-link[data-citazioni-id]').forEach(function(toggleButton) {
        var id = toggleButton.dataset.citazioniId;
        var panel = document.getElementById('citazione-pannello-' + id);
        var textarea = document.getElementById('citazione-testo-' + id);
        var copyButton = document.getElementById('citazione-copia-' + id);
        var dataElement = document.getElementById('citazioni-dati-' + id);
        if (!panel || !textarea) return;

        var citations = null;
        if (dataElement) {
            try {
                citations = JSON.parse(dataElement.textContent);
                var tabs = panel.querySelectorAll('.citazione-tab');
                var showFormat = function(format) {
                    textarea.value = citations[format] || '';
                    tabs.forEach(function(tab) {
                        tab.classList.toggle('citazione-tab--active', tab.dataset.formato === format);
                    });
                };
                showFormat('chicago');
                tabs.forEach(function(tab) {
                    tab.addEventListener('click', function() {
                        showFormat(this.dataset.formato);
                    });
                });
            } catch (e) {
                console.warn('Errore citazioni:', e);
            }
        }

        toggleButton.addEventListener('click', function() {
            var isHidden = panel.style.display === 'none' || !panel.style.display;
            panel.style.display = isHidden ? 'block' : 'none';
        });

        if (copyButton) {
            copyButton.addEventListener('click', function() {
                textarea.select();
                var originalText = copyButton.textContent;
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(textarea.value).then(function() {
                        copyButton.textContent = '✅ Copiato!';
                        setTimeout(function() { copyButton.textContent = originalText; }, 1500);
                    }).catch(function() {
                        document.execCommand('copy');
                        copyButton.textContent = '✅ Copiato!';
                        setTimeout(function() { copyButton.textContent = originalText; }, 1500);
                    });
                } else {
                    document.execCommand('copy');
                    copyButton.textContent = '✅ Copiato!';
                    setTimeout(function() { copyButton.textContent = originalText; }, 1500);
                }
            });
        }
    });

});
