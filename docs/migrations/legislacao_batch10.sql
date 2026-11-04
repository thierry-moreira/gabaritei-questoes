-- =============================================================================
-- RAG leve de legislação — correções de grafia e mapeamento temático
-- Arquivo: docs/migrations/legislacao_batch10.sql
-- Aplicação: SQL Editor do Supabase / painel admin (service_role).
-- Idempotente: referências são atualizadas por chave ou inseridas via upsert.
-- Textos adicionais conferidos na legislação compilada do Planalto:
--   https://www.planalto.gov.br/ccivil_03/leis/l4320compilado.htm
--   https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm
-- =============================================================================

-- Corrige duas transcrições do CPM/CPPM presentes no banco remoto.
-- O lote local já contém as formas corretas: “Deserção”.
update public.legislacao_artigos l
set referencia = replace(replace(l.referencia, 'Desersão', 'Deserção'), 'desersão', 'deserção'),
    texto = replace(replace(l.texto, 'Desersão', 'Deserção'), 'desersão', 'deserção')
where l.referencia in (
    'CPM — art. 187 e 195 (Dever Militar: Desersão e Abandono de Posto)',
    'CPPM — art. 451 e 458 (Processos Especiais de Desersão e Insubmissão)'
)
and not exists (
    select 1
    from public.legislacao_artigos existente
    where existente.id <> l.id
      and existente.referencia = replace(replace(l.referencia, 'Desersão', 'Deserção'), 'desersão', 'deserção')
);

-- Torna explícitas no rótulo as leis alteradoras já citadas no texto dos trechos.
with refs(old_ref, new_ref) as (
    values
        ('CP — art. 121-A (caput)',
         'CP — art. 121-A (caput; incluído pela Lei nº 14.994/2024)'),
        ('LINDB — art. 20 (caput)',
         'LINDB — art. 20, caput (incluído pela Lei nº 13.655/2018)'),
        ('LINDB — art. 22',
         'LINDB — art. 22 (incluído pela Lei nº 13.655/2018)'),
        ('LINDB — art. 28',
         'LINDB — art. 28 (incluído pela Lei nº 13.655/2018)')
)
update public.legislacao_artigos l
set referencia = r.new_ref
from refs r
where l.referencia = r.old_ref
  and not exists (
      select 1
      from public.legislacao_artigos existente
      where existente.referencia = r.new_ref
  );

-- O mesmo art. 3º da LC 123 é usado também em Direito Tributário (tópico 575).
insert into public.legislacao_artigos
    (referencia, texto, vigencia_de, id_materia, id_topico)
