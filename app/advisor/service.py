"""Commercial advisor helpers for the AutoPME demo.

Pure functions only: deterministic, testable, and safe to use offline during a demo.
"""
from __future__ import annotations

from typing import Any


NICHE_LABELS = {
    "dental": "clinica dentaria",
    "legal": "escritorio de advocacia",
    "accounting": "escritorio de contabilidade",
    "automotive": "oficina automovel",
    "real_estate": "imobiliaria",
    "fitness": "ginasio",
    "pharmacy": "farmacia",
}


NICHE_PAINS = {
    "dental": [
        "chamadas perdidas fora de horas e durante atendimento ao balcao",
        "marcacoes e remarcacoes manuais que aumentam no-shows",
        "perguntas repetidas sobre precos, seguros e urgencias",
    ],
    "legal": [
        "triagem manual de pedidos sem qualificar urgencia e area juridica",
        "tempo gasto a responder sempre as mesmas perguntas sobre consulta inicial",
        "seguimento comercial irregular depois do primeiro contacto",
    ],
    "accounting": [
        "muito tempo administrativo em esclarecimentos repetidos",
        "pedidos de documentos e follow-up feitos manualmente",
        "perda de leads por falta de resposta rapida fora do horario",
    ],
    "automotive": [
        "pedidos de orcamento e marcacao a chegar por varios canais sem centralizacao",
        "clientes sem confirmacao automatica da revisao ou entrega da viatura",
        "equipa ocupada a responder FAQs em vez de vender servicos de maior margem",
    ],
    "real_estate": [
        "leads frias sem follow-up consistente",
        "triagem manual de visitas e qualificacao do comprador",
        "respostas lentas a perguntas sobre imoveis e disponibilidade",
    ],
    "fitness": [
        "abandono de leads depois da primeira visita ou aula experimental",
        "muitas perguntas repetidas sobre mensalidades e horarios",
        "baixa reativacao de antigos membros",
    ],
    "pharmacy": [
        "equipa interrompida com perguntas repetidas sobre stock e horario",
        "reservas e levantamentos ainda muito manuais",
        "pouco follow-up para servicos de vacina e bem-estar",
    ],
}


NICHE_WINS = {
    "dental": [
        "confirmacao automatica de consultas e recuperacao de no-shows",
        "agente de voz para horario, precos e triagem inicial",
        "reativacao de pacientes inativos por WhatsApp",
    ],
    "legal": [
        "qualificacao inicial antes da reuniao com recolha do assunto",
        "seguimento comercial estruturado apos a primeira consulta",
        "captura automatica de documentos enviados por clientes",
    ],
    "accounting": [
        "onboarding mais rapido com recolha automatica de dados e documentos",
        "respostas instantaneas para perguntas recorrentes",
        "campanhas de reativacao para empresas que pediram proposta e nao fecharam",
    ],
    "automotive": [
        "confirmacoes e lembretes de oficina sem carga manual",
        "triagem de pedidos por tipo de servico e urgencia",
        "captura de fotos/documentos da viatura com resumo por email",
    ],
    "real_estate": [
        "resposta imediata a novos leads e agendamento de visitas",
        "follow-up automatico de interessados sem resposta",
        "qualificacao de comprador antes da visita",
    ],
    "fitness": [
        "reativacao de inativos com mensagens personalizadas",
        "resposta automatica para planos, aulas e horarios",
        "seguimento apos aula experimental para fechar inscricoes",
    ],
    "pharmacy": [
        "reservas e confirmacoes de levantamento por WhatsApp",
        "triagem automatica para vacinas e servicos de bem-estar",
        "captura de pedidos com menos interrupcoes ao balcao",
    ],
}


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _detected_pains(niche: str, extracted: dict[str, Any], extra: dict[str, Any]) -> list[str]:
    pains = list(NICHE_PAINS.get(niche, []))
    if not extracted.get("website"):
        pains.append("presenca digital incompleta ou dificil de converter em lead")
    if not (extra.get("prices") or extracted.get("prices")):
        pains.append("informacao de precos dispersa, o que gera perguntas repetidas e atrito comercial")
    if not (extra.get("opening_hours") or extracted.get("opening_hours")):
        pains.append("horarios pouco claros, aumentando chamadas e mensagens de baixa complexidade")
    return pains[:4]


