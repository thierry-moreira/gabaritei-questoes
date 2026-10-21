/**
 * Validação de Força de Senha - Cadastro de Aluno
 */
document.addEventListener("DOMContentLoaded", function() {
    const inputSenha = document.getElementById('password'); 
    const barraForca = document.getElementById('barra-forca');
    const textoForca = document.getElementById('texto-forca');

    if (!inputSenha || !barraForca || !textoForca) return;

    inputSenha.addEventListener('input', function() {
        const senha = inputSenha.value;
        let forca = 0;

        // Se vazio, zera
        if (senha.length === 0) {
            barraForca.style.width = '0%';
            barraForca.className = 'progress-bar';
            textoForca.innerHTML = 'Mínimo 6 caracteres.';
            textoForca.className = 'form-text small mt-1 fw-bold text-muted';
            return;
        }

        // Cálculo da força
        if (senha.length >= 6) forca += 25; 
        if (senha.length >= 8) forca += 25; 
        if (/[A-Z]/.test(senha) && /[a-z]/.test(senha)) forca += 25; 
        if (/[0-9]/.test(senha) && /[^A-Za-z0-9]/.test(senha)) forca += 25; 

        // Atualiza visual
        barraForca.style.width = forca + '%';

        if (forca <= 25) {
            barraForca.className = 'progress-bar bg-danger';
            textoForca.innerHTML = 'Senha muito fraca';
            textoForca.className = 'form-text small mt-1 fw-bold text-danger';
        } else if (forca <= 50) {
            barraForca.className = 'progress-bar bg-warning';
            textoForca.innerHTML = 'Senha fraca';
            textoForca.className = 'form-text small mt-1 fw-bold text-warning';
        } else if (forca <= 75) {
            barraForca.className = 'progress-bar bg-info';
            textoForca.innerHTML = 'Senha boa';
            textoForca.className = 'form-text small mt-1 fw-bold text-info';
        } else {
            barraForca.className = 'progress-bar bg-success';
            textoForca.innerHTML = 'Senha forte!';
            textoForca.className = 'form-text small mt-1 fw-bold text-success';
        }
    });
});
