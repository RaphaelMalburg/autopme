# WhatsApp a sério — Cloud API, custos e que BSP escolher

Como ligar o WhatsApp de um cliente ao bot de forma **compliant** (sem risco de
ban) e quanto custa. Dados de 2026.

## Duas formas, duas fases
| | Baileys (na demo) | WhatsApp Cloud API (produção) |
|---|---|---|
| Ligação | Lê QR (como WhatsApp Web) | Número registado na Meta via BSP |
| Compliant? | ❌ Viola ToS (risco ban) | ✅ Oficial |
| Proativo (lembretes) | Frágil | ✅ Via templates aprovados |
| Usar para | Demo + piloto (nº descartável) | Clientes a pagar |

## A decisão nº1: que número
- **Número novo dedicado (recomendado p/ começar):** o cliente mantém o WhatsApp dele intacto. Menos medo, arranque rápido.
- **Migrar o número atual:** melhor reconhecimento, MAS perde a app do WhatsApp nesse número (tudo passa pelo teu sistema → precisa de caixa partilhada para a equipa).
- ⚠️ O mesmo número **não pode** estar na app e na Cloud API ao mesmo tempo.

## Como funciona o custo (2026)
Acabou o "por conversa" — agora é **por mensagem entregue**, com 4 categorias:
- **Serviço** (respostas dentro da janela de 24h após o cliente escrever): **grátis**.
- **Utility** (confirmações, lembretes, atualizações): muito barata (~80-90% < marketing).
- **Authentication** (códigos OTP): barata; raramente precisas.
- **Marketing** (promoções, reativação): mais cara; varia pelo **país do destinatário**.
- Bónus: anúncios **click-to-WhatsApp** abrem **72h grátis** de mensagens.

> Tradução prática: o teu wedge (confirmações + FAQ) cai em **serviço/utility** →
> custo por cliente de poucos €/mês em baixo volume. Repercute no retainer.

## Que BSP escolher
| | 360dialog | Twilio |
|---|---|---|
| Modelo | ~**€49/mês fixo**, zero markup nas msgs | Pay-as-you-go (~**$0.005/msg** + Meta) |
| Dados | **UE / RGPD** ✅ | EUA (cuidado Schrems II) |
| Melhor para | Escala / WhatsApp-first / Portugal | Arrancar rápido, baixo volume, já tens código |
| Dashboard incluído | Não (constróis tu) | Não |

**Recomendação:** **Twilio** para os primeiros 1-2 clientes (rápido, já há base de
código no `agente-consultoria`). **360dialog** a partir do 3.º pela economia e RGPD.

## Passos para ligar (com BSP) — ~meio dia
1. Meta Business Manager **do cliente** (ele é dono; tu tens acesso).
2. Adicionar WhatsApp + criar WABA.
3. Registar número + verificar OTP.
4. Iniciar verificação do negócio (documentos; pode demorar dias).
5. Obter Phone Number ID + token → meter no backend.
6. Apontar webhook para `/api/whatsapp/webhook`.
7. Submeter [templates](templates.md) e aguardar aprovação.

## A regra que molda o produto: janela de 24h
- Cliente escreveu primeiro → respondes **livre** 24h (FAQ, conversa).
- Enviar **proativo** fora disso → **só com template aprovado** (por isso confirmações/lembretes são templates de UTILITY).

---
### Fontes
- [respond.io — pricing 2026](https://respond.io/blog/whatsapp-business-api-pricing) · [engagelab](https://www.engagelab.com/blog/whatsapp-business-api-pricing)
- [360dialog pricing](https://360dialog.com/pricing) · [Twilio WhatsApp pricing](https://www.twilio.com/en-us/whatsapp/pricing)
- [BSP comparison — EZContact](https://ezcontact.ai/en/blog/whatsapp-bsp-comparison/)
