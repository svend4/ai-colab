# Knowledge report — data\knowledge-corpus

- Корпус: `data\knowledge-corpus` — занесено документов: **8**
- База памяти: `logs/knowledge.db` (L6 workbench.db, запрашиваемая)

## Состав по типам
| Тип | Документов |
|---|---|
| md | 4 |
| txt | 2 |
| csv | 1 |
| json | 1 |

## Состав по рискам
| Риск | Документов |
|---|---|
| low | 8 |

## Запрос: «bridge» — 7 совпадений (ранжировано, FTS5)
| Документ | Тип | Summary |
|---|---|---|
| knowledge:knowledge-corpus:glossary.md | md | # Bridge Glossary |
| knowledge:knowledge-corpus:README.md | md | # Knowledge Bridge Corpus |
| knowledge:knowledge-corpus:agent-handbook.md | md | # Bridge Agent Handbook |
| knowledge:knowledge-corpus:pipeline-faq.md | md | # Bridge Pipeline FAQ |
| knowledge:knowledge-corpus:workflow-table.csv | csv | id,bridge_area,status,note |
| knowledge:knowledge-corpus:risk-register.txt | txt | Synthetic risk register for bridge infrastructure. |
| knowledge:knowledge-corpus:operations-note.txt | txt | Operations note for the synthetic bridge corpus. |

_Запросить позже: `python tools/knowledge.py query logs/knowledge.db "<текст>"`_
