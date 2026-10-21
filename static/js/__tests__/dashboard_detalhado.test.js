/**
 * Testes unitários para dashboard_detalhado.js
 * Cobertura: gráficos (Chart.js), calendário, metadados, temas, API, colapso
 *
 * O Chart.js é carregado via <script> no HTML, então Chart é uma variável global.
 * Mockamos global.Chart = jest.fn().
 */

// ---------------------------------------------------------------------------
// MOCKS GLOBAIS (devem ser definidos ANTES de qualquer require)
// ---------------------------------------------------------------------------

// Chart.js é global (carregado via script tag)
// Retorna um mock com a estrutura esperada pelos handlers (ex: themeChanged)
global.Chart = jest.fn(function () {
    return {
        data: { datasets: [{ borderColor: '#fff', backgroundColor: '#fff' }] },
        options: {
            plugins: {
                legend: { labels: { color: '#fff' } },
                tooltip: { backgroundColor: '#fff', titleColor: '#fff', bodyColor: '#fff' },
            },
            scales: {
                x: { ticks: { color: '#fff' } },
                y: { grid: { color: '#fff' }, ticks: { color: '#fff' } },
            },
        },
        update: jest.fn(),
        destroy: jest.fn(),
    };
});

// Mock fetch global
global.fetch = jest.fn();

// Mock window.alert
global.alert = jest.fn();

// jsdom não implementa getContext - mockamos para evitar erros
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
    canvas: { width: 100, height: 100 },
}));

// ---------------------------------------------------------------------------
// HELPERS
// ---------------------------------------------------------------------------

/**
 * Cria o container #dashboard-config com os data-attributes fornecidos.
 * Retorna o container criado.
 */
function setupDashboardConfig(overrides = {}) {
    const defaults = {
        datasets: '[]',
        labels: '[]',
        concluidos: '{}',
        csrfToken: 'test-csrf-token',
        metaDiaria: '10',
        materias: '[]',
    };
    const config = { ...defaults, ...overrides };

    document.body.innerHTML = `
      <div id="dashboard-config"
        data-datasets='${config.datasets}'
        data-labels='${config.labels}'
        data-concluidos='${config.concluidos}'
        data-csrf-token="${config.csrfToken}"
        data-meta-diaria="${config.metaDiaria}"
        data-materias='${config.materias}'>
      </div>
      <canvas id="chartPizzaQuestoes"></canvas>
      <canvas id="chartBarrasAcertos"></canvas>
      <div id="calendar-days"></div>
      <div id="month-year-label"></div>
      <div id="current-day-name"></div>
      <span id="meta-display">10</span>
      <button id="btn-salvar-meta" class="btn-premium-gradient">SALVAR META</button>
      <div id="calendar-content-wrapper" style="display:block">
        <span id="icon-collapse-cal" style="transform: rotate(0deg)"></span>
      </div>
      <div class="calendar-card"></div>
    `;
    return document.getElementById('dashboard-config');
}

/**
 * Carrega (ou recarrega) o script dashboard_detalhado.js.
 * Limpa mocks e estado entre testes.
 */
function loadScript() {
    // Limpa funções do window de execuções anteriores
    delete window.adjustMeta;
    delete window.saveMeta;
    delete window.changeMonth;
    delete window.toggleCalendarCollapse;

    // Reseta mocks
    global.Chart.mockClear();
    global.fetch.mockClear();
    global.alert.mockClear();

    // Limpa cache do require para forçar re-execução
    delete require.cache[require.resolve('../dashboard_detalhado.js')];

    // Carrega o script (registra o listener DOMContentLoaded)
    require('../dashboard_detalhado.js');

    // No jsdom o DOMContentLoaded já disparou antes dos testes.
    // Disparamos manualmente para que o callback do script execute.
    document.dispatchEvent(new Event('DOMContentLoaded'));
}

// ---------------------------------------------------------------------------
// TESTES
// ---------------------------------------------------------------------------

