# Мульти-судейский кворум: 3 судьи × 9 инвариантов (валидация red-team-вердиктов)

Каждый судья независимо оценил: устоял ли инвариант (survived) или атака опровергает (refuted)/неясно (open).

## scope-split (исходный red-team: refuted)
- judge: panel/steelman | verdict: refuted | reason: Как сформулирован, инвариант содержит ЗАПРЕТ на коллапс («сведение к единому значению запрещено, пока проверка не провал
- judge: panel/prosecutor | verdict: survived | reason: Атака доказывает менее сильное утверждение, чем нужно для refuted. Разберу её по двум шагам, которые она склеивает. ШАГ 
- judge: panel/arbiter | verdict: refuted | reason: Атака валидна по существу, это не придирка. Вся сила инварианта держится на его условии остановки ("коллапс запрещён, ПО

## blindness (исходный red-team: open)
- judge: panel/steelman | verdict: refuted | reason: Линза steelman спрашивает: читается ли инвариант КАК СФОРМУЛИРОВАН благожелательно так, что атака не фатальна? Нет — и и
- judge: panel/prosecutor | verdict: refuted | reason: Атака дожата и ломает инвариант КАК СФОРМУЛИРОВАН, без спасительного чтения. Инвариант склеивает два глагола: «раннее ра
- judge: panel/arbiter | verdict: open | reason: Атака валидна ПО СУЩЕСТВУ, не придирка — но бьёт формулировку второго предложения, не операционное ядро. Разбор по пронг

## independence-weight (исходный red-team: refuted)
- judge: panel/steelman | verdict: survived | reason: Инвариант объявляет единицей анализа ИСТОЧНИК и предписывает схлопывать «коррелированные источники», требуя «доказуемо Н
- judge: panel/prosecutor | verdict: survived | reason: Атака ПЕРЕБОР: она опровергает наивную меру «похожий текст = коррелированный источник», но методичка эту наивную меру яв
- judge: panel/arbiter | verdict: survived | reason: Атака валидна по существу (не придирка) против НАИВНОЙ операционализации, и проект сам это зафиксировал: redteam/indepen

## reason-not-vote (исходный red-team: refuted)
- judge: panel/steelman | verdict: refuted | reason: Я судья-steelman и честно искал благожелательное прочтение — но фатальность атаки подтверждена СОБСТВЕННЫМИ артефактами 
- judge: panel/prosecutor | verdict: refuted | reason: Атака решающе ломает инвариант КАК СФОРМУЛИРОВАН, без спасительного чтения. Инвариант утверждает, что коллизии разрешают
- judge: panel/arbiter | verdict: refuted | reason: Атака валидна по существу против инварианта КАК СФОРМУЛИРОВАН, а не придирка. Фактическая основа подтверждена кодом репо

## minority-preserve (исходный red-team: refuted)
- judge: panel/steelman | verdict: refuted | reason: Я судья-steelman и искал благожелательное прочтение с минимальной поправкой — оно не спасает инвариант КАК СФОРМУЛИРОВАН
- judge: panel/prosecutor | verdict: refuted | reason: Инвариант защищает claim по двум дешёвым LLM-предикатам (уникальный + неопровергнут) без фитнес-оракула. «Неопровергнут»
- judge: panel/arbiter | verdict: refuted | reason: Атака валидна по существу, не придирка. Инвариант как СФОРМУЛИРОВАН опирается на load-bearing предикат «неопровергнут», 

## meaning-not-string (исходный red-team: refuted)
- judge: panel/steelman | verdict: refuted | reason: Инвариант «перефраз = тот же узел» вводит презумпцию ТОЖДЕСТВА без порога и без понятия «уникальный остаток». Steelman-р
- judge: panel/prosecutor | verdict: survived | reason: Атака строит лобовое противоречие на ложной дихотомии. Инвариант и И-3 оперируют на непересекающихся входах по их же опр
- judge: panel/arbiter | verdict: survived | reason: Прочитал первоисточники: variants/independent-first-reconcile-2026-06-25/claude.md (И-3, §2) и tools/consensus_by_meanin

## no-silent-delete (исходный red-team: refuted)
- judge: panel/steelman | verdict: survived | reason: Атака предполагает, что tombstone — привилегированная операция REMOVE вне режима доверия ADD. Но grow-only по конструкци
- judge: panel/prosecutor | verdict: survived | reason: Атака приписывает grow-only асимметрию ADD vs REMOVE, которой нет в самой формулировке инварианта-носителя. Несущий инва
- judge: panel/arbiter | verdict: refuted | reason: Атака валидна по существу, не придирка. Инвариант как СФОРМУЛИРОВАН ("убрать можно лишь явной записью с ПРИЧИНОЙ" — одна

## falsifiability (исходный red-team: refuted)
- judge: panel/steelman | verdict: survived | reason: Атака — классический tu quoque к критерию демаркации, и снимается двумя стандартными (не ad hoc) ходами благожелательног
- judge: panel/prosecutor | verdict: survived | reason: Атака держится на контрабандной посылке «тест = только эмпирический тест», которой инвариант не содержит: он говорит «ди
- judge: panel/arbiter | verdict: refuted | reason: Атака валидна по существу, не придирка. Инвариант процитирован в голой форме: "каждый claim несёт дискриминирующее услов

## pre-registration (исходный red-team: open)
- judge: panel/steelman | verdict: survived | reason: Инвариант фиксирует лишь ОДНУ переменную: момент заморозки критерия относительно порождения вариантов, запрещая пост-хок
- judge: panel/prosecutor | verdict: survived | reason: Атака бьёт мимо мишени. Инвариант — чисто процедурный: критерий нельзя двигать ПОСЛЕ того, как увидели варианты. Он нигд
- judge: panel/arbiter | verdict: survived | reason: Атака совершает сдвиг тезиса. Инвариант — узкое процедурное правило о ВРЕМЕНИ фиксации критерия (заморозить ДО вариантов

