-- =============================================================================
-- RAG leve de legislação — Corpus Curado (Batch 7)
-- Matérias e Tópicos Complementares:
-- - Direito Administrativo: Atos (91), Org. Adm (93), Contratos Lei 14.133 (504),
--   Resp. Civil (92), Poderes (63), Serviços Públicos (327), Controle (165),
--   Bens Públicos (65), Intervenção na Propriedade (292)
-- - Direito Constitucional: Controle de Constitucionalidade (221), Defesa do Estado (122), Ordem Social (247)
-- - Direito Processual Penal: Competência (204), Recursos e HC (81), Júri (153), Nulidades (220)
-- - Legislação Penal Especial: Lavagem de Dinheiro (128), Crimes Ambientais (102/275), Crimes Tributários (174)
-- - Segurança Pública: SUSP (486), Orgânica Polícias Civis (485), Segurança Privada (488)
-- - Vulneráveis: PCD (475), Pessoa Idosa (480), Igualdade Racial (481)
-- - Trânsito: Circulação (463), Infrações/Penalidades (467)
-- - Previdenciário: RGPS (258)
-- - Processo Civil: Tutelas de Urgência/Evidência e Procedimento (355)
--
-- Fontes Oficiais: Presidência da República (Planalto) e Constituição Federal.
-- Dispositivos atualizados e vigentes. Sem revogações. Idempotente: on conflict do update.
-- =============================================================================

