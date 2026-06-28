# Checklist de Onboarding de Cliente

Copia por cada cliente. Do "sim" ao "no ar", com segurança/whitelist.

## Fase 0 — Antes de tocar em código
- [ ] Proposta aceite (setup + retainer, mín. 3 meses) · 50% do setup pago.
- [ ] **Decisão do número:** ( ) novo dedicado  ( ) migrar atual.
- [ ] Contexto recolhido: horário, serviços, preços, morada, FAQ (5-10).
- [ ] Automação nº1 escolhida (ver catálogo).

## Fase 1 — Piloto (impressionar em dias) — Baileys
- [ ] Número dedicado descartável.
- [ ] Gateway Baileys ligado (scan QR no dashboard).
- [ ] Negócio carregado na demo (preset) → agente responde como o negócio.
- [ ] Mostrar a funcionar ao cliente.
> Piloto = mostrar valor. Não é produção.

## Fase 2 — Produção (compliant) — Cloud API
- [ ] BSP escolhido: Twilio (1.os) ou 360dialog (escala).
- [ ] Meta Business Manager do cliente (ele dono; tu com acesso) + WABA.
- [ ] Número registado + OTP + verificação do negócio iniciada.
- [ ] Credenciais (Phone Number ID + token) no backend.
- [ ] Webhook → `/api/whatsapp/webhook`.
- [ ] Templates submetidos e aprovados.

## Fase 3 — Configurar o assistente
- [ ] Contexto carregado (horário/serviços/preços/notas).
- [ ] Automação(ões) ativada(s).
- [ ] Horário + mensagem fora de horas.
- [ ] Regras de escalonamento para humano.

## Fase 4 — Segurança & whitelist
- [ ] **Whitelist de números de teste** (`AUTHORIZED_DEMO_NUMBERS`) durante o setup.
- [ ] **Só templates aprovados**; nunca proativo sem template.
- [ ] **Opt-in (RGPD)** para qualquer marketing/reativação.
- [ ] Escalonamento humano claro.
- [ ] Volume baixo no início; vigiar **quality rating** do número (Meta).
- [ ] Dados no Business Manager do cliente; guardar só o necessário.

## Fase 5 — Go-live & handover
- [ ] Teste end-to-end (confirmação + lembrete + FAQ + escalonamento).
- [ ] 2.ª metade do setup paga.
- [ ] Formar a equipa (caixa partilhada se migraram número).
- [ ] Relatório mensal definido.
- [ ] Revisão aos 30 dias (medir ROI → base de upsell).

## Riscos a vigiar
- Baileys em produção = **não** (risco ban). Só piloto/descartável.
- Mesmo número não pode estar na app + Cloud API.
- Quality rating baixo → Meta limita envios. Mantém opt-in e relevância.
- Categoria de template errada = rejeição.