def _recommended_stack(niche: str) -> list[str]:
    stack = [
        "agente de voz para atendimento inicial e qualificacao",
        "WhatsApp para follow-up comercial e FAQ",
        "captura de documentos com resumo automatico por email",
        "painel de ROI para sustentar a proposta comercial",
    ]
    if niche in ("fitness", "dental", "real_estate"):
        stack.append("campanhas de reativacao de contactos inativos")
    return stack


def _roi_summary(roi: dict[str, Any]) -> dict[str, Any]:
    day = float(roi.get("consultations_per_day") or 0)
    cur = float(roi.get("current_no_show_rate") or 0)
    tgt = float(roi.get("target_no_show_rate") or 0)
    rev = float(roi.get("revenue_per_consultation") or 0)
    monthly_gain = float(roi.get("monthly_gain") or 0)
    saved_slots = day * 22 * max(cur - tgt, 0) / 100
    return {
        "consultations_per_day": day,
        "current_no_show_rate": cur,
        "target_no_show_rate": tgt,
        "revenue_per_consultation": rev,
        "monthly_gain": monthly_gain,
        "saved_slots_per_month": round(saved_slots, 1),
    }


def _thirty_day_plan(niche: str) -> list[dict[str, str]]:
    label = NICHE_LABELS.get(niche, "negocio")
    return [
        {
            "phase": "Semana 1",
            "title": "Mapear atendimento e objeccoes",
            "outcome": f"levantamento rapido dos fluxos de telefone, WhatsApp e documentos da {label}",
        },
        {
            "phase": "Semana 2",
            "title": "Entrar em producao com FAQ e triagem",
            "outcome": "respostas automáticas para perguntas recorrentes e captura estruturada de leads",
        },
        {
            "phase": "Semana 3",
            "title": "Automatizar confirmacoes e follow-up",
            "outcome": "reduzir no-shows, acelerar resposta e nao deixar leads arrefecer",
        },
        {
            "phase": "Semana 4",
            "title": "Medir ganho e afinar roteiro",
            "outcome": "relatorio com ROI, gargalos removidos e proximas automacoes prioritarias",
        },
    ]


def _follow_up(
    business_name: str,
    niche: str,
    summary: str,
    monthly_gain: float,
    quick_wins: list[str],
) -> dict[str, Any]:
    label = NICHE_LABELS.get(niche, "negocio")
    first_win = quick_wins[0] if quick_wins else "automatizar o atendimento inicial"
    subject = f"Proposta de automacao para {business_name}"
    email_body = (
        f"Olá,\n\n"
        f"Conforme a nossa demo, identifiquei uma oportunidade clara para a {business_name}: {summary}\n\n"
        f"Nos primeiros 30 dias eu recomendaria começar por:\n"
        f"- {first_win}\n"
        f"- automatizar follow-up comercial via WhatsApp\n"
        f"- medir impacto em atendimento e conversao\n\n"
        f"Com os pressupostos da demo, o potencial estimado ronda {monthly_gain:.0f} EUR/mês em ganho ou recuperação de receita.\n\n"
        f"Se fizer sentido, envio-lhe um plano de implementação muito objetivo para esta {label} e alinhamos os próximos passos.\n\n"
        f"Cumprimentos,"
    )
    whatsapp_message = (
        f"Ola! Depois da demo, vejo espaco claro para ajudar a {business_name} com {first_win}. "
        f"Pelo cenario que simulamos, ha potencial para recuperar cerca de {monthly_gain:.0f} EUR/mes. "
        "Se quiser, envio-lhe um plano de 30 dias muito direto."
    )
    agenda = [
        "confirmar volume de contactos e gargalos atuais",
        "priorizar o canal com retorno mais rapido",
        "definir piloto de 30 dias e metricas de sucesso",
    ]
    return {
        "email_subject": subject,
        "email_body": email_body,
        "whatsapp_message": whatsapp_message,
        "next_meeting_agenda": agenda,
    }


