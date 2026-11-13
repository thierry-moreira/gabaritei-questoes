/**
 * questoes_common.js
 * Lógica compartilhada para o sistema de questões (IA, Comentários, Tesoura)
 */

// 1. Lógica da IA Explica
function chamarIA(botao) {
    const idQuestao = botao.getAttribute('data-id');
    const idMateria = botao.getAttribute('data-materia'); // Novo: Suporte a matéria
    const container = document.getElementById(`container-ia-${idQuestao}`);
    const divTexto = container.querySelector('.resposta-texto');

    if (!container.classList.contains('d-none')) {
        container.classList.add('d-none');
        return;
    }

    container.classList.remove('d-none');

    if (divTexto.innerHTML.trim() !== "" && !divTexto.innerHTML.includes('text-danger')) {
        return;
    }

    divTexto.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary"></div> <p class="mt-2 small fw-bold text-primary">IA está gerando uma explicação detalhada para você...</p></div>';
    botao.disabled = true;

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    fetch('/api/ia_explica', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            id_questao: idQuestao,
            id_materia: idMateria // Enviando matéria se disponível
        })
    })
        .then(res => res.json().then(d => ({ ok: res.ok, d })))
        .then(({ ok, d }) => {
            if (!ok) {
                // Resposta tratada do back (ex.: IA não configurada — BYOK):
                // exibe o motivo com destaque + atalho p/ Configurações da conta.
                const msg = d.explicacao || d.erro || 'Não foi possível gerar a explicação agora.';
                const btnConfig = msg.includes('não configurada')
                    ? '<a href="/aluno/conta" class="btn btn-sm btn-premium-save mt-2">Configurar minha chave de IA</a>'
                    : '';
                divTexto.innerHTML =
                    '<div class="alert alert-warning rounded-4 text-center py-4 px-3 mb-0">' +
                    '<i class="bi bi-key-fill fs-2 d-block mb-2"></i>' +
                    '<span class="small d-block">' + msg + '</span>' + btnConfig +
                    '</div>';
                return;
            }
            const data = d;
            let explicacaoConvertida = data.explicacao
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&amp;/g, '&');
            if (typeof marked !== 'undefined') {
                let textoLimpo = explicacaoConvertida;
                if (textoLimpo) {
                    // ===========================================================
                    // PADRÃO EXTRACT → PARSE → RESTORE
                    // Protege todos os blocos LaTeX do Marked.js antes de processar.
                    // Isso evita que underscores (_) sejam convertidos em <em> e
                    // que chaves de comandos LaTeX sejam corrompidas pelo Markdown.
                    // ===========================================================
                    const latexBlocks = [];
                    const PLACEHOLDER = (i) => `\x02LATEX_BLOCK_${i}\x03`;

                    const extractLatex = (text) => {
                        // Ordem importa: captura os delimitadores mais longos primeiro
                        return text
                            .replace(/\$\$[\s\S]*?\$\$/g, (match) => {
                                latexBlocks.push(match);
                                return PLACEHOLDER(latexBlocks.length - 1);
                            })
                            .replace(/\\\[[\s\S]*?\\\]/g, (match) => {
                                latexBlocks.push(match);
                                return PLACEHOLDER(latexBlocks.length - 1);
                            })
                            .replace(/\\\([\s\S]*?\\\)/g, (match) => {
                                latexBlocks.push(match);
                                return PLACEHOLDER(latexBlocks.length - 1);
                            })
                            .replace(/\$[^$\n]+?\$/g, (match) => {
                                latexBlocks.push(match);
                                return PLACEHOLDER(latexBlocks.length - 1);
                            });
                    };

                    // PASSO 1: Extrai LaTeX para placeholders (Marked nunca vê o LaTeX)
                    const textoProtegido = extractLatex(textoLimpo);

                    // PASSO 2: Renderiza o Markdown com segurança
                    let htmlRaw = marked.parse(textoProtegido, { breaks: true, gfm: true });

                    // PASSO 3: Restaura os blocos LaTeX no HTML gerado
                    latexBlocks.forEach((block, i) => {
                        htmlRaw = htmlRaw.replace(PLACEHOLDER(i), block);
                    });

                    divTexto.innerHTML = htmlRaw;

                    // Proteção para R$ (Moeda) — evita que o símbolo $ seja capturado pelo KaTeX
                    divTexto.innerHTML = divTexto.innerHTML.replace(/R\$/g, 'R<span>$</span>');

                    // Renderiza as fórmulas LaTeX restauradas
                    if (typeof renderMathInElement !== 'undefined') {
                        renderMathInElement(divTexto, {
                            delimiters: [
                                { left: '$$', right: '$$', display: true },
                                { left: '$', right: '$', display: false },
                                { left: '\\(', right: '\\)', display: false },
                                { left: '\\[', right: '\\]', display: true }
                            ],
                            throwOnError: false
                        });
                    }
                }
            } else {
                divTexto.innerHTML = data.explicacao.replace(/\n/g, '<br>');
            }
        })
        .catch(() => {
            divTexto.innerHTML = '<span class="text-danger">Erro ao conectar com a IA do Gabaritei.</span>';
        })
        .finally(() => {
            botao.disabled = false;
        });
}