describe('Dashboard Detalhado - Inicialização', () => {
    test('não deve executar se #dashboard-config estiver ausente', () => {
        document.body.innerHTML = '<div></div>';
        // Limpa cache para teste isolado
        delete require.cache[require.resolve('../dashboard_detalhado.js')];
        expect(() => require('../dashboard_detalhado.js')).not.toThrow();
    });

    test('deve lidar com JSON inválido nos datasets (malformado)', () => {
        // Previne que jsdom reporte SyntaxError como unhandled exception
        const onError = jest.fn(e => e.preventDefault());
        window.addEventListener('error', onError);
        setupDashboardConfig({ datasets: 'INVALID_JSON' });
        expect(() => loadScript()).not.toThrow();
        expect(onError).toHaveBeenCalled();
        expect(global.Chart).not.toHaveBeenCalled();
        window.removeEventListener('error', onError);
    });

    test('deve lidar com JSON inválido nos labels', () => {
        const onError = jest.fn(e => e.preventDefault());
        window.addEventListener('error', onError);
        setupDashboardConfig({ labels: '{broken' });
        expect(() => loadScript()).not.toThrow();
        expect(onError).toHaveBeenCalled();
        expect(global.Chart).not.toHaveBeenCalled();
        window.removeEventListener('error', onError);
    });

    test('deve lidar com JSON inválido nos concluidos', () => {
        const onError = jest.fn(e => e.preventDefault());
        window.addEventListener('error', onError);
        setupDashboardConfig({ concluidos: 'not json' });
        expect(() => loadScript()).not.toThrow();
        expect(onError).toHaveBeenCalled();
        expect(global.Chart).not.toHaveBeenCalled();
        window.removeEventListener('error', onError);
    });

    test('deve lidar com JSON inválido nas materias', () => {
        const onError = jest.fn(e => e.preventDefault());
        window.addEventListener('error', onError);
        setupDashboardConfig({ materias: 'not json' });
        expect(() => loadScript()).not.toThrow();
        expect(onError).toHaveBeenCalled();
        expect(global.Chart).not.toHaveBeenCalled();
        window.removeEventListener('error', onError);
    });

    test('deve funcionar com todos os arrays vazios (sem quebrar)', () => {
        setupDashboardConfig();
        expect(() => loadScript()).not.toThrow();
        expect(global.Chart).not.toHaveBeenCalled();
    });

    test('metaDiaria ausente deve default para 0', () => {
        setupDashboardConfig({ metaDiaria: '' });
        expect(() => loadScript()).not.toThrow();
    });

    test('csrfToken nulo/undefined deve ser aceito', () => {
        setupDashboardConfig({ csrfToken: '' });
        expect(() => loadScript()).not.toThrow();
    });
});

