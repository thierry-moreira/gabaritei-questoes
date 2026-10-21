/**
 * Lógica do Dashboard Detalhado do Aluno
 * Gráficos de Evolução, Calendário de Metas e Análise de Desempenho.
 */

document.addEventListener("DOMContentLoaded", function () {
    const dashboardContainer = document.getElementById('dashboard-config');
    if (!dashboardContainer) return;

    // --- DADOS DINÂMICOS VINDOS DO TEMPLATE ---
    const datasets = JSON.parse(dashboardContainer.dataset.datasets || '[]');
    const labels = JSON.parse(dashboardContainer.dataset.labels || '[]');
    const concluidosPorDia = JSON.parse(dashboardContainer.dataset.concluidos || '{}');
    const csrfToken = dashboardContainer.dataset.csrfToken;
    let currentMeta = parseInt(dashboardContainer.dataset.metaDiaria) || 0;

    // --- LÓGICA DO GRÁFICO (Chart.js) ---
    const materiasData = JSON.parse(dashboardContainer.dataset.materias || '[]');
    const colorMap = {};
    datasets.forEach(ds => {
        colorMap[ds.label] = ds.borderColor || ds.backgroundColor || '#3b82f6';
    });

    const mLabels = materiasData.map(m => m.nome);
    const mQuestoes = materiasData.map(m => m.total);
    const mAcertos = materiasData.map(m => m.taxa);
    const mColors = materiasData.map(m => colorMap[m.nome] || '#3b82f6');

    const ctxPizza = document.getElementById('chartPizzaQuestoes');
    const ctxBarras = document.getElementById('chartBarrasAcertos');
    let chartPizza, chartBarras;

    function getChartTheme() {
        const theme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        return {
            grid: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0,0,0,0.05)',
            text: theme === 'dark' ? '#8b949e' : '#6b7280',
            bg: theme === 'dark' ? '#161b22' : '#fff'
        };
    }

    if (ctxPizza && materiasData.length > 0) {
        const theme = getChartTheme();
        chartPizza = new Chart(ctxPizza.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: mLabels,
                datasets: [{
                    data: mQuestoes,
                    backgroundColor: mColors,
                    borderWidth: 2,
                    borderColor: theme.bg
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: window.innerWidth < 1024 ? 'bottom' : 'right',
                        labels: { color: theme.text, font: { family: 'Inter' }, usePointStyle: true, padding: 20 }
                    },
                    tooltip: {
                        backgroundColor: theme.bg,
                        titleColor: theme.bg === '#161b22' ? '#fff' : '#1f2937',
                        bodyColor: theme.bg === '#161b22' ? '#8b949e' : '#6b7280',
                        borderColor: 'rgba(0,0,0,0.1)',
                        borderWidth: 1,
                        callbacks: {
                            label: function (context) {
                                return ' ' + context.label + ': ' + context.parsed + ' questões';
                            }
                        }
                    }
                }
            }
        });
    }

    if (ctxBarras && materiasData.length > 0) {
        const theme = getChartTheme();
        chartBarras = new Chart(ctxBarras.getContext('2d'), {
            type: 'bar',
            data: {
                labels: mLabels,
                datasets: [{
                    label: 'Taxa de Acertos (%)',
                    data: mAcertos,
                    backgroundColor: mColors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: theme.bg,
                        titleColor: theme.bg === '#161b22' ? '#fff' : '#1f2937',
                        bodyColor: theme.bg === '#161b22' ? '#8b949e' : '#6b7280',
                        borderColor: 'rgba(0,0,0,0.1)',
                        borderWidth: 1,
                        callbacks: {
                            label: function (context) {
                                return ' Taxa de Acertos: ' + context.parsed.y + '%';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: theme.text, font: { family: 'Inter' }, maxRotation: 45, minRotation: 45 }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: theme.grid },
                        ticks: { color: theme.text, font: { family: 'Inter' }, callback: val => val + '%' }
                    }
                }
            }
        });
    }

    // --- LÓGICA DO CALENDÁRIO ---
    let displayedDate = new Date();
    const realToday = new Date();

    function renderCalendar() {
        const daysContainer = document.getElementById('calendar-days');
        const monthYearLabel = document.getElementById('month-year-label');
        const dayHeader = document.getElementById('current-day-name');
        if (!daysContainer) return;

        const optionsHeader = { weekday: 'long', day: 'numeric', month: 'long' };
        dayHeader.innerText = realToday.toLocaleDateString('pt-BR', optionsHeader);

        const monthNames = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
        monthYearLabel.innerText = `${monthNames[displayedDate.getMonth()]} de ${displayedDate.getFullYear()}`;

        const year = displayedDate.getFullYear();
        const month = displayedDate.getMonth();
        const firstDay = new Date(year, month, 1).getDay();
        const lastDate = new Date(year, month + 1, 0).getDate();

        daysContainer.innerHTML = '';

        const prevLastDate = new Date(year, month, 0).getDate();
        for (let i = firstDay; i > 0; i--) {
            const div = document.createElement('div');
            div.className = 'day other-month';
            div.innerText = prevLastDate - i + 1;
            daysContainer.appendChild(div);
        }

        for (let i = 1; i <= lastDate; i++) {
            const div = document.createElement('div');
            div.className = 'day';
            div.innerText = i;

            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            const resolvidos = concluidosPorDia[dateStr] || 0;

            if (currentMeta > 0 && resolvidos >= currentMeta) {
                div.classList.add('goal-met');
                div.setAttribute('title', `${resolvidos} questões resolvidas!`);
            } else if (resolvidos > 0) {
                div.setAttribute('title', `${resolvidos} questões`);
            }

            if (i === realToday.getDate() && month === realToday.getMonth() && year === realToday.getFullYear()) {
                div.classList.add('today');
            }
            daysContainer.appendChild(div);
        }
    }

    // Funções globais mapeadas para o escopo window para manter compatibilidade com onclick inline (ou refatorar para listeners)
    window.adjustMeta = function (val) {
        currentMeta = Math.max(0, currentMeta + val);
        document.getElementById('meta-display').innerText = currentMeta;
        renderCalendar();
        const btn = document.getElementById('btn-salvar-meta');
        btn.classList.remove('btn-success');
        btn.innerHTML = 'SALVAR META';
    };

    window.saveMeta = async function () {
        const btn = document.getElementById('btn-salvar-meta');
        btn.disabled = true;
        btn.innerText = 'SALVANDO...';

        try {
            const response = await fetch('/aluno/api/set-meta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ meta: currentMeta })
            });

            if (response.ok) {
                btn.innerText = 'SALVO! ✅';
                btn.classList.replace('btn-premium-gradient', 'btn-success');
                setTimeout(() => {
                    btn.classList.replace('btn-success', 'btn-premium-gradient');
                    btn.innerText = 'SALVAR META';
                    btn.disabled = false;
                }, 2000);
            } else {
                alert('Erro ao salvar meta.');
                btn.disabled = false;
                btn.innerText = 'SALVAR META';
            }
        } catch (error) {
            btn.disabled = false;
            btn.innerText = 'SALVAR META';
        }
    };

    window.changeMonth = function (dir) {
        displayedDate.setMonth(displayedDate.getMonth() + dir);
        renderCalendar();
    };

    window.toggleCalendarCollapse = function () {
        const wrapper = document.getElementById('calendar-content-wrapper');
        const icon = document.getElementById('icon-collapse-cal');
        const card = document.querySelector('.calendar-card');

        if (wrapper.style.display === 'none') {
            wrapper.style.display = 'block';
            icon.style.transform = 'rotate(0deg)';
            card.classList.remove('pb-0');
        } else {
            wrapper.style.display = 'none';
            icon.style.transform = 'rotate(180deg)';
        }
    };

    renderCalendar();

    // --- EXPORTAÇÕES PARA TESTES UNITÁRIOS ---
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { getChartTheme, renderCalendar };
    }

    // Evento de mudança de tema
    window.addEventListener('themeChanged', () => {
        const newTheme = getChartTheme();
        if (chartPizza) {
            chartPizza.data.datasets[0].borderColor = newTheme.bg;
            chartPizza.options.plugins.legend.labels.color = newTheme.text;
            chartPizza.update();
        }
        if (chartBarras) {
            chartBarras.options.scales.y.grid.color = newTheme.grid;
            chartBarras.options.scales.x.ticks.color = newTheme.text;
            chartBarras.options.scales.y.ticks.color = newTheme.text;
            chartBarras.update();
        }
        renderCalendar(); // Re-renderiza para aplicar cores de tema se necessário
    });
});