// 1.1 Gerar Ponto de Estudo (Resumo ou Flashcard) via IA
function gerarEstudoIA(idQuestao, tipo) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    const titulos = {
        'resumo': 'Gerando Resumo...',
        'flashcard': 'Criando Flashcard...'
    };

    const mensagens = {
        'resumo': 'A IA está extraindo os pontos principais para seu caderno...',
        'flashcard': 'A IA está formulando um card de memorização para você...'
    };

    Swal.fire({
        title: titulos[tipo],
        text: mensagens[tipo],
        allowOutsideClick: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    fetch('/api/ia/gerar_estudo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ id_questao: idQuestao, tipo: tipo })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const isCache = data.cache === true;
                Swal.fire({
                    icon: isCache ? 'info' : 'success',
                    title: isCache ? 'Já está no Caderno!' : (tipo === 'resumo' ? 'Resumo Adicionado!' : 'Flashcard Criado!'),
                    text: data.mensagem || (tipo === 'resumo'
                        ? 'O ponto de revisão foi salvo no seu Caderno de Resumos.'
                        : 'O card foi salvo na categoria da matéria.'),
                    showCancelButton: true,
                    confirmButtonText: tipo === 'resumo' ? 'Ver Caderno' : 'Ver Flashcards',
                    cancelButtonText: 'Continuar Estudando',
                    confirmButtonColor: 'var(--premium-accent)',
                    cancelButtonColor: '#6c757d',
                    reverseButtons: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = tipo === 'resumo' ? '/aluno/resumos' : '/aluno/flashcards';
                    }
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Ocorreu um problema',
                    html: data.error || 'Não foi possível gerar o conteúdo agora.'
                });
            }
        })
        .catch(err => {
            Swal.fire({
                icon: 'error',
                title: 'Erro de Conexão',
                text: 'Verifique sua internet ou tente novamente mais tarde.'
            });
        });
}

// 2. Lógica de Comentários
/**
 * Monta um card de comentário usando apenas APIs de texto do DOM.
 *
 * F-11: nome_usuario e texto_comentario são conteúdo de usuário. Eles NUNCA
 * podem ser interpolados em template literals entregues a innerHTML — um
 * payload como <img src=x onerror=...> executaria no mesmo-origin. textContent
 * e createTextNode tratam o valor como texto literal.
 */