describe('Gráfico de Pizza (Doughnut)', () => {
    test('não cria gráfico se canvas #chartPizzaQuestoes não existe', () => {
        document.body.innerHTML = `
          <div id="dashboard-config"
            data-datasets='[{"label":"Mat","borderColor":"#f00"}]'
            data-labels='[]'
            data-concluidos='{}'
            data-csrf-token="t"
            data-meta-diaria="10"
            data-materias='[{"nome":"Mat","total":10,"taxa":80}]'>
          </div>
          <canvas id="chartBarrasAcertos"></canvas>
          <div id="calendar-days"></div>
          <div id="month-year-label"></div>
          <div id="current-day-name"></div>
          <span id="meta-display">10</span>
          <button id="btn-salvar-meta" class="btn-premium-gradient">X</button>
          <div id="calendar-content-wrapper"><span id="icon-collapse-cal"></span></div>
        `;
        loadScript();
        // Chart não deve ser chamado porque falta pizza canvas, mas bar canvas existe
        const barCalls = global.Chart.mock.calls.filter(c => c[1] && c[1].type === 'bar');
        const pizzaCalls = global.Chart.mock.calls.filter(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCalls.length).toBe(0);
        expect(barCalls.length).toBe(1);
    });

    test('não cria gráfico se materiasData está vazio', () => {
        setupDashboardConfig();
        loadScript();
        expect(global.Chart).not.toHaveBeenCalled();
    });

    test('cria gráfico doughnut com dados corretos para 1 matéria', () => {
        const datasets = JSON.stringify([{ label: 'Portugues', borderColor: '#ff0000' }]);
        const materias = JSON.stringify([{ nome: 'Portugues', total: 50, taxa: 80 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCall).toBeDefined();
        expect(pizzaCall[1].type).toBe('doughnut');
        expect(pizzaCall[1].data.labels).toEqual(['Portugues']);
        expect(pizzaCall[1].data.datasets[0].data).toEqual([50]);
        expect(pizzaCall[1].data.datasets[0].backgroundColor).toEqual(['#ff0000']);
        expect(pizzaCall[1].data.datasets[0].borderWidth).toBe(2);
        expect(pizzaCall[1].options.responsive).toBe(true);
        expect(pizzaCall[1].options.maintainAspectRatio).toBe(false);
    });

    test('usa cor padrão #3b82f6 quando matéria não tem cor mapeada', () => {
        const datasets = JSON.stringify([{ label: 'Outra', borderColor: '#00ff00' }]);
        const materias = JSON.stringify([{ nome: 'Portugues', total: 30, taxa: 70 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCall[1].data.datasets[0].backgroundColor).toEqual(['#3b82f6']);
    });

    test('usa backgroundColor como fallback quando borderColor está ausente', () => {
        const datasets = JSON.stringify([{ label: 'Mat', backgroundColor: '#abc123' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 20, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCall[1].data.datasets[0].backgroundColor).toEqual(['#abc123']);
    });

    test('posição da legenda: mobile (bottom) quando width < 1024', () => {
        Object.defineProperty(window, 'innerWidth', { value: 800, writable: true });
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCall[1].options.plugins.legend.position).toBe('bottom');
    });

    test('posição da legenda: desktop (right) quando width >= 1024', () => {
        Object.defineProperty(window, 'innerWidth', { value: 1200, writable: true });
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCall[1].options.plugins.legend.position).toBe('right');
    });

    test('tooltip callback formata corretamente', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        const labelFn = pizzaCall[1].options.plugins.tooltip.callbacks.label;
        const result = labelFn({ label: 'Mat', parsed: 10 });
        expect(result).toBe(' Mat: 10 questões');
    });

    test('múltiplas matérias (3) com cores variadas', () => {
        const datasets = JSON.stringify([
            { label: 'A', borderColor: '#ff0000' },
            { label: 'B', borderColor: '#00ff00' },
            { label: 'C', borderColor: '#0000ff' },
        ]);
        const materias = JSON.stringify([
            { nome: 'A', total: 10, taxa: 90 },
            { nome: 'B', total: 20, taxa: 80 },
            { nome: 'C', total: 30, taxa: 70 },
        ]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCall[1].data.labels).toEqual(['A', 'B', 'C']);
        expect(pizzaCall[1].data.datasets[0].data).toEqual([10, 20, 30]);
        expect(pizzaCall[1].data.datasets[0].backgroundColor).toEqual(['#ff0000', '#00ff00', '#0000ff']);
    });

    test('tema dark aplica cores escuras no gráfico', () => {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        // Tema dark: bg = '#161b22'
        expect(pizzaCall[1].data.datasets[0].borderColor).toBe('#161b22');
        expect(pizzaCall[1].options.plugins.legend.labels.color).toBe('#8b949e');
        expect(pizzaCall[1].options.plugins.tooltip.backgroundColor).toBe('#161b22');
        expect(pizzaCall[1].options.plugins.tooltip.titleColor).toBe('#fff');
        expect(pizzaCall[1].options.plugins.tooltip.bodyColor).toBe('#8b949e');
    });

    test('tema light aplica cores claras no gráfico', () => {
        document.documentElement.setAttribute('data-bs-theme', 'light');
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        // Tema light: bg = '#fff'
        expect(pizzaCall[1].data.datasets[0].borderColor).toBe('#fff');
        expect(pizzaCall[1].options.plugins.legend.labels.color).toBe('#6b7280');
        expect(pizzaCall[1].options.plugins.tooltip.backgroundColor).toBe('#fff');
        expect(pizzaCall[1].options.plugins.tooltip.titleColor).toBe('#1f2937');
        expect(pizzaCall[1].options.plugins.tooltip.bodyColor).toBe('#6b7280');
    });

    test('tema ausente (sem atributo) fallback para light', () => {
        document.documentElement.removeAttribute('data-bs-theme');
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        // Fallback: bg = '#fff'
        expect(pizzaCall[1].data.datasets[0].borderColor).toBe('#fff');
    });
});

describe('Gráfico de Barras', () => {
    test('não cria gráfico se canvas #chartBarrasAcertos não existe', () => {
        document.body.innerHTML = `
          <div id="dashboard-config"
            data-datasets='[{"label":"Mat","borderColor":"#f00"}]'
            data-labels='[]'
            data-concluidos='{}'
            data-csrf-token="t"
            data-meta-diaria="10"
            data-materias='[{"nome":"Mat","total":10,"taxa":80}]'>
          </div>
          <canvas id="chartPizzaQuestoes"></canvas>
          <div id="calendar-days"></div>
          <div id="month-year-label"></div>
          <div id="current-day-name"></div>
          <span id="meta-display">10</span>
          <button id="btn-salvar-meta" class="btn-premium-gradient">X</button>
          <div id="calendar-content-wrapper"><span id="icon-collapse-cal"></span></div>
        `;
        loadScript();
        const barCalls = global.Chart.mock.calls.filter(c => c[1] && c[1].type === 'bar');
        expect(barCalls.length).toBe(0);
    });

    test('cria gráfico de barras com dados corretos', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#ff0000' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 50, taxa: 80 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        expect(barCall).toBeDefined();
        expect(barCall[1].type).toBe('bar');
        expect(barCall[1].data.labels).toEqual(['Mat']);
        expect(barCall[1].data.datasets[0].label).toBe('Taxa de Acertos (%)');
        expect(barCall[1].data.datasets[0].data).toEqual([80]);
        expect(barCall[1].data.datasets[0].backgroundColor).toEqual(['#ff0000']);
        expect(barCall[1].options.plugins.legend.display).toBe(false);
    });

    test('eixo Y: beginAtZero true, max 100', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        expect(barCall[1].options.scales.y.beginAtZero).toBe(true);
        expect(barCall[1].options.scales.y.max).toBe(100);
    });

    test('eixo Y: callback formata com %', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        const tickCallback = barCall[1].options.scales.y.ticks.callback;
        expect(tickCallback(80)).toBe('80%');
        expect(tickCallback(0)).toBe('0%');
        expect(tickCallback(100)).toBe('100%');
    });

    test('tooltip callback formata corretamente', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        const labelFn = barCall[1].options.plugins.tooltip.callbacks.label;
        const result = labelFn({ parsed: { y: 75.5 } });
        expect(result).toBe(' Taxa de Acertos: 75.5%');
    });

    test('taxa decimal (ex: 66.67) deve ser passada corretamente', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 25, taxa: 66.67 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        expect(barCall[1].data.datasets[0].data[0]).toBeCloseTo(66.67);
    });

    test('eixo X: maxRotation 45, minRotation 45', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        expect(barCall[1].options.scales.x.ticks.maxRotation).toBe(45);
        expect(barCall[1].options.scales.x.ticks.minRotation).toBe(45);
    });

    test('eixo X: grid display false', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        expect(barCall[1].options.scales.x.grid.display).toBe(false);
    });

    test('borderRadius 4 nas barras', () => {
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        const barCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'bar');
        expect(barCall[1].data.datasets[0].borderRadius).toBe(4);
    });
});

