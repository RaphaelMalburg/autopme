"""Presets de contexto por nicho (canonico, embutido na app).

Fonte de verdade dos exemplos usados pelo botao "Carregar exemplo do nicho" do
dashboard. Espelhado em docs/kit/presets/*.json (o teste test_kit_presets garante
que nao divergem). Editar AQUI e correr o teste para sincronizar os docs.
"""
from __future__ import annotations

from typing import Any

NICHE_PRESETS: dict[str, dict[str, Any]] = {
    "accounting": {
        "niche": "accounting",
        "business_name": "Gabinete de Contabilidade (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sex 9h-18h",
            "services": "Contabilidade de empresas e ENI, IRS, IVA, recursos humanos, criação de empresa",
            "prices": "Avença desde 80€/mês (ENI), empresas conforme volume. IRS desde 40€.",
            "notes": "Primeira reunião gratuita. Software certificado. Apoio na criação de empresa."
        },
        "free_context": "FAQ: Quanto custa a avença? Desde 80€/mês para ENI; empresas conforme volume. Ajudam a abrir empresa? Sim. Fazem IRS a particulares? Sim, desde 40€. A primeira reunião é grátis? Sim. Nota: o assistente recolhe os dados e marca reunião, não dá aconselhamento fiscal."
    },
    "automotive": {
        "niche": "automotive",
        "business_name": "Oficina Auto Central (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sex 8h30-18h30, Sáb 9h-13h",
            "services": "Revisões, mudança de óleo, travões, pneus, diagnóstico, inspeção pré-IPO, chapa e pintura",
            "prices": "Revisão desde 90€, mudança de óleo desde 60€, diagnóstico 35€ (abatido na reparação)",
            "notes": "Orçamento gratuito. Viatura de cortesia mediante disponibilidade. Levantamento até às 18h30."
        },
        "free_context": "FAQ: Dão orçamento? Sim, gratuito antes de reparar. Têm carro de cortesia? Conforme disponibilidade. Quanto demora uma revisão? Geralmente no próprio dia. Avisam quando está pronto? Sim, por WhatsApp."
    },
    "bakery": {
        "niche": "bakery",
        "business_name": "Padaria & Pastelaria do Bairro (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sáb 7h-20h, Dom 7h30-13h",
            "services": "Pão fresco, bolos de aniversário por encomenda, salgados, cafetaria, catering",
            "prices": "Bolo de aniversário desde 25€, salgados desde 0,80€, encomendas com 48h",
            "notes": "Encomendas de bolos com 48h de antecedência. Catering para eventos. Opções sem glúten."
        },
        "free_context": "FAQ: Como encomendo um bolo? Indique sabor, tamanho e data, com 48h de antecedência. Têm sem glúten? Sim, algumas opções. Fazem catering? Sim, para eventos. Pagam-se as encomendas adiantado? Sinal de 50%."
    },
    "beauty": {
        "niche": "beauty",
        "business_name": "Studio Beleza & Estética (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Ter-Sáb 10h-20h",
            "services": "Manicure/pedicure, faciais, depilação a laser, massagens, micropigmentação",
            "prices": "Manicure 18€, facial desde 45€, laser desde 35€/sessão, massagem 50€/60min",
            "notes": "Marcação obrigatória. Pacotes de sessões com desconto. Cartão-presente disponível."
        },
        "free_context": "FAQ: Preciso de marcar? Sim, sempre. Fazem pacotes? Sim, com desconto para várias sessões. Têm cartão-presente? Sim. Cancelo com quanto tempo? Até 24h antes sem custo."
    },
    "dental": {
        "niche": "dental",
        "business_name": "Clínica Dentária Sorriso (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sex 9h-19h, Sáb 9h-13h",
            "services": "Consultas de check-up, limpezas, branqueamento, implantes, ortodontia, urgências",
            "prices": "Primeira consulta 30€, limpeza 50€, branqueamento desde 250€, implante desde 800€",
            "notes": "Aceita seguros e planos de saúde. Estacionamento próximo. Urgências no próprio dia se houver vaga."
        },
        "free_context": "FAQ: Têm consulta de urgência? Sim, no próprio dia conforme disponibilidade. Trabalham com seguros? Sim, principais seguradoras. É preciso pagar a primeira consulta? Sim, 30€, abatidos se avançar com tratamento. Onde estacionar? Parque a 2 min."
    },
    "fitness": {
        "niche": "fitness",
        "business_name": "Estúdio FitPorto (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sex 7h-22h, Sáb-Dom 9h-14h",
            "services": "Musculação, aulas de grupo, personal training, avaliação física, nutrição",
            "prices": "Mensalidade desde 35€, aula experimental grátis, PT 25€/sessão, avaliação 20€",
            "notes": "Primeira aula experimental gratuita. Planos sem fidelização disponíveis. Duche e cacifos."
        },
        "free_context": "FAQ: Tenho aula grátis? Sim, a primeira é experimental. Há fidelização? Há planos com e sem. Posso congelar a mensalidade? Sim, até 1 mês/ano. Têm acompanhamento? Sim, PT e nutrição."
    },
    "hospitality": {
        "niche": "hospitality",
        "business_name": "Alojamento Local Ribeira (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Receção 8h-22h. Check-in 15h, check-out 11h.",
            "services": "Quartos duplos e família, pequeno-almoço, transfers, dicas turísticas",
            "prices": "Quarto duplo desde 75€/noite, família desde 110€, pequeno-almoço incluído",
            "notes": "Check-in flexível mediante aviso. Bagagem pode ficar guardada. Perto do centro histórico."
        },
        "free_context": "FAQ: A que horas é o check-in? A partir das 15h, flexível mediante aviso. O pequeno-almoço está incluído? Sim. Têm transfer do aeroporto? Sim, mediante marcação. Posso deixar a bagagem? Sim. (Responder também em inglês/espanhol se o hóspede mudar de idioma.)"
    },
    "legal": {
        "niche": "legal",
        "business_name": "Escritório de Advocacia (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sex 9h-18h",
            "services": "Direito da família, imobiliário, laboral, comercial, contencioso",
            "prices": "Primeira consulta 60€ (abatida se avançar). Honorários conforme caso.",
            "notes": "Atendimento por marcação. Confidencialidade total. Primeira reunião para avaliar o caso."
        },
        "free_context": "FAQ: Quanto custa a primeira consulta? 60€, abatidos se avançarmos. Tratam de que áreas? Família, imobiliário, laboral, comercial. É confidencial? Totalmente. Atendem online? Sim, mediante marcação. Nota: o assistente recolhe o assunto e a urgência, não dá aconselhamento jurídico."
    },
    "pharmacy": {
        "niche": "pharmacy",
        "business_name": "Farmácia Saúde (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sáb 9h-20h. Serviço de urgência conforme escala.",
            "services": "Medicamentos, reservas, aconselhamento, medição de tensão, vacinação, dermocosmética",
            "prices": "Medição de tensão grátis. Vacinação conforme serviço. Reservas sem custo.",
            "notes": "Reserva de medicamentos por WhatsApp para levantamento. Entregas ao domicílio na zona."
        },
        "free_context": "FAQ: Posso reservar um medicamento? Sim, indique o nome e levanta quando estiver pronto. Fazem entregas? Sim, na zona. Têm serviço de vacinação? Sim. Medem a tensão? Sim, gratuito. Nota: o assistente não dá aconselhamento clínico; encaminha para o farmacêutico."
    },
    "real_estate": {
        "niche": "real_estate",
        "business_name": "Imobiliária Porto Premium (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Seg-Sex 9h30-19h, Sáb 10h-13h",
            "services": "Venda e arrendamento, avaliação de imóveis, gestão de visitas, financiamento",
            "prices": "Avaliação gratuita. Comissão de venda conforme contrato.",
            "notes": "Visitas mediante marcação. Apoio em crédito habitação. Carteira de imóveis no centro e arredores."
        },
        "free_context": "FAQ: A avaliação é grátis? Sim. Como marco uma visita? Indique o imóvel e a disponibilidade. Ajudam com crédito? Sim, temos parceiros. Trabalham arrendamento? Sim."
    },
    "restaurant": {
        "niche": "restaurant",
        "business_name": "Tasca do Porto (exemplo)",
        "language": "pt-PT",
        "extra": {
            "opening_hours": "Ter-Dom 12h-15h e 19h-23h. Encerra à segunda.",
            "services": "Almoços, jantares, menu do dia, grupos e eventos, takeaway",
            "prices": "Menu do dia 12€, pratos principais 12-22€, menu de grupo desde 25€/pessoa",
            "notes": "Reserva recomendada ao fim de semana. Sala para grupos até 30. Opções vegetarianas."
        },
        "free_context": "FAQ: Preciso de reservar? Recomendado, sobretudo fim de semana. Têm menu vegetariano? Sim. Aceitam grupos? Sim, até 30 pessoas. Fazem takeaway? Sim."
    }
}


def get_preset(niche: str) -> dict[str, Any] | None:
    return NICHE_PRESETS.get(niche)


def list_presets() -> list[dict[str, str]]:
    return [
        {"niche": k, "business_name": v.get("business_name", ""), "language": v.get("language", "pt-PT")}
        for k, v in NICHE_PRESETS.items()
    ]
