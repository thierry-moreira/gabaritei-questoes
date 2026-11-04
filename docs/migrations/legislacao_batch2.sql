-- =============================================================================
-- RAG leve de legislação — Corpus Curado (Batch 2)
-- Matérias: Direito Penal (ID 12) e Direito Processual Penal (ID 13)
-- Arquivo: docs/migrations/legislacao_batch2.sql
--
-- Aplicar no Supabase (SQL Editor ou pipeline administrativo com service_role).
-- Mapeamento rigoroso com a taxonomia real (public.materias e public.topicos).
-- Idempotente: on conflict (referencia) do update.
-- =============================================================================

insert into public.legislacao_artigos (referencia, texto, vigencia_de, id_materia, id_topico) values

-- -----------------------------------------------------------------------------
-- DIREITO PENAL (ID 12) — TÓPICO 71: Aplicação da Lei Penal (Decreto-Lei nº 2.848/1940)
-- -----------------------------------------------------------------------------
('CP — art. 1º', 'Não há crime sem lei anterior que o defina. Não há pena sem prévia cominação legal.', '1940-12-07', 12, 71),
('CP — art. 2º (caput)', 'Ninguém pode ser punido por fato que lei posterior deixa de considerar crime, cessando em virtude dela a execução e os efeitos penais da sentença condenatória.', '1940-12-07', 12, 71),
('CP — art. 2º, parágrafo único', 'A lei posterior, que de qualquer modo favorecer o agente, aplica-se aos fatos anteriores, ainda que decididos por sentença condenatória transitada em julgado.', '1984-07-11', 12, 71),
('CP — art. 3º', 'A lei excepcional ou temporária, embora decorrido o período de sua duração ou cessadas as circunstâncias que a determinaram, aplica-se ao fato praticado durante sua vigência.', '1984-07-11', 12, 71),
('CP — art. 4º', 'Considera-se praticado o crime no momento da ação ou omissão, ainda que outro seja o momento do resultado.', '1984-07-11', 12, 71),
('CP — art. 5º (caput)', 'Aplica-se a lei brasileira, sem prejuízo de convenções, tratados e regras de direito internacional, ao crime cometido no território nacional.', '1984-07-11', 12, 71),
('CP — art. 5º, § 1º', 'Para os efeitos penais, consideram-se como extensão do território nacional as embarcações e aeronaves brasileiras, de natureza pública ou a serviço do governo brasileiro onde quer que se encontrem, bem como as aeronaves e as embarcações brasileiras, mercantes ou de propriedade privada, que se achem, respectivamente, no espaço aéreo correspondente ou em alto-mar.', '1984-07-11', 12, 71),
('CP — art. 5º, § 2º', 'É também aplicável a lei brasileira aos crimes praticados a bordo de aeronaves ou embarcações estrangeiras de propriedade privada, achando-se aquelas em pouso no território nacional ou em vôo no espaço aéreo correspondente, e estas em porto ou mar territorial do Brasil.', '1984-07-11', 12, 71),
('CP — art. 6º', 'Considera-se praticado o crime no lugar em que ocorreu a ação ou omissão, no todo ou em parte, bem como onde se produziu ou deveria produzir-se o resultado.', '1984-07-11', 12, 71),
('CP — art. 7º, I', 'Ficam sujeitos à lei brasileira, embora cometidos no estrangeiro: I - os crimes: a) contra a vida ou a liberdade do Presidente da República; b) contra o patrimônio ou a fé pública da União, do Distrito Federal, de Estado, de Território, de Município, de empresa pública, sociedade de economia mista, autarquia ou fundação instituída pelo Poder Público; c) contra a administração pública, por quem está a seu serviço; d) de genocídio, quando o agente for brasileiro ou domiciliado no Brasil;', '1984-07-11', 12, 71),
('CP — art. 7º, II', 'Ficam sujeitos à lei brasileira, embora cometidos no estrangeiro: II - os crimes: a) que, por tratado ou convenção, o Brasil se obrigou a reprimir; b) praticados por brasileiro; c) praticados em aeronaves ou embarcações brasileiras, mercantes ou de propriedade privada, quando em território estrangeiro e aí não sejam julgados.', '1984-07-11', 12, 71),
('CP — art. 8º', 'A pena cumprida no estrangeiro atenua a pena imposta no Brasil pelo mesmo crime, quando diversas, ou nela é computada, quando idênticas.', '1984-07-11', 12, 71),
('CP — art. 10', 'O dia do começo inclui-se no cômputo do prazo. Contam-se os dias, os meses e os anos pelo calendário comum.', '1984-07-11', 12, 71),

