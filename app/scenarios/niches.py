"""Niche presets for the AutoPME Demo Studio.

Ported and adapted from agente-consultoria/app/routers/webhooks_vapi.py (NICHE_CONFIG).
Seven niches for PMEs in Porto, with European Portuguese (PT-PT) wording.

Each niche config contains:
- label: human-friendly PT-PT label for the dashboard.
- role: the persona role spoken by the agent.
- booking_term: generic term for an appointment/booking (used by the dashboard UI).
- first_message_inbound / first_message_outbound: opening lines with {business_name}.
- booking_flow: step-by-step capture flow ("recolhe um dado de cada vez").
- what_you_do: the "O QUE FAZES" section content.
- capture_tool_desc: description for the captureAppointment tool.
- capture_fields: dict of field name -> PT-PT label (consistent keys across niches:
  callerName, callerPhone, preferredDateTime, reason).
- example_knowledge: a realistic knowledge block used when no `extra` is provided,
  so the demo can start without any input.
"""

from typing import Any


def _knowledge(*body: str) -> str:
    """Wrap business-knowledge body lines in the standard PT-PT knowledge block."""
    return "\n".join([
        "=== CONHECIMENTO DO NEGÓCIO ===",
        "Usa APENAS estas informações para responder. Se a pergunta não está coberta aqui, "
        "diz que vais verificar e alguém da equipa entrará em contacto.",
        "",
        *body,
        "=== FIM DO CONHECIMENTO ===",
    ])


