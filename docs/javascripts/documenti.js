document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.fullscreen-btn').forEach((button) => {
        button.addEventListener('click', () => {
            const iframe = document.getElementById(button.dataset.target);
            if (!iframe) return;
            const requestFullscreen = iframe.requestFullscreen
                || iframe.webkitRequestFullscreen
                || iframe.msRequestFullscreen;
            if (requestFullscreen) requestFullscreen.call(iframe);
        });
    });

    document.querySelectorAll('.text-bilingue').forEach((section) => {
        const buttons = section.querySelectorAll('.lingua-btn');
        const contents = section.querySelectorAll('[data-lingua-content]');
        buttons.forEach((button) => {
            button.addEventListener('click', () => {
                buttons.forEach((item) => item.classList.toggle('lingua-btn--active', item === button));
                contents.forEach((content) => {
                    content.style.display = content.dataset.linguaContent === button.dataset.lingua ? '' : 'none';
                });
            });
        });
    });

    document.querySelectorAll('.citazione-link[data-citazioni-id]').forEach((toggleButton) => {
        const id = toggleButton.dataset.citazioniId;
        const panel = document.getElementById(`citazione-pannello-${id}`);
        const textarea = document.getElementById(`citazione-testo-${id}`);
        const copyButton = document.getElementById(`citazione-copia-${id}`);
        const dataElement = document.getElementById(`citazioni-dati-${id}`);
        if (!panel || !textarea) return;

        let citations = null;
        if (dataElement) {
            try {
                citations = JSON.parse(dataElement.textContent);
                const tabs = panel.querySelectorAll('.citazione-tab');
                const showFormat = (format) => {
                    textarea.value = citations[format] || '';
                    tabs.forEach((tab) => tab.classList.toggle('citazione-tab--active', tab.dataset.formato === format));
                };
                showFormat('chicago');
                tabs.forEach((tab) => tab.addEventListener('click', () => showFormat(tab.dataset.formato)));
            } catch (error) {
                console.warn('Impossibile leggere i dati bibliografici.', error);
            }
        }

        toggleButton.addEventListener('click', () => {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        });

        if (copyButton) {
            copyButton.addEventListener('click', async () => {
                textarea.select();
                const originalLabel = copyButton.textContent;
                try {
                    await navigator.clipboard.writeText(textarea.value);
                } catch (_) {
                    document.execCommand('copy');
                }
                copyButton.textContent = 'Copiato!';
                setTimeout(() => { copyButton.textContent = originalLabel; }, 1500);
            });
        }
    });
});
