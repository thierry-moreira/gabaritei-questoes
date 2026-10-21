/**
 * Gerenciamento de Cadernos do Aluno
 */

function salvarNovoCaderno() {
    const input = document.getElementById('input-nome-caderno');
    const nome = input.value.trim();
    if (!nome) return alert("Por favor, digite um nome para o caderno.");

    const btn = event.currentTarget;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Criando...';

    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';

    fetch('/api/cadernos/novo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome: nome })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            Swal.fire({
                title: 'Limite Atingido',
                text: data.error || "Erro ao criar caderno.",
                icon: 'warning',
                background: isDark ? '#1e1e2d' : '#fff',
                color: isDark ? '#f8f9fa' : '#212529',
                confirmButtonColor: 'var(--premium-accent)',
                confirmButtonText: 'Entendido'
            });
            btn.disabled = false;
            btn.innerHTML = 'Criar Caderno';
        }
    })
    .catch(err => {
        Swal.fire({
            title: 'Erro',
            text: "Ocorreu um erro na conexão. Tente novamente.",
            icon: 'error',
            background: isDark ? '#1e1e2d' : '#fff',
            color: isDark ? '#f8f9fa' : '#212529'
        });
        btn.disabled = false;
        btn.innerHTML = 'Criar Caderno';
    });
}

function excluirCaderno(button) {
    const group = button.closest('.premium-tool-group');
    const id = group.dataset.id;
    const nome = group.dataset.nome;
    const card = button.closest('.premium-card');
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';

    Swal.fire({
        title: 'Excluir Caderno?',
        text: `Tem certeza que deseja excluir o caderno "${nome}"? Esta ação não pode ser desfeita.`,
        icon: 'warning',
        showCancelButton: true,
        background: isDark ? '#1e1e2d' : '#fff',
        color: isDark ? '#f8f9fa' : '#212529',
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sim, excluir!',
        cancelButtonText: 'Cancelar',
        customClass: {
            popup: 'premium-popup-radius'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            button.disabled = true;
            button.innerHTML = '<i class="bi bi-hourglass-split spinner-border-sm"></i>';

            fetch('/api/cadernos/excluir/' + id, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    Swal.fire({
                        title: 'Excluído!',
                        text: 'O caderno foi removido.',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false,
                        background: isDark ? '#1e1e2d' : '#fff',
                        color: isDark ? '#f8f9fa' : '#212529'
                    });
                    if(card) {
                        card.style.opacity = '0';
                        card.style.transform = 'scale(0.9)';
                    }
                    setTimeout(() => location.reload(), 1500);
                } else {
                    Swal.fire('Erro', data.error || 'Erro ao excluir', 'error');
                    button.disabled = false;
                    button.innerHTML = '<i class="bi bi-trash3"></i>';
                }
            })
            .catch(err => Swal.fire('Erro', 'Erro de conexão!', 'error'));
        }
    });
}