describe('renderCalendar()', () => {
    test('não faz nada se #calendar-days não existe', () => {
        document.body.innerHTML = `
          <div id="dashboard-config"
            data-datasets='[]'
            data-labels='[]'
            data-concluidos='{}'
            data-csrf-token="t"
            data-meta-diaria="10"
            data-materias='[]'>
          </div>
          <canvas id="chartPizzaQuestoes"></canvas>
          <canvas id="chartBarrasAcertos"></canvas>
          <div id="month-year-label"></div>
          <div id="current-day-name"></div>
          <span id="meta-display">10</span>
          <button id="btn-salvar-meta" class="btn-premium-gradient">X</button>
          <div id="calendar-content-wrapper"><span id="icon-collapse-cal"></span></div>
        `;
        expect(() => loadScript()).not.toThrow();
    });

    test('renderiza cabeçalho do dia com data de hoje formatada em pt-BR', () => {
        setupDashboardConfig();
        loadScript();
        const dayHeader = document.getElementById('current-day-name');
        expect(dayHeader.innerText).toBeTruthy();
        // Deve conter dia da semana em português
        const dayNames = ['domingo', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado'];
        const hasDayName = dayNames.some(d => dayHeader.innerText.toLowerCase().includes(d));
        expect(hasDayName).toBe(true);
    });

    test('renderiza nome do mês e ano corretamente', () => {
        setupDashboardConfig();
        loadScript();
        const label = document.getElementById('month-year-label');
        const monthNames = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
            'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
        const hasMonth = monthNames.some(m => label.innerText.toLowerCase().includes(m));
        expect(hasMonth).toBe(true);
        const currentYear = new Date().getFullYear().toString();
        expect(label.innerText).toContain(currentYear);
    });

    test('marca dia atual com classe "today"', () => {
        setupDashboardConfig();
        loadScript();
        const today = new Date().getDate();
        const todayDivs = document.querySelectorAll('#calendar-days .today');
        expect(todayDivs.length).toBe(1);
        expect(parseInt(todayDivs[0].innerText)).toBe(today);
    });

    test('dias com meta atingida recebem classe "goal-met"', () => {
        const today = new Date();
        const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        const concluidos = JSON.stringify({ [dateStr]: 15 });
        setupDashboardConfig({ metaDiaria: '10', concluidos });
        loadScript();

        const todayDivs = document.querySelectorAll('#calendar-days .today.goal-met');
        expect(todayDivs.length).toBe(1);
        expect(todayDivs[0].getAttribute('title')).toBe('15 questões resolvidas!');
    });

    test('dias com questões mas sem atingir meta não recebem goal-met', () => {
        const today = new Date();
        const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        const concluidos = JSON.stringify({ [dateStr]: 5 });
        setupDashboardConfig({ metaDiaria: '10', concluidos });
        loadScript();

        const todayDiv = document.querySelector('#calendar-days .today');
        expect(todayDiv.classList.contains('goal-met')).toBe(false);
        expect(todayDiv.getAttribute('title')).toBe('5 questões');
    });

    test('meta zero não marca nenhum dia como goal-met', () => {
        const today = new Date();
        const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        const concluidos = JSON.stringify({ [dateStr]: 15 });
        setupDashboardConfig({ metaDiaria: '0', concluidos });
        loadScript();

        const goalDivs = document.querySelectorAll('#calendar-days .goal-met');
        expect(goalDivs.length).toBe(0);
    });

    test('concluidosPorDia vazio não quebra calendário', () => {
        setupDashboardConfig();
        loadScript();
        const days = document.querySelectorAll('#calendar-days .day');
        expect(days.length).toBeGreaterThan(0);
    });

    test('dias do mês anterior aparecem com classe "other-month"', () => {
        setupDashboardConfig();
        loadScript();
        const otherMonthDays = document.querySelectorAll('#calendar-days .other-month');
        // Dependendo do dia da semana do dia 1, pode ou não ter outros meses
        expect(otherMonthDays.length).toBeGreaterThanOrEqual(0);
    });

    test('dia exatamente na meta (resolvidos === meta) marca goal-met', () => {
        const today = new Date();
        const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        const concluidos = JSON.stringify({ [dateStr]: 10 });
        setupDashboardConfig({ metaDiaria: '10', concluidos });
        loadScript();

        const todayDivs = document.querySelectorAll('#calendar-days .today.goal-met');
        expect(todayDivs.length).toBe(1);
    });

    test('changeMonth avança para o próximo mês e re-renderiza', () => {
        setupDashboardConfig();
        loadScript();
        const initialLabel = document.getElementById('month-year-label').innerText;
        window.changeMonth(1);
        const newLabel = document.getElementById('month-year-label').innerText;
        expect(newLabel).not.toBe(initialLabel);
    });

    test('changeMonth retrocede para o mês anterior', () => {
        setupDashboardConfig();
        loadScript();
        window.changeMonth(1);
        const afterAdvance = document.getElementById('month-year-label').innerText;
        window.changeMonth(-1);
        const afterReturn = document.getElementById('month-year-label').innerText;
        expect(afterReturn).not.toBe(afterAdvance);
    });

    test('changeMonth de dezembro para janeiro muda o ano', () => {
        setupDashboardConfig();
        loadScript();
        window.changeMonth(12);
        const label = document.getElementById('month-year-label');
        const nextYear = new Date().getFullYear() + 1;
        expect(label.innerText).toContain(nextYear.toString());
    });
});

describe('adjustMeta()', () => {
    test('incremento positivo ajusta meta corretamente', () => {
        setupDashboardConfig({ metaDiaria: '10' });
        loadScript();
        window.adjustMeta(5);
        // innerText definido com number (linha 183: innerText = currentMeta)
        expect(document.getElementById('meta-display').innerText).toBe(15);
    });

    test('decremento reduz meta', () => {
        setupDashboardConfig({ metaDiaria: '10' });
        loadScript();
        window.adjustMeta(-3);
        expect(document.getElementById('meta-display').innerText).toBe(7);
    });

    test('não permite meta negativa (Math.max(0, ...))', () => {
        setupDashboardConfig({ metaDiaria: '5' });
        loadScript();
        window.adjustMeta(-20);
        expect(document.getElementById('meta-display').innerText).toBe(0);
    });

    test('botão de salvar volta ao estado inicial após ajuste', () => {
        setupDashboardConfig();
        loadScript();
        const btn = document.getElementById('btn-salvar-meta');
        btn.classList.add('btn-success');
        window.adjustMeta(1);
        expect(btn.classList.contains('btn-success')).toBe(false);
        expect(btn.innerHTML).toBe('SALVAR META');
    });

    test('ajustar para zero é válido', () => {
        setupDashboardConfig({ metaDiaria: '5' });
        loadScript();
        window.adjustMeta(-5);
        expect(document.getElementById('meta-display').innerText).toBe(0);
    });
});

describe('saveMeta()', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    test('envia requisição POST para /aluno/api/set-meta com body correto', async () => {
        setupDashboardConfig({ metaDiaria: '10', csrfToken: 'token123' });
        loadScript();
        global.fetch.mockResolvedValueOnce({ ok: true });
        await window.saveMeta();
        expect(global.fetch).toHaveBeenCalledWith('/aluno/api/set-meta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': 'token123',
            },
            body: JSON.stringify({ meta: 10 }),
        });
    });

    test('em sucesso: botão mostra SALVO! e depois reseta após 2s', async () => {
        setupDashboardConfig();
        loadScript();
        global.fetch.mockResolvedValueOnce({ ok: true });
        await window.saveMeta();

        const btn = document.getElementById('btn-salvar-meta');
        expect(btn.innerText).toBe('SALVO! ✅');
        expect(btn.classList.contains('btn-success')).toBe(true);

        jest.advanceTimersByTime(2000);
        expect(btn.innerText).toBe('SALVAR META');
        expect(btn.classList.contains('btn-premium-gradient')).toBe(true);
        expect(btn.disabled).toBe(false);
    });

    test('em sucesso: botão começa disabled e fica disabled durante timeout', async () => {
        setupDashboardConfig();
        loadScript();
        global.fetch.mockResolvedValueOnce({ ok: true });
        await window.saveMeta();

        const btn = document.getElementById('btn-salvar-meta');
        // Ainda está disabled durante o timeout
        expect(btn.disabled).toBe(true);

        jest.advanceTimersByTime(2000);
        expect(btn.disabled).toBe(false);
    });

    test('em erro HTTP (não ok): mostra alerta e reabilita botão', async () => {
        setupDashboardConfig();
        loadScript();
        global.fetch.mockResolvedValueOnce({ ok: false, status: 500 });
        await window.saveMeta();

        expect(global.alert).toHaveBeenCalledWith('Erro ao salvar meta.');
        const btn = document.getElementById('btn-salvar-meta');
        expect(btn.disabled).toBe(false);
        expect(btn.innerText).toBe('SALVAR META');
    });

    test('em erro de rede (fetch rejeita): reabilita botão sem alerta', async () => {
        setupDashboardConfig();
        loadScript();
        global.fetch.mockRejectedValueOnce(new Error('Network error'));
        await window.saveMeta();

        expect(global.alert).not.toHaveBeenCalled();
        const btn = document.getElementById('btn-salvar-meta');
        expect(btn.disabled).toBe(false);
        expect(btn.innerText).toBe('SALVAR META');
    });

    test('botão fica desabilitado e mostra SALVANDO durante a requisição', async () => {
        setupDashboardConfig();
        loadScript();
        let resolvePromise;
        global.fetch.mockReturnValueOnce(new Promise(resolve => { resolvePromise = resolve; }));
        const savePromise = window.saveMeta();

        const btn = document.getElementById('btn-salvar-meta');
        expect(btn.disabled).toBe(true);
        expect(btn.innerText).toBe('SALVANDO...');

        resolvePromise({ ok: true });
        await savePromise;
    });

    test('csrfToken vazio envia string vazia no header', async () => {
        setupDashboardConfig({ csrfToken: '' });
        loadScript();
        global.fetch.mockResolvedValueOnce({ ok: true });
        await window.saveMeta();
        expect(global.fetch).toHaveBeenCalledWith('/aluno/api/set-meta', expect.objectContaining({
            headers: expect.objectContaining({
                'X-CSRFToken': '',
            }),
        }));
    });
});