def _export_markdown(
    business_name: str,
    niche: str,
    executive_summary: str,
    pains: list[str],
    opportunities: list[str],
    plan: list[dict[str, str]],
    roi_summary: dict[str, Any],
    follow_up: dict[str, Any],
) -> str:
    lines = [
        f"# AutoPME Demo - {business_name}",
        "",
        f"- Nicho: {niche}",
        f"- Resumo executivo: {executive_summary}",
        "",
        "## Dores detetadas",
    ]
    lines.extend(f"- {item}" for item in pains)
    lines.extend(["", "## Oportunidades prioritarias"])
    lines.extend(f"- {item}" for item in opportunities)
    lines.extend(["", "## Plano 30 dias"])
    lines.extend(f"- {item['phase']}: {item['title']} - {item['outcome']}" for item in plan)
    lines.extend(
        [
            "",
            "## ROI estimado",
            f"- Ganho mensal potencial: {roi_summary['monthly_gain']:.2f} EUR",
            f"- Slots recuperados por mes: {roi_summary['saved_slots_per_month']}",
            "",
            "## Follow-up sugerido",
            f"- Assunto email: {follow_up['email_subject']}",
            "",
            "```text",
            follow_up["email_body"],
            "```",
            "",
            "```text",
            follow_up["whatsapp_message"],
            "```",
        ]
    )
    return "\n".join(lines)


def build_commercial_brief(payload: dict[str, Any]) -> dict[str, Any]:
    niche = str(payload.get("niche") or "dental")
    business_name = str(payload.get("business_name") or "Negocio").strip() or "Negocio"
    extracted = payload.get("extracted") if isinstance(payload.get("extracted"), dict) else {}
    extra = payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
    roi = _roi_summary(payload.get("roi") if isinstance(payload.get("roi"), dict) else {})
    pains = _detected_pains(niche, extracted, extra)
    quick_wins = list(NICHE_WINS.get(niche, []))[:3]
    opportunities = _recommended_stack(niche)
    executive_summary = (
        f"a {business_name} pode ganhar velocidade comercial ao reduzir tarefas repetitivas, "
        f"responder mais depressa e transformar atendimento em conversao previsivel"
    )
    if roi["monthly_gain"] > 0:
        executive_summary += f", com potencial para recuperar cerca de {roi['monthly_gain']:.0f} EUR/mês"

    plan = _thirty_day_plan(niche)
    follow_up = _follow_up(business_name, niche, executive_summary, roi["monthly_gain"], quick_wins)
    export_markdown = _export_markdown(
        business_name=business_name,
        niche=niche,
        executive_summary=executive_summary,
        pains=pains,
        opportunities=opportunities,
        plan=plan,
        roi_summary=roi,
        follow_up=follow_up,
    )

    return {
        "business_name": business_name,
        "niche": niche,
        "niche_label": NICHE_LABELS.get(niche, niche),
        "executive_summary": executive_summary,
        "detected_pains": pains,
        "quick_wins": quick_wins,
        "recommended_stack": opportunities,
        "thirty_day_plan": plan,
        "roi_summary": roi,
        "closing_angle": (
            "Comecar por um piloto curto, medir tempo poupado e receita recuperada, "
            "e depois expandir para mais canais."
        ),
        "follow_up": follow_up,
        "extracted_snapshot": {
            "services": _safe_list(extracted.get("services") or extra.get("services")),
            "prices": _safe_list(extracted.get("prices") or extra.get("prices")),
            "opening_hours": extracted.get("opening_hours") or extra.get("opening_hours") or "",
            "website": extracted.get("website") or "",
            "phone": extracted.get("telefone") or extracted.get("contacto_telefone") or "",
        },
        "export_markdown": export_markdown,
    }