insert into public.legislacao_artigos (referencia, texto, vigencia_de, id_materia, id_topico) values

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 91: Atos Administrativos
-- -----------------------------------------------------------------------------
('Lei nº 9.784/1999 — art. 53', 'A Administração deve anular seus próprios atos, quando eivados de vício de legalidade, e pode revogá-los por motivo de conveniência ou oportunidade, respeitados os direitos adquiridos.', '1999-01-29', 14, 91),
('Lei nº 9.784/1999 — art. 54', 'O direito da Administração de anular os atos administrativos de que decorram efeitos favoráveis para os destinatários decai em cinco anos, contados da data em que foram praticados, salvo comprovada má-fé.', '1999-01-29', 14, 91),
('Lei nº 9.784/1999 — art. 55', 'Em decisão na qual se evidencie não acarretarem lesão ao interesse público nem prejuízo a terceiros, os atos que apresentarem defeitos sanáveis poderão ser convalidados pela própria Administração.', '1999-01-29', 14, 91),
('Lei nº 4.717/1965 — art. 2º', 'São nulos os atos lesivos ao patrimônio das entidades mencionadas no artigo anterior, nos casos de: a) incompetência; b) vício de forma; c) ilegalidade do objeto; d) inexistência dos motivos; e) desvio de finalidade.', '1965-06-29', 14, 91),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 93: Organização Administrativa
-- -----------------------------------------------------------------------------
('Decreto-Lei nº 200/1967 — art. 4º', 'A Administração Federal compreende: I - A Administração Direta, que se constitui dos serviços integrados na estrutura da Presidência da República e dos Ministérios. II - A Administração Indireta, que compreende as seguintes categorias de entidades, dotadas de personalidade jurídica própria: a) Autarquias; b) Empresas Públicas; c) Sociedades de Economia Mista; d) fundações públicas.', '1967-02-25', 14, 93),
('Decreto-Lei nº 200/1967 — art. 5º', 'Para os fins desta lei, considera-se: I - Autarquia - o serviço autônomo, criado por lei, com personalidade jurídica de direito público, patrimônio e receita próprios, para executar atividades típicas da Administração Pública; II - Empresa Pública - a entidade dotada de personalidade jurídica de direito privado, com patrimônio próprio e capital exclusivo da União; III - Sociedade de Economia Mista - a entidade dotada de personalidade jurídica de direito privado, criada por lei para a exploração de atividade econômica, sob a forma de sociedade anônima, cujas ações com direito a voto pertençam em sua maioria à União ou a entidade da Administração Indireta.', '1967-02-25', 14, 93),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 504: Contratos (Lei nº 14.133/2021)
-- -----------------------------------------------------------------------------
('Lei nº 14.133/2021 — art. 89', 'Os contratos de que trata esta Lei regular-se-ão pelas suas cláusulas e pelos preceitos de direito público, e a eles serão aplicados, supletivamente, os princípios da teoria geral dos contratos e as disposições de direito privado.', '2021-04-01', 14, 504),
('Lei nº 14.133/2021 — art. 104', 'O regime jurídico dos contratos instituído por esta Lei confere à Administração, em relação a eles, as prerrogativas de: I - modificá-los, unilateralmente, para melhor adequação às finalidades de interesse público, respeitados os direitos do contratado; II - extingui-los, unilateralmente, nos casos especificados nesta Lei; III - fiscalizar sua execução; IV - aplicar sanções motivadas pela inexecução total ou parcial do ajuste; V - ocupar provisoriamente bens móveis e imóveis e utilizar pessoal e serviços vinculados ao objeto do contrato, nas hipóteses de necessidade de acautelar apuração administrativa de faltas contratuais ou de rescisão.', '2021-04-01', 14, 504),
('Lei nº 14.133/2021 — art. 124', 'Os contratos regidos por esta Lei poderão ser alterados, com as devidas justificativas: I - unilateralmente pela Administração: a) quando houver modificação do projeto ou das especificações, para melhor adequação técnica a seus objetivos; b) quando for necessária a modificação do valor contratual em decorrência de acréscimo ou diminuição quantitativa de seu objeto, nos limites permitidos por esta Lei.', '2021-04-01', 14, 504),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 92: Responsabilidade Civil do Estado
-- -----------------------------------------------------------------------------
('CF/88 — art. 37, § 6º', 'As pessoas jurídicas de direito público e as de direito privado prestadoras de serviços públicos responderão pelos danos que seus agentes, nessa qualidade, causarem a terceiros, assegurado o direito de regresso contra o responsável nos casos de dolo ou culpa.', '1988-10-05', 14, 92),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 63: Poderes Administrativos
-- -----------------------------------------------------------------------------
('CTN — art. 78', 'Considera-se poder de polícia atividade da administração pública que, limitando ou disciplinando direito, interêsse ou liberdade, regula a prática de ato ou abstenção de fato, em razão de intêresse público concernente à segurança, à higiene, à ordem, aos costumes, à disciplina da produção e do mercado, ao exercício de atividades econômicas dependentes de concessão ou autorização do Poder Público, à tranqüilidade pública ou ao respeito à propriedade e aos direitos individuais ou coletivos.', '1966-10-25', 14, 63),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 327: Serviços Públicos e Concessões
-- -----------------------------------------------------------------------------
('Lei nº 8.987/1995 — art. 6º', 'Toda concessão ou permissão pressupõe a prestação de serviço adequado ao pleno atendimento dos usuários, conforme estabelecido nesta Lei, nas normas pertinentes e no respectivo contrato. § 1º Serviço adequado é o que satisfaz as condições de regularidade, continuidade, eficiência, segurança, atualidade, generalidade, cortesia na sua prestação e modicidade das tarifas.', '1995-02-13', 14, 327),
('Lei nº 8.987/1995 — art. 35', 'Extingue-se a concessão por: I - advento do termo contratual; II - encampação; III - caducidade; IV - rescisão; V - anulação; VI - falência ou extinção da empresa concessionária e falecimento ou incapacidade do titular, no caso de empresa individual. § 1º A encampação é a retomada do serviço pelo poder concedente durante o prazo da concessão, por motivo de interesse público, mediante lei autorizativa específica e após prévio pagamento da indenização.', '1995-02-13', 14, 327),
('Lei nº 11.079/2004 — art. 2º', 'Parceria público-privada é o contrato administrativo de concessão, na modalidade patrocinada ou administrativa. § 1º Concessão patrocinada é a concessão de serviços públicos ou de obras públicas de que trata a Lei nº 8.987, de 13 de fevereiro de 1995, quando envolver, adicionalmente à tarifa cobrada dos usuários contraprestação pecuniária do parceiro público ao parceiro privado. § 2º Concessão administrativa é o contrato de prestação de serviços de que a Administração Pública seja a usuária direta ou indireta, ainda que envolva execução de obra ou fornecimento e instalação de bens.', '2004-12-30', 14, 327),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 165: Controle da Administração
-- -----------------------------------------------------------------------------
('CF/88 — art. 70', 'A fiscalização contábil, financeira, orçamentária, operacional e patrimonial da União e das entidades da administração direta e indireta, quanto à legalidade, legitimidade, economicidade, aplicação das subvenções e renúncia de receitas, será exercida pelo Congresso Nacional, mediante controle externo, e pelo sistema de controle interno de cada Poder.', '1988-10-05', 14, 165),
('CF/88 — art. 71, I e II', 'O controle externo, a cargo do Congresso Nacional, será exercido com o auxílio do Tribunal de Contas da União, ao qual compete: I - apreciar as contas prestadas anualmente pelo Presidente da República, mediante parecer prévio que deverá ser elaborado em sessenta dias a contar de seu recebimento; II - julgar as contas dos administradores e demais responsáveis por dinheiros, bens e valores públicos da administração direta e indireta.', '1988-10-05', 14, 165),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 65: Bens Públicos
-- -----------------------------------------------------------------------------
('CC — art. 98 e 99', 'São públicos os bens do domínio nacional pertencentes às pessoas jurídicas de direito público interno; todos os outros são particulares. São bens públicos: I - os de uso comum do povo, tais como rios, mares, estradas, ruas e praças; II - os de uso especial, tais como edifícios ou terrenos destinados a serviço ou estabelecimento da administração federal, estadual, territorial ou municipal, inclusive os de suas autarquias; III - os dominicais, que constituem o patrimônio das pessoas jurídicas de direito público, como objeto de direito pessoal, ou real, de cada uma dessas entidades.', '2002-01-10', 14, 65),
('CC — art. 100 e 102', 'Os bens públicos de uso comum do povo e os de uso especial são inalienáveis, enquanto conservarem a sua qualificação, na forma que a lei dispuser. Os bens públicos não estão sujeitos a usucapião.', '2002-01-10', 14, 65),