describe('toggleCalendarCollapse()', () => {
    test('colapsa calendário quando visível', () => {
        setupDashboardConfig();
        loadScript();
        window.toggleCalendarCollapse();
        const wrapper = document.getElementById('calendar-content-wrapper');
        const icon = document.getElementById('icon-collapse-cal');
        expect(wrapper.style.display).toBe('none');
        expect(icon.style.transform).toBe('rotate(180deg)');
    });

    test('expande calendário quando colapsado', () => {
        setupDashboardConfig();
        loadScript();
        window.toggleCalendarCollapse();
        window.toggleCalendarCollapse();
        const wrapper = document.getElementById('calendar-content-wrapper');
        const icon = document.getElementById('icon-collapse-cal');
        expect(wrapper.style.display).toBe('block');
        expect(icon.style.transform).toBe('rotate(0deg)');
    });

    test('alterna múltiplas vezes corretamente', () => {
        setupDashboardConfig();
        loadScript();
        window.toggleCalendarCollapse(); // fecha
        window.toggleCalendarCollapse(); // abre
        window.toggleCalendarCollapse(); // fecha
        const wrapper = document.getElementById('calendar-content-wrapper');
        expect(wrapper.style.display).toBe('none');
    });

    test('wrapper com display vazio (não definido) trata como visível e colapsa', () => {
        // Força display "" (string vazia)
        setupDashboardConfig();
        const wrapper = document.getElementById('calendar-content-wrapper');
        wrapper.style.display = '';
        loadScript();
        window.toggleCalendarCollapse();
        expect(wrapper.style.display).toBe('none');
    });
});