function montarCardComentario(comentario, podeDenunciar) {
    const card = document.createElement('div');
    card.className = 'mb-2 p-2 bg-white rounded border shadow-sm text-dark';

    const cabecalho = document.createElement('div');
    cabecalho.className = 'd-flex justify-content-between align-items-center mb-1';

    const nome = document.createElement('strong');
    nome.className = 'small text-primary';
    const iconePessoa = document.createElement('i');
    iconePessoa.className = 'bi bi-person-circle';
    nome.appendChild(iconePessoa);
    nome.appendChild(document.createTextNode(` ${comentario.nome_usuario || 'Aluno'}`));

    const meta = document.createElement('span');
    meta.className = 'd-flex align-items-center';

    const data = document.createElement('small');
    data.className = 'text-muted';
    data.style.fontSize = '0.75rem';
    data.textContent = comentario.criado_em
        ? new Date(comentario.criado_em).toLocaleDateString('pt-BR')
        : '';
    meta.appendChild(data);

    if (podeDenunciar && comentario.id_comentario) {
        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'btn btn-link btn-sm text-muted p-0 ms-1 btn-reportar-comentario';
        botao.dataset.comentarioId = String(comentario.id_comentario);
        botao.title = 'Denunciar comentário';
        botao.setAttribute('aria-label', 'Denunciar comentário');
        const iconeDenuncia = document.createElement('i');
        iconeDenuncia.className = 'bi bi-flag-fill';
        botao.appendChild(iconeDenuncia);
        meta.appendChild(botao);
    }

    cabecalho.appendChild(nome);
    cabecalho.appendChild(meta);

    const texto = document.createElement('p');
    texto.className = 'mb-0 small';
    texto.textContent = comentario.texto_comentario || comentario.texto || '';

    card.appendChild(cabecalho);
    card.appendChild(texto);
    return card;
}

function carregarComentarios(idQuestao, pagina = 1, anexar = false) {
    const divLista = document.getElementById(`lista-comentarios-${idQuestao}`);
    if (!divLista) return;

    const botaoAnterior = divLista.querySelector('.btn-carregar-mais-comentarios');
    if (anexar && botaoAnterior) {
        botaoAnterior.disabled = true;
        botaoAnterior.textContent = 'Carregando...';
    } else if (!anexar) {
        divLista.innerHTML = '<div class="text-center small text-muted my-2"><div class="spinner-border spinner-border-sm text-primary"></div> Carregando comentários...</div>';
    }

    fetch(`/api/comentarios/${encodeURIComponent(idQuestao)}?page=${pagina}`)
        .then(res => {
            if (!res.ok) throw new Error('Falha ao carregar comentários.');
            return res.json();
        })
        .then(data => {
            const listaComentarios = Array.isArray(data) ? data : (data.comentarios || []);
            const temMais = !Array.isArray(data) && Boolean(data.tem_mais);
            if (botaoAnterior) botaoAnterior.remove();
            if (!anexar) divLista.textContent = '';

            if (listaComentarios.length === 0 && !anexar) {
                const vazio = document.createElement('p');
                vazio.className = 'small text-muted mb-0 text-center';
                vazio.textContent = 'Nenhum comentário ainda. Seja o primeiro!';
                divLista.appendChild(vazio);
                return;
            }

            const podeDenunciar = window.GABARITEI_AUTH && window.GABARITEI_AUTH.isAuthenticated;
            const fragmento = document.createDocumentFragment();
            listaComentarios.forEach(comentario => {
                fragmento.appendChild(montarCardComentario(comentario, podeDenunciar));
            });
            divLista.appendChild(fragmento);

            if (temMais) {
                const botaoMais = document.createElement('button');
                botaoMais.type = 'button';
                botaoMais.className = 'btn btn-link btn-sm d-block mx-auto btn-carregar-mais-comentarios';
                botaoMais.textContent = 'Carregar comentários anteriores';
                botaoMais.addEventListener('click', () => {
                    carregarComentarios(idQuestao, pagina + 1, true);
                });
                divLista.appendChild(botaoMais);
            }

        })
        .catch(() => {
            if (anexar && botaoAnterior) {
                botaoAnterior.disabled = false;
                botaoAnterior.textContent = 'Carregar comentários anteriores';
                return;
            }
            divLista.innerHTML = '<span class="text-danger small">Erro ao carregar comentários.</span>';
        });
}