-- -----------------------------------------------------------------------------
-- DIREITO ADMINISTRATIVO (ID 14) — TÓPICO 292: Intervenção na Propriedade
-- -----------------------------------------------------------------------------
('Decreto-Lei nº 3.365/1941 — art. 2º e 5º', 'Mediante declaração de utilidade pública, todos os bens poderão ser desapropriados pela União, pelos Estados, Municípios, Distrito Federal e Territórios. Consideram-se casos de utilidade pública: a segurança nacional; a defesa do Estado; o socorro público em caso de calamidade; a abertura, conservação e melhoramento de vias ou logradouros públicos; o funcionamento dos meios de transporte coletivo; a construção de edifícios públicos.', '1941-06-21', 14, 292),

-- -----------------------------------------------------------------------------
-- DIREITO CONSTITUCIONAL (ID 15) — TÓPICO 221: Controle de Constitucionalidade
-- -----------------------------------------------------------------------------
('CF/88 — art. 97', 'Somente pelo voto da maioria absoluta de seus membros ou dos membros do respectivo órgão especial poderão os tribunais declarar a inconstitucionalidade de lei ou ato normativo do Poder Público (cláusula de reserva de plenário).', '1988-10-05', 15, 221),
('CF/88 — art. 102, I, a', 'Compete ao Supremo Tribunal Federal, precipuamente, a guarda da Constituição, cabendo-lhe: I - processar e julgar, originariamente: a) a ação direta de inconstitucionalidade de lei ou ato normativo federal ou estadual e a ação declaratória de constitucionalidade de lei ou ato normativo federal;', '1988-10-05', 15, 221),
('CF/88 — art. 103', 'Podem propor a ação direta de inconstitucionalidade e a ação declaratória de constitucionalidade: I - o Presidente da República; II - a Mesa do Senado Federal; III - a Mesa da Câmara dos Deputados; IV - a Mesa de Assembléia Legislativa ou da Câmara Legislativa do Distrito Federal; V - o Governador de Estado ou do Distrito Federal; VI - o Procurador-Geral da República; VII - o Conselho Federal da Ordem dos Advogados do Brasil; VIII - partido político com representação no Congresso Nacional; IX - confederação sindical ou entidade de classe de âmbito nacional.', '1988-10-05', 15, 221),
('Lei nº 9.868/1999 — art. 27', 'Ao declarar a inconstitucionalidade de lei ou ato normativo, e tendo em vista razões de segurança jurídica ou de excepcional interesse social, poderá o Supremo Tribunal Federal, por maioria de dois terços de seus membros, restringir os efeitos daquela declaração ou decidir que ela só tenha eficácia a partir de seu trânsito em julgado ou de outro momento que venha a ser fixado (modulação temporal dos efeitos).', '1999-11-10', 15, 221),
('Lei nº 9.882/1999 — art. 4º, § 1º', 'Não será admitida argüição de descumprimento de preceito fundamental quando houver qualquer outro meio eficaz de sanar a lesividade (princípio da subsidiariedade da ADPF).', '1999-12-03', 15, 221),

