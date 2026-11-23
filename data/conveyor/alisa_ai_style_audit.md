# Аудит всех статей на ИИ-отпечаток — детектор-прогон

**Дата:** 23.11.2026 · **Объём:** 242 статей блога · **Метод:** код-детектор по 12 признакам ИИ-текста (полная выгрузка body_html из репо, ветка astrowind-migration).

## Шкала вердиктов

| Диапазон | Вердикт | Статей |
|---|---|---|
| 0–10 | 🟢 человеческая | 1 |
| 10–20 | 🟠 пограничная | 56 |
| 20–35 | 🟡 заметный ИИ | 166 |
| 35+ | 🔴 сильный ИИ | 19 |

**Средний score:** 25.7 · **Медиана:** 25

## Методика (что именно проверял детектор)

1. **Классические ИИ-клише** — 30 фраз («стоит отметить», «таким образом», «уникальная возможность»…)
2. **Шаблонные связки-частотность** — «однако», «при этом», «тем не менее», «в целом»…
3. **Директивные штампы** — «важно учитывать», «не забывайте», «обратите внимание»…
4. **Тире-ритм** — плотность « — » (ИИ-тексты тире жалуют в 3–4 раза сильнее живых)
5. **Буллеты «<b>Термин:</b> факт.»** — механический ритм списков
6. **Шаблонный скелет** — блок «Коротко» в начале и «Что запомнить» в финале
7. **Шаблонные вопрос-заголовки** — ≥3 H2, начинающихся с «Как/Что/Сколько/Почему»
8. **Конвейерные 4-граммы** — фразы, дословно повторяющиеся в ≥15 статьях
9. **Ровный ритм** — доля предложений 10–22 слова (живой текст шумит длинами)

**Калибровка:** три переработанные живым голосом статьи (пилоты) сработали внизу списка — детектор видит разницу: m11-trassa 9.4, hongqi-v-rossii-2026 12.7, changan-q05-q06-q07-razem-i-zaryadka 14.0, to-elektromobilya-ceny — в пограничной зоне. То есть шкала откалибрована на эталоне, который владелец признал живым.

## Топ-20 самых «ИИ-пахнущих» статей

| Score | Статья | Доказательства |
|---|---|---|
| 43.3 | [tesla-v-rossii-zaryadka-i-riski](/blog/tesla-v-rossii-zaryadka-i-riski/) | клише×1; Коротко; Что запомнить; буллеты×18; тире 41/1000; шаблонные H2×4. Пример: «…ряжать Tesla в России: практика EU-версии (Type 2 / CCS2) — лучший выбор. Городские станции и домашние wallbox с Type 2 подходят напрямую, быстрые CCS…» |
| 42.3 | [samyi-bystryi-elektromobil](/blog/samyi-bystryi-elektromobil/) | Коротко; Что запомнить; буллеты×9; тире 41/1000; шаблонные H2×3 |
| 42.3 | [skolko-stoit-zaryadnaya-stanciya](/blog/skolko-stoit-zaryadnaya-stanciya/) | Коротко; Что запомнить; буллеты×11; тире 50/1000; шаблонные H2×3 |
| 42.2 | [besplatnaya-parkovka-elektromobilya](/blog/besplatnaya-parkovka-elektromobilya/) | Коротко; Что запомнить; буллеты×7; тире 45/1000; ровный ритм 67%; шаблонные H2×3 |
| 42.2 | [samye-nadezhnye-elektromobilya](/blog/samye-nadezhnye-elektromobilya/) | Коротко; Что запомнить; буллеты×7; тире 47/1000; шаблонные H2×4 |
| 41.1 | [adapter-po-toku-nagrev](/blog/adapter-po-toku-nagrev/) | Коротко; Что запомнить; буллеты×4; тире 50/1000; шаблонные H2×5 |
| 40.7 | [karta-zaryadnyh-stanciy-moskvy](/blog/karta-zaryadnyh-stanciy-moskvy/) | Коротко; Что запомнить; буллеты×7; тире 43/1000; шаблонные H2×3 |
| 40.7 | [skolko-elektromobiley-v-rossii](/blog/skolko-elektromobiley-v-rossii/) | Коротко; Что запомнить; буллеты×10; тире 59/1000 |
| 39.9 | [rekuperaciya-elektromobilya](/blog/rekuperaciya-elektromobilya/) | Коротко; Что запомнить; буллеты×3; тире 38/1000; ровный ритм 66%; шаблонные H2×4 |
| 39.7 | [zaryadka-v-chastnom-dome](/blog/zaryadka-v-chastnom-dome/) | Коротко; Что запомнить; буллеты×7; тире 41/1000 |
| 39.6 | [zaryadnaya-stanciya-22-kvt](/blog/zaryadnaya-stanciya-22-kvt/) | Коротко; Что запомнить; буллеты×6; тире 37/1000; шаблонные H2×3 |
| 39.0 | [zaryadka-ot-generatora](/blog/zaryadka-ot-generatora/) | Коротко; Что запомнить; буллеты×5; тире 44/1000; шаблонные H2×4 |
| 38.9 | [arenda-elektromobilya](/blog/arenda-elektromobilya/) | Коротко; Что запомнить; буллеты×15; тире 45/1000 |
| 38.3 | [kabel-dlya-zaryadki-elektromobilya](/blog/kabel-dlya-zaryadki-elektromobilya/) | Коротко; Что запомнить; буллеты×7; тире 44/1000 |
| 38.3 | [zaryadnaya-stanciya-dlya-biznesa](/blog/zaryadnaya-stanciya-dlya-biznesa/) | Коротко; Что запомнить; буллеты×9; шаблонные H2×3 |
| 38.2 | [pandora-wall-e](/blog/pandora-wall-e/) | Коротко; Что запомнить; буллеты×7; тире 46/1000 |
| 38.2 | [sechenie-kabelya-dlya-zaryadki](/blog/sechenie-kabelya-dlya-zaryadki/) | клише×1; Коротко; Что запомнить; буллеты×3; тире 49/1000; шаблонные H2×3 |
| 37.6 | [zaryadki-na-trassah-m4-m11-m12](/blog/zaryadki-na-trassah-m4-m11-m12/) | Коротко; Что запомнить; буллеты×4; тире 50/1000; шаблонные H2×5 |
| 37.5 | [test-drayv-elektromobilya-atom-evolute](/blog/test-drayv-elektromobilya-atom-evolute/) | Коротко; Что запомнить; буллеты×25; тире 36/1000 |
| 34.8 | [zaryadka-dlya-zeekr](/blog/zaryadka-dlya-zeekr/) | Коротко; Что запомнить; буллеты×6; тире 63/1000 |

## Весь блог (все 242 статьи, по убыванию подозрительности)