-- -----------------------------------------------------------------------------
-- DIREITO PENAL (ID 12) — TÓPICO 72: Teoria Geral do Crime (Decreto-Lei nº 2.848/1940)
-- -----------------------------------------------------------------------------
('CP — art. 13 (caput)', 'O resultado, de que depende a existência do crime, somente é imputável a quem lhe deu causa. Considera-se causa a ação ou omissão sem a qual o resultado não teria ocorrido.', '1984-07-11', 12, 72),
('CP — art. 13, § 1º', 'A superveniência de causa relativamente independente exclui a imputação quando, por si só, produziu o resultado; os fatos anteriores, entretanto, imputam-se a quem os praticou.', '1984-07-11', 12, 72),
('CP — art. 13, § 2º', 'A omissão é penalmente relevante quando o omitente devia e podia agir para evitar o resultado. O dever de agir incumbe a quem: a) tenha por lei obrigação de cuidado, proteção ou vigilância; b) de outra forma, assumiu a responsabilidade de impedir o resultado; c) com seu comportamento anterior, criou o risco da ocorrência do resultado.', '1984-07-11', 12, 72),
('CP — art. 14, I', 'Diz-se o crime: I - consumado, quando nele se reúnem todos os elementos de sua definição legal;', '1984-07-11', 12, 72),
('CP — art. 14, II', 'Diz-se o crime: II - tentado, quando, iniciada a execução, não se consuma por circunstâncias alheias à vontade do agente.', '1984-07-11', 12, 72),
('CP — art. 14, parágrafo único', 'Salvo disposição em contrário, pune-se a tentativa com a pena correspondente ao crime consumado, diminuída de um a dois terços.', '1984-07-11', 12, 72),
('CP — art. 15', 'O agente que, voluntariamente, desiste de prosseguir na execução ou impede que o resultado se produza, só responde pelos atos já praticados.', '1984-07-11', 12, 72),
('CP — art. 16', 'Nos crimes cometidos sem violência ou grave ameaça à pessoa, reparado o dano ou restituída a coisa, até o recebimento da denúncia ou da queixa, por ato voluntário do agente, a pena será reduzida de um a dois terços.', '1984-07-11', 12, 72),
('CP — art. 17', 'Não se pune a tentativa quando, por ineficácia absoluta do meio ou por absoluta impropriedade do objeto, é impossível consumar-se o crime.', '1984-07-11', 12, 72),
('CP — art. 18, I', 'Diz-se o crime: I - doloso, quando o agente quis o resultado ou assumiu o risco de produzi-lo;', '1984-07-11', 12, 72),
('CP — art. 18, II', 'Diz-se o crime: II - culposo, quando o agente deu causa ao resultado por imprudência, negligência ou imperícia.', '1984-07-11', 12, 72),
('CP — art. 18, parágrafo único', 'Salvo os casos expressos em lei, ninguém pode ser punido por fato previsto como crime, senão quando o pratica dolosamente.', '1984-07-11', 12, 72),
('CP — art. 20 (caput)', 'O erro sobre elemento constitutivo do tipo legal de crime exclui o dolo, mas permite a punição por crime culposo, se previsto em lei.', '1984-07-11', 12, 72),
('CP — art. 20, § 1º', 'É isento de pena quem, por erro plenamente justificado pelas circunstâncias, supõe situação de fato que, se existisse, tornaria a ação legítima. Não há isenção de pena quando o erro deriva de culpa e o fato é punível como crime culposo.', '1984-07-11', 12, 72),
('CP — art. 21', 'O desconhecimento da lei é inescusável. O erro sobre a ilicitude do fato, se inevitável, isenta de pena; se evitável, poderá diminuí-la de um sexto a um terço.', '1984-07-11', 12, 72),
('CP — art. 22', 'Se o fato é cometido sob coação irresistível ou em estrita obediência a ordem, não manifestamente ilegal, de superior hierárquico, só é punível o autor da coação ou da ordem.', '1984-07-11', 12, 72),
('CP — art. 23', 'Não há crime quando o agente pratica o fato: I - em estado de necessidade; II - em legítima defesa; III - em estrito cumprimento de dever legal ou no exercício regular de direito. Parágrafo único - O agente, em qualquer das hipóteses deste artigo, responderá pelo excesso doloso ou culposo.', '1984-07-11', 12, 72),
('CP — art. 24', 'Considera-se em estado de necessidade quem pratica o fato para salvar de perigo atual, que não provocou por sua vontade, nem podia de outro modo evitar, direito próprio ou alheio, cujo sacrifício, nas circunstâncias, não era razoável exigir-se.', '1984-07-11', 12, 72),
('CP — art. 25', 'Entende-se em legítima defesa quem, usando moderadamente dos meios necessários, repele injusta agressão, atual ou iminente, a direito seu ou de outrem.', '1984-07-11', 12, 72),
('CP — art. 26 (caput)', 'É isento de pena o agente que, por doença mental ou desenvolvimento mental incompleto ou retardado, era, ao tempo da ação ou da omissão, inteiramente incapaz de entender o caráter ilícito do fato ou de determinar-se de acordo com esse entendimento.', '1984-07-11', 12, 72),
('CP — art. 27', 'Os menores de 18 (dezoito) anos são penalmente inimputáveis, ficando sujeitos às normas estabelecidas na legislação especial.', '1984-07-11', 12, 72),
('CP — art. 28, I', 'Não excluem a imputabilidade penal: I - a emoção ou a paixão;', '1984-07-11', 12, 72),
('CP — art. 28, II', 'Não excluem a imputabilidade penal: II - a embriaguez, voluntária ou culposa, pelo álcool ou substância de efeitos análogos. § 1º É isento de pena o agente que, por embriaguez completa, proveniente de caso fortuito ou força maior, era, ao tempo da ação ou da omissão, inteiramente incapaz de entender o caráter ilícito do fato ou de determinar-se de acordo com esse entendimento.', '1984-07-11', 12, 72),