-- -----------------------------------------------------------------------------
-- DIREITO CONSTITUCIONAL (ID 15) — TÓPICO 122: Defesa do Estado e Instituições
-- -----------------------------------------------------------------------------
('CF/88 — art. 136', 'O Presidente da República pode, ouvidos o Conselho da República e o Conselho de Defesa Nacional, decretar estado de defesa na vigência do qual vigorarão medidas restritivas a direitos para preservar ou prontamente restabelecer, em locais certos e determinados, a ordem pública ou a paz social ameaçadas por grave e iminente instabilidade institucional ou atingidas por calamidades de grandes proporções na natureza.', '1988-10-05', 15, 122),
('CF/88 — art. 137', 'O Presidente da República pode, ouvidos o Conselho da República e o Conselho de Defesa Nacional, solicitar ao Congresso Nacional autorização para decretar o estado de sítio nos casos de: I - comoção grave de repercussão nacional ou ocorrência de fatos que comprovem a ineficácia de medida tomada durante o estado de defesa; II - declaração de estado de guerra ou resposta a agressão armada estrangeira.', '1988-10-05', 15, 122),
('CF/88 — art. 142', 'As Forças Armadas, constituídas pela Marinha, pelo Exército e pela Aeronáutica, são instituições nacionais permanentes e regulares, organizadas com base na hierarquia e na disciplina, sob a autoridade suprema do Presidente da República, e destinam-se à defesa da Pátria, à garantia dos poderes constitucionais e, por iniciativa de qualquer destes, da lei e da ordem.', '1988-10-05', 15, 122),