NICHE_CONFIG: dict[str, dict[str, Any]] = {
    "dental": {
        "label": "Clínica Dentária",
        "role": "recepcionista",
        "booking_term": "consulta",
        "first_message_inbound": "Olá, {business_name}, em que posso ajudar?",
        "first_message_outbound": "Olá, falo de {business_name}, estou a ligar para confirmar a sua consulta.",
        "booking_flow": (
            "## FLUXO DE MARCAÇÃO\n"
            "Passo 1: \"Claro, posso ajudar com isso. Qual é o seu nome?\"\n"
            "Passo 2: \"E um número de telefone para contacto?\"\n"
            "Passo 3: \"Que dia e hora prefere?\"\n"
            "Passo 4: \"E qual o motivo da consulta? Por exemplo, limpeza, dor, revisão...\"\n"
            "Passo 5: Confirma tudo, usa captureAppointment, diz que está registado e pergunta se pode ajudar com mais alguma coisa.\n"
            "Passo 6: Se a pessoa disser que não, despede-te e usa endCall.\n"
            "Recolhe um dado de cada vez. Não peças tudo ao mesmo tempo.\n"
        ),
        "what_you_do": (
            "1. Responder perguntas sobre a clínica (horários, tratamentos, preços, localização) "
            "usando APENAS o conhecimento abaixo.\n"
            "2. Informar sobre procedimentos disponíveis e preços (limpeza, branqueamento, implantes, etc.). "
            "Se o cliente perguntar, explica o que inclui cada procedimento.\n"
            "3. Marcar consultas: recolhe nome, telefone, data/hora preferida e motivo. "
            "Depois usa a ferramenta captureAppointment para registar.\n"
            "4. Se a pessoa quer falar com alguém específico ou tem um assunto fora do teu alcance, "
            "diz que vais passar a mensagem e alguém liga de volta.\n"
        ),
        "capture_tool_desc": "Registar um pedido de consulta. Usa APENAS depois de teres nome, telefone, data/hora e motivo.",
        "capture_fields": {
            "callerName": "Nome do paciente",
            "callerPhone": "Telefone do paciente",
            "preferredDateTime": "Data e hora preferida",
            "reason": "Motivo da consulta (limpeza, dor, revisão, etc.)",
        },
        "example_knowledge": _knowledge(
            "Horários: Segunda a sexta das 9h às 19h. Sábado das 9h às 13h. Encerrado ao domingo e feriados.",
            "Serviços: Consulta de dentística (limpeza e profilaxia), ortodontia (brackets e alinhadores), implantes dentários, endodontia (tratamento de canais), exames radiográficos (panorâmica e intra-oral), branqueamento dental, próteses fixas e removíveis, extrações e cirurgia oral.",
            "Preços: Consulta de avaliação 40€. Limpeza e profilaxia 55€. Branqueamento 180€. Tratamento de canal desde 150€ por dente. Implante desde 1500€ (inclui coroa). Orçamento gratuito para tratamentos complexos.",
            "Notas: Parque gratuito na rua durante 30 minutos. Acesso para cadeiras de rodas. Atendemos seguros de saúde (aceitamos reembolso). Em caso de urgência dental fora de horário, ligar para o número de emergência disponibilizado no site.",
        ),
    },
    "legal": {
        "label": "Advocacia",
        "role": "recepcionista",
        "booking_term": "reunião",
        "first_message_inbound": "Olá, {business_name}, em que posso ajudar?",
        "first_message_outbound": "Olá, falo de {business_name}, estou a ligar para confirmar a sua reunião.",
        "booking_flow": (
            "## FLUXO DE MARCAÇÃO\n"
            "Passo 1: \"Claro, posso ajudar com isso. Qual é o seu nome?\"\n"
            "Passo 2: \"E um número de telefone para contacto?\"\n"
            "Passo 3: \"Que dia e hora prefere?\"\n"
            "Passo 4: \"Pode indicar brevemente o assunto da reunião?\"\n"
            "Passo 5: Confirma tudo, usa captureAppointment, diz que está registado e pergunta se pode ajudar com mais alguma coisa.\n"
            "Passo 6: Se a pessoa disser que não, despede-te e usa endCall.\n"
            "Recolhe um dado de cada vez. Não peças tudo ao mesmo tempo.\n"
        ),
        "what_you_do": (
            "1. Responder perguntas sobre o escritório (horários, áreas de atuação, valores de consulta, localização) "
            "usando APENAS o conhecimento abaixo.\n"
            "2. Informar sobre serviços jurídicos disponíveis e respetivos valores.\n"
            "3. Marcar reuniões: recolhe nome, telefone, data/hora preferida e assunto. "
            "Depois usa a ferramenta captureAppointment para registar.\n"
            "4. Se a pessoa quer falar com alguém específico ou tem um assunto fora do teu alcance, "
            "diz que vais passar a mensagem e alguém liga de volta.\n"
        ),
        "capture_tool_desc": "Registar um pedido de reunião. Usa APENAS depois de teres nome, telefone, data/hora e assunto.",
        "capture_fields": {
            "callerName": "Nome do cliente",
            "callerPhone": "Telefone do cliente",
            "preferredDateTime": "Data e hora preferida",
            "reason": "Assunto da reunião",
        },
        "example_knowledge": _knowledge(
            "Horários: Segunda a sexta das 9h às 18h. Atendimento por marcação. Encerrado ao fim de semana.",
            "Serviços: Direito civil (divórcios, heranças e sucessões), direito do trabalho (acidentes de trabalho e despedimentos), direito comercial (constituição de sociedades e contratos), direito imobiliário (compra e venda, arrendamentos), direito de família, execuções e cobrança de dívidas.",
            "Preços: Consulta inicial 60€ (30 minutos). Análise de processo 120€. Honorários variáveis conforme o tipo de caso — orçamento após a primeira consulta. Divórcio por mútuo consentimento desde 500€ mais custas.",
            "Notas: Estacionamento pago no parque vizinho. Reuniões online ou presenciais. Atendemos em português, inglês e espanhol. Não prestamos serviços de direito penal nem administrativo.",
        ),
    },
    "accounting": {
        "label": "Contabilistas / TOC",
        "role": "recepcionista",
        "booking_term": "reunião",
        "first_message_inbound": "Olá, {business_name}, em que posso ajudar?",
        "first_message_outbound": "Olá, falo de {business_name}, estou a ligar para confirmar a sua reunião.",
        "booking_flow": (
            "## FLUXO DE MARCAÇÃO\n"
            "Passo 1: \"Claro, posso ajudar com isso. Qual é o seu nome?\"\n"
            "Passo 2: \"E um número de telefone para contacto?\"\n"
            "Passo 3: \"Que dia e hora prefere?\"\n"
            "Passo 4: \"Pode indicar o assunto? Por exemplo, IRS, contabilidade, faturação...\"\n"
            "Passo 5: Confirma tudo, usa captureAppointment, diz que está registado e pergunta se pode ajudar com mais alguma coisa.\n"
            "Passo 6: Se a pessoa disser que não, despede-te e usa endCall.\n"
            "Recolhe um dado de cada vez. Não peças tudo ao mesmo tempo.\n"
        ),
        "what_you_do": (
            "1. Responder perguntas sobre o escritório (horários, serviços, pacotes, preços, localização) "
            "usando APENAS o conhecimento abaixo.\n"
            "2. Informar sobre serviços de contabilidade, pacotes e preços (IRS, contabilidade mensal, faturação, etc.).\n"
            "3. Marcar reuniões: recolhe nome, telefone, data/hora preferida e assunto. "
            "Depois usa a ferramenta captureAppointment para registar.\n"
            "4. Se a pessoa quer falar com alguém específico ou tem um assunto fora do teu alcance, "
            "diz que vais passar a mensagem e alguém liga de volta.\n"
        ),
        "capture_tool_desc": "Registar um pedido de reunião. Usa APENAS depois de teres nome, telefone, data/hora e assunto.",
        "capture_fields": {
            "callerName": "Nome do cliente",
            "callerPhone": "Telefone do cliente",
            "preferredDateTime": "Data e hora preferida",
            "reason": "Assunto da reunião (IRS, contabilidade, faturação, etc.)",
        },
        "example_knowledge": _knowledge(
            "Horários: Segunda a sexta das 9h às 18h. Atendimento por marcação. Encerrado ao fim de semana e nas duas primeiras semanas de agosto (férias coletivas).",
            "Serviços: Contabilidade geral e fiscal (IRS, IVA, IRTS), apoio à constituição de empresas, processamento de salários (contratos e recibos verdes), faturação e emissão de documentos, declarações periódicas, elaboração de balanços e contas, representação fiscal, apoio a inspeções da Autoridade Tributária.",
            "Preços: Pacote mensal para empresas desde 80€/mês (contabilidade e declarações). IRS simples 60€. IRS com rendimentos de propriedades e dependentes 100€. Constituição de sociedade desde 250€ mais custas. Processamento de salários 15€ por funcionário/mês.",
            "Notas: Atendimento por marcação presencial ou telefónica. Aceitamos clientes em todo o país (trabalho remoto). Prazo de entrega de documentos até ao dia 5 de cada mês. Não prestamos serviços de auditoria.",
        ),
    },
    "automotive": {
        "label": "Oficinas",
        "role": "recepcionista",
        "booking_term": "marcação",
        "first_message_inbound": "Olá, {business_name}, em que posso ajudar?",
        "first_message_outbound": "Olá, falo de {business_name}, estou a ligar para confirmar a sua marcação na oficina.",
        "booking_flow": (
            "## FLUXO DE MARCAÇÃO\n"
            "Passo 1: \"Claro, posso ajudar com isso. Qual é o seu nome?\"\n"
            "Passo 2: \"E um número de telefone para contacto?\"\n"
            "Passo 3: \"Qual é a viatura? Marca, modelo e matrícula, se souber.\"\n"
            "Passo 4: \"Qual o serviço que precisa? Por exemplo, revisão, mudança de óleo, diagnóstico, travões...\"\n"
            "Passo 5: \"Que dia e hora prefere para deixar a viatura?\"\n"
            "Passo 6: Confirma tudo, usa captureAppointment, diz que está registado e pergunta se pode ajudar com mais alguma coisa.\n"
            "Passo 7: Se a pessoa disser que não, despede-te e usa endCall.\n"
            "Recolhe um dado de cada vez. Não peças tudo ao mesmo tempo.\n"
        ),
        "what_you_do": (
            "1. Responder perguntas sobre a oficina (horários, serviços, preços, localização) "
            "usando APENAS o conhecimento abaixo.\n"
            "2. Informar sobre serviços disponíveis e preços (revisões, mudança de óleo, travões, diagnóstico, "
            "preparação para inspeção, etc.).\n"
            "3. Marcar serviços: recolhe nome, telefone, viatura (marca, modelo e matrícula), tipo de serviço e data/hora. "
            "Depois usa a ferramenta captureAppointment para registar.\n"
            "4. Se a pessoa quer falar com alguém específico ou tem um assunto fora do teu alcance, "
            "diz que vais passar a mensagem e alguém liga de volta.\n"
        ),
        "capture_tool_desc": "Registar um pedido de marcação na oficina. Usa APENAS depois de teres nome, telefone, viatura, serviço e data/hora.",
        "capture_fields": {
            "callerName": "Nome do cliente",
            "callerPhone": "Telefone do cliente",
            "preferredDateTime": "Data e hora preferida",
            "reason": "Serviço pretendido e viatura (marca, modelo, matrícula)",
        },
        "example_knowledge": _knowledge(
            "Horários: Segunda a sexta das 8h às 19h. Sábado das 9h às 13h. Encerrado ao domingo.",
            "Serviços: Revisões gerais e manutenção, mudança de óleo e filtros, diagnóstico eletrónico, travões (pastilhas e discos), embraiagem, suspensão e amortecedores, alinhamento e equilíbrio de pneus, montagem de pneus, sistemas de escape, bateria e alternador, ar condicionado, preparação para inspeção periódica (IPO).",
            "Preços: Diagnóstico eletrónico 35€. Mudança de óleo desde 45€. Revisão geral desde 120€. Pastilhas de travão (por eixo) desde 60€. Alinhamento de direção 40€. Montagem de pneus 15€ por pneu. Orçamento gratuito para reparações maiores.",
            "Notas: Estacionamento gratuito dentro do recinto para viaturas em reparação. Viatura de cortesia sujeita a disponibilidade (mediante caução). Atendemos todas as marcas. Trabalhos com duração superior a um dia incluem acompanhamento por mensagem.",
        ),
    },
    "real_estate": {
        "label": "Imobiliárias",
        "role": "assistente",
        "booking_term": "visita",
        "first_message_inbound": "Olá, {business_name}, em que posso ajudar?",
        "first_message_outbound": "Olá, falo de {business_name}, estou a ligar para confirmar a sua visita ao imóvel.",
        "booking_flow": (
            "## FLUXO DE MARCAÇÃO DE VISITA\n"
            "Passo 1: \"Claro, posso ajudar com isso. Qual é o seu nome?\"\n"
            "Passo 2: \"E um número de telefone para contacto?\"\n"
            "Passo 3: \"Qual o imóvel que gostaria de visitar? Tem alguma referência?\"\n"
            "Passo 4: \"Que dia e hora prefere para a visita?\"\n"
            "Passo 5: Confirma tudo, usa captureAppointment, diz que está registado e pergunta se pode ajudar com mais alguma coisa.\n"
            "Passo 6: Se a pessoa disser que não, despede-te e usa endCall.\n"
            "Recolhe um dado de cada vez. Não peças tudo ao mesmo tempo.\n"
        ),
        "what_you_do": (
            "1. Responder perguntas sobre a imobiliária (imóveis disponíveis, localizações, preços, comissões) "
            "usando APENAS o conhecimento abaixo.\n"
            "2. Informar sobre imóveis, preços e condições. Ajudar o cliente a encontrar "
            "o imóvel mais adequado ao que procura.\n"
            "3. Marcar visitas: recolhe nome, telefone, imóvel de interesse e data/hora. "
            "Depois usa a ferramenta captureAppointment para registar.\n"
            "4. Se a pessoa quer falar com alguém específico ou tem um assunto fora do teu alcance, "
            "diz que vais passar a mensagem e alguém liga de volta.\n"
        ),
        "capture_tool_desc": "Registar um pedido de visita. Usa APENAS depois de teres nome, telefone, imóvel e data/hora.",
        "capture_fields": {
            "callerName": "Nome do cliente",
            "callerPhone": "Telefone do cliente",
            "preferredDateTime": "Data e hora preferida para a visita",
            "reason": "Imóvel de interesse e detalhes (referência, zona, tipo)",
        },
        "example_knowledge": _knowledge(
            "Horários: Segunda a sexta das 9h30 às 18h30. Sábado das 10h às 13h. Encerrado ao domingo.",
            "Serviços: Mediação na compra e venda de imóveis, arrendamento (longa e curta duração), avaliação gratuita de imóveis, gestão de arrendamentos, acompanhamento em visitas, apoio a financiamento habitacional, fotografia e divulgação de imóveis.",
            "Preços: Comissão de 3% mais IVA na venda (paga pelo vendedor). Arrendamento: 1 mês de renda mais IVA. Avaliação de imóvel gratuita. Sem cobrança ao comprador. Visitas sem compromisso.",
            "Notas: Carteira atual: T1 a T4 no Porto e Vila Nova de Gaia, moradias na Maia e Matosinhos, terrenos para construção. Acompanhamos sempre o cliente em visitas. Não prestamos financiamento próprio, mas ajudamos com a ligação ao banco.",
        ),
    },
    "fitness": {
        "label": "Ginásios",
        "role": "recepcionista",
        "booking_term": "marcação",
        "first_message_inbound": "Olá, {business_name}, em que posso ajudar?",
        "first_message_outbound": "Olá, falo de {business_name}, estou a ligar para confirmar a sua marcação.",
        "booking_flow": (
            "## FLUXO DE MARCAÇÃO\n"
            "Passo 1: \"Claro, posso ajudar com isso. Qual é o seu nome?\"\n"
            "Passo 2: \"E um número de telefone para contacto?\"\n"
            "Passo 3: \"Que tipo de sessão ou aula pretende?\"\n"
            "Passo 4: \"Que dia e hora prefere?\"\n"
            "Passo 5: Confirma tudo, usa captureAppointment, diz que está registado e pergunta se pode ajudar com mais alguma coisa.\n"
            "Passo 6: Se a pessoa disser que não, despede-te e usa endCall.\n"
            "Recolhe um dado de cada vez. Não peças tudo ao mesmo tempo.\n"
        ),
        "what_you_do": (
            "1. Responder perguntas sobre o ginásio/centro (horários, aulas, planos, mensalidades, localização) "
            "usando APENAS o conhecimento abaixo.\n"
            "2. Informar sobre planos, mensalidades e preços. Recomendar o plano mais adequado "
            "com base no que o cliente procura.\n"
            "3. Marcar sessões/aulas: recolhe nome, telefone, tipo de sessão e data/hora. "
            "Depois usa a ferramenta captureAppointment para registar.\n"
            "4. Se a pessoa quer falar com alguém específico ou tem um assunto fora do teu alcance, "
            "diz que vais passar a mensagem e alguém liga de volta.\n"
        ),
        "capture_tool_desc": "Registar um pedido de marcação. Usa APENAS depois de teres nome, telefone, tipo de sessão e data/hora.",
        "capture_fields": {
            "callerName": "Nome do cliente",
            "callerPhone": "Telefone do cliente",
            "preferredDateTime": "Data e hora preferida",
            "reason": "Tipo de sessão ou aula pretendida e objetivo",
        },
        "example_knowledge": _knowledge(
            "Horários: Segunda a sexta das 6h às 23h. Sábado e domingo das 8h às 20h. Feriados das 9h às 14h.",
            "Serviços: Sala de musculação e cardio, aulas de grupo (zumba, body pump, pilates, spinning, yoga e hidroginástica), personal training, avaliação física, plano de treino personalizado, balneários com sauna e banho turco, estacionamento para utentes.",
            "Preços: Mensalidade padrão 35€/mês (sem fidelização). Mensalidade premium 55€/mês (inclui aulas de grupo e sauna). Cartão de 10 sessões 60€. Aula avulsa 8€. Personal training 30€/sessão. Inscrição gratuita em janeiro e setembro.",
            "Notas: Primeira visita e aula experimental gratuitas. Pagamentos por débito direto, MB WAY e multibanco. Balneários com cacifos (cadeado próprio). Aceitamos utentes a partir dos 16 anos com autorização dos encarregados de educação.",
        ),
    },
    "pharmacy": {
        "label": "Farmácias",
        "role": "recepcionista",
        "booking_term": "encomenda",
        "first_message_inbound": "Olá, {business_name}, em que posso ajudar?",
        "first_message_outbound": "Olá, falo de {business_name}, estou a ligar para confirmar a sua encomenda.",
        "booking_flow": (
            "## FLUXO DE ENCOMENDA\n"
            "Passo 1: \"Claro, posso ajudar com isso. Qual é o seu nome?\"\n"
            "Passo 2: \"E um número de telefone para contacto?\"\n"
            "Passo 3: \"Qual é o produto ou medicamento que pretende encomendar ou reservar?\"\n"
            "Passo 4: \"A que horas prefere levantar? Posso deixar pronto para o mesmo dia ou para outro dia.\"\n"
            "Passo 5: Confirma tudo, usa captureAppointment, diz que a encomenda fica reservada e pergunta se pode ajudar com mais alguma coisa.\n"
            "Passo 6: Se a pessoa disser que não, despede-te e usa endCall.\n"
            "Recolhe um dado de cada vez. Não peças tudo ao mesmo tempo.\n"
        ),
        "what_you_do": (
            "1. Responder perguntas sobre a farmácia (horários, serviços, disponibilidade de medicamentos, localização) "
            "usando APENAS o conhecimento abaixo.\n"
            "2. Informar sobre medicamentos, produtos e serviços disponíveis (vacinação, medição de tensão arterial "
            "e glicemia, aconselhamento farmacêutico). Se a pergunta for sobre um medicamento sujeito a receita, "
            "pede a receita médica.\n"
            "3. Receber encomendas e reservas para levantamento: recolhe nome, telefone, produto e data/hora de "
            "levantamento. Depois usa a ferramenta captureAppointment para registar.\n"
            "4. Se a pessoa quer falar com o farmacêutico ou tem um assunto fora do teu alcance, "
            "diz que vais passar a mensagem e alguém liga de volta.\n"
        ),
        "capture_tool_desc": "Registar uma encomenda ou reserva para levantamento. Usa APENAS depois de teres nome, telefone, produto e data/hora de levantamento.",
        "capture_fields": {
            "callerName": "Nome do cliente",
            "callerPhone": "Telefone do cliente",
            "preferredDateTime": "Data e hora de levantamento preferida",
            "reason": "Produto ou medicamento a encomendar ou reservar",
        },
        "example_knowledge": _knowledge(
            "Horários: Segunda a sexta das 9h às 20h. Sábado das 9h às 13h e das 15h às 19h. Serviço de urgência noturno e ao domingo (escala de farmácias de serviço).",
            "Serviços: Dispensa de medicamentos com e sem receita, encomenda e reserva de medicamentos para levantamento, medição de tensão arterial e glicemia, vacinação (gripe, COVID-19 e outras), aconselhamento farmacêutico, venda de produtos de saúde e bem-estar, dermatocosmética, produtos para mãe e bebé.",
            "Preços: Receita médica comparticipada conforme tabela do SNS. Medicamentos sem receita ao preço de pauta. Medições gratuitas (tensão arterial e glicemia). Vacina da gripe 15€. Consulta de aconselhamento farmacêutico gratuita.",
            "Notas: Reservas de medicamentos prontas em 2 horas para levantamento no mesmo dia. Aceitamos receitas digitais (SNS) e em papel. Entregas ao domicílio gratuitas a partir de 25€ num raio de 5 km. Não fornecemos medicamentos sujeitos a receita sem a respetiva receita válida.",
        ),
    },
}


# Display order of niches in the dashboard.
NICHE_ORDER: list[str] = [
    "dental",
    "legal",
    "accounting",
    "automotive",
    "real_estate",
    "fitness",
    "pharmacy",
]


def list_niches() -> list[dict[str, str]]:
    """Return niche summaries for the dashboard, in NICHE_ORDER."""
    return [
        {
            "id": niche_id,
            "label": NICHE_CONFIG[niche_id]["label"],
            "role": NICHE_CONFIG[niche_id]["role"],
            "booking_term": NICHE_CONFIG[niche_id]["booking_term"],
        }
        for niche_id in NICHE_ORDER
    ]


def get_niche_config(niche: str | None) -> dict[str, Any] | None:
    """Return the full config for a niche id, or None if unknown."""
    if not niche:
        return None
    return NICHE_CONFIG.get(niche)
