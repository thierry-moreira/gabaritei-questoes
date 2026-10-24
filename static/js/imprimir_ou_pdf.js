// ============================================================
// imprimir_ou_pdf.js — padrão unificado de impressão/PDF do Gabaritei.
//
// - App desktop (Electron): electronAPI.printToPDF() gera um PDF nativo
//   (A4, fundos impressos) e abre no leitor padrão do sistema.
// - Navegador: cai no window.print() clássico (preview do Chromium).
//
// Uso em qualquer botão:
//   <button onclick="imprimirOuPDF(this)">Imprimir</button>
// (o argumento é opcional — usado apenas para feedback visual)
// ============================================================
async function imprimirOuPDF(btn) {
    const noDesktop = window.electronAPI && typeof window.electronAPI.printToPDF === 'function';

    // Fallback: navegador comum — preview de impressão nativo do Chromium
    if (!noDesktop) {
        window.print();
        return;
    }

    const textoOriginal = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '⏳ Gerando PDF...';
    }
    try {
        const resultado = await window.electronAPI.printToPDF();
        if (resultado && resultado.ok === false) {
            alert('Erro ao gerar PDF: ' + (resultado.error || 'Desconhecido'));
        }
    } catch (e) {
        alert('Erro inesperado ao gerar PDF: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = textoOriginal;
        }
    }
}