-- -----------------------------------------------------------------------------
-- DIREITO CONSTITUCIONAL (ID 15) — TÓPICO 247: Ordem Social
-- -----------------------------------------------------------------------------
('CF/88 — art. 194 e 195', 'A seguridade social compreende um conjunto integrado de ações de iniciativa dos Poderes Públicos e da sociedade, destinadas a assegurar os direitos relativos à saúde, à previdência e à assistência social. A seguridade social será financiada por toda a sociedade, de forma direta e indireta, mediante recursos dos orçamentos e de contribuições sociais do empregador, da folha, da receita/faturamento, do lucro líquido, do trabalhador e de concursos de prognósticos.', '1988-10-05', 15, 247),
('CF/88 — art. 196', 'A saúde é direito de todos e dever do Estado, garantido mediante políticas sociais e econômicas que visem à redução do risco de doença e de outros agravos e ao acesso universal e igualitário às ações e serviços para sua promoção, proteção e recuperação.', '1988-10-05', 15, 247),
('CF/88 — art. 225 (caput)', 'Todos têm direito ao meio ambiente ecologicamente equilibrado, bem de uso comum do povo e essencial à sadia qualidade de vida, impondo-se ao Poder Público e à coletividade o dever de defendê-lo e preservá-lo para as presentes e futuras gerações.', '1988-10-05', 15, 247),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 204: Competência Jurisdicional
-- -----------------------------------------------------------------------------
('CPP — art. 69 e 70', 'Determinará a competência jurisdicional: o lugar da infração; o domicílio ou residência do réu; a natureza da infração; a distribuição; a conexão ou continência; a prevenção; a prerrogativa de função. A competência será, de regra, determinada pelo lugar em que se consumar a infração, ou, no caso de tentativa, pelo lugar em que for praticado o último ato de execução.', '1941-10-13', 13, 204),
('CPP — art. 76', 'A competência será determinada pela conexão: I - se, ocorrendo duas ou mais infrações, houverem sido praticadas, ao mesmo tempo, por várias pessoas reunidas, ou por várias pessoas em concurso, embora diverso o tempo e o lugar, ou por várias pessoas, umas contra as outras; II - se, no mesmo caso, houverem sido umas praticadas para facilitar ou ocultar as outras, ou para conseguir impunidade ou vantagem em relação a qualquer delas; III - quando a prova de uma infração ou de qualquer de suas circunstâncias elementares influir na prova de outra infração.', '1941-10-13', 13, 204),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 81: Recursos e Habeas Corpus
-- -----------------------------------------------------------------------------
('CPP — art. 581 (caput)', 'Caberá recurso, no sentido estrito, da decisão, despacho ou sentença: I - que não receber a denúncia ou a queixa; IV - que pronunciar o réu; V - que conceder, negar, arbitrar, cassar ou julgar inidônea a fiança, indeferir requerimento de prisão preventiva ou revogá-la, conceder liberdade provisória ou relaxar a prisão em flagrante; VII - que julgar quebrada a fiança ou perdido o seu valor; VIII - que decretar a prescrição ou julgar, por outro modo, extinta a punibilidade.', '1941-10-13', 13, 81),
('CPP — art. 593', 'Caberá apelação no prazo de 5 (cinco) dias: I - das sentenças definitivas de condenação ou absolvição proferidas por juiz singular; II - das decisões definitivas, ou com força de definitivas, proferidas por juiz singular nos casos não previstos no Capítulo anterior; III - das decisões do Tribunal do Júri, quando: a) ocorrer nulidade posterior à pronúncia; b) for a sentença do juiz-presidente contrária à lei expressa ou à decisão dos jurados; c) houver erro ou injustiça no tocante à aplicação da pena; d) for a decisão dos jurados manifestamente contrária à prova dos autos.', '1941-10-13', 13, 81),
('CPP — art. 647 e 648', 'Dar-se-á habeas corpus sempre que alguém sofrer ou se achar ameaçado de sofrer violência ou coação em sua liberdade de locomoção, por ilegalidade ou abuso de poder. A coação considerar-se-á ilegal: I - quando não houver justa causa; II - quando alguém estiver preso por mais tempo do que determina a lei; III - quando quem ordenar a coação não tiver autoridade para fazê-lo; IV - quando houver cessado o motivo que autorizou a coação; VI - quando o processo for manifestamente nulo; VII - quando extinta a punibilidade.', '1941-10-13', 13, 81),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 153: Tribunal do Júri
-- -----------------------------------------------------------------------------
('CPP — art. 413, 414 e 415', 'O juiz, fundamentadamente, pronunciará o acusado, se convencido da materialidade do fato e da existência de indícios suficientes de autoria ou de participação. Não se convencendo da materialidade ou indícios, o juiz, fundamentadamente, impronunciará o acusado. O juiz absolverá desde logo o acusado (absolvição sumária), quando: provada a inexistência do fato; provado não ser ele autor ou partícipe; o fato não constituir infração penal; demonstrada causa de isenção de pena ou exclusão do crime.', '2008-06-09', 13, 153),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 220: Nulidades
-- -----------------------------------------------------------------------------
('CPP — art. 563 e 564', 'Nenhum ato será declarado nulo, se da nulidade não resultar prejuízo para a acusação ou para a defesa (pas de nullité sans grief). A nulidade ocorrerá nos seguintes casos: I - por incompetência, suspeição ou suborno do juiz; II - por ilegitimidade de parte; III - por falta das fórmulas ou dos termos seguintes: da denúncia ou da queixa; do exame do corpo de delito nos crimes que deixam vestígios; da nomeação de defensor ao réu presente ou ausente; da intervenção do Ministério Público.', '1941-10-13', 13, 220),

