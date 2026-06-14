# Decisão 02 — Detecção da contribuição do Claude

## Por quê

Um repo só entra na amostra se o Claude **realmente contribuiu**. A hipótese do
estudo é que, se o Claude commitou, alguém pediu para ele commitar → ele teve
impacto real no projeto.

## Como (dois sinais)

Um repo qualifica se **qualquer** commit casar A ou B:

- **(A) Mensagem de commit** com `Co-Authored-By: Claude <noreply@anthropic.com>`.
- **(B) Autor/committer** com e-mail `@anthropic.com` ou nome contendo "Claude".

Regex em `src/config.py` (`CLAUDE_COAUTHORED_RE`, `CLAUDE_AUTHOR_EMAIL_RE`,
`CLAUDE_AUTHOR_NAME_RE`). A Fase 1 descobre via GitHub Search Commits API; a Fase 2
**reconfirma** no `git log` local (`clone_build._confirm_claude`) e grava
`claude_confirmed`.

## O que foi rejeitado

- Confiar só na busca da API sem reconfirmar localmente (a API pode indexar de forma
  inconsistente) — por isso a dupla checagem na Fase 2.

## Limitações (ver 08-threats-to-validity)

- Mede **presença**, não **proporção** do código escrito pelo Claude.
- Depende de os contribuidores usarem a convenção `Co-Authored-By` do Claude Code.

## Referências

Convenção de co-autoria do Claude Code (Anthropic). Sem referência acadêmica formal;
é um critério operacional do estudo.