| Score | Вердикт | Статья | Слова | Признаки |
|---|---|---|---|---|
| 43.3 | 🔴 сильный ИИ | [tesla-v-rossii-zaryadka-i-riski](/blog/tesla-v-rossii-zaryadka-i-riski/) | 1632 | клише×1; Коротко; Что запомнить; буллеты×18; тире 41/1000; шаблонные H2×4 |
| 42.3 | 🔴 сильный ИИ | [samyi-bystryi-elektromobil](/blog/samyi-bystryi-elektromobil/) | 995 | Коротко; Что запомнить; буллеты×9; тире 41/1000; шаблонные H2×3 |
| 42.3 | 🔴 сильный ИИ | [skolko-stoit-zaryadnaya-stanciya](/blog/skolko-stoit-zaryadnaya-stanciya/) | 986 | Коротко; Что запомнить; буллеты×11; тире 50/1000; шаблонные H2×3 |
| 42.2 | 🔴 сильный ИИ | [besplatnaya-parkovka-elektromobilya](/blog/besplatnaya-parkovka-elektromobilya/) | 907 | Коротко; Что запомнить; буллеты×7; тире 45/1000; ровный ритм 67%; шаблонные H2×3 |
| 42.2 | 🔴 сильный ИИ | [samye-nadezhnye-elektromobilya](/blog/samye-nadezhnye-elektromobilya/) | 944 | Коротко; Что запомнить; буллеты×7; тире 47/1000; шаблонные H2×4 |
| 41.1 | 🔴 сильный ИИ | [adapter-po-toku-nagrev](/blog/adapter-po-toku-nagrev/) | 609 | Коротко; Что запомнить; буллеты×4; тире 50/1000; шаблонные H2×5 |
| 40.7 | 🔴 сильный ИИ | [karta-zaryadnyh-stanciy-moskvy](/blog/karta-zaryadnyh-stanciy-moskvy/) | 919 | Коротко; Что запомнить; буллеты×7; тире 43/1000; шаблонные H2×3 |
| 40.7 | 🔴 сильный ИИ | [skolko-elektromobiley-v-rossii](/blog/skolko-elektromobiley-v-rossii/) | 912 | Коротко; Что запомнить; буллеты×10; тире 59/1000 |
| 39.9 | 🔴 сильный ИИ | [rekuperaciya-elektromobilya](/blog/rekuperaciya-elektromobilya/) | 965 | Коротко; Что запомнить; буллеты×3; тире 38/1000; ровный ритм 66%; шаблонные H2×4 |
| 39.7 | 🔴 сильный ИИ | [zaryadka-v-chastnom-dome](/blog/zaryadka-v-chastnom-dome/) | 1604 | Коротко; Что запомнить; буллеты×7; тире 41/1000 |
| 39.6 | 🔴 сильный ИИ | [zaryadnaya-stanciya-22-kvt](/blog/zaryadnaya-stanciya-22-kvt/) | 1126 | Коротко; Что запомнить; буллеты×6; тире 37/1000; шаблонные H2×3 |
| 39.0 | 🔴 сильный ИИ | [zaryadka-ot-generatora](/blog/zaryadka-ot-generatora/) | 779 | Коротко; Что запомнить; буллеты×5; тире 44/1000; шаблонные H2×4 |
| 38.9 | 🔴 сильный ИИ | [arenda-elektromobilya](/blog/arenda-elektromobilya/) | 1022 | Коротко; Что запомнить; буллеты×15; тире 45/1000 |
| 38.3 | 🔴 сильный ИИ | [kabel-dlya-zaryadki-elektromobilya](/blog/kabel-dlya-zaryadki-elektromobilya/) | 1749 | Коротко; Что запомнить; буллеты×7; тире 44/1000 |
| 38.3 | 🔴 сильный ИИ | [zaryadnaya-stanciya-dlya-biznesa](/blog/zaryadnaya-stanciya-dlya-biznesa/) | 990 | Коротко; Что запомнить; буллеты×9; шаблонные H2×3 |
| 38.2 | 🔴 сильный ИИ | [pandora-wall-e](/blog/pandora-wall-e/) | 818 | Коротко; Что запомнить; буллеты×7; тире 46/1000 |
| 38.2 | 🔴 сильный ИИ | [sechenie-kabelya-dlya-zaryadki](/blog/sechenie-kabelya-dlya-zaryadki/) | 1607 | клише×1; Коротко; Что запомнить; буллеты×3; тире 49/1000; шаблонные H2×3 |
| 37.6 | 🔴 сильный ИИ | [zaryadki-na-trassah-m4-m11-m12](/blog/zaryadki-na-trassah-m4-m11-m12/) | 1192 | Коротко; Что запомнить; буллеты×4; тире 50/1000; шаблонные H2×5 |
| 37.5 | 🔴 сильный ИИ | [test-drayv-elektromobilya-atom-evolute](/blog/test-drayv-elektromobilya-atom-evolute/) | 973 | Коротко; Что запомнить; буллеты×25; тире 36/1000 |
| 34.8 | 🟡 заметный ИИ | [zaryadka-dlya-zeekr](/blog/zaryadka-dlya-zeekr/) | 924 | Коротко; Что запомнить; буллеты×6; тире 63/1000 |
| 34.7 | 🟡 заметный ИИ | [zaryadnyy-kabel-elektromobilya](/blog/zaryadnyy-kabel-elektromobilya/) | 887 | Коротко; Что запомнить; буллеты×5; тире 50/1000 |
| 34.4 | 🟡 заметный ИИ | [li-auto-8a-ogranichenie-zaryada](/blog/li-auto-8a-ogranichenie-zaryada/) | 541 | Коротко; Что запомнить; тире 46/1000; шаблонные H2×4 |
| 33.9 | 🟡 заметный ИИ | [nio-app-telematics](/blog/nio-app-telematics/) | 474 | клише×1; Коротко; тире 35/1000 |
| 33.4 | 🟡 заметный ИИ | [kredit-na-elektromobil](/blog/kredit-na-elektromobil/) | 846 | Коротко; Что запомнить; буллеты×10 |
| 33.1 | 🟡 заметный ИИ | [portativnaya-zaryadnaya-stanciya](/blog/portativnaya-zaryadnaya-stanciya/) | 1034 | Коротко; Что запомнить; тире 49/1000; шаблонные H2×4 |
| 32.8 | 🟡 заметный ИИ | [cltc-nedc-wltp-kuda-devaetsya-zapas-xoda](/blog/cltc-nedc-wltp-kuda-devaetsya-zapas-xoda/) | 823 | Коротко; Что запомнить; тире 46/1000; ровный ритм 67%; шаблонные H2×5 |
| 32.7 | 🟡 заметный ИИ | [zaryadka-ot-solnechnykh-paneley](/blog/zaryadka-ot-solnechnykh-paneley/) | 932 | Коротко; Что запомнить; буллеты×3; тире 46/1000 |
| 32.6 | 🟡 заметный ИИ | [byd-v-rossii-2026](/blog/byd-v-rossii-2026/) | 844 | Коротко; буллеты×11; тире 50/1000 |
| 32.6 | 🟡 заметный ИИ | [hongqi-e-qm5-cena-zaryadka-2026](/blog/hongqi-e-qm5-cena-zaryadka-2026/) | 342 | Коротко; буллеты×8; тире 55/1000; ровный ритм 84% |
| 32.3 | 🟡 заметный ИИ | [m-hero-917-problemy-i-servis](/blog/m-hero-917-problemy-i-servis/) | 537 | Коротко; Что запомнить; тире 65/1000; ровный ритм 68%; шаблонные H2×3 |
| 32.3 | 🟡 заметный ИИ | [zeekr-001-gbt-diff](/blog/zeekr-001-gbt-diff/) | 620 | Коротко; Что запомнить; тире 51/1000; ровный ритм 70%; шаблонные H2×3 |
| 32.2 | 🟡 заметный ИИ | [skolko-stoit-elektromobil](/blog/skolko-stoit-elektromobil/) | 1749 | Коротко; Что запомнить; тире 55/1000; шаблонные H2×6 |
| 32.1 | 🟡 заметный ИИ | [elektromobil-zimoy-v-rossii](/blog/elektromobil-zimoy-v-rossii/) | 983 | Коротко; Что запомнить; тире 45/1000; ровный ритм 76%; шаблонные H2×4 |
| 32.1 | 🟡 заметный ИИ | [kia-ev6-ioniq5-iccu-12v-problema](/blog/kia-ev6-ioniq5-iccu-12v-problema/) | 697 | Коротко; Что запомнить; тире 51/1000; ровный ритм 70%; шаблонные H2×4 |
| 31.9 | 🟡 заметный ИИ | [vw-id4-ruchki-i-ekran](/blog/vw-id4-ruchki-i-ekran/) | 545 | Коротко; Что запомнить; тире 58/1000; ровный ритм 74% |
| 31.8 | 🟡 заметный ИИ | [pandora-mini-22](/blog/pandora-mini-22/) | 781 | Коротко; Что запомнить; буллеты×9 |
| 31.8 | 🟡 заметный ИИ | [zeekr-x-cena-zaryadka-2026](/blog/zeekr-x-cena-zaryadka-2026/) | 355 | Коротко; буллеты×9; тире 56/1000; ровный ритм 74% |
| 31.7 | 🟡 заметный ИИ | [geely-geometry-zaryadka-i-likvidnost](/blog/geely-geometry-zaryadka-i-likvidnost/) | 571 | Коротко; Что запомнить; тире 50/1000; шаблонные H2×4 |
| 31.7 | 🟡 заметный ИИ | [lizing-elektromobilya-2026](/blog/lizing-elektromobilya-2026/) | 1066 | Коротко; Что запомнить; буллеты×3; тире 37/1000 |
| 31.7 | 🟡 заметный ИИ | [voyah-ceny-zaryadka-2026](/blog/voyah-ceny-zaryadka-2026/) | 382 | Коротко; буллеты×8; тире 54/1000; ровный ритм 82% |
| 31.6 | 🟡 заметный ИИ | [pandora-mini-711c](/blog/pandora-mini-711c/) | 863 | Коротко; Что запомнить; буллеты×3 |
| 31.6 | 🟡 заметный ИИ | [zeekr-001-2026-zaryadka-harakteristiki](/blog/zeekr-001-2026-zaryadka-harakteristiki/) | 474 | Коротко; буллеты×13; тире 42/1000; ровный ритм 70% |
| 31.4 | 🟡 заметный ИИ | [skolko-sluzhit-elektromobilya](/blog/skolko-sluzhit-elektromobilya/) | 1178 | Коротко; Что запомнить; тире 46/1000 |
| 31.4 | 🟡 заметный ИИ | [stanciya-v-kvartire-tyanut-li-avtomaty](/blog/stanciya-v-kvartire-tyanut-li-avtomaty/) | 1219 | клише×1; Коротко; Что запомнить; тире 45/1000 |
| 31.4 | 🟡 заметный ИИ | [winter-ev-2026](/blog/winter-ev-2026/) | 1367 | Коротко; Что запомнить; тире 49/1000; ровный ритм 67%; шаблонные H2×3 |
| 31.3 | 🟡 заметный ИИ | [samyi-deshevyi-elektromobil-2026](/blog/samyi-deshevyi-elektromobil-2026/) | 1169 | Коротко; Что запомнить; тире 41/1000; шаблонные H2×3 |
| 31.2 | 🟡 заметный ИИ | [util-sbor-na-elektromobil-2026](/blog/util-sbor-na-elektromobil-2026/) | 907 | Коротко; Что запомнить; тире 40/1000; шаблонные H2×4 |
| 31.2 | 🟡 заметный ИИ | [zaryadka-dlya-nissan](/blog/zaryadka-dlya-nissan/) | 787 | Коротко; буллеты×10; тире 48/1000 |
| 31.1 | 🟡 заметный ИИ | [zazemlenie-dlya-zaryadki-elektromobilya](/blog/zazemlenie-dlya-zaryadki-elektromobilya/) | 774 | Коротко; Что запомнить; тире 40/1000; шаблонные H2×3 |
| 30.9 | 🟡 заметный ИИ | [zeekr-9x-reduktor-problema](/blog/zeekr-9x-reduktor-problema/) | 746 | Коротко; Что запомнить; тире 44/1000; шаблонные H2×6 |
| 30.7 | 🟡 заметный ИИ | [elektromobil-dlya-taksi](/blog/elektromobil-dlya-taksi/) | 981 | Коротко; Что запомнить; тире 37/1000 |
| 30.7 | 🟡 заметный ИИ | [zeekr-7x-2026-zaryadka-harakteristiki](/blog/zeekr-7x-2026-zaryadka-harakteristiki/) | 359 | Коротко; буллеты×8; тире 47/1000 |
| 30.7 | 🟡 заметный ИИ | [zeekr-9x-gibrid-cena-zaryadka-2026](/blog/zeekr-9x-gibrid-cena-zaryadka-2026/) | 261 | Коротко; буллеты×7; тире 61/1000 |
| 30.6 | 🟡 заметный ИИ | [exlantix-et-zaryadka-cena-2026](/blog/exlantix-et-zaryadka-cena-2026/) | 482 | Коротко; буллеты×12; тире 45/1000; ровный ритм 75% |
| 30.6 | 🟡 заметный ИИ | [zeekr-8x-gibrid-cena-zaryadka-2026](/blog/zeekr-8x-gibrid-cena-zaryadka-2026/) | 333 | Коротко; буллеты×8; тире 54/1000 |
| 30.5 | 🟡 заметный ИИ | [likvidnost-kitayskikh-elektromobiley](/blog/likvidnost-kitayskikh-elektromobiley/) | 693 | Коротко; Что запомнить; шаблонные H2×3 |
| 30.5 | 🟡 заметный ИИ | [xiaomi-su7-cena-zaryadka-2026](/blog/xiaomi-su7-cena-zaryadka-2026/) | 408 | Коротко; буллеты×8; тире 39/1000; ровный ритм 70% |
| 30.5 | 🟡 заметный ИИ | [zaryadka-dlya-evolute](/blog/zaryadka-dlya-evolute/) | 746 | Коротко; буллеты×12; тире 57/1000 |
| 30.4 | 🟡 заметный ИИ | [bystroaya-zaryadka-kazhdyj-den](/blog/bystroaya-zaryadka-kazhdyj-den/) | 558 | Коротко; тире 41/1000; шаблонные H2×4 |
| 30.3 | 🟡 заметный ИИ | [bezopasnaya-zaryadka-elektromobilya](/blog/bezopasnaya-zaryadka-elektromobilya/) | 787 | Коротко; Что запомнить; тире 41/1000 |
| 30.3 | 🟡 заметный ИИ | [zapchasti-i-servis-dlya-seryx-ev](/blog/zapchasti-i-servis-dlya-seryx-ev/) | 584 | Коротко; Что запомнить; тире 35/1000; шаблонные H2×4 |
| 30.2 | 🟡 заметный ИИ | [leapmotor-2026-ceny-zaryadka](/blog/leapmotor-2026-ceny-zaryadka/) | 510 | Коротко; буллеты×13; тире 41/1000 |
| 30.1 | 🟡 заметный ИИ | [exlantix-v-rossii-2026](/blog/exlantix-v-rossii-2026/) | 608 | Коротко; буллеты×9; тире 52/1000 |
| 30.1 | 🟡 заметный ИИ | [xiaomi-yu7-cena-zaryadka-2026](/blog/xiaomi-yu7-cena-zaryadka-2026/) | 359 | Коротко; буллеты×8; тире 44/1000 |
| 29.9 | 🟡 заметный ИИ | [aito-m5-cena-zaryadka-2026](/blog/aito-m5-cena-zaryadka-2026/) | 412 | Коротко; буллеты×8; тире 63/1000 |
| 29.9 | 🟡 заметный ИИ | [leapmotor-app-telematics](/blog/leapmotor-app-telematics/) | 474 | Коротко; тире 35/1000; шаблонные H2×4 |
| 29.9 | 🟡 заметный ИИ | [stanciya-ne-rabotaet](/blog/stanciya-ne-rabotaet/) | 439 | Коротко; тире 38/1000; шаблонные H2×3 |
| 29.8 | 🟡 заметный ИИ | [lixiang-l7-cena-zaryadka-2026](/blog/lixiang-l7-cena-zaryadka-2026/) | 344 | Коротко; буллеты×8; тире 61/1000 |
| 29.6 | 🟡 заметный ИИ | [hongqi-e-hs9-probeg-i-12v](/blog/hongqi-e-hs9-probeg-i-12v/) | 644 | Коротко; Что запомнить; тире 45/1000 |
| 29.6 | 🟡 заметный ИИ | [zaryadnoe-ustroystvo-dlya-elektromobilya](/blog/zaryadnoe-ustroystvo-dlya-elektromobilya/) | 1824 | Коротко; буллеты×6; тире 41/1000 |
| 29.6 | 🟡 заметный ИИ | [zeekr-001-zaryadka-doma](/blog/zeekr-001-zaryadka-doma/) | 889 | Коротко; Что запомнить; шаблонные H2×3 |
| 29.5 | 🟡 заметный ИИ | [bystraya-zaryadka-elektromobilya](/blog/bystraya-zaryadka-elektromobilya/) | 2145 | Коротко; буллеты×3; тире 37/1000; шаблонные H2×3 |
| 29.5 | 🟡 заметный ИИ | [lixiang-l9-2026-cena-zaryadka](/blog/lixiang-l9-2026-cena-zaryadka/) | 459 | Коротко; буллеты×13; тире 47/1000 |
| 29.5 | 🟡 заметный ИИ | [zeekr-001-ne-zaryazhaetsya](/blog/zeekr-001-ne-zaryazhaetsya/) | 639 | Коротко; Что запомнить; тире 42/1000; ровный ритм 69% |
| 29.4 | 🟡 заметный ИИ | [avatr-12-cena-zaryadka-2026](/blog/avatr-12-cena-zaryadka-2026/) | 451 | Коротко; буллеты×16; тире 39/1000 |
| 29.4 | 🟡 заметный ИИ | [geely-v-rossii-2026](/blog/geely-v-rossii-2026/) | 807 | Коротко; буллеты×16; тире 38/1000 |
| 29.4 | 🟡 заметный ИИ | [zeekr-009-elektromobil-cena-zaryadka-2026](/blog/zeekr-009-elektromobil-cena-zaryadka-2026/) | 555 | Коротко; буллеты×13; тире 48/1000 |
| 29.3 | 🟡 заметный ИИ | [avatr-v-rossii-2026](/blog/avatr-v-rossii-2026/) | 672 | Коротко; буллеты×12; тире 47/1000 |
| 29.3 | 🟡 заметный ИИ | [zeekr-v-rossii-2026](/blog/zeekr-v-rossii-2026/) | 799 | Коротко; буллеты×9; тире 41/1000 |
| 29.1 | 🟡 заметный ИИ | [elektromobili-v-rossii-2026-statistika](/blog/elektromobili-v-rossii-2026-statistika/) | 514 | Коротко; буллеты×3; тире 70/1000 |
| 29.1 | 🟡 заметный ИИ | [zaryadka-elektromobilya-v-garazhe](/blog/zaryadka-elektromobilya-v-garazhe/) | 942 | Коротко; Что запомнить; тире 56/1000 |
| 29.0 | 🟡 заметный ИИ | [umo-5-elektromobil-cena-harakteristiki-2026](/blog/umo-5-elektromobil-cena-harakteristiki-2026/) | 661 | Коротко; буллеты×8; тире 49/1000 |
| 28.9 | 🟡 заметный ИИ | [mg-zs-ev-mg4-zaryadka-12v](/blog/mg-zs-ev-mg4-zaryadka-12v/) | 520 | Коротко; Что запомнить; тире 50/1000 |
| 28.8 | 🟡 заметный ИИ | [rastamozhka-elektromobilya](/blog/rastamozhka-elektromobilya/) | 1384 | Коротко; Что запомнить; тире 37/1000 |
| 28.7 | 🟡 заметный ИИ | [elektromobil-iz-kitaya-kak-privezti](/blog/elektromobil-iz-kitaya-kak-privezti/) | 1295 | Коротко; Что запомнить; тире 49/1000 |
| 28.6 | 🟡 заметный ИИ | [stoit-li-pokupat-elektromobil](/blog/stoit-li-pokupat-elektromobil/) | 944 | Коротко; Что запомнить; тире 52/1000 |
| 28.3 | 🟡 заметный ИИ | [evolute-0x13-ne-zaryazhaetsya](/blog/evolute-0x13-ne-zaryazhaetsya/) | 534 | Коротко; шаблонные H2×3 |
| 28.3 | 🟡 заметный ИИ | [zaryadka-na-dache-elektromobil](/blog/zaryadka-na-dache-elektromobil/) | 1003 | Коротко; Что запомнить; тире 49/1000 |
| 28.2 | 🟡 заметный ИИ | [elektromobil-s-probegom](/blog/elektromobil-s-probegom/) | 1512 | Коротко; тире 40/1000; шаблонные H2×4 |
| 28.2 | 🟡 заметный ИИ | [obsluzhivanie-elektromobilya](/blog/obsluzhivanie-elektromobilya/) | 1029 | Коротко; тире 36/1000; шаблонные H2×3 |
| 28.0 | 🟡 заметный ИИ | [article_zapravka](/blog/article_zapravka/) | 541 | Коротко; тире 53/1000; шаблонные H2×3 |
| 27.9 | 🟡 заметный ИИ | [udlinitel-dlya-zaryadki-elektromobilya](/blog/udlinitel-dlya-zaryadki-elektromobilya/) | 1151 | Коротко; Что запомнить; тире 44/1000 |
| 27.9 | 🟡 заметный ИИ | [zaryadka-dlya-byd](/blog/zaryadka-dlya-byd/) | 1246 | Коротко; буллеты×5; тире 50/1000 |
| 27.8 | 🟡 заметный ИИ | [akkumulyator-12v-elektromobilya](/blog/akkumulyator-12v-elektromobilya/) | 765 | Коротко; Что запомнить; шаблонные H2×3 |
| 27.6 | 🟡 заметный ИИ | [privoz-elektromobilya-iz-kitaya](/blog/privoz-elektromobilya-iz-kitaya/) | 1169 | Коротко; Что запомнить; тире 49/1000 |
| 27.6 | 🟡 заметный ИИ | [skolko-zhivet-batareya-elektromobilya](/blog/skolko-zhivet-batareya-elektromobilya/) | 671 | Коротко; тире 41/1000; шаблонные H2×4 |
| 27.6 | 🟡 заметный ИИ | [zamena-batarei-elektromobilya](/blog/zamena-batarei-elektromobilya/) | 1040 | клише×1; Коротко; Что запомнить |
| 27.4 | 🟡 заметный ИИ | [skolko-stoit-zaryadit-elektromobil](/blog/skolko-stoit-zaryadit-elektromobil/) | 1252 | Коротко; буллеты×5 |
| 27.2 | 🟡 заметный ИИ | [nissan-leaf-v-rossii](/blog/nissan-leaf-v-rossii/) | 1365 | Коротко; Что запомнить; тире 43/1000 |
| 27.2 | 🟡 заметный ИИ | [skolko-zaryazhaetsya-elektromobil](/blog/skolko-zaryazhaetsya-elektromobil/) | 554 | Коротко; тире 36/1000; ровный ритм 72%; шаблонные H2×3 |
| 27.1 | 🟡 заметный ИИ | [bystroaya-zaryadka-elektromobilya](/blog/bystroaya-zaryadka-elektromobilya/) | 808 | Коротко; тире 47/1000; шаблонные H2×3 |
| 26.8 | 🟡 заметный ИИ | [zeekr-001-kakoj-adapter-vybrat](/blog/zeekr-001-kakoj-adapter-vybrat/) | 523 | Коротко; Что запомнить; ровный ритм 65% |
| 26.7 | 🟡 заметный ИИ | [strahovka-elektromobilya](/blog/strahovka-elektromobilya/) | 1530 | Коротко; тире 39/1000; шаблонные H2×3 |
| 26.7 | 🟡 заметный ИИ | [zaryadka-podogrev-shtraf](/blog/zaryadka-podogrev-shtraf/) | 391 | Коротко; тире 40/1000; шаблонные H2×3 |
| 26.7 | 🟡 заметный ИИ | [zaryadnaya-stanciya-7-kvt](/blog/zaryadnaya-stanciya-7-kvt/) | 866 | Коротко; Что запомнить; тире 39/1000 |
| 26.6 | 🟡 заметный ИИ | [vyezdnoy-zaryadka-elektromobilya](/blog/vyezdnoy-zaryadka-elektromobilya/) | 676 | Коротко; тире 47/1000; шаблонные H2×4 |
| 26.5 | 🟡 заметный ИИ | [deepal-s07-razem-i-zaryadka](/blog/deepal-s07-razem-i-zaryadka/) | 695 | Коротко; Что запомнить; тире 40/1000 |
| 26.5 | 🟡 заметный ИИ | [exlantix-et-es-sterra-razem-i-zaryadka](/blog/exlantix-et-es-sterra-razem-i-zaryadka/) | 739 | Коротко; Что запомнить; тире 50/1000 |
| 26.4 | 🟡 заметный ИИ | [moskvich-3e-zaryadka-zimoy](/blog/moskvich-3e-zaryadka-zimoy/) | 542 | Коротко; Что запомнить; тире 44/1000; ровный ритм 70% |
| 26.1 | 🟡 заметный ИИ | [handshake-oshibka-dc-zaryadki](/blog/handshake-oshibka-dc-zaryadki/) | 455 | Коротко; тире 37/1000; шаблонные H2×3 |
| 26.1 | 🟡 заметный ИИ | [zaryadka-dlya-elektromobilya](/blog/zaryadka-dlya-elektromobilya/) | 1598 | Коротко; тире 50/1000; шаблонные H2×3 |
| 25.9 | 🟡 заметный ИИ | [batareya-na-moroze-12-voprosov](/blog/batareya-na-moroze-12-voprosov/) | 900 | Коротко; Что запомнить; тире 46/1000 |
| 25.9 | 🟡 заметный ИИ | [gibrid-ili-elektromobil](/blog/gibrid-ili-elektromobil/) | 1035 | Коротко; Что запомнить; тире 41/1000 |
| 25.9 | 🟡 заметный ИИ | [kvt-i-kvt-ch-raznica](/blog/kvt-i-kvt-ch-raznica/) | 587 | Коротко; тире 39/1000; шаблонные H2×3 |
| 25.6 | 🟡 заметный ИИ | [elektromobil-dlya-dostavki-ekonomika](/blog/elektromobil-dlya-dostavki-ekonomika/) | 950 | Коротко; Что запомнить; тире 48/1000 |
| 25.5 | 🟡 заметный ИИ | [gibrid-zimoy](/blog/gibrid-zimoy/) | 1344 | Коротко; тире 37/1000; шаблонные H2×3 |
| 25.5 | 🟡 заметный ИИ | [perehodnik-dlya-zaryadki-elektromobilya](/blog/perehodnik-dlya-zaryadki-elektromobilya/) | 736 | Коротко; Что запомнить; тире 44/1000 |
| 25.5 | 🟡 заметный ИИ | [zeekr-7x-kakoy-adapter](/blog/zeekr-7x-kakoy-adapter/) | 1358 | Коротко; тире 43/1000; шаблонные H2×3 |
| 25.3 | 🟡 заметный ИИ | [zapravka-elektromobilya](/blog/zapravka-elektromobilya/) | 1514 | Коротко; тире 39/1000; шаблонные H2×5 |
| 25.1 | 🟡 заметный ИИ | [li-l7-battery-heat](/blog/li-l7-battery-heat/) | 279 | Коротко; тире 39/1000; ровный ритм 67% |
| 25.0 | 🟡 заметный ИИ | [voyah-app-telematics](/blog/voyah-app-telematics/) | 532 | Коротко; тире 35/1000; шаблонные H2×3 |
| 25.0 | 🟡 заметный ИИ | [zeekr-7x-trassa-dc-800v](/blog/zeekr-7x-trassa-dc-800v/) | 1222 | Коротко; тире 40/1000; шаблонные H2×3 |
| 24.9 | 🟡 заметный ИИ | [plata-za-prostoy-na-zaryadnyh-stanciyah](/blog/plata-za-prostoy-na-zaryadnyh-stanciyah/) | 708 | Коротко; ровный ритм 68%; шаблонные H2×5 |
| 24.9 | 🟡 заметный ИИ | [zaryadka-dlya-otelya](/blog/zaryadka-dlya-otelya/) | 948 | Коротко; шаблонные H2×4 |
| 24.8 | 🟡 заметный ИИ | [karta-elektrozapravok](/blog/karta-elektrozapravok/) | 1810 | Коротко; шаблонные H2×4 |
| 24.7 | 🟡 заметный ИИ | [kak-prodat-elektromobil](/blog/kak-prodat-elektromobil/) | 485 | Коротко; тире 59/1000 |
| 24.7 | 🟡 заметный ИИ | [plyusy-i-minusy-elektromobilya](/blog/plyusy-i-minusy-elektromobilya/) | 970 | Коротко; Что запомнить; тире 52/1000 |
| 24.7 | 🟡 заметный ИИ | [workersbee-vs-auxus](/blog/workersbee-vs-auxus/) | 228 | Коротко; тире 39/1000 |
| 24.5 | 🟡 заметный ИИ | [xpeng-app-telematics](/blog/xpeng-app-telematics/) | 555 | Коротко; шаблонные H2×3 |
| 24.4 | 🟡 заметный ИИ | [luchshie-elektromobili-2026](/blog/luchshie-elektromobili-2026/) | 1558 | Коротко; шаблонные H2×4 |
| 24.3 | 🟡 заметный ИИ | [phev-rossiya-2026](/blog/phev-rossiya-2026/) | 706 | Коротко; тире 42/1000; ровный ритм 72% |
| 23.9 | 🟡 заметный ИИ | [avtokredit-na-elektromobil](/blog/avtokredit-na-elektromobil/) | 980 | Коротко; тире 36/1000 |
| 23.8 | 🟡 заметный ИИ | [kak-zaryadit-elektromobil](/blog/kak-zaryadit-elektromobil/) | 1558 | Коротко; тире 56/1000 |
| 23.8 | 🟡 заметный ИИ | [leapmotor-kupit-2026](/blog/leapmotor-kupit-2026/) | 275 | Коротко; тире 54/1000; ровный ритм 78% |
| 23.8 | 🟡 заметный ИИ | [rasxod-zimoy-bortovoy-kompyuter](/blog/rasxod-zimoy-bortovoy-kompyuter/) | 564 | Коротко; шаблонные H2×4 |
| 23.8 | 🟡 заметный ИИ | [zaryadka-v-zhk-bez-mashinomesta](/blog/zaryadka-v-zhk-bez-mashinomesta/) | 665 | Коротко; буллеты×3; тире 45/1000 |
| 23.6 | 🟡 заметный ИИ | [avatr-app-telematics](/blog/avatr-app-telematics/) | 404 | Коротко; тире 39/1000 |
| 23.5 | 🟡 заметный ИИ | [avatr-11-12-esp-teploobmennik](/blog/avatr-11-12-esp-teploobmennik/) | 1311 | клише×1; Коротко; тире 37/1000 |
| 23.5 | 🟡 заметный ИИ | [cross-zaryadka-chuzhaya-mashina](/blog/cross-zaryadka-chuzhaya-mashina/) | 1112 | Коротко; тире 42/1000 |
| 23.5 | 🟡 заметный ИИ | [gbt-zaryadka-elektromobilya](/blog/gbt-zaryadka-elektromobilya/) | 708 | Коротко; тире 39/1000; ровный ритм 71% |
| 23.5 | 🟡 заметный ИИ | [strakhovka-ev-phev-2026](/blog/strakhovka-ev-phev-2026/) | 683 | Коротко; тире 49/1000 |
| 23.2 | 🟡 заметный ИИ | [geely-ex5-zaryadka](/blog/geely-ex5-zaryadka/) | 678 | Коротко; тире 45/1000 |
| 23.1 | 🟡 заметный ИИ | [domashnyaya-zaryadka-elektromobilya](/blog/domashnyaya-zaryadka-elektromobilya/) | 1241 | Коротко; тире 46/1000 |
| 23.1 | 🟡 заметный ИИ | [gbt-stancii-2026](/blog/gbt-stancii-2026/) | 533 | Коротко; тире 41/1000 |
| 23.1 | 🟡 заметный ИИ | [subsidii-na-elektromobil-2026](/blog/subsidii-na-elektromobil-2026/) | 1474 | Коротко; шаблонные H2×5 |
| 22.9 | 🟡 заметный ИИ | [li-auto-l7-zaryadka-i-obsluzhivanie](/blog/li-auto-l7-zaryadka-i-obsluzhivanie/) | 386 | Коротко; тире 38/1000; ровный ритм 87% |
| 22.8 | 🟡 заметный ИИ | [zaryadnaya-stanciya-dlya-doma](/blog/zaryadnaya-stanciya-dlya-doma/) | 1571 | Коротко; тире 55/1000 |
| 22.8 | 🟡 заметный ИИ | [zeekr-009-trassa-dc](/blog/zeekr-009-trassa-dc/) | 604 | Коротко; буллеты×3 |
| 22.7 | 🟡 заметный ИИ | [kupit-zaryadku-dlya-elektromobilya](/blog/kupit-zaryadku-dlya-elektromobilya/) | 665 | Коротко; тире 42/1000 |
| 22.7 | 🟡 заметный ИИ | [rozetka-dlya-zaryadki-elektromobilya](/blog/rozetka-dlya-zaryadki-elektromobilya/) | 602 | Коротко; тире 56/1000; ровный ритм 70% |
| 22.6 | 🟡 заметный ИИ | [stanciya-otdaet-menshe-moshchnosti](/blog/stanciya-otdaet-menshe-moshchnosti/) | 666 | Коротко |
| 22.5 | 🟡 заметный ИИ | [li-auto-master-account](/blog/li-auto-master-account/) | 583 | Коротко; тире 37/1000 |
| 22.5 | 🟡 заметный ИИ | [vybor-tarifa-dlya-domashnoy-zaryadki](/blog/vybor-tarifa-dlya-domashnoy-zaryadki/) | 607 | Коротко; шаблонные H2×4 |
| 22.5 | 🟡 заметный ИИ | [zaryadka-v-parkinge-elektromobilya](/blog/zaryadka-v-parkinge-elektromobilya/) | 1654 | Коротко; тире 39/1000 |
| 22.2 | 🟡 заметный ИИ | [nissan-leaf-batareya-soh-i-zamena](/blog/nissan-leaf-batareya-soh-i-zamena/) | 568 | Коротко; тире 52/1000 |
| 22.1 | 🟡 заметный ИИ | [zeekr-7x-zaryadka-doma](/blog/zeekr-7x-zaryadka-doma/) | 901 | Коротко; Что запомнить |
| 22.0 | 🟡 заметный ИИ | [tesla-remont-i-servis-v-rossii](/blog/tesla-remont-i-servis-v-rossii/) | 443 | Коротко; тире 47/1000 |
| 22.0 | 🟡 заметный ИИ | [xpeng-ofitsialno-rossiya-2026](/blog/xpeng-ofitsialno-rossiya-2026/) | 289 | Коротко; тире 48/1000 |
| 21.9 | 🟡 заметный ИИ | [soh-pri-pokupke-bu-elektromobilya](/blog/soh-pri-pokupke-bu-elektromobilya/) | 834 | Коротко; тире 47/1000 |
| 21.9 | 🟡 заметный ИИ | [zimnyaya-zaryadka-medlennee](/blog/zimnyaya-zaryadka-medlennee/) | 434 | Коротко |
| 21.8 | 🟡 заметный ИИ | [transportnyi-nalog-elektromobilya](/blog/transportnyi-nalog-elektromobilya/) | 578 | Коротко |
| 21.7 | 🟡 заметный ИИ | [zaryadka-dlya-geely](/blog/zaryadka-dlya-geely/) | 1582 | Коротко; тире 40/1000; ровный ритм 72% |
| 21.5 | 🟡 заметный ИИ | [voyah-free-osobennosti](/blog/voyah-free-osobennosti/) | 342 | Коротко; тире 43/1000 |
| 21.4 | 🟡 заметный ИИ | [article_mobilnaya](/blog/article_mobilnaya/) | 492 | Коротко; тире 48/1000 |
| 21.4 | 🟡 заметный ИИ | [xpeng-kakoy-adapter](/blog/xpeng-kakoy-adapter/) | 691 | Коротко; буллеты×3 |
| 21.4 | 🟡 заметный ИИ | [zeekr-001-razyom-i-problemy](/blog/zeekr-001-razyom-i-problemy/) | 450 | Коротко; тире 48/1000; ровный ритм 67% |
| 21.3 | 🟡 заметный ИИ | [besplatnye-trassy-parkovka-ev](/blog/besplatnye-trassy-parkovka-ev/) | 456 | Коротко |
| 21.3 | 🟡 заметный ИИ | [denza-d9-ne-zaryazhaetsya](/blog/denza-d9-ne-zaryazhaetsya/) | 952 | клише×1; Коротко |
| 21.2 | 🟡 заметный ИИ | [obnovleniya-po-sim-elektromobilya](/blog/obnovleniya-po-sim-elektromobilya/) | 981 | клише×1; Коротко |
| 20.9 | 🟡 заметный ИИ | [zaryadki-dlya-elektromobiley-v-ekaterinburge](/blog/zaryadki-dlya-elektromobiley-v-ekaterinburge/) | 991 | тире 41/1000; шаблонные H2×3 |
| 20.8 | 🟡 заметный ИИ | [zeekr-x-kupit-2026](/blog/zeekr-x-kupit-2026/) | 218 | Коротко; тире 77/1000; ровный ритм 77% |
| 20.6 | 🟡 заметный ИИ | [planirovanie-dalnej-poezdki-ev](/blog/planirovanie-dalnej-poezdki-ev/) | 587 | Коротко |
| 20.5 | 🟡 заметный ИИ | [kakoy-elektromobil-vybrat-2026](/blog/kakoy-elektromobil-vybrat-2026/) | 1213 | Коротко; тире 46/1000 |
| 20.5 | 🟡 заметный ИИ | [rukovodstva-na-russkom](/blog/rukovodstva-na-russkom/) | 437 | Коротко; тире 43/1000 |
| 20.4 | 🟡 заметный ИИ | [denza-app-telematics](/blog/denza-app-telematics/) | 476 | Коротко; тире 39/1000 |
| 20.4 | 🟡 заметный ИИ | [kia-ev9-zaryadka](/blog/kia-ev9-zaryadka/) | 494 | Коротко |
| 20.4 | 🟡 заметный ИИ | [toyota-bz3x-bz4x-razyom](/blog/toyota-bz3x-bz4x-razyom/) | 507 | Коротко; тире 39/1000 |
| 20.3 | 🟡 заметный ИИ | [byd-master-account](/blog/byd-master-account/) | 561 | Коротко |
| 20.3 | 🟡 заметный ИИ | [tipy-razyomov-zaryadki](/blog/tipy-razyomov-zaryadki/) | 1096 | Коротко; тире 51/1000 |
| 20.3 | 🟡 заметный ИИ | [zeekr-master-account](/blog/zeekr-master-account/) | 679 | Коротко |
| 20.2 | 🟡 заметный ИИ | [atom-elektromobil-cena-harakteristiki-2026](/blog/atom-elektromobil-cena-harakteristiki-2026/) | 598 | Коротко; тире 40/1000 |
| 20.2 | 🟡 заметный ИИ | [byd-seal-zaryadka-doma](/blog/byd-seal-zaryadka-doma/) | 399 | Коротко; тире 42/1000 |
| 20.1 | 🟡 заметный ИИ | [stanciya-otdaet-menshe-moshchnosti-150-kt-ot-60-80](/blog/stanciya-otdaet-menshe-moshchnosti-150-kt-ot-60-80/) | 802 | Коротко; ровный ритм 78%; шаблонные H2×6 |
| 20.1 | 🟡 заметный ИИ | [zaryadka-dlya-voyah](/blog/zaryadka-dlya-voyah/) | 1352 | Коротко; тире 44/1000 |
| 20.1 | 🟡 заметный ИИ | [zeekr-7x-ne-zaryazhaetsya](/blog/zeekr-7x-ne-zaryazhaetsya/) | 1554 | Коротко; тире 39/1000 |
| 20.0 | 🟠 пограничная | [ustanovka-zaryadnoy-stancii-elektromobilya](/blog/ustanovka-zaryadnoy-stancii-elektromobilya/) | 1606 | Коротко; тире 49/1000 |
| 19.9 | 🟠 пограничная | [deepal-kupit-2026](/blog/deepal-kupit-2026/) | 239 | Коротко; тире 79/1000; ровный ритм 67% |
| 19.9 | 🟠 пограничная | [geely-ex5-kupit-2026](/blog/geely-ex5-kupit-2026/) | 269 | Коротко; тире 40/1000; ровный ритм 67% |
| 19.9 | 🟠 пограничная | [zapas-hoda-elektromobilya](/blog/zapas-hoda-elektromobilya/) | 545 | Коротко |
| 19.9 | 🟠 пограничная | [zaryadka-vo-dvore](/blog/zaryadka-vo-dvore/) | 963 | Коротко; тире 47/1000 |
| 19.8 | 🟠 пограничная | [zaryadka-dlya-zhk-i-ofisa](/blog/zaryadka-dlya-zhk-i-ofisa/) | 838 | Коротко; тире 35/1000; ровный ритм 67% |
| 19.7 | 🟠 пограничная | [moskvich-3e-trassa-ccs2](/blog/moskvich-3e-trassa-ccs2/) | 485 | Коротко |
| 19.6 | 🟠 пограничная | [voyah-gibrid-rezhim-zaryadki](/blog/voyah-gibrid-rezhim-zaryadki/) | 686 | Коротко; тире 40/1000 |
| 19.6 | 🟠 пограничная | [zeekr-009-zaryadka-doma](/blog/zeekr-009-zaryadka-doma/) | 644 | Коротко; тире 35/1000; ровный ритм 78% |
| 19.5 | 🟠 пограничная | [byd-dolphin-zaryadka-doma](/blog/byd-dolphin-zaryadka-doma/) | 430 | Коротко; тире 44/1000 |
| 19.5 | 🟠 пограничная | [skolko-kilovatt-dlya-zaryadki-elektromobilya](/blog/skolko-kilovatt-dlya-zaryadki-elektromobilya/) | 1271 | Коротко; тире 44/1000 |
| 19.5 | 🟠 пограничная | [to-elektromobilya-ceny](/blog/to-elektromobilya-ceny/) | 575 | тире 46/1000; шаблонные H2×3 |
| 19.5 | 🟠 пограничная | [zaryadka-dlya-gibrida](/blog/zaryadka-dlya-gibrida/) | 1319 | Коротко; тире 43/1000 |
| 19.4 | 🟠 пограничная | [byd-dolphin-kupit-2026](/blog/byd-dolphin-kupit-2026/) | 252 | Коротко; тире 63/1000 |
| 19.4 | 🟠 пограничная | [gac-aion-kupit-2026](/blog/gac-aion-kupit-2026/) | 261 | Коротко; тире 57/1000 |
| 19.3 | 🟠 пограничная | [elektromobil-7-mest-dlya-semi](/blog/elektromobil-7-mest-dlya-semi/) | 1727 | Коротко; тире 37/1000 |
| 19.3 | 🟠 пограничная | [voyah-kupit-2026](/blog/voyah-kupit-2026/) | 384 | Коротко; тире 59/1000 |
| 19.2 | 🟠 пограничная | [proverka-pered-pokupkoy](/blog/proverka-pered-pokupkoy/) | 544 | Коротко; тире 36/1000 |
| 19.2 | 🟠 пограничная | [voyah-free-zaryadka-doma](/blog/voyah-free-zaryadka-doma/) | 645 | Коротко; тире 38/1000 |
| 19.0 | 🟠 пограничная | [aito-kupit-2026](/blog/aito-kupit-2026/) | 304 | Коротко; тире 52/1000 |
| 19.0 | 🟠 пограничная | [avatr-kupit-2026](/blog/avatr-kupit-2026/) | 249 | Коротко; тире 52/1000 |
| 19.0 | 🟠 пограничная | [changan-v-rossii-2026](/blog/changan-v-rossii-2026/) | 884 | буллеты×4; тире 66/1000 |
| 19.0 | 🟠 пограничная | [exlantix-et-es-kupit-2026](/blog/exlantix-et-es-kupit-2026/) | 384 | Коротко; тире 57/1000 |
| 19.0 | 🟠 пограничная | [li-mega-kupit-2026](/blog/li-mega-kupit-2026/) | 291 | Коротко; тире 51/1000 |
| 19.0 | 🟠 пограничная | [skolko-zaryazhaetsya-tesla](/blog/skolko-zaryazhaetsya-tesla/) | 615 | Коротко; тире 42/1000 |
| 19.0 | 🟠 пограничная | [tesla-kupit-v-rossii-2026](/blog/tesla-kupit-v-rossii-2026/) | 766 | Коротко; тире 58/1000 |
| 19.0 | 🟠 пограничная | [voyah-free-ne-zaryazhaetsya](/blog/voyah-free-ne-zaryazhaetsya/) | 991 | Коротко |
| 19.0 | 🟠 пограничная | [xiaomi-su7-kupit-2026](/blog/xiaomi-su7-kupit-2026/) | 246 | Коротко; тире 65/1000 |
| 18.9 | 🟠 пограничная | [aito-app-telematics](/blog/aito-app-telematics/) | 474 | Коротко |
| 18.8 | 🟠 пограничная | [besplatnye-zaryadki-dlya-elektromobiley](/blog/besplatnye-zaryadki-dlya-elektromobiley/) | 1598 | тире 43/1000; шаблонные H2×3 |
| 18.3 | 🟠 пограничная | [xiaomi-su7-telematics](/blog/xiaomi-su7-telematics/) | 511 | Коротко |
| 18.2 | 🟠 пограничная | [kitaiskoe-vremya-v-raspisanii-zaryadki-posle-rusifikatsii](/blog/kitaiskoe-vremya-v-raspisanii-zaryadki-posle-rusifikatsii/) | 860 | клише×1; Коротко; ровный ритм 81% |
| 18.1 | 🟠 пограничная | [biznes-na-zaryadnyh-stanciyah](/blog/biznes-na-zaryadnyh-stanciyah/) | 1811 | Коротко |
| 18.1 | 🟠 пограничная | [moskvich-3e-zaryadka-doma](/blog/moskvich-3e-zaryadka-doma/) | 516 | Коротко |
| 18.1 | 🟠 пограничная | [poteri-pri-zaryadke-5-10](/blog/poteri-pri-zaryadke-5-10/) | 787 | Коротко |
| 18.1 | 🟠 пограничная | [zeekr-009-ne-zaryazhaetsya](/blog/zeekr-009-ne-zaryazhaetsya/) | 503 | Коротко; ровный ритм 74% |
| 18.1 | 🟠 пограничная | [zimnoe-khranenie-elektromobilya-parking-2-4-nedeli](/blog/zimnoe-khranenie-elektromobilya-parking-2-4-nedeli/) | 651 | Коротко |
| 18.0 | 🟠 пограничная | [deepal-telematics](/blog/deepal-telematics/) | 388 | Коротко |
| 17.6 | 🟠 пограничная | [dongfeng-box-telematics](/blog/dongfeng-box-telematics/) | 487 | Коротко |
| 17.2 | 🟠 пограничная | [voyah-kakoy-adapter](/blog/voyah-kakoy-adapter/) | 562 | Коротко |
| 17.2 | 🟠 пограничная | [xpeng-g6-g9-zaryadka-doma](/blog/xpeng-g6-g9-zaryadka-doma/) | 967 | Коротко |
| 17.1 | 🟠 пограничная | [zeekr-007-zaryadka](/blog/zeekr-007-zaryadka/) | 1131 | Коротко |
| 17.0 | 🟠 пограничная | [xpeng-g6-g9-ne-zaryazhaetsya](/blog/xpeng-g6-g9-ne-zaryazhaetsya/) | 1082 | Коротко |
| 16.9 | 🟠 пограничная | [moskvich-3e-na-stanciyah](/blog/moskvich-3e-na-stanciyah/) | 462 | Коротко |
| 16.9 | 🟠 пограничная | [moskvich-3e-ne-zaryazhaetsya](/blog/moskvich-3e-ne-zaryazhaetsya/) | 570 | Коротко |
| 15.9 | 🟠 пограничная | [xpeng-trassa-800v](/blog/xpeng-trassa-800v/) | 801 | Коротко |
| 15.9 | 🟠 пограничная | [zaryadki-elektromobiley-po-gorodam](/blog/zaryadki-elektromobiley-po-gorodam/) | 1228 | тире 43/1000 |
| 15.5 | 🟠 пограничная | [zaryadka-elektromobilya-v-dozhd](/blog/zaryadka-elektromobilya-v-dozhd/) | 1214 | тире 36/1000 |
| 14.8 | 🟠 пограничная | [zaryadki-dlya-elektromobiley-v-spb](/blog/zaryadki-dlya-elektromobiley-v-spb/) | 1702 | тире 37/1000 |
| 14.0 | 🟠 пограничная | [changan-q05-q06-q07-razem-i-zaryadka](/blog/changan-q05-q06-q07-razem-i-zaryadka/) | 714 | тире 47/1000 |
| 13.9 | 🟠 пограничная | [parking-zhil](/blog/parking-zhil/) | 4573 | клише×1; Коротко |
| 13.7 | 🟠 пограничная | [elektromobil-v-lizing](/blog/elektromobil-v-lizing/) | 1207 | — |
| 13.7 | 🟠 пограничная | [nastennaya-zaryadnaya-stanciya](/blog/nastennaya-zaryadnaya-stanciya/) | 2187 | тире 42/1000 |
| 13.1 | 🟠 пограничная | [prilozhenie-dlya-zaryadki-elektromobilya](/blog/prilozhenie-dlya-zaryadki-elektromobilya/) | 2482 | тире 39/1000 |
| 12.7 | 🟠 пограничная | [hongqi-v-rossii-2026](/blog/hongqi-v-rossii-2026/) | 516 | тире 48/1000 |
| 11.6 | 🟠 пограничная | [m12-trassa](/blog/m12-trassa/) | 3865 | Коротко |
| 9.4 | 🟢 человеческая | [m11-trassa](/blog/m11-trassa/) | 4201 | Коротко |

## Что это значит и что делать

Только 1 статья из 242 читается как полностью человеческая; 166 несут заметный конвейерный отпечаток. Главные носители — не лексика, а **структура и ритм**: одинаковый скелет, дословные повторяющиеся блоки, ровный ритм предложений, тире-интенсивность.

**План правки (волна «Живой голос 3», по образцу пилотов):**

1. **Волна A (срочно, 19 статей score>35):** полная переработка — интро-ситуация, разбор скелета, ротация CTA и финалок.
2. **Волна B (166 статей 20–35):** точечно — заменить «Коротко» на живой заголовок-вопрос у ~40% статей, ротировать CTA-блок (165 дословных повторов), разбить буллеты «Термин:» в абзацы, снизить плотность тире.
3. **Волна C (56 пограничных):** только ротация CTA и финалок, без глубокой переработки.
4. Приоритет внутри волн — **карточки-лидеры спроса** (маркетинговое тело) и топ-кластеры.

*Отчёт подготовлен Алисой · 23.11.2026 · детектор калиброван на пилотах живого стиля*