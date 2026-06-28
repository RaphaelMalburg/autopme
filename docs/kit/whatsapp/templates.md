# Biblioteca de Templates WhatsApp (Cloud API) — PT-PT

Templates prontos a **submeter para aprovação**. Versão legível; o equivalente
pronto a API está em [templates.json](templates.json).

## Regras rápidas
- **UTILITY** = transacional (confirmações/lembretes). Barato, aprovação fácil, proativo. **É o teu wedge.**
- **MARKETING** = promoções/reativação. Precisa opt-in, custa mais.
- Variáveis `{{1}}`, `{{2}}`… preenchidas no envio. Idioma `pt_PT`.
- Dentro da janela 24h (cliente escreveu) **não** precisas de template.

---
## 1. `confirmacao_marcacao` (UTILITY)
```
Olá {{1}}! A sua marcação na {{2}} está confirmada para {{3}} às {{4}}.
Se precisar de remarcar ou cancelar, responda a esta mensagem. Até breve!
```
1=nome · 2=negócio · 3=data · 4=hora · Botões: `Confirmar` · `Remarcar`

## 2. `lembrete_24h` (UTILITY)
```
Olá {{1}}, lembrete da sua marcação na {{2}} amanhã, dia {{3}} às {{4}}. Confirma a presença?
```
Botões: `Confirmo presença` · `Preciso de remarcar`

## 3. `lembrete_dia` (UTILITY)
```
Bom dia {{1}}! Hoje às {{2}} tem a sua marcação na {{3}}. Estamos à sua espera. Morada: {{4}}.
```

## 4. `remarcacao_ok` (UTILITY)
```
Combinado, {{1}}! A sua marcação foi alterada para {{2}} às {{3}}. Se não der jeito, responda e tratamos.
```

## 5. `vaga_disponivel` (UTILITY)
```
Olá {{1}}! Libertou-se uma vaga na {{2}} para {{3}} às {{4}}. Quer ficar com ela? Responda SIM nos próximos 30 minutos.
```
Botões: `Sim, quero` · `Agora não`

## 6. `reativacao` (MARKETING — só com opt-in)
```
Olá {{1}}! Há algum tempo que não o vemos na {{2}}. Quer marcar {{3}}? Temos disponibilidade esta semana.
```
Botões: `Quero marcar` · `Não, obrigado`

## 7. `pedido_avaliacao` (UTILITY)
```
Obrigado pela sua visita à {{2}}, {{1}}! Se correu bem, deixava-nos uma avaliação? Ajuda imenso: {{3}}
```

## 8. `pedido_orcamento_recebido` (UTILITY)
```
Olá {{1}}, recebemos o seu pedido na {{2}}. Vamos analisar e respondemos em {{3}}. Obrigado!
```

## Fora de horário (NÃO é template — mensagem de sessão, texto livre)
```
Olá! Obrigado pela mensagem. Estamos fora do horário, mas posso já ajudar com
horários, serviços, preços e marcações da {{negócio}}. Em que posso ajudar?
```

## Variantes por nicho
- **Saúde/estética/fisio:** "consulta/tratamento". Tom cuidado.
- **Ginásio:** "aula/avaliação/plano". Tom enérgico.
- **Restaurante:** "reserva"; lembrete 2h antes.
- **Oficina:** "revisão/viatura pronta para levantamento".
- **Imobiliária:** "visita ao imóvel".

## Dicas de aprovação
- Categoria certa (lembrete=UTILITY, promoção=MARKETING) — erro nº1 de rejeição.
- Sem promessas exageradas, sem CAPS, sem links suspeitos.