-- -----------------------------------------------------------------------------
-- DIREITO PENAL (ID 12) — TÓPICO 69: Crimes Contra a Pessoa (Decreto-Lei nº 2.848/1940)
-- -----------------------------------------------------------------------------
('CP — art. 121 (caput)', 'Matar alguém: Pena - reclusão, de seis a vinte anos.', '1940-12-07', 12, 69),
('CP — art. 121, § 1º', 'Se o agente comete o crime impelido por motivo de relevante valor social ou moral, ou sob o domínio de violenta emoção, logo em seguida a injusta provocação da vítima, o juiz pode reduzir a pena de um sexto a um terço.', '1940-12-07', 12, 69),
('CP — art. 121, § 2º', 'Se o homicídio é cometido: I - mediante paga ou promessa de recompensa, ou por outro motivo torpe; II - por motivo fútil; III - com emprego de veneno, fogo, explosivo, asfixia, tortura ou outro meio insidioso ou cruel, ou de que possa resultar perigo comum; IV - à traição, de emboscada, ou mediante dissimulação ou outro recurso que dificulte ou torne impossível a defesa do ofendido; V - para assegurar a execução, a ocultação, a impunidade ou a vantagem de outro crime; VII - contra autoridade ou agente descrito nos arts. 142 e 144 da Constituição Federal, integrantes do sistema prisional e da Força Nacional de Segurança Pública, no exercício da função ou em razão dela; VIII - com emprego de arma de fogo de uso restrito ou proibido; IX - contra menor de 14 anos: Pena - reclusão, de doze a trinta anos.', '1940-12-07', 12, 69),
('CP — art. 121-A (caput; incluído pela Lei nº 14.994/2024)', 'Matar mulher por razões da condição do sexo feminino: Pena - reclusão, de 20 (vinte) a 40 (quarenta) anos. § 1º Considera-se que há razões da condição do sexo feminino quando o crime envolve: I - violência doméstica e familiar; II - menosprezo ou discriminação à condição de mulher. (Incluído pela Lei nº 14.994, de 2024)', '2024-10-09', 12, 69),
('CP — art. 129 (caput)', 'Ofender a integridade corporal ou a saúde de outrem: Pena - detenção, de três meses a um ano.', '1940-12-07', 12, 69),
('CP — art. 129, § 1º', 'Se resulta: I - incapacidade para as ocupações habituais, por mais de trinta dias; II - perigo de vida; III - debilidade permanente de membro, sentido ou função; IV - aceleração de parto: Pena - reclusão, de um a cinco anos.', '1940-12-07', 12, 69),
('CP — art. 129, § 2º', 'Se resulta: I - Incapacidade permanente para o trabalho; II - Enfermidade incurável; III - Perda ou inutilização do membro, sentido ou função; IV - Deformidade permanente; V - Aborto: Pena - reclusão, de dois a oito anos.', '1940-12-07', 12, 69),

