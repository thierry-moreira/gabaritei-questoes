/**
 * Gerenciamento do Ciclo de Estudos por Edital
 * Lógica para resposta de questões, integração com IA e report de erros.
 */

document.addEventListener("DOMContentLoaded", function() {
    // Busca o ID do edital e o CSRF Token dos atributos de dados do formulário
    const formQuestao = document.getElementById('formQuestao');
    if (!formQuestao) return;

    const idEdital = formQuestao.dataset.idEdital;
    const csrfToken = formQuestao.dataset.csrfToken;

    // --- LÓGICA DE RESPOSTA DO EDITAL ---
    const btnResponder = document.getElementById('btnResponder');
    if (btnResponder) {
        btnResponder.addEventListener('click', async function() {
            const radio = document.querySelector('input[name="res"]:checked');
            if (!radio) { 
                alert("⚠️ Selecione uma alternativa!"); 
                return; 
            }

            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Analisando...';

            const dados = {
                id_edital: parseInt(idEdital),
                id_questao: formQuestao.querySelector('input[name="id_questao"]').value,
                alternativa: radio.value
            };

            try {
                const response = await fetch('/aluno/editais/responder', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(dados)
                });
                const res = await response.json();

                if (res.sucesso) {
                    this.classList.add('d-none');
                    
                    // Marca as alternativas (Usa as classes extraídas para o CSS global)
                    document.querySelectorAll('.item-alternativa').forEach(container => {
                        const inp = container.querySelector('input');
                        if (inp) {
                            inp.disabled = true;
                            if (inp.value === res.letra_correta) container.classList.add('alternative-correct');
                            if (inp.value === radio.value && !res.correta) container.classList.add('alternative-wrong');
                        }
                    });

                    const feed = document.getElementById('feedback-resposta');
                    const tit = document.getElementById('feedback-titulo');
                    feed.classList.remove('d-none');
                    
                    if (res.correta) {
                        tit.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i> Excelente! Você acertou.';
                        feed.className = 'mt-4 p-4 rounded-4 border border-success bg-success bg-opacity-10';
                    } else {
                        tit.innerHTML = `<i class="bi bi-x-circle-fill text-danger"></i> Você errou. A correta era a ${res.letra_correta}.`;
                        feed.className = 'mt-4 p-4 rounded-4 border border-danger bg-danger bg-opacity-10';
                    }
                }
            } catch (e) { 
                console.error("Erro ao responder:", e);
                alert("Erro de conexão."); 
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Responder e Avançar';
            }
        });
    }

    const btnProx = document.getElementById('btnProximaQuestao');
    if (btnProx) btnProx.addEventListener('click', () => location.reload());

    // --- FUNÇÃO REPORTAR ---
    const formFeedback = document.getElementById('form-feedback');
    if (formFeedback) {
        formFeedback.addEventListener('submit', function(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-enviar-feedback');
            btn.disabled = true;

            const idQuestao = document.getElementById('feedback-questao-id').value;
            const tipoErro = document.getElementById('feedback-tipo').value;
            const descricao = document.getElementById('feedback-descricao').value;

            fetch('/api/feedback', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    id_questao: idQuestao,
                    tipo_erro: tipoErro,
                    descricao: descricao
                })
            }).then(() => {
                alert('Reporte enviado!');
                const modalEl = document.getElementById('modalFeedback');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }).catch(err => {
                console.error("Erro ao enviar feedback:", err);
                alert("Erro ao enviar reporte.");
            }).finally(() => btn.disabled = false);
        });
    }
});

/**
 * Função global chamada pelo botão "IA Explica"
 * @param {HTMLElement} btn 
 */
async function chamarIA(btn) {
    const questaoId = btn.getAttribute('data-id');
    const container = document.getElementById(`container-ia-${questaoId}`);
    const resultDiv = container.querySelector('.resposta-texto');
    
    // O formulário contém o CSRF Token centralizado
    const formQuestao = document.getElementById('formQuestao');
    const csrfToken = formQuestao ? formQuestao.dataset.csrfToken : '';

    if (!container.classList.contains('d-none')) {
        container.classList.add('d-none');
        return;
    }

    container.classList.remove('d-none');
    
    // Se já tem conteúdo (e não é o spinner), não precisa carregar de novo
    if (resultDiv.innerHTML !== "" && !resultDiv.querySelector('.spinner-border')) {
        return;
    }

    resultDiv.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 fw-bold text-primary">IA está gerando uma explicação detalhada para você...</p></div>';

    try {
        const response = await fetch('/api/ia_explica', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                id_questao: questaoId,
                id_materia: btn.getAttribute('data-materia')
            })
        });

        const data = await response.json();
        if (data.explicacao) {
            // Assume que 'marked' está disponível globalmente via CDN
            if (window.marked) {
                resultDiv.innerHTML = marked.parse(data.explicacao);
            } else {
                resultDiv.innerHTML = data.explicacao.replace(/\n/g, '<br>');
            }
        } else {
            resultDiv.innerHTML = `<p class="text-danger">${data.erro || 'Não foi possível gerar a explicação agora.'}</p>`;
        }
    } catch (error) {
        console.error("Erro na IA:", error);
        resultDiv.innerHTML = '<p class="text-danger">Erro ao conectar com a IA.</p>';
    }
}

/**
 * Função global chamada pelo botão Reportar para preencher o ID no modal
 * @param {string|number} id 
 */
window.prepararFeedback = function(id) {
    const inputId = document.getElementById('feedback-questao-id');
    const form = document.getElementById('form-feedback');
    if (inputId) inputId.value = id;
    if (form) form.reset();
};
