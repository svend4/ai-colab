# Knowledge report — data\fixtures

- Корпус: `data\fixtures` — занесено документов: **8**
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

## Запрос: «sample» — 4 совпадений (ранжировано, FTS5)
| Документ | Тип | Summary |
|---|---|---|
| knowledge:fixtures:sample-doc.md | md | # Synthetic Sample Document |
| knowledge:fixtures:sample-data.json | json | { |
| knowledge:fixtures:sample-table.csv | csv | id,category,status,note |
| knowledge:fixtures:sample-notes.txt | txt | Synthetic notes for fixture testing. |

_Запросить позже: `python tools/knowledge.py query logs/knowledge.db "<текст>"`_