-- -----------------------------------------------------------------------------
-- DIREITO PENAL (ID 12) — TÓPICO 74: Crimes Contra a Administração Pública
-- -----------------------------------------------------------------------------
('CP — art. 312 (caput)', 'Apropriar-se o funcionário público de dinheiro, valor ou qualquer outro bem móvel, público ou particular, de que tem a posse em razão do cargo, ou desviá-lo, em proveito próprio ou alheio: Pena - reclusão, de dois a doze anos, e multa.', '1940-12-07', 12, 74),
('CP — art. 312, § 1º', 'Aplica-se a mesma pena, se o funcionário público, embora não tendo a posse do dinheiro, valor ou bem, o subtrai, ou concorre para que seja subtraído, em proveito próprio ou alheio, valendo-se de facilidade que lhe proporciona a qualidade de funcionário.', '1940-12-07', 12, 74),
('CP — art. 312, § 2º', 'Se o funcionário concorre culposamente para o crime de outrem: Pena - detenção, de três meses a um ano.', '1940-12-07', 12, 74),
('CP — art. 312, § 3º', 'No caso do § 2º, a reparação do dano, se precede à sentença irrecorrível, extingue a punibilidade; se lhe é posterior, reduz de metade a pena imposta.', '1940-12-07', 12, 74),
('CP — art. 313', 'Apropriar-se de dinheiro ou qualquer utilidade que, no exercício do cargo, recebeu por erro de outrem: Pena - reclusão, de um a quatro anos, e multa.', '1940-12-07', 12, 74),
('CP — art. 313-A', 'Inserir ou facilitar, o funcionário autorizado, a inserção de dados falsos, alterar ou excluir indevidamente dados corretos nos sistemas informatizados ou bancos de dados da Administração Pública com o fim de obter vantagem indevida para si ou para outrem ou para causar dano: Pena - reclusão, de 2 a 12 anos, e multa.', '2000-10-19', 12, 74),
('CP — art. 316 (caput)', 'Exigir, para si ou para outrem, direta ou indiretamente, ainda que fora da função ou antes de assumi-la, mas em razão dela, vantagem indevida: Pena - reclusão, de 2 a 12 anos, e multa.', '1940-12-07', 12, 74),
('CP — art. 316, § 1º', 'Se o funcionário exige tributo ou contribuição social que sabe ou deveria saber indevido, ou, quando devido, emprega na cobrança meio vexatório ou gravoso, que a lei não autoriza: Pena - reclusão, de 3 a 8 anos, e multa.', '1940-12-07', 12, 74),
('CP — art. 317 (caput)', 'Solicitar ou receber, para si ou para outrem, direta ou indiretamente, ainda que fora da função ou antes de assumi-la, mas em razão dela, vantagem indevida, ou aceitar promessa de tal vantagem: Pena - reclusão, de 2 a 12 anos, e multa.', '1940-12-07', 12, 74),
('CP — art. 317, § 1º', 'A pena é aumentada de um terço, se, em conseqüência da vantagem ou promessa, o funcionário retarda ou deixa de praticar qualquer ato de ofício ou o pratica infringindo dever funcional.', '1940-12-07', 12, 74),
('CP — art. 317, § 2º', 'Se o funcionário pratica, deixa de praticar ou retarda ato de ofício, com infração de dever funcional, cedendo a pedido ou influência de outrem: Pena - detenção, de três meses a um ano, ou multa.', '1940-12-07', 12, 74),
('CP — art. 319', 'Retardar ou deixar de praticar, indevidamente, ato de ofício, ou praticá-lo contra disposição expressa de lei, para satisfazer interesse ou sentimento pessoal: Pena - detenção, de três meses a um ano, e multa.', '1940-12-07', 12, 74),
('CP — art. 319-A', 'Deixar o Diretor de Penitenciária e/ou agente público, de cumprir seu dever de vedar ao preso o acesso a aparelho telefônico, de rádio ou similar, que permita a comunicação com outros presos ou com o ambiente externo: Pena - detenção, de 3 meses a 1 ano.', '2007-03-29', 12, 74),
('CP — art. 320', 'Deixar o funcionário, por indulgência, de responsabilizar subordinado que cometeu infração no exercício do cargo ou, quando lhe falte competência, não levar o fato ao conhecimento da autoridade competente: Pena - detenção, de quinze dias a um mês, ou multa.', '1940-12-07', 12, 74),
('CP — art. 321', 'Patrocinar, direta ou indiretamente, interesse privado perante a administração pública, valendo-se da qualidade de funcionário: Pena - detenção, de um a três meses, ou multa.', '1940-12-07', 12, 74),
('CP — art. 327 (caput)', 'Considera-se funcionário público, para os efeitos penais, quem, embora transitoriamente ou sem remuneração, exerce cargo, emprego ou função pública.', '1940-12-07', 12, 74),
('CP — art. 327, § 1º', 'Equipara-se a funcionário público quem exerce cargo, emprego ou função em entidade paraestatal, e quem trabalha para empresa prestadora de serviço contratada ou conveniada para a execução de atividade típica da Administração Pública.', '2000-10-19', 12, 74),
('CP — art. 327, § 2º', 'A pena será aumentada da terça parte quando os autores dos crimes previstos neste Capítulo forem ocupantes de cargos em comissão ou de função de direção ou assessoramento de órgãos da administração direta, sociedade de economia mista, empresa pública ou fundação instituída pelo poder público.', '2000-10-19', 12, 74),
('CP — art. 328', 'Usurpar o exercício de função pública: Pena - detenção, de três meses a dois anos, e multa.', '1940-12-07', 12, 74),
('CP — art. 329', 'Opor-se à execução de ato legal, mediante violência ou ameaça a funcionário competente para executá-lo ou a quem lhe esteja prestando auxílio: Pena - detenção, de dois meses a dois anos.', '1940-12-07', 12, 74),
('CP — art. 330', 'Desobedecer a ordem legal de funcionário público: Pena - detenção, de quinze dias a seis meses, e multa.', '1940-12-07', 12, 74),
('CP — art. 331', 'Desacatar funcionário público no exercício da função ou em razão dela: Pena - detenção, de seis meses a dois anos, ou multa.', '1940-12-07', 12, 74),
('CP — art. 333 (caput)', 'Oferecer ou prometer vantagem indevida a funcionário público, para determiná-lo a praticar, omitir ou retardar ato de ofício: Pena – reclusão, de 2 a 12 anos, e multa.', '1940-12-07', 12, 74),