-- -----------------------------------------------------------------------------
-- LEGISLAÇÃO PENAL ESPECIAL (ID 19) — TÓPICO 128: Lavagem de Dinheiro
-- -----------------------------------------------------------------------------
('Lei nº 9.613/1998 — art. 1º (caput)', 'Ocultar ou dissimular a natureza, origem, localização, disposição, movimentação ou propriedade de bens, direitos ou valores provenientes, direta ou indiretamente, de infração penal. Pena: reclusão, de 3 (três) a 10 (dez) anos, e multa.', '1998-03-03', 19, 128),
('Lei nº 9.613/1998 — art. 2º, II e art. 4º', 'O processo e julgamento dos crimes previstos nesta Lei independem do processo e julgamento das infrações penais antecedentes, ainda que praticadas em outro país, cabendo ao juiz competente a decisão sobre a existência da infração penal antecedente. Havendo indícios suficientes de infração penal, o juiz poderá decretar medidas assecuratórias de bens, direitos ou valores do investigado ou acusado, ou existentes em nome de interpostas pessoas.', '1998-03-03', 19, 128),

-- -----------------------------------------------------------------------------
-- LEGISLAÇÃO PENAL ESPECIAL (ID 19 / 38) — TÓPICO 102/275: Crimes Ambientais
-- -----------------------------------------------------------------------------
('Lei nº 9.605/1998 — art. 2º e 3º', 'Quem, de qualquer forma, concorre para a prática dos crimes previstos nesta Lei, incide nas penas a estes cominadas, na medida da sua culpabilidade, bem como diretores, administradores e gerentes que, sabendo da conduta criminosa de outrem, deixarem de agir para evitá-la. As pessoas jurídicas serão responsabilizadas administrativa, civil e penalmente nos casos em que a infração seja cometida por decisão de seu representante legal ou contratual, ou de seu órgão colegiado, no interesse ou benefício da sua entidade.', '1998-02-12', 19, 102),

-- -----------------------------------------------------------------------------
-- LEGISLAÇÃO PENAL ESPECIAL (ID 19) — TÓPICO 174: Crimes Tributários
-- -----------------------------------------------------------------------------
('Lei nº 8.137/1990 — art. 1º', 'Constitui crime contra a ordem tributária suprimir ou reduzir tributo, ou contribuição social e qualquer acessório, mediante: omitir informação, ou prestar declaração falsa às autoridades fazendárias; fraudar a fiscalização tributária, inserindo elementos inexatos; falsificar ou alterar nota fiscal. Pena: reclusão de 2 a 5 anos, e multa. (Súmula Vinculante 24 do STF: Não se tipifica crime material contra a ordem tributária antes do lançamento definitivo do tributo).', '1990-12-27', 19, 174),

