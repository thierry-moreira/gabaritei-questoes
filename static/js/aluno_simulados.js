/**
 * Gerenciador de Simulados do Aluno
 * Lógica para filtros avançados e geração dinâmica de blocos de matéria/assunto
 */

document.addEventListener('DOMContentLoaded', function() {
    // Lógica para selecionar todos os cargos de um órgão pai (Filtros Avançados)
    document.body.addEventListener('change', function(e) {
        if (e.target.classList.contains('check-orgao-pai-sim')) {
            const paiValue = e.target.value;
            const isChecked = e.target.checked;
            document.querySelectorAll(`.check-cargo-filho-sim[data-pai="${paiValue}"]`).forEach(filho => {
                filho.checked = isChecked;
            });
        }
    });
});

/**
 * Busca tópicos/assuntos via API quando uma matéria é selecionada no modal
 */
async function carregarTopicosSimulado(selectElement) {
    const row = selectElement.closest('.bloco-materia');
    const btnTopicos = row.querySelector('.btn-topicos');
    const menuTopicos = row.querySelector('.menu-topicos');
    const hiddenTopicos = row.querySelector('.hidden-topicos');
    const idMateria = selectElement.value;

    hiddenTopicos.value = '';
    btnTopicos.textContent = 'Carregando...';
    btnTopicos.disabled = true;
    menuTopicos.innerHTML = '<li><span class="text-muted small px-2"><i class="bi bi-hourglass-split"></i> Buscando...</span></li>';

    if (!idMateria) {
        btnTopicos.textContent = 'Todos os assuntos';
        menuTopicos.innerHTML = '<li><span class="text-muted small px-2">Selecione uma matéria para filtrar assuntos.</span></li>';
        btnTopicos.disabled = true;
        return;
    }

    try {
        const response = await fetch(`/api/topicos/${idMateria}`);
        const topicos = await response.json();
        
        // Ordenar tópicos em ordem alfabética
        topicos.sort((a, b) => a.nome_topico.localeCompare(b.nome_topico));

        menuTopicos.innerHTML = ''; 

        
        if (topicos.length === 0) {
            btnTopicos.textContent = 'Todos os Assuntos';
            menuTopicos.innerHTML = '<li><span class="text-muted small px-2">Nenhum assunto específico cadastrado.</span></li>';
            btnTopicos.disabled = false;
            return;
        }

        btnTopicos.textContent = 'Selecionar Todos';
        btnTopicos.disabled = false;

        const masterId = `master_sim_${idMateria}_${Math.random().toString(36).substr(2, 5)}`;
        const liMaster = document.createElement('li');
        liMaster.className = 'px-2 py-1 border-bottom';
        liMaster.innerHTML = `
            <div class="form-check item-filtro" style="cursor: pointer; padding: 8px 12px; border-radius: 8px;">
                <input class="form-check-input check-todos-sim" type="checkbox" id="${masterId}">
                <label class="form-check-label small fw-bold text-primary w-100" for="${masterId}">Marcar Todo o Edital</label>
            </div>
        `;
        menuTopicos.appendChild(liMaster);

        topicos.forEach(t => {
            const uniqueId = `sim_t${t.id_topico}_${Math.random().toString(36).substr(2, 5)}`;
            const li = document.createElement('li');
            li.className = 'px-2 py-1 border-bottom';
            li.innerHTML = `
                <div class="form-check item-filtro" style="cursor: pointer; padding: 8px 12px; border-radius: 8px;">
                    <input class="form-check-input check-topico-sim" type="checkbox" value="${t.id_topico}" id="${uniqueId}">
                    <label class="form-check-label small w-100 d-block" for="${uniqueId}">${t.nome_topico}</label>
                </div>
            `;
            menuTopicos.appendChild(li);
        });

        const checkboxes = menuTopicos.querySelectorAll('.check-topico-sim');
        const masterCheckbox = liMaster.querySelector('.check-todos-sim');

        masterCheckbox.addEventListener('change', function() {
            checkboxes.forEach(chk => chk.checked = this.checked);
            atualizarContagemSim(checkboxes, btnTopicos, hiddenTopicos);
        });

        checkboxes.forEach(chk => {
            chk.addEventListener('change', () => {
                if (!chk.checked) masterCheckbox.checked = false;
                const todosMarcados = Array.from(checkboxes).every(c => c.checked);
                if (todosMarcados) masterCheckbox.checked = true;
                atualizarContagemSim(checkboxes, btnTopicos, hiddenTopicos);
            });
        });

    } catch (error) {
        console.error("Erro ao carregar tópicos:", error);
        btnTopicos.textContent = 'Erro ao carregar';
    }
}

function atualizarContagemSim(checkboxes, btnTopicos, hiddenTopicos) {
    const selecionados = Array.from(checkboxes).filter(c => c.checked).map(c => c.value);
    hiddenTopicos.value = selecionados.join(',');
    if (selecionados.length === 0) btnTopicos.textContent = 'Selecionar Todos';
    else if (selecionados.length === checkboxes.length) btnTopicos.textContent = 'Todo o Edital';
    else btnTopicos.textContent = `${selecionados.length} selecionados`;
}

/**
 * Adiciona um novo bloco de seleção de matéria no modal
 */
window.adicionarMateria = function() {
    const container = document.getElementById('container-materias');
    const blocos = container.querySelectorAll('.bloco-materia');
    const novoBloco = blocos[0].cloneNode(true);
    
    // Limpa os valores do novo bloco
    novoBloco.querySelector('input[type="number"]').value = '5';
    novoBloco.querySelector('.select-materia').value = '';
    novoBloco.querySelector('.hidden-topicos').value = '';
    
    const btnTopicos = novoBloco.querySelector('.btn-topicos');
    btnTopicos.innerHTML = 'Todos os assuntos';
    btnTopicos.disabled = true;
    
    novoBloco.querySelector('.menu-topicos').innerHTML = '<li><span class="text-muted small px-2">Selecione uma matéria para filtrar assuntos.</span></li>';
    novoBloco.querySelector('.btn-remover').disabled = false;
    
    container.appendChild(novoBloco);
    atualizarBotoesRemover();
};

/**
 * Remove um bloco de matéria
 */
window.removerMateria = function(botao) {
    botao.closest('.bloco-materia').remove();
    atualizarBotoesRemover();
};

function atualizarBotoesRemover() {
    const blocos = document.querySelectorAll('.bloco-materia');
    blocos.forEach(bloco => {
        const btnRemover = bloco.querySelector('.btn-remover');
        if (btnRemover) {
            btnRemover.disabled = (blocos.length === 1);
        }
    });
}