// 3. Função para expandir/minimizar texto de apoio
function toggleTextoBtn(id) {
    setTimeout(() => {
        const el = document.getElementById(`txt${id}`);
        const btnText = document.getElementById(`text-btn-${id}`);
        const btnIcon = document.getElementById(`icon-btn-${id}`);

        if (el && el.classList.contains('show')) {
            btnText.innerText = 'Minimizar';
            btnIcon.classList.replace('bi-chevron-down', 'bi-chevron-up');
        } else if (el) {
            btnText.innerText = 'Expandir';
            btnIcon.classList.replace('bi-chevron-up', 'bi-chevron-down');
        }
    }, 350);
}

// 4. Inicialização global (Tesoura e Listeners)
function initQuestoes() {
    // Tesoura de Eliminação
    document.addEventListener('click', function (e) {
        if (e.target.closest('.btn-tesoura')) {
            const btn = e.target.closest('.btn-tesoura');
            e.preventDefault();
            e.stopPropagation();
            const alternativaCaixa = btn.closest('.item-alternativa');
            alternativaCaixa.classList.toggle('alternativa-eliminada');

            if (alternativaCaixa.classList.contains('alternativa-eliminada')) {
                btn.classList.replace('text-secondary', 'text-danger');
            } else {
                btn.classList.replace('text-danger', 'text-secondary');
            }
        }
    });

    // Destaque visual ao selecionar uma alternativa
    document.addEventListener('change', function (e) {
        if (e.target.matches('input[type="radio"]')) {
            const container = e.target.closest('.item-alternativa');
            if (container) {
                const group = container.closest('.alternatives-group');
                if (group) {
                    group.querySelectorAll('.item-alternativa').forEach(el => {
                        el.classList.remove('selected');
                    });
                    container.classList.add('selected');
                }
            }
        }
    });

    // Listener para carregar comentários ao expandir o collapse
    document.querySelectorAll('.collapse[id^="comentarios-"]').forEach(collapseEl => {
        collapseEl.addEventListener('show.bs.collapse', function () {
            const idQuestao = this.id.replace('comentarios-', '');
            carregarComentarios(idQuestao);
        });
    });

    // Denunciar comentário (🚩) — moderação humana: a denúncia chega ao painel
    // do admin (tabela reports_comentarios). Sem moderação por IA.
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-reportar-comentario');
        if (!btn) return;
        e.preventDefault();

        const idComentario = btn.getAttribute('data-comentario-id');
        Swal.fire({
            title: 'Denunciar comentário',
            text: 'Ajude a manter a comunidade respeitosa. A denúncia será registrada para análise.',
            customClass: {
                popup: 'report-form-popup'
            },
            input: 'select',
            inputOptions: {
                'Conteúdo ofensivo ou desrespeitoso': 'Conteúdo ofensivo ou desrespeitoso',
                'Discurso de ódio ou assédio': 'Discurso de ódio ou assédio',
                'Spam ou propaganda': 'Spam ou propaganda',
                'Informação ilegal ou perigosa': 'Informação ilegal ou perigosa',
                'Outro motivo': 'Outro motivo'
            },
            inputPlaceholder: 'Selecione o motivo',
            showCancelButton: true,
            confirmButtonText: 'Denunciar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545',
            preConfirm: (motivo) => {
                if (!motivo) Swal.showValidationMessage('Selecione um motivo.');
                return motivo;
            }
        }).then((result) => {
            if (!result.isConfirmed) return;
            fetch(`/api/comentarios/${idComentario}/reportar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
                },
                body: JSON.stringify({ motivo: result.value })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Denúncia enviada',
                            text: 'Obrigado por manter a comunidade respeitosa!',
                            timer: 2200,
                            showConfirmButton: false
                        });
                    } else {
                        Swal.fire({ icon: 'warning', title: 'Atenção', text: data.error || 'Não foi possível enviar a denúncia.' });
                    }
                })
                .catch(() => Swal.fire({ icon: 'error', title: 'Erro', text: 'Erro de conexão ao denunciar.' }));
        });
    });

    // Enviar comentário
    document.querySelectorAll('.form-enviar-comentario').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const idQuestao = this.getAttribute('data-questao-id');
            const inputTexto = this.querySelector('input[name="texto_comentario"]');
            const btnSubmit = this.querySelector('button[type="submit"]');
            const texto = inputTexto.value.trim();

            if (!texto) return;

            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

            fetch('/api/comentarios', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
                },
                body: JSON.stringify({ id_questao: idQuestao, texto: texto })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        inputTexto.value = '';
                        btnSubmit.innerHTML = '<i class="bi bi-check"></i> Enviado';
                        btnSubmit.classList.add('btn-success');
                        const badgeCounter = document.getElementById(`contador-comentarios-${idQuestao}`);
                        if (badgeCounter) {
                            const total = Number.parseInt(badgeCounter.textContent, 10);
                            badgeCounter.textContent = String((Number.isFinite(total) ? total : 0) + 1);
                        }
                        carregarComentarios(idQuestao);
                        setTimeout(() => {
                            btnSubmit.innerHTML = 'Enviar';
                            btnSubmit.classList.remove('btn-success');
                            btnSubmit.disabled = false;
                        }, 2000);
                    } else {
                        alert('Erro ao enviar: ' + (data.error || 'Tente novamente.'));
                        btnSubmit.disabled = false;
                        btnSubmit.innerHTML = 'Enviar';
                    }
                })
                .catch(() => {
                    alert("Erro ao enviar comentário.");
                    btnSubmit.disabled = false;
                    btnSubmit.innerHTML = 'Enviar';
                });
        });
    });
    // Responder questão
    document.querySelectorAll('.form-resposta').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = form.querySelector('button[type="submit"]');
            const formData = new FormData(form);
            const questaoId = formData.get('questao_id');
            const alternativaSelecionada = formData.get('res');

            if (!alternativaSelecionada) return;

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Analisando...';

            const endpoint = '/aluno/responder';

            fetch(endpoint, {
                method: 'POST',
                body: JSON.stringify({ questao_id: questaoId, alternativa: alternativaSelecionada }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
                }
            })
                .then(res => res.json())
                .then(data => {
                    const sucesso = data.sucesso || data.success;
                    const isCorrect = data.correta || data.is_correct;

                    if (sucesso) {
                        const containers = form.querySelectorAll('.alternative-container');
                        containers.forEach(container => {
                            const input = container.querySelector('input');
                            const tesoura = container.querySelector('.btn-tesoura');

                            container.classList.remove('alternativa-eliminada');
                            container.classList.remove('eliminated'); // Compatibilidade

                            if (tesoura) tesoura.style.display = 'none';

                            if (input.value === data.letra_correta) {
                                container.classList.add('alternative-correct');
                            }
                            if (input.value === alternativaSelecionada && !isCorrect) {
                                container.classList.add('alternative-wrong');
                            }
                            input.disabled = true;
                        });

                        const feedbackDiv = document.createElement('div');
                        feedbackDiv.className = `alert mt-4 shadow-sm border-0 animate__animated animate__fadeIn ${isCorrect ? 'alert-success' : 'alert-danger'}`;
                        feedbackDiv.innerHTML = `
                        <div class="d-flex align-items-center">
                            <i class="bi ${isCorrect ? 'bi-check-circle-fill' : 'bi-x-circle-fill'} fs-4 me-2"></i>
                            <h6 class="fw-bold mb-0">${isCorrect ? 'Parabéns, você acertou!' : 'Resposta incorreta.'}</h6>
                        </div>
                        <hr class="my-2">
                        <p class="mb-0 small">A alternativa correta é a <strong>${data.letra_correta}</strong>.</p>
                    `;
                        form.appendChild(feedbackDiv);
                        btn.remove();

                        // Atualizar o badge de status na header do card
                        const cardBody = form.closest('.card-body');
                        if (cardBody) {
                            const headerBadges = cardBody.querySelector('.d-flex.flex-wrap.align-items-center.gap-2');
                            if (headerBadges) {
                                // Remove old to prevent duplicates
                                const oldBadges = headerBadges.querySelectorAll('.badge.bg-success, .badge.bg-danger');
                                oldBadges.forEach(b => {
                                    if (b.querySelector('.bi-check-circle-fill') || b.querySelector('.bi-x-circle-fill')) {
                                        b.remove();
                                    }
                                });

                                const statusBadge = document.createElement('span');
                                statusBadge.className = `badge ${isCorrect ? 'bg-success' : 'bg-danger'} ms-1 shadow-sm animate__animated animate__zoomIn`;
                                statusBadge.title = isCorrect ? "Você acertou esta questão" : "Você errou esta questão";
                                statusBadge.innerHTML = `<i class="bi ${isCorrect ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}"></i>`;
                                
                                // Insert after the first span (the ID badge)
                                const firstBadge = headerBadges.querySelector('span.badge');
                                if (firstBadge && firstBadge.nextSibling) {
                                    headerBadges.insertBefore(statusBadge, firstBadge.nextSibling);
                                } else {
                                    headerBadges.appendChild(statusBadge);
                                }
                            }
                        }
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Resposta não registrada',
                            html: data.error || 'Não foi possível registrar sua resposta. Tente novamente.',
                            confirmButtonColor: 'var(--premium-accent)',
                            confirmButtonText: 'Fechar'
                        });
                        btn.disabled = false;
                        btn.innerHTML = '<i class="bi bi-check2-circle me-2"></i> Responder';
                    }
                })
                .catch(err => {
                    console.error("Erro na resposta:", err);
                    btn.disabled = false;
                    btn.innerHTML = 'FALHA AO ENVIAR';
                });
        });
    });

    // Submissão de Feedback (Reportar Erro)
    const formFeedback = document.getElementById('form-feedback');
    if (formFeedback) {
        formFeedback.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = document.getElementById('btn-enviar-feedback');
            const idQuestao = document.getElementById('feedback-questao-id').value;
            const tipoErro = document.getElementById('feedback-tipo').value;
            const descricao = document.getElementById('feedback-descricao').value;

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...';

            fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
                },
                body: JSON.stringify({
                    id_questao: idQuestao,
                    tipo_erro: tipoErro,
                    descricao: descricao
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
                    const modalEl = document.getElementById('modalFeedback');
                    const modalInstance = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;
                    if (modalInstance) modalInstance.hide();
                    Swal.fire({
                        icon: 'success',
                        title: 'Reporte enviado',
                        text: 'Muito obrigado! Seu reporte foi enviado para análise.',
                        timer: 2200,
                        showConfirmButton: false
                    });
                })
                .catch(err => {
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro ao enviar reporte',
                        text: err.message || 'Erro na conexão ao enviar reporte.'
                    });
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.innerHTML = 'Enviar Reporte <i class="bi bi-send ms-1"></i>';
                });
        });
    }
}

// 5. Lógica de Modais (Feedback e Cadernos)
window.prepararFeedback = function (idQuestao) {
    const hiddenId = document.getElementById('feedback-questao-id');
    const form = document.getElementById('form-feedback');
    if (hiddenId) hiddenId.value = idQuestao;
    if (form) form.reset();
};

window.prepararCaderno = function (idQuestao) {
    const hiddenId = document.getElementById('salvar-questao-id');
    if (hiddenId) hiddenId.value = idQuestao;
    carregarListaCadernos();
};

function carregarListaCadernos() {
    const lista = document.getElementById('lista-meus-cadernos');
    if (!lista) return;

    fetch('/api/cadernos')
        .then(res => res.json())
        .then(cadernos => {
            lista.innerHTML = '';
            if (cadernos.length === 0) {
                lista.innerHTML = '<div class="p-4 text-center text-muted small">Você ainda não tem cadernos salvos.</div>';
                return;
            }
            cadernos.forEach(c => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center py-3';
                btn.innerHTML = `
                <span class="fw-bold text-dark text-truncate me-2">${c.nome_caderno}</span>
                <i class="bi bi-plus-circle-fill text-success fs-5"></i>
            `;
                btn.onclick = () => confirmarSalvar(c.id_caderno);
                lista.appendChild(btn);
            });
        })
        .catch(err => {
            lista.innerHTML = '<div class="p-4 text-center text-danger small">Erro ao carregar cadernos.</div>';
        });
}

function criarNovoCaderno() {
    const input = document.getElementById('novo-caderno-nome');
    const nome = input ? input.value : '';
    if (!nome) return alert("Digite um nome para o caderno!");

    fetch('/api/cadernos/novo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
        },
        body: JSON.stringify({ nome: nome })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (input) input.value = '';
                carregarListaCadernos();
            } else {
                Swal.fire({
                    icon: 'warning',
                    title: 'Limite Atingido',
                    text: data.error || "Erro ao criar caderno.",
                    confirmButtonColor: 'var(--premium-accent)'
                });
            }
        })
        .catch(err => {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: "Erro de conexão ao criar caderno."
            });
        });
}

function confirmarSalvar(idCaderno) {
    const idQuestaoEl = document.getElementById('salvar-questao-id');
    const idQuestao = idQuestaoEl ? idQuestaoEl.value : null;
    if (!idQuestao) return;

    fetch('/api/cadernos/salvar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
        },
        body: JSON.stringify({ id_caderno: idCaderno, id_questao: idQuestao })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert("Questão salva com sucesso!");
                const modalEl = document.getElementById('modalCadernos');
                const modalInstance = bootstrap.Modal.getInstance(modalEl);
                if (modalInstance) modalInstance.hide();
            } else {
                alert(data.error || "Erro ao salvar questão.");
            }
        })
        .catch(err => alert("Erro de conexão ao salvar no caderno."));
}

// 6. Lógica de Filtros (Busca em Tempo Real, Cascata e Gerenciamento)
window.initFilterSearch = function () {
    document.querySelectorAll('.filter-search').forEach(input => {
        input.addEventListener('input', function () {
            const termo = this.value.toLowerCase();
            const targetId = this.getAttribute('data-target');
            const container = document.getElementById(targetId);
            if (!container) return;

            const itens = container.querySelectorAll('.item-filtro');
            itens.forEach(item => {
                const texto = item.textContent.toLowerCase();
                item.style.display = texto.includes(termo) ? 'block' : 'none';
            });
        });
    });
};

window.initFilterCascades = function () {
    // A. Cascata de Matérias -> Assuntos
    const checksMateria = document.querySelectorAll('.check-materia');
    const containerAssuntos = document.getElementById('list-assuntos');

    if (checksMateria.length > 0 && containerAssuntos) {
        function carregarAssuntos() {
            const selecionadas = Array.from(document.querySelectorAll('.check-materia:checked')).map(c => c.value);
            if (selecionadas.length === 0) {
                containerAssuntos.innerHTML = '<p class="text-muted small text-center my-4">Marque uma ou mais matérias para carregar os assuntos...</p>';
                return;
            }

            containerAssuntos.innerHTML = '<div class="text-center my-4 small"><div class="spinner-border spinner-border-sm text-primary"></div> <span class="text-muted">Carregando assuntos...</span></div>';

            fetch('/api/get_assuntos_cascata', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids_materias: selecionadas })
            })
                .then(res => res.json())
                .then(data => {
                    // Ordenar tópicos em ordem alfabética
                    data.sort((a, b) => a.nome.localeCompare(b.nome));
                    
                    let html = '';
                    data.forEach(topico => {
                        // Ordenar subtopicos em ordem alfabética
                        if (topico.subtopicos) {
                            topico.subtopicos.sort((a, b) => a.nome.localeCompare(b.nome));
                        }
                        html += `
                    <div class="item-filtro mb-2 border-bottom pb-1">
                        <div class="form-check">
                            <input class="form-check-input check-pai" type="checkbox" name="id_topico" value="${topico.id}" id="t${topico.id}">
                            <label class="form-check-label fw-bold small" for="t${topico.id}">${topico.nome}</label>
                        </div>
                        <div class="ms-3 mt-1 border-start ps-2">
                            ${topico.subtopicos.map(sub => `
                                <div class="form-check">
                                    <input class="form-check-input check-filho" type="checkbox" name="id_subtopico" value="${sub.id}" id="s${sub.id}" data-pai="${topico.id}">
                                    <label class="form-check-label small text-muted" for="s${sub.id}">${sub.nome}</label>
                                </div>
                            `).join('')}
                        </div>
                    </div>`;
                    });
                    containerAssuntos.innerHTML = html || '<p class="text-muted small text-center my-4">Nenhum assunto encontrado.</p>';

                    // Listener para selecionar filhos automaticamente
                    containerAssuntos.querySelectorAll('.check-pai').forEach(p => {
                        p.addEventListener('change', function () {
                            containerAssuntos.querySelectorAll(`.check-filho[data-pai="${this.value}"]`).forEach(f => f.checked = this.checked);
                        });
                    });
                })
                .catch(err => {
                    containerAssuntos.innerHTML = '<p class="text-danger small text-center my-4">Erro ao carregar assuntos.</p>';
                });
        }

        checksMateria.forEach(c => c.addEventListener('change', carregarAssuntos));
        // Disparar inicial se houver algo marcado
        if (document.querySelectorAll('.check-materia:checked').length > 0) carregarAssuntos();
    }

    // B. Cascata de Órgão -> Cargo
    document.querySelectorAll('.check-orgao-pai').forEach(pai => {
        pai.addEventListener('change', function () {
            document.querySelectorAll(`.check-cargo-filho[data-pai="${this.value}"]`).forEach(f => f.checked = this.checked);
        });
    });

    // C. Modal Salvar Filtro (Popula o hidden intent)
    const modalSalvarFiltro = document.getElementById('modalSalvarFiltro');
    if (modalSalvarFiltro) {
        modalSalvarFiltro.addEventListener('show.bs.modal', function () {
            const form = document.getElementById('formFiltros');
            const hiddenInput = document.getElementById('hiddenUrlParams');
            if (form && hiddenInput) {
                const formData = new FormData(form);
                const queryString = new URLSearchParams(formData).toString();
                hiddenInput.value = queryString;
            }
        });
    }
};

window.deletarFiltro = function (idFiltro) {
    confirmarAcao({
        tipo: 'danger',
        title: 'Excluir filtro?',
        text: 'Tem certeza que deseja excluir este filtro?',
        confirmButtonText: 'Sim, excluir'
    }).then((result) => {
        if (!result.isConfirmed) return;
        fetch(`/aluno/excluir_filtro/${idFiltro}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
            }
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "sucesso") {
                    window.location.reload();
                } else {
                    alert("Erro ao excluir filtro.");
                }
            })
            .catch(() => alert("Erro na conexão ao excluir filtro."));
    });
};

// Exposto para testes unitários (no navegador, declarações de função já são
// propriedades de window; no CommonJS do Jest isso precisa ser explícito).
window.carregarComentarios = carregarComentarios;

// Chamar init ao carregar
document.addEventListener('DOMContentLoaded', () => {
    initQuestoes();
    initFilterSearch();
    // initFilterCascades() deve ser chamado na página que contém os filtros
});