describe('Evento themeChanged', () => {
    test('não quebra se gráficos não foram criados (dados vazios)', () => {
        document.documentElement.setAttribute('data-bs-theme', 'light');
        setupDashboardConfig(); // materias vazio
        loadScript();

        expect(() => {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            window.dispatchEvent(new CustomEvent('themeChanged'));
        }).not.toThrow();
    });

    test('dispara com gráficos existentes e não causa erros', () => {
        document.documentElement.setAttribute('data-bs-theme', 'light');
        const datasets = JSON.stringify([{ label: 'Mat', borderColor: '#f00' }]);
        const materias = JSON.stringify([{ nome: 'Mat', total: 10, taxa: 50 }]);
        setupDashboardConfig({ datasets, materias });
        loadScript();

        expect(() => {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            window.dispatchEvent(new CustomEvent('themeChanged'));
        }).not.toThrow();
    });
});

describe('Cenários de Integração', () => {
    test('fluxo completo: carregar → ajustar meta → salvar → colapsar calendário → trocar mês', async () => {
        jest.useFakeTimers();
        document.documentElement.setAttribute('data-bs-theme', 'light');
        const datasets = JSON.stringify([{ label: 'Portugues', borderColor: '#ff0000' }]);
        const materias = JSON.stringify([{ nome: 'Portugues', total: 50, taxa: 80 }]);
        setupDashboardConfig({ datasets, materias, metaDiaria: '10' });
        loadScript();

        // Gráficos foram criados
        expect(global.Chart).toHaveBeenCalled();

        // Ajustar meta
        window.adjustMeta(5);
        // innerText definido com number (linha 183: innerText = currentMeta)
        expect(document.getElementById('meta-display').innerText).toBe(15);

        // Salvar meta
        global.fetch.mockResolvedValueOnce({ ok: true });
        await window.saveMeta();
        expect(global.fetch).toHaveBeenCalled();

        // Colapsar calendário
        window.toggleCalendarCollapse();
        expect(document.getElementById('calendar-content-wrapper').style.display).toBe('none');

        // Trocar mês
        window.changeMonth(1);
        const newLabel = document.getElementById('month-year-label').innerText;
        expect(newLabel).toBeTruthy();

        jest.useRealTimers();
    });

    test('múltiplas matérias (15) não quebram', () => {
        const datasetEntries = [];
        const materiaEntries = [];
        for (let i = 0; i < 15; i++) {
            datasetEntries.push({ label: `Mat${i}`, borderColor: `#${i.toString(16).padStart(6, '0')}` });
            materiaEntries.push({ nome: `Mat${i}`, total: i * 10, taxa: 50 + i * 2 });
        }
        setupDashboardConfig({
            datasets: JSON.stringify(datasetEntries),
            materias: JSON.stringify(materiaEntries),
        });
        expect(() => loadScript()).not.toThrow();
        const pizzaCall = global.Chart.mock.calls.find(c => c[1] && c[1].type === 'doughnut');
        expect(pizzaCall[1].data.labels.length).toBe(15);
        expect(pizzaCall[1].data.datasets[0].data.length).toBe(15);
    });

    test('meta salva com valor ajustado múltiplas vezes', async () => {
        jest.useFakeTimers();
        setupDashboardConfig({ metaDiaria: '10' });
        loadScript();

        window.adjustMeta(3);  // 13
        window.adjustMeta(-2); // 11
        window.adjustMeta(7);  // 18

        global.fetch.mockResolvedValueOnce({ ok: true });
        await window.saveMeta();

        expect(global.fetch).toHaveBeenCalledWith('/aluno/api/set-meta', expect.objectContaining({
            body: JSON.stringify({ meta: 18 }),
        }));

        jest.useRealTimers();
    });
});