-- -----------------------------------------------------------------------------
-- SEGURANÇA PÚBLICA (ID 48) — TÓPICOS 486, 485 e 488
-- -----------------------------------------------------------------------------
('Lei nº 13.675/2018 — art. 9º (SUSP)', 'É instituído o Sistema Único de Segurança Pública (Susp), que tem como órgãos operacionais: I - Polícia Federal; II - Polícia Rodoviária Federal; III - polícias civis; IV - polícias militares; V - corpos de bombeiros militares; VI - guardas municipais; VII - órgãos do sistema penitenciário (polícias penais); VIII - institutos de criminalística, de medicina legal e de identificação.', '2018-06-11', 48, 486),
('Lei nº 14.735/2023 — art. 1º e 3º (LONPC)', 'Esta Lei institui a Lei Orgânica Nacional das Polícias Civis. São princípios institucionais das polícias civis: proteção da dignidade da pessoa humana e direitos humanos; legalidade, impessoalidade, moralidade, publicidade e eficiência; hierarquia e disciplina; indivisibilidade da investigação criminal; autonomia técnico-científica na apuração infracional penal.', '2023-11-23', 48, 485),
('Lei nº 14.967/2024 — art. 1º e 3º (Estatuto da Segurança Privada)', 'Esta Lei institui o Estatuto da Segurança Privada e da Segurança das Instituições Financeiras. São serviços de segurança privada: vigilância patrimonial; transporte de valores; escolta armada; segurança pessoal; e segurança em eventos sociais e desportivos, exercidos em caráter complementar à segurança pública exercida pelo Estado, sob fiscalização da Polícia Federal.', '2024-09-09', 48, 488),

-- -----------------------------------------------------------------------------
-- PROTEÇÃO A GRUPOS VULNERÁVEIS (ID 61) — TÓPICOS 475, 480 e 481
-- -----------------------------------------------------------------------------
('Lei nº 13.146/2015 — art. 2º e 84 (PCD)', 'Considera-se pessoa com deficiência aquela que tem impedimento de longo prazo de natureza física, mental, intelectual ou sensorial, o qual, em interação com uma ou mais barreiras, pode obstruir sua participação plena e efetiva na sociedade em igualdade de condições. A avaliação da deficiência, quando necessária, será biopsicossocial. A pessoa com deficiência tem assegurado o direito ao exercício de sua capacidade legal em igualdade de condições; a curatela constituirá medida extraordinária afetando tão somente atos patrimoniais e negociais.', '2015-07-06', 61, 475),
('Lei nº 10.741/2003 — art. 1º e 3º (Pessoa Idosa)', 'É instituído o Estatuto da Pessoa Idosa, destinado a regular os direitos assegurados às pessoas com idade igual ou superior a 60 (sessenta) anos. Dentre os idosos, é assegurada prioridade especial aos maiores de 80 (oitenta) anos, atendendo-se suas necessidades sempre preferencialmente em relação aos demais idosos. (Redação da Lei nº 14.423/2022 e Lei nº 13.466/2017)', '2003-10-01', 61, 480),
('Lei nº 12.288/2010 — art. 1º (Igualdade Racial)', 'Esta Lei institui o Estatuto da Igualdade Racial, destinado a garantir à população negra a efetivação da igualdade de oportunidades, a defesa dos direitos étnicos individuais, coletivos e difusos e o combate à discriminação. Considera-se discriminação racial toda distinção, exclusão, restrição ou preferência baseada em raça, cor, descendência ou origem nacional ou étnica; e ações afirmativas os programas para correção de desigualdades.', '2010-07-20', 61, 481),

