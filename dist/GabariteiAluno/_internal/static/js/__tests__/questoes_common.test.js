/**
 * F-07/F-11 — Paginação e XSS armazenado em comentários.
 *
 * O feed de comentários recebe nome_usuario/texto_comentario do Supabase.
 * Antes da correção, esses valores eram interpolados em template literals e
 * entregues a innerHTML; um <img onerror=...> executava no mesmo-origin.
 * Estes testes provam que o card é montado com textContent/createTextNode.
 */

global.fetch = jest.fn();

function carregarModulo() {
    jest.resetModules();
    delete window.carregarComentarios;
    require('../questoes_common.js');
}

describe('F-07/F-11 — feed de comentários', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        delete window.GABARITEI_AUTH;
        delete window.__xss;
        document.body.innerHTML = `
            <div id="lista-comentarios-1"></div>
            <span id="contador-comentarios-1"></span>
        `;
        carregarModulo();
    });

    test('nome e texto maliciosos não criam elementos HTML nem executam JS', async () => {
        const payload = '<img src=x onerror="window.__xss=1">';
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => [{
                id_comentario: '11111111-1111-4111-8111-111111111111',
                nome_usuario: payload,
                texto_comentario: payload,
                criado_em: '2026-01-01T00:00:00Z',
            }],
        });

        window.carregarComentarios(1);
        await new Promise(resolve => setTimeout(resolve, 0));

        const lista = document.getElementById('lista-comentarios-1');
        expect(lista.querySelector('img')).toBeNull();
        expect(lista.querySelector('script')).toBeNull();
        expect(lista.textContent).toContain(payload);
        expect(window.__xss).toBeUndefined();
    });

    test('id do comentário vai para dataset, não para HTML', async () => {
        window.GABARITEI_AUTH = { isAuthenticated: true };
        const idMalicioso = '"><img src=x onerror=window.__xss=1>';
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => [{
                id_comentario: idMalicioso,
                nome_usuario: 'Aluno',
                texto_comentario: 'Comentário normal.',
                criado_em: '2026-01-01T00:00:00Z',
            }],
        });

        window.carregarComentarios(1);
        await new Promise(resolve => setTimeout(resolve, 0));

        const botao = document.querySelector('.btn-reportar-comentario');
        expect(botao).not.toBeNull();
        expect(botao.dataset.comentarioId).toBe(idMalicioso);
        expect(document.querySelector('img')).toBeNull();
        expect(window.__xss).toBeUndefined();
    });

    test('carrega páginas seguintes sem remover comentários já exibidos', async () => {
        global.fetch
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    comentarios: [{
                        id_comentario: 'comentario-1',
                        nome_usuario: 'Aluno 1',
                        texto_comentario: 'Mais recente.',
                        criado_em: '2026-01-02T00:00:00Z',
                    }],
                    pagina: 1,
                    tem_mais: true,
                }),
            })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    comentarios: [{
                        id_comentario: 'comentario-2',
                        nome_usuario: 'Aluno 2',
                        texto_comentario: 'Mais antigo.',
                        criado_em: '2026-01-01T00:00:00Z',
                    }],
                    pagina: 2,
                    tem_mais: false,
                }),
            });

        window.carregarComentarios(1);
        await new Promise(resolve => setTimeout(resolve, 0));

        const lista = document.getElementById('lista-comentarios-1');
        const botaoMais = lista.querySelector('.btn-carregar-mais-comentarios');
        expect(botaoMais).not.toBeNull();
        expect(global.fetch).toHaveBeenNthCalledWith(
            1, '/api/comentarios/1?page=1'
        );

        botaoMais.click();
        await new Promise(resolve => setTimeout(resolve, 0));

        expect(global.fetch).toHaveBeenNthCalledWith(
            2, '/api/comentarios/1?page=2'
        );
        expect(lista.textContent).toContain('Mais recente.');
        expect(lista.textContent).toContain('Mais antigo.');
        expect(lista.querySelector('.btn-carregar-mais-comentarios')).toBeNull();
    });
});
