/**
 * feedback_ia.js — Reporte de problemas em respostas geradas pela IA
 * (explicações, resumos e flashcards).
 *
 * O relato é anônimo e chega à triagem humana do painel admin (tabela
 * feedbacks_ia), que pode invalidar o cache para o conteúdo ser regerado.
 * Sem moderação por IA — blocklist local é a primeira barreira no backend.
 */

const MOTIVOS_FEEDBACK_IA = {
    'conteudo_incorreto': 'Conteúdo incorreto',
    'citacao_legal': 'Citação de lei errada ou desatualizada',
    'desatualizado': 'Conteúdo desatualizado',
    'formatacao': 'Problema de formatação',
    'outro': 'Outro'
};

const ROTULOS_TIPO_FEEDBACK_IA = {
    'explicacao': 'explicação',
    'resumo': 'resumo',
    'flashcard': 'flashcard'
};

// Botão 🚩 reutilizável nas superfícies que renderizam conteúdo de IA
function botaoFeedbackIA(idQuestao, tipo, classes) {
    const classe = classes || 'btn btn-link btn-sm text-muted p-0 ms-1';
    const rotulo = ROTULOS_TIPO_FEEDBACK_IA[tipo] || 'resposta';
    return `<button type="button" class="${classe}" onclick="reportarRespostaIA(${idQuestao}, '${tipo}')"
        title="Reportar problema nesta ${rotulo}" aria-label="Reportar problema nesta ${rotulo} da IA">
        <i class="bi bi-flag-fill"></i></button>`;
}

function reportarRespostaIA(idQuestao, tipo) {
    if (!idQuestao) return;
    const rotulo = ROTULOS_TIPO_FEEDBACK_IA[tipo] || 'resposta';

    Swal.fire({
        title: `Reportar problema nesta ${rotulo}`,
        html: `
            <p class="small text-muted mb-3">O relato é anônimo e será analisado pela equipe. Se confirmado, o conteúdo pode ser regerado.</p>
            <select id="feedback-ia-motivo" class="form-select mb-2">
                <option value="">Selecione o motivo...</option>
                ${Object.entries(MOTIVOS_FEEDBACK_IA)
                    .map(([valor, texto]) => `<option value="${valor}">${texto}</option>`)
                    .join('')}
            </select>
            <textarea id="feedback-ia-relato" class="form-control" rows="3" maxlength="1000"
                placeholder="Descreva o problema (opcional)"></textarea>
        `,
        customClass: {
            popup: 'report-form-popup',
            confirmButton: 'report-ia-confirm'
        },
        showCancelButton: true,
        confirmButtonText: 'Enviar reporte',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: 'var(--premium-accent, #0d6efd)',
        preConfirm: () => {
            const motivo = document.getElementById('feedback-ia-motivo').value;
            if (!motivo) {
                Swal.showValidationMessage('Selecione um motivo.');
                return false;
            }
            return {
                motivo: motivo,
                relato: document.getElementById('feedback-ia-relato').value
            };
        }
    }).then((result) => {
        if (!result.isConfirmed) return;
        fetch('/api/feedback_ia', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
            },
            body: JSON.stringify({
                id_questao: idQuestao,
                tipo: tipo,
                motivo: result.value.motivo,
                relato: result.value.relato
            })
        })
            .then(async res => {
                const data = await res.json().catch(() => ({}));
                if (!res.ok || !data.success) {
                    throw new Error(data.error || 'Não foi possível enviar o reporte.');
                }
                return data;
            })
            .then(() => {
                Swal.fire({
                    icon: 'success',
                    title: 'Reporte enviado',
                    text: 'Obrigado! Vamos analisar e corrigir o conteúdo.',
                    timer: 2200,
                    showConfirmButton: false
                });
            })
            .catch(err => {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro ao enviar reporte',
                    text: err.message || 'Erro de conexão ao enviar o reporte.'
                });
            });
    });
}