-- -----------------------------------------------------------------------------
-- DIREITO PENAL (ID 12) — TÓPICO 98: Crimes Contra o Patrimônio
-- -----------------------------------------------------------------------------
('CP — art. 155 (caput)', 'Subtrair, para si ou para outrem, coisa alheia móvel: Pena - reclusão, de um a quatro anos, e multa.', '1940-12-07', 12, 98),
('CP — art. 155, § 1º', 'A pena aumenta-se de um terço, se o crime é praticado durante o repouso noturno.', '1940-12-07', 12, 98),
('CP — art. 155, § 2º', 'Se o criminoso é primário, e é de pequeno valor a coisa furtada, o juiz pode substituir a pena de reclusão pela de detenção, diminuí-la de um a dois terços, ou aplicar somente a pena de multa.', '1940-12-07', 12, 98),
('CP — art. 155, § 4º', 'A pena é de reclusão de dois a oito anos, e multa, se o crime é cometido: I - com destruição ou rompimento de obstáculo à subtração da coisa; II - com abuso de confiança, ou mediante fraude, escalada ou destreza; III - com emprego de chave falsa; IV - mediante concurso de duas ou mais pessoas.', '1940-12-07', 12, 98),
('CP — art. 157 (caput)', 'Subtrair coisa móvel alheia, para si ou para outrem, mediante grave ameaça ou violência a pessoa, ou depois de havê-la, por qualquer meio, reduzido à impossibilidade de resistência: Pena - reclusão, de quatro a dez anos, e multa.', '1940-12-07', 12, 98),
('CP — art. 157, § 1º', 'Na mesma pena incorre quem, logo depois de subtraída a coisa, emprega violência contra pessoa ou grave ameaça, a fim de assegurar a impunidade do crime ou a detenção da coisa para si ou para terceiro.', '1940-12-07', 12, 98),
('CP — art. 157, § 2º', 'A pena aumenta-se de 1/3 (um terço) até metade: II - se há o concurso de duas ou mais pessoas; VII - se a violência ou grave ameaça é exercida com emprego de arma branca;', '2019-12-24', 12, 98),
('CP — art. 157, § 2º-A, I', 'A pena aumenta-se de 2/3 (dois terços): I – se a violência ou ameaça é exercida com emprego de arma de fogo;', '2018-04-23', 12, 98),
('CP — art. 157, § 3º, II', 'Se da violência resulta: II – morte, a pena é de reclusão de 20 (vinte) a 30 (trinta) anos, e multa (latrocínio).', '2018-04-23', 12, 98),
('CP — art. 168 (caput)', 'Apropriar-se de coisa alheia móvel, de que tem a posse ou a detenção: Pena - reclusão, de um a quatro anos, e multa.', '1940-12-07', 12, 98),
('CP — art. 171 (caput)', 'Obter, para si ou para outrem, vantagem ilícita, em prejuízo alheio, induzindo ou mantendo alguém em erro, mediante artifício, ardil, ou qualquer outro meio fraudulento: Pena - reclusão, de um a cinco anos, e multa.', '1940-12-07', 12, 98),
('CP — art. 171, § 5º', 'Somente se procede mediante representação, salvo se a vítima for: I - a Administração Pública, direta ou indireta; II - criança ou adolescente; III - pessoa com deficiência mental; ou IV - maior de 70 (setenta) anos ou incapaz.', '2019-12-24', 12, 98),
('CP — art. 180 (caput)', 'Adquirir, receber, transportar, conduzir ou ocultar, em proveito próprio ou alheio, coisa que sabe ser produto de crime, ou influir para que terceiro, de boa-fé, a adquira, receba ou oculte: Pena - reclusão, de um a quatro anos, e multa.', '1940-12-07', 12, 98),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 539: Juiz das Garantias (Decreto-Lei nº 3.689/1941)
-- -----------------------------------------------------------------------------
('CPP — art. 3º-A', 'O processo penal terá estrutura acusatória, vedadas a iniciativa do juiz na fase de investigação e a substituição da atuação probatória do órgão de acusação.', '2019-12-24', 13, 539),
('CPP — art. 3º-B (caput)', 'O juiz das garantias é responsável pelo controle da legalidade da investigação criminal e pela salvaguarda dos direitos individuais cuja franquia tenha sido reservada à autorização prévia do Poder Judiciário.', '2019-12-24', 13, 539),
('CPP — art. 3º-C (caput)', 'A competência do juiz das garantias abrange todas as infrações penais, exceto as de menor potencial ofensivo, e cessa com o recebimento da denúncia ou queixa na forma do art. 399 deste Código.', '2019-12-24', 13, 539),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 99: Inquérito Policial (Decreto-Lei nº 3.689/1941)
-- -----------------------------------------------------------------------------
('CPP — art. 4º (caput)', 'A polícia judiciária será exercida pelas autoridades policiais no território de suas respectivas circunscrições e terá por fim a apuração das infrações penais e da sua autoria.', '1941-10-03', 13, 99),
('CPP — art. 4º, parágrafo único', 'A competência definida neste artigo não excluirá a de autoridades administrativas, a quem por lei seja cometida a mesma função.', '1941-10-03', 13, 99),
('CPP — art. 5º, I', 'Nos crimes de ação pública o inquérito policial será iniciado: I - de ofício;', '1941-10-03', 13, 99),
('CPP — art. 5º, II', 'Nos crimes de ação pública o inquérito policial será iniciado: II - mediante requisição da autoridade judiciária ou do Ministério Público, ou a requerimento do ofendido ou de quem tiver qualidade para representá-lo.', '1941-10-03', 13, 99),
('CPP — art. 5º, § 4º', 'O inquérito, nos crimes em que a ação pública depender de representação, não poderá sem ela ser iniciado.', '1941-10-03', 13, 99),
('CPP — art. 5º, § 5º', 'Nos crimes de ação privada, a autoridade policial somente poderá proceder a inquérito a requerimento de quem tenha qualidade para intentá-la.', '1941-10-03', 13, 99),
('CPP — art. 6º', 'Logo que tiver conhecimento da prática da infração penal, a autoridade policial deverá: I - dirigir-se ao local, providenciando para que não se alterem o estado e conservação das coisas, até a chegada dos peritos criminais; II - apreender os objetos que tiverem relação com o fato, após liberados pelos peritos criminais; III - colher todas as provas que servirem para o esclarecimento do fato e suas circunstâncias; IV - ouvir o ofendido; V - ouvir o indiciado; VI - proceder a reconhecimento de pessoas e coisas e a acareações; VII - determinar, se for caso, que se proceda a exame de corpo de delito e a quaisquer outras perícias.', '1941-10-03', 13, 99),
('CPP — art. 9º', 'Todas as peças do inquérito policial serão, num só processado, reduzidas a escrito ou datilografadas e, neste caso, rubricadas pela autoridade.', '1941-10-03', 13, 99),
('CPP — art. 10 (caput)', 'O inquérito deverá terminar no prazo de 10 dias, se o indiciado tiver sido preso em flagrante, ou estiver preso preventivamente, contado o prazo, nesta hipótese, a partir do dia em que se executar a ordem de prisão, ou no prazo de 30 dias, quando estiver solto, mediante fiança ou sem ela.', '1941-10-03', 13, 99),
('CPP — art. 10, § 3º', 'Quando o fato for de difícil elucidação, e o indiciado estiver solto, a autoridade poderá requerer ao juiz a devolução dos autos, para ulteriores diligências, que serão realizadas no prazo marcado pelo juiz.', '1941-10-03', 13, 99),
('CPP — art. 14', 'O ofendido, ou seu representante legal, e o indiciado poderão requerer qualquer diligência, que será realizada, ou não, a juízo da autoridade.', '1941-10-03', 13, 99),
('CPP — art. 17', 'A autoridade policial não poderá mandar arquivar autos de inquérito.', '1941-10-03', 13, 99),
('CPP — art. 20', 'A autoridade assegurará no inquérito o sigilo necessário à elucidação do fato ou exigido pelo interesse da sociedade.', '1941-10-03', 13, 99),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 172: Das Provas e Cadeia de Custódia
-- -----------------------------------------------------------------------------
('CPP — art. 155 (caput)', 'O juiz formará sua convicção pela livre apreciação da prova produzida em contraditório judicial, não podendo fundamentar sua decisão exclusivamente nos elementos informativos colhidos na investigação, ressalvadas as provas cautelares, não repetíveis e antecipadas.', '2008-06-09', 13, 172),
('CPP — art. 156 (caput)', 'A prova da alegação incumbirá a quem a fizer, sendo, porém, facultado ao juiz de ofício: I – ordenar, mesmo antes de iniciada a ação penal, a produção antecipada de provas consideradas urgentes e relevantes, observando a necessidade, adequação e proporcionalidade da medida; II – determinar, no curso da instrução, ou antes de proferir sentença, a realização de diligências para dirimir dúvida sobre ponto relevante.', '2008-06-09', 13, 172),
('CPP — art. 157 (caput)', 'São inadmissíveis, devendo ser desentranhadas do processo, as provas ilícitas, assim entendidas as obtidas em violação a normas constitucionais ou legais.', '2008-06-09', 13, 172),
('CPP — art. 157, § 1º', 'São também inadmissíveis as provas derivadas das ilícitas, salvo quando não evidenciado o nexo de causalidade entre umas e outras, ou quando as derivadas puderem ser obtidas por uma fonte independente das primeiras.', '2008-06-09', 13, 172),
('CPP — art. 158', 'Quando a infração deixar vestígios, será indispensável o exame de corpo de delito, direto ou indireto, não podendo supri-lo a confissão do acusado.', '1941-10-03', 13, 172),
('CPP — art. 158-A (caput)', 'Considera-se cadeia de custódia o conjunto de todos os procedimentos utilizados para manter e documentar a história cronológica do vestígio coletado em locais ou em vítimas de crimes, para rastrear sua posse e manuseio a partir de seu reconhecimento até o descarte.', '2019-12-24', 13, 172),
('CPP — art. 158-B', 'A cadeia de custódia compreende o rastreamento do vestígio nas seguintes etapas: I - reconhecimento; II - isolamento; III - fixação; IV - coleta; V - acondicionamento; VI - transporte; VII - recebimento; VIII - processamento; IX - armazenamento; X - descarte.', '2019-12-24', 13, 172),

