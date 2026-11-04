(() => {
    const api = window.electronAPI;
    const titlebar = document.getElementById('electron-titlebar');
    const title = document.getElementById('electron-titlebar-title');

    if (!api?.isElectron || !api.supportsTitleBarOverlay || !titlebar || !title) return;

    document.documentElement.classList.add('electron-shell');
    titlebar.setAttribute('aria-hidden', 'false');

    const atualizarTitulo = () => {
        title.textContent = document.title || 'Gabaritei Questões';
    };

    const converterParaHex = (cor) => {
        const rgb = cor.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
        if (!rgb) return null;
        return `#${rgb.slice(1, 4).map((canal) => Number(canal).toString(16).padStart(2, '0')).join('')}`;
    };

    const atualizarCoresNativas = () => {
        const estilo = window.getComputedStyle(titlebar);
        const fundo = converterParaHex(estilo.backgroundColor);
        const texto = converterParaHex(estilo.color);
        if (fundo && texto) api.setTitleBarColors(fundo, texto);
    };

    atualizarTitulo();
    atualizarCoresNativas();

    const elementoTitulo = document.querySelector('title');
    if (elementoTitulo) {
        new MutationObserver(atualizarTitulo).observe(elementoTitulo, {
            childList: true,
            subtree: true,
            characterData: true,
        });
    }

    new MutationObserver(atualizarCoresNativas).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme'],
    });
})();
