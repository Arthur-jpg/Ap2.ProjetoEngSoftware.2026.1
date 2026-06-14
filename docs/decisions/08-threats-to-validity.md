# Decisão 08 — Ameaças à validade

Registro honesto das limitações do estudo e de como o desenho as mitiga. Deve
virar uma seção "Ameaças à Validade" no artigo.

## Validade de construto (medimos o que dizemos medir?)

- **Forte ponto positivo (vs. versão anterior):** trocamos as métricas-proxy
  (javalang: CBO=imports, DIT=0/1, LCOM caseiro) pela ferramenta **CK**, que
  computa as métricas de Chidamber & Kemerer de fato. O DIT real chega a 74
  (antes era no máx. 1). Isso corrige uma ameaça de construto grave.
- **LCOM\* vs LCOM5:** usamos o `lcom*` do CK (Henderson-Sellers 1996),
  rotulado honestamente como `LCOM_norm` — não é o "LCOM5 (Hitz & Montazeri)"
  do plano original. Nome e referência corrigidos.
- **Bugs = achados do SpotBugs**, não defeitos reais de produção. SpotBugs
  detecta *padrões suspeitos* no bytecode; é um proxy de qualidade aceito na
  literatura, mas não equivale a falhas observadas em campo.

## Validade interna (a relação observada é real?)

- **Bugs só para repos que compilam (6/10).** SpotBugs exige bytecode. Tratamos
  `Number_of_bugs` como **0** para classes analisadas sem achado e **NaN** para
  classes de repos que não compilaram (ausência ≠ zero). A análise de bugs usa
  apenas as **1.771 classes** dos 6 repos compilados; as 9.688 restantes entram
  só na caracterização estrutural.
- **Confundidor tamanho.** Métricas de tamanho (LOC, NM) correlacionam tanto com
  outras métricas quanto com bugs; parte do efeito métrica→bugs pode ser tamanho.
  Reportamos correlações de forma descritiva (Spearman), sem alegar causalidade.

## Validade externa (generaliza?)

- **N pequeno: 10 repos**, a maioria com 0–1 estrela. A população de repos Java
  com contribuição confirmada do Claude é pequena e jovem.
- **Viés de seleção:** top-by-stars entre os que casam o sinal do Claude, com
  curadoria (exclusão de Android e de repos rotulados "Java" sem serem projetos
  Java OO). Não é amostra aleatória.
- **Heterogeneidade:** os 6 repos compilados variam muito em porte (de ~100 a
  ~600 classes) e domínio (EMS financeiro, editor de texto, API de golf...).

## Validade de conclusão (a estatística sustenta?)

- Dados fortemente assimétricos e não normais (KS rejeita normalidade em todas as
  métricas) → usamos **Spearman** (não paramétrico) e estatística robusta.
- **Achado principal (n=1.771):** todas as métricas de tamanho/complexidade/coesão
  correlacionam **positiva e significativamente** com bugs (ρ≈0,20–0,31, p<10⁻¹⁷);
  herança é fraca (**DIT** ρ≈0,05; **NOC** não significativo, p≈0,60). Coerente com
  Subramanyam & Krishnan 2003 e Basili 1996, mas os ρ são **moderados**, não fortes
  — não se deve sobreinterpretar como modelo preditivo.
- Evitamos regressão sobre-ajustada; ficamos em correlação descritiva, como
  recomenda a literatura de avaliação de predição de defeitos (D'Ambros 2012).

## A própria dificuldade de build é um achado

Ver `09-dificuldade-build-projetos-ia.md`: a baixa taxa de compilação pronta
(20%→60% com esforço) e o uso de JDKs muito recentes sem toolchain travada são,
eles próprios, sinais de portabilidade/manutenibilidade do código de IA.

## Referências
`docs/refs.bib`: `ck1994`, `hendersonsellers1996`, `subramanyam2003`, `basili1996`,
`dambros2012`, `spotbugs`.
