/**
 * edital_premium.js
 * Lógica original recuperada e adaptada para o Gerador de Ciclos do Edital
 */

async function carregarTopicosEdital(selectElement) {
    const row = selectElement.closest('.bloco-materia-premium');
    const btnTopicos = row.querySelector('.btn-topicos');
    const menuTopicos = row.querySelector('.menu-topicos');
    const hiddenTopicos = row.querySelector('.hidden-topicos');
    const idMateria = selectElement.value;

    hiddenTopicos.value = '';
    btnTopicos.textContent = 'Carregando...';
    btnTopicos.disabled = true;
    menuTopicos.innerHTML = '<li><span class="text-muted small px-3"><i class="bi bi-hourglass-split"></i> Buscando...</span></li>';

    if (!idMateria) return;

    try {
        const response = await fetch(`/api/topicos/${idMateria}`);
        const topicos = await response.json();

        // Ordenar tópicos em ordem alfabética
        topicos.sort((a, b) => a.nome_topico.localeCompare(b.nome_topico));

        menuTopicos.innerHTML = '';


        if (topicos.length === 0) {
            btnTopicos.textContent = 'Sem Assuntos';
            menuTopicos.innerHTML = '<li><span class="text-muted small px-3">Nenhum assunto cadastrado.</span></li>';
            return;
        }

        btnTopicos.textContent = 'Selecionar Assuntos';
        btnTopicos.disabled = false;

        // Adiciona a opção "Selecionar Todos" (Recuperado do original)
        const idMaster = `todos_${Math.random().toString(36).substr(2, 5)}`;
        menuTopicos.innerHTML = `
            <li class="px-2 py-1 border-bottom" style="border-color: rgba(255,255,255,0.1); background: rgba(99, 102, 241, 0.05);">
                <div class="form-check item-filtro" style="cursor: pointer; padding: 8px 12px; border-radius: 8px;">
                    <input class="form-check-input check-todos-edital" type="checkbox" id="${idMaster}">
                    <label class="form-check-label small fw-bold text-primary w-100 cursor-pointer" for="${idMaster}">Marcar Todo o Edital</label>
                </div>
            </li>
        `;

        topicos.forEach(t => {
            const uniqueId = `ed_${t.id_topico}_${Math.random().toString(36).substr(2, 5)}`;
            const li = document.createElement('li');
            li.className = 'px-2 py-1 border-bottom';
            li.style.borderColor = 'rgba(255,255,255,0.05)';
            li.innerHTML = `
                <div class="form-check item-filtro" style="cursor: pointer; padding: 8px 12px; border-radius: 8px;">
                    <input class="form-check-input check-topico-edital" type="checkbox" value="${t.id_topico}" id="${uniqueId}">
                    <label class="form-check-label small w-100 cursor-pointer d-block text-muted" title="${t.nome_topico}" for="${uniqueId}">${t.nome_topico}</label>
                </div>
            `;
            menuTopicos.appendChild(li);
        });

        // Lógica dos Checkboxes
        const checkboxes = menuTopicos.querySelectorAll('.check-topico-edital');
        const checkTodos = menuTopicos.querySelector('.check-todos-edital');

        checkTodos.addEventListener('change', function () {
            checkboxes.forEach(c => c.checked = this.checked);
            atualizarHiddenBtn(checkboxes, hiddenTopicos, btnTopicos);
        });

        checkboxes.forEach(chk => {
            chk.addEventListener('change', () => {
                atualizarHiddenBtn(checkboxes, hiddenTopicos, btnTopicos);
                checkTodos.checked = Array.from(checkboxes).every(c => c.checked);
            });
        });

    } catch (error) {
        console.error('Erro ao carregar tópicos do edital:', error);
        btnTopicos.textContent = 'Erro ao carregar';
    }
}

function atualizarHiddenBtn(checkboxes, hiddenInput, btn) {
    const selecionados = Array.from(checkboxes).filter(c => c.checked).map(c => c.value);
    hiddenInput.value = selecionados.join(',');

    if (selecionados.length === 0) {
        btn.textContent = 'Selecionar Assuntos';
    } else if (selecionados.length === checkboxes.length) {
        btn.textContent = 'Todo o Edital';
    } else if (selecionados.length === 1) {
        btn.textContent = '1 assunto selecionado';
    } else {
        btn.textContent = `${selecionados.length} assuntos selecionados`;
    }
}

function adicionarMateriaEdital() {
    const container = document.getElementById('container-materias');
    const blocos = container.querySelectorAll('.bloco-materia-premium');
    const novoBloco = blocos[0].cloneNode(true);

    // Limpa os valores do novo bloco (modo adaptativo: sem campos manuais de quantidade)
    novoBloco.querySelector('.select-materia').value = '';
    novoBloco.querySelector('.hidden-topicos').value = '';

    const btnTopicos = novoBloco.querySelector('.btn-topicos');
    btnTopicos.innerHTML = 'Selecione a matéria';
    btnTopicos.disabled = true;
    novoBloco.querySelector('.menu-topicos').innerHTML = '<li><span class="text-muted small px-3">Aguardando matéria...</span></li>';

    novoBloco.querySelector('.btn-remover').disabled = false;

    // Animação suave (Fade In)
    novoBloco.style.opacity = '0';
    container.appendChild(novoBloco);
    setTimeout(() => novoBloco.style.opacity = '1', 10);

    atualizarBotoesRemoverEdital();
}

function removerMateriaEdital(botao) {
    const container = document.getElementById('container-materias');
    const blocos = container.querySelectorAll('.bloco-materia-premium');
    if (blocos.length > 1) {
        botao.closest('.bloco-materia-premium').remove();
        atualizarBotoesRemoverEdital();
    }
}

function atualizarBotoesRemoverEdital() {
    const blocos = document.querySelectorAll('.bloco-materia-premium');
    blocos.forEach(b => {
        const btnRemover = b.querySelector('.btn-remover');
        if (btnRemover) {
            btnRemover.disabled = (blocos.length === 1);
        }
    });
}