-- -----------------------------------------------------------------------------
-- LEGISLAÇÃO DE TRÂNSITO (ID 59) — TÓPICOS 463 e 467: Circulação e Infrações
-- -----------------------------------------------------------------------------
('CTB — art. 29 (caput)', 'O trânsito de veículos nas vias terrestres abertas à circulação obedecerá às seguintes normas: a circulação far-se-á sempre pelo lado direito da via; o condutor deverá guardar distância de segurança lateral e frontal; quando veículos, transitando por fluxos que se cruzem, se aproximarem de local não sinalizado, terá preferência de passagem: rodovia (quem estiver circulando por ela); rotatória (quem estiver nela); nos demais casos, o que vier pela direita do condutor.', '1997-09-23', 59, 463),
('CTB — art. 165 e 165-A', 'Dirigir sob a influência de álcool ou recusar-se a ser submetido a teste de alcoolemia (bafômetro): Infração gravíssima; Penalidade: multa (dez vezes) e suspensão do direito de dirigir por 12 meses; Medida administrativa: recolhimento da habilitação e retenção do veículo.', '1997-09-23', 59, 467),
('CTB — art. 256', 'A autoridade de trânsito deverá aplicar, às infrações previstas neste Código, as seguintes penalidades: I - advertência por escrito; II - multa; III - suspensão do direito de dirigir; IV - cassação da Carteira Nacional de Habilitação; V - cassação da Permissão para Dirigir; VI - freqüência obrigatória em curso de reciclagem.', '1997-09-23', 59, 467),

-- -----------------------------------------------------------------------------
-- DIREITO PREVIDENCIÁRIO (ID 35) — TÓPICO 258: RGPS
-- -----------------------------------------------------------------------------
('CF/88 — art. 201 (caput)', 'A previdência social será organizada sob a forma do Regime Geral de Previdência Social, de caráter contributivo e de filiação obrigatória, observados critérios que preservem o equilíbrio financeiro e atuarial. É vedada a adoção de requisitos diferenciados para benefícios, ressalvadas hipóteses de trabalhadores com deficiência ou atividades sob condições especiais.', '1988-10-05', 35, 258),
('Lei nº 8.213/1991 — art. 11 e 16', 'São segurados obrigatórios da Previdência Social: empregado, empregado doméstico, contribuinte individual, trabalhador avulso e segurado especial (produtor rural em regime de economia familiar). São dependentes: classe I (cônjuge, companheiro e filhos menores de 21 anos ou inválidos); classe II (pais); classe III (irmãos menores de 21 anos ou inválidos). A existência de dependente de qualquer classe exclui os das classes seguintes.', '1991-07-24', 35, 258),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL CIVIL (ID 33) — TÓPICO 355: Tutelas e Audiência
-- -----------------------------------------------------------------------------
('CPC/2015 — art. 300', 'A tutela de urgência será concedida quando houver elementos que evidenciem a probabilidade do direito e o perigo de dano ou o risco ao resultado útil do processo. Não será concedida a tutela de urgência de natureza antecipada quando houver perigo de irreversibilidade dos efeitos da decisão.', '2015-03-16', 33, 355),
('CPC/2015 — art. 311', 'A tutela da evidência será concedida, independentemente da demonstração de perigo de dano ou de risco ao resultado útil do processo, quando: I - ficar caracterizado o abuso do direito de defesa ou o manifesto propósito protelatório da parte; II - as alegações de fato puderem ser comprovadas apenas documentalmente e houver tese firmada em julgamento de casos repetitivos ou em súmula vinculante; III - pedido reipersecutório fundado em contrato de depósito; IV - petição inicial instruída com prova documental suficiente a que o réu não oponha dúvida razoável.', '2015-03-16', 33, 355),
('CPC/2015 — art. 334', 'Se a petição inicial preencher os requisitos essenciais, o juiz designará audiência de conciliação ou de mediação com antecedência mínima de 30 dias, devendo ser citado o réu com pelo menos 20 dias de antecedência. A audiência não será realizada se ambas as partes manifestarem, expressamente, desinteresse na composição consensual, ou quando não se admitir a autocomposição.', '2015-03-16', 33, 355)

on conflict (referencia) do update set 
    texto = excluded.texto, 
    vigencia_de = excluded.vigencia_de, 
    id_materia = excluded.id_materia, 
    id_topico = excluded.id_topico;