values
    ('LC nº 123/2006 — art. 3º (Enquadramento ME/EPP — Direito Tributário)',
     'Para os efeitos desta Lei Complementar, consideram-se microempresas ou empresas de pequeno porte a sociedade empresária, a sociedade simples, a empresa individual de responsabilidade limitada e o empresário individual devidamente registrados que aufiram, em cada ano-calendário: I - microempresa: receita bruta igual ou inferior a R$ 360.000,00; II - empresa de pequeno porte: receita bruta superior a R$ 360.000,00 e igual ou inferior a R$ 4.800.000,00.',
     '2006-12-14', 37, 575),
    ('Lei nº 6.404/1976 — arts. 1º, 2º e 4º (Normatização contábil)',
     'A companhia ou sociedade anônima terá o capital dividido em ações, e a responsabilidade dos sócios ou acionistas será limitada ao preço de emissão das ações subscritas ou adquiridas. A companhia é aberta ou fechada conforme os valores mobiliários de sua emissão estejam ou não admitidos à negociação no mercado de valores mobiliários.',
     '1976-12-15', 17, 227),
    ('Lei nº 4.320/1964 — arts. 81–85 (Controle externo e contabilidade)',
     'Art. 81. O controle da execução orçamentária, pelo Poder Legislativo, terá por objetivo verificar a probidade da administração, a guarda e legal emprego dos dinheiros públicos e o cumprimento da Lei de Orçamento. Art. 82. O Poder Executivo, anualmente, prestará contas ao Poder Legislativo, no prazo estabelecido nas Constituições ou nas Leis Orgânicas dos Municípios. § 1º As contas do Poder Executivo serão submetidas ao Poder Legislativo, com parecer prévio do Tribunal de Contas ou órgão equivalente. § 2º Quando, no Município, não houver Tribunal de Contas ou órgão equivalente, a Câmara de Vereadores poderá designar peritos contadores para verificarem as contas do prefeito e sobre elas emitirem parecer. Art. 83. A contabilidade evidenciará perante a Fazenda Pública a situação de todos quantos, de qualquer modo, arrecadem receitas, efetuem despesas, administrem ou guardem bens a ela pertencentes ou confiados. Art. 84. Ressalvada a competência do Tribunal de Contas ou órgão equivalente, a tomada de contas dos agentes responsáveis por bens ou dinheiros públicos será realizada ou superintendida pelos serviços de contabilidade. Art. 85. Os serviços de contabilidade serão organizados de forma a permitirem o acompanhamento da execução orçamentária, o conhecimento da composição patrimonial, a determinação dos custos dos serviços industriais, o levantamento dos balanços gerais, a análise e a interpretação dos resultados econômicos e financeiros.',
     '1964-03-17', 22, 139),
    ('Lei nº 4.320/1964 — arts. 101–103 (Balanços)',
     'Art. 101. Os resultados gerais do exercício serão demonstrados no Balanço Orçamentário, no Balanço Financeiro, no Balanço Patrimonial, na Demonstração das Variações Patrimoniais, segundo os Anexos números 12, 13, 14 e 15 e os quadros demonstrativos constantes dos Anexos números 1, 6, 7, 8, 9, 10, 11, 16 e 17. Art. 102. O Balanço Orçamentário demonstrará as receitas e despesas previstas em confronto com as realizadas. Art. 103. O Balanço Financeiro demonstrará a receita e a despesa orçamentárias bem como os recebimentos e os pagamentos de natureza extra-orçamentária, conjugados com os saldos em espécie provenientes do exercício anterior, e os que se transferem para o exercício seguinte. Parágrafo único. Os Restos a Pagar do exercício serão computados na receita extra-orçamentária para compensar sua inclusão na despesa orçamentária.',
     '1964-03-17', 22, 139),
    ('CDC — arts. 61, 63–65 (Crimes de consumo: nocividade e periculosidade)',
     'Art. 61. Constituem crimes contra as relações de consumo previstas neste código, sem prejuízo do disposto no Código Penal e leis especiais, as condutas tipificadas nos artigos seguintes. Art. 63. Omitir dizeres ou sinais ostensivos sobre a nocividade ou periculosidade de produtos, nas embalagens, nos invólucros, recipientes ou publicidade: Pena - detenção de seis meses a dois anos e multa. § 1º Incorrerá nas mesmas penas quem deixar de alertar, mediante recomendações escritas ostensivas, sobre a periculosidade do serviço a ser prestado. § 2º Se o crime é culposo: Pena - detenção de um a seis meses ou multa. Art. 64. Deixar de comunicar à autoridade competente e aos consumidores a nocividade ou periculosidade de produtos cujo conhecimento seja posterior à sua colocação no mercado: Pena - detenção de seis meses a dois anos e multa. Parágrafo único. Incorrerá nas mesmas penas quem deixar de retirar do mercado, imediatamente quando determinado pela autoridade competente, os produtos nocivos ou perigosos, na forma deste artigo. Art. 65. Executar serviço de alto grau de periculosidade, contrariando determinação de autoridade competente: Pena - detenção de seis meses a dois anos e multa.',
     '1990-09-11', 19, 341),
    ('CDC — arts. 66–69 (Crimes de consumo: informação e publicidade)',
     'Art. 66. Fazer afirmação falsa ou enganosa, ou omitir informação relevante sobre a natureza, característica, qualidade, quantidade, segurança, desempenho, durabilidade, preço ou garantia de produtos ou serviços: Pena - detenção de três meses a um ano e multa. § 1º Incorrerá nas mesmas penas quem patrocinar a oferta. § 2º Se o crime é culposo: Pena - detenção de um a seis meses ou multa. Art. 67. Fazer ou promover publicidade que sabe ou deveria saber ser enganosa ou abusiva: Pena - detenção de três meses a um ano e multa. Art. 68. Fazer ou promover publicidade que sabe ou deveria saber ser capaz de induzir o consumidor a se comportar de forma prejudicial ou perigosa à sua saúde ou segurança: Pena - detenção de seis meses a dois anos e multa. Art. 69. Deixar de organizar dados fáticos, técnicos e científicos que dão base à publicidade: Pena - detenção de um a seis meses ou multa.',
     '1990-09-11', 19, 341),
    ('CDC — arts. 70–74 (Crimes de consumo: reparação, cobrança e garantia)',
     'Art. 70. Empregar na reparação de produtos, peça ou componentes de reposição usados, sem autorização do consumidor: Pena - detenção de três meses a um ano e multa. Art. 71. Utilizar, na cobrança de dívidas, de ameaça, coação, constrangimento físico ou moral, afirmações falsas incorretas ou enganosas ou de qualquer outro procedimento que exponha o consumidor, injustificadamente, a ridículo ou interfira com seu trabalho, descanso ou lazer: Pena - detenção de três meses a um ano e multa. Art. 72. Impedir ou dificultar o acesso do consumidor às informações que sobre ele constem em cadastros, banco de dados, fichas e registros: Pena - detenção de seis meses a um ano ou multa. Art. 73. Deixar de corrigir imediatamente informação sobre consumidor constante de cadastro, banco de dados, fichas ou registros que sabe ou deveria saber ser inexata: Pena - detenção de um a seis meses ou multa. Art. 74. Deixar de entregar ao consumidor o termo de garantia adequadamente preenchido e com especificação clara de seu conteúdo: Pena - detenção de um a seis meses ou multa.',
     '1990-09-11', 19, 341),
    ('CDC — arts. 75, 77 e 78 (Concurso de agentes e penas)',
     'Art. 75. Quem, de qualquer forma, concorrer para os crimes referidos neste código, incide nas penas a esses cominadas na medida de sua culpabilidade, bem como o diretor, administrador ou gerente da pessoa jurídica que promover, permitir ou por qualquer modo aprovar o fornecimento, oferta, exposição à venda ou manutenção em depósito de produtos ou a oferta e prestação de serviços nas condições por ele proibidas. Art. 77. A pena pecuniária prevista nesta Seção será fixada em dias-multa, correspondente ao mínimo e ao máximo de dias de duração da pena privativa da liberdade cominada ao crime. Na individualização desta multa, o juiz observará o disposto no art. 60, § 1º, do Código Penal. Art. 78. Além das penas privativas de liberdade e de multa, podem ser impostas, cumulativa ou alternadamente, observado o disposto nos arts. 44 a 47 do Código Penal: I - a interdição temporária de direitos; II - a publicação em órgãos de comunicação de grande circulação ou audiência, às expensas do condenado, de notícia sobre os fatos e a condenação; III - a prestação de serviços à comunidade.',
     '1990-09-11', 19, 341)
on conflict (referencia) do update set
    texto = excluded.texto,
    vigencia_de = excluded.vigencia_de,
    vigencia_ate = null,
    id_materia = excluded.id_materia,
    id_topico = excluded.id_topico;