-- -----------------------------------------------------------------------------
-- DIREITO PROCESSUAL PENAL (ID 13) — TÓPICO 79: Prisão, Medidas Cautelares e Liberdade Provisória
-- -----------------------------------------------------------------------------
('CPP — art. 282, § 2º', 'As medidas cautelares serão decretadas pelo juiz a requerimento das partes ou, no curso da investigação criminal, por representação da autoridade policial ou mediante requerimento do Ministério Público.', '2019-12-24', 13, 79),
('CPP — art. 283 (caput)', 'Ninguém poderá ser preso senão em flagrante delito ou por ordem escrita e fundamentada da autoridade judiciária competente, em decorrência de prisão cautelar ou em virtude de condenação criminal transitada em julgado.', '2019-12-24', 13, 79),
('CPP — art. 301', 'Qualquer do povo poderá e as autoridades policiais e seus agentes deverão prender quem quer que seja encontrado em flagrante delito.', '1941-10-03', 13, 79),
('CPP — art. 302', 'Considera-se em flagrante delito quem: I - está cometendo a infração penal; II - acaba de cometê-la; III - é perseguido, logo após, pela autoridade, pelo ofendido ou por qualquer pessoa, em situação que faça presumir ser autor da infração; IV - é encontrado, logo depois, com instrumentos, armas, objetos ou papéis que façam presumir ser ele autor da infração.', '1941-10-03', 13, 79),
('CPP — art. 306, § 1º', 'Em até 24 (vinte e quatro) horas após a realização da prisão, será encaminhado ao juiz competente o auto de prisão em flagrante e, caso o autuado não informe o nome de seu advogado, cópia integral para a Defensoria Pública.', '2011-05-04', 13, 79),
('CPP — art. 310 (caput)', 'Após receber o auto de prisão em flagrante, no prazo máximo de até 24 (vinte e quatro) horas após a realização da prisão, o juiz deverá promover audiência de custódia com a presença do acusado, seu advogado constituído ou membro da Defensoria Pública e o membro do Ministério Público, e, fundamentadamente, deverá: I - relaxar a prisão ilegal; ou II - converter a prisão em flagrante em preventiva, quando presentes os requisitos constantes do art. 312 deste Código, e se revelarem inadequadas ou insuficientes as medidas cautelares diversas da prisão; ou III - conceder liberdade provisória, com ou sem fiança.', '2019-12-24', 13, 79),
('CPP — art. 311', 'Em qualquer fase da investigação policial ou do processo penal, caberá a prisão preventiva decretada pelo juiz, a requerimento do Ministério Público, do querelante ou do assistente, ou por representação da autoridade policial.', '2019-12-24', 13, 79),
('CPP — art. 312 (caput)', 'A prisão preventiva poderá ser decretada como garantia da ordem pública, da ordem econômica, por conveniência da instrução criminal ou para assegurar a aplicação da lei penal, quando houver prova da existência do crime e indício suficiente de autoria e de perigo gerado pelo estado de liberdade do imputado.', '2019-12-24', 13, 79),
('CPP — art. 313, I', 'Nos termos do art. 312 deste Código, será admitida a decretação da prisão preventiva: I - nos crimes dolosos punidos com pena privativa de liberdade máxima superior a 4 (quatro) anos;', '2011-05-04', 13, 79),
('CPP — art. 313, II', 'Nos termos do art. 312 deste Código, será admitida a decretação da prisão preventiva: II - se tiver sido condenado por outro crime doloso, em sentença transitada em julgado, ressalvado o disposto no inciso I do caput do art. 64 do Código Penal;', '2011-05-04', 13, 79),
('CPP — art. 315, § 1º', 'Na motivação da decretação, da manutenção ou da revogação da prisão preventiva, o juiz deverá indicar concretamente a existência de fatos novos ou contemporâneos que justifiquem a aplicação da medida adotada.', '2019-12-24', 13, 79),
('CPP — art. 316, parágrafo único', 'Decretada a prisão preventiva, deverá o órgão emissor da decisão revisar a necessidade de sua manutenção a cada 90 (noventa) dias, mediante decisão fundamentada, de ofício, sob pena de tornar a prisão ilegal.', '2019-12-24', 13, 79)

on conflict (referencia) do update set 
    texto = excluded.texto, 
    vigencia_de = excluded.vigencia_de, 
    id_materia = excluded.id_materia, 
    id_topico = excluded.id_topico;
