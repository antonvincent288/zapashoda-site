/* ============================================================
   GAS v7 (02.11): _leadDoPost понимает формат модалки сайта t='lead'
   (name/contact/city/carModel/product/price/source) — раньше эти поля
   писались не в те колонки (v6 ждал phone/model/items/total).
   Для t='lead' TG-дубль НЕ шлётся: lead.js уже шлёт сообщение в канал напрямую.
   Формат мини-аппа (miniapp) — без изменений.
   Установка: заменить ВЕСЬ код GAS-проекта на этот файл, запустить forumSetup().
   ============================================================ */

/**
 * Запас хода — приёмник заявок + бот + ФОРУМ + ПОЛЬЗОВАТЕЛИ + КАПЧА (GAS) — v6
 *  v6: заявки из мини-аппа в Telegram помечаются «Заявка из мини-аппа ⚡️»;
 *      WEBAPP_URL обновлён на zapashoda-ev.ru/app/ (кнопка /app в боте)
 *  (после деплоя сайта с капчей включите REQUIRE_CAPTCHA = true — ниже)
 *
 * Режим работы (обход ограничения GAS: Telegram не принимает 302-ответ GAS-вебхука):
 *  • Заявки из мини-аппа → POST на /exec → строка в лист «Лиды» + уведомление в личку (работает как раньше)
 *  • /start и другие команды → без вебхука: скрипт сам опрашивает Telegram (getUpdates)
 *    раз в минуту через триггер и отвечает на новые сообщения
 * v8.0 (03.11.2026): КОНФИГУРАТОР ОД (B2B2C) — ветка t='od_order': промокод ZSH-XXXXXX
 *       (скидка 5% клиенту), кэшбэк менеджеру 5–10%, листы «Менеджеры» и «Промокоды»,
 *       HMAC-верификация initData, команды /promo и /bonusweek, sendPhoto в POST_QUEUE (p.photo).
 *       УСТАНОВКА: вставить файл ЦЕЛИКОМ, вернуть TELEGRAM_TOKEN и CHAT_ID,
 *       один раз выполнить odSetup() (листы + реестр менеджеров + команды).
 * v9.0 (04.11.2026): SHOP — Т-Касса (Интернет-эквайринг Т-Банка): t='shop_init' → v2/Init
 *       (PaymentURL), webhook Т-Кассы → лист «Заказы» → одноразовый токен → MailApp +
 *       выдача на success-странице; doGet?t= → PDF. Настройка: shopSetCreds(), shopSetPdf(),
 *       проверка shopSelfTest(false/true). Секреты — только в Script Properties.
 *
 * ЗАПУСК ОДИН РАЗ из редактора: выполните функцию setupBotPolling
 *  (она удалит вебхук, создаст триггер «каждую минуту» и поставит команды меню бота)
 *
 * v3.1: добавлены команды меню /app и /help (обработчики + setBotCommands)
 * v3.2: отложенный постинг в канал — очередь POST_QUEUE публикуется опросником,
 *       у каждого поста URL-кнопка «Открыть гид» (web_app в каналах не работает) + startapp-метка
 * v3.3: состав заказа пишется в таблицу — новая колонка «Состав» (перечень позиций
 *       с количеством и ценой). Если таблица уже создана в старом формате, колонка
 *       добавится автоматически при первой же заявке.
 * v3.5: у каждого поста канала — вторая кнопка «🌐 Сайт zapashoda-ev.ru» (сайт опубликован на GitHub Pages)
 * v3.6: БОТ-КВИЗ «Подбор за 30 секунд»: /quiz или кнопка «🧩 Подбор» → марка → модель → разъёмы,
 *       комплект и ссылки на страницу модели (137 моделей зашиты в бот). Выбор пишется в «Лиды» (t=bot_quiz).
 *       ЕСЛИ ЗАМЕЩАЕТЕ СТАРЫЙ ФАЙЛ: вставьте заново TELEGRAM_TOKEN и CHAT_ID, затем запустите setupBotPolling.
 * v3.4: очередь контента на 30–31.10 (2 поста + первый опрос канала), поддержка опросов
 *       в POST_QUEUE (type: 'poll' → sendPoll). Пост про разъёмы перенесён на 12:00 МСК 30.10.
 *
 * НАСТРОЙКА — три строки ниже:
 *   TELEGRAM_TOKEN — токен из @BotFather
 *   CHAT_ID        — твой Telegram ID (из @userinfobot)
 *   CHANNEL        — юзернейм канала (без @)
 *   WEBAPP_URL     — адрес мини-аппа
 */

const TELEGRAM_TOKEN = 'ВСТАВЬ_ТОКЕН_БОТА';
const CHAT_ID = 'ВСТАВЬ_ТВОЙ_ID';
const CHANNEL = 'zapashoda_ev';
const REQUIRE_CAPTCHA = false; // ← включить true после того, как сайт начнёт отправлять капчу (сделает Алиса)
const WEBAPP_URL = 'https://zapashoda-ev.ru/app/';
const SHEET_NAME = 'Лиды';
const OFFSET_KEY = 'tg_update_offset';
const POSTS_SENT_KEY = 'posts_sent';

// Отложенные посты канала: публикуются автоматически опросником checkUpdates.
// Время указано с часовым поясом МСК (+03:00) — GAS сам разберётся.
// Если вставить файл позже запланированного времени — просроченные уйдут сразу.
// NOTE: посты «зима» и «деньги» уже опубликованы вручную ночью 29.10 (message_id 17, 18) — в очередь не включены.
const POST_QUEUE = [
  { key: 'post_razemy', at: '2026-10-30T12:00:00+03:00',
    text: '🔌 Zeekr и Li Auto заряжаются от китайского разъёма GB/T. Большинство станций в России — Type 2 и CCS2.\n\nБез переходника такие машины не зарядятся почти нигде. Это первая проблема, с которой сталкивается каждый владелец «китайца».\n\nУ какой у вас модели какой разъём — есть в гиде: отдельная страница под каждую из 137 моделей.\n\n📖 Проверить свою модель: @zapashoda_ev_bot\n#разъёмы #адаптеры' },
  { key: 'post_zima_5', at: '2026-10-30T18:00:00+03:00',
    text: '❄️ 5 ошибок новичка на электромобиле зимой\n\n1. Гнать заряд до 100% каждый день. Полный заряд нужен перед дальней дорогой — в городе хватает 80%.\n2. Греть салон на максимуме. Печка — главный пожиратель хода, подогрев сидений и руля экономнее в разы.\n3. Ставить машину на быструю станцию с холодной батареей. Заряд идёт в разы медленнее — сначала прогрейте батарею в поездке.\n4. Оставлять машину надолго на морозе с почти пустой батареей.\n5. Забывать, что зимой хода меньше. Закладывайте запас 30–40% на любое расстояние.\n\nСохраните себе и поделитесь с тем, кто сел за электромобиль первый раз 👇\n#зима #лайфхаки' },
  { key: 'post_batareya', at: '2026-10-31T12:00:00+03:00',
    text: '🔋 Сколько живёт батарея электромобиля?\n\nПростыми словами: почти все производители дают гарантию 8 лет или 150 000 км — за это время батарея должна сохранять не меньше 70% ёмкости.\n\nНа практике деградация идёт медленнее обещаний. Главные враги — постоянные заряды до 100% и долгие простои на морозе с нулём.\n\nКак правильно заряжать именно вашу модель — есть отдельная страница в гиде 👇\n#батарея #цифры' },
  { key: 'poll_cars', at: '2026-10-31T20:00:00+03:00', type: 'poll',
    question: 'На чём вы ездите (или присматриваетесь)?',
    options: ['Zeekr', 'Li Auto / Lixiang', 'BYD', 'Другой электромобиль', 'Пока только присматриваюсь'] },
];

// Кнопки над клавиатурой (reply-клавиатура)
const REPLY_KB = {
  keyboard: [
    [{ text: '🧩 Подбор' }, { text: '🛍️ Каталог' }],
    [{ text: '📖 Справочник' }, { text: '💬 Поддержка' }]
  ],
  resize_keyboard: true,
  input_field_placeholder: 'Выберите раздел'
};

// ==== КВИЗ-ДАННЫЕ: 78 марок / 137 моделей, порядок топ-марок под спрос ====
const QUIZ={"brands":{"BYD":[{"m":"Song Plus EV","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"},{"m":"Song Plus DM-i / Sealion 05","type":"PHEV","ac":"GB/T AC","dc":"— (у большинства нет DC)","freq":"Массовый"},{"m":"Yuan Plus / Atto 3 / Yuan Up / Pro","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Массовый"},{"m":"Dolphin","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Массовый"},{"m":"Han EV / Song L","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"Tang EV / Tang DM-i","type":"BEV/PHEV","ac":"GB/T AC","dc":"GB/T DC (только EV)","freq":"Средний"},{"m":"Seal","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Средний"},{"m":"Seagull","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"Qin Plus DM-i","type":"PHEV","ac":"GB/T AC","dc":"—","freq":"Средний"},{"m":"Fangchengbao Bao 5 / Bao 8","type":"PHEV","ac":"GB/T AC","dc":"GB/T DC (уточнить)","freq":"Средний"},{"m":"Yangwang U8 / U9","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"},{"m":"Han DM-i / Tang DM-i","type":"PHEV","ac":"GB/T AC","dc":"—","freq":"Средний"}],"Voyah":[{"m":"Free EVR (гибрид)","type":"EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"},{"m":"Free EV (ранние официальные RU)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Редкий"},{"m":"Dream / Dreamer (PHEV)","type":"PHEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"Passion / Passion S","type":"PHEV","ac":"GB/T AC","dc":"GB/T DC (уточнить)","freq":"Средний"},{"m":"Courage","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"},{"m":"Taishan","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Zeekr":[{"m":"001 / 001 FR","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"},{"m":"007 / 007GT","type":"BEV","ac":"GB/T AC (1 фаза)","dc":"GB/T DC 800V","freq":"Массовый"},{"m":"7X / X / MIX","type":"BEV","ac":"GB/T AC","dc":"GB/T DC (7X — 800V)","freq":"Массовый"},{"m":"009 / 009 Grand","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"8X / 9X","type":"EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Li Auto":[{"m":"L6 / L7 / L8 / L9 (2022–2025)","type":"EREV","ac":"GB/T AC (1 фаза)","dc":"GB/T DC","freq":"Массовый"},{"m":"ONE","type":"EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"Mega","type":"BEV","ac":"GB/T AC","dc":"GB/T DC 800V","freq":"Средний"},{"m":"i6 / i8","type":"BEV","ac":"GB/T AC","dc":"GB/T DC 800V","freq":"Редкий"}],"Geely":[{"m":"Galaxy E5 / E8 / TT","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"},{"m":"EX5 / Monjaro Hi-P (PHEV)","type":"BEV/PHEV","ac":"GB/T (уточнить RU-поставку)","dc":"GB/T","freq":"Массовый"},{"m":"Geometry C / A","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"Galaxy L7 / Starship 7 (PHEV)","type":"PHEV","ac":"GB/T AC","dc":"— (уточнить)","freq":"Средний"}],"Kia":[{"m":"EV6 (KR)","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Массовый"},{"m":"EV9 (KR)","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Средний"},{"m":"Niro EV / e-Niro","type":"BEV","ac":"Type 1 (KR) / Type 2 (EU)","dc":"CCS1 (KR) / CCS2 (EU)","freq":"Средний"},{"m":"Soul EV (ранние)","type":"BEV","ac":"Type 1","dc":"CHAdeMO","freq":"Редкий"}],"Nissan":[{"m":"Leaf ZE1 (JP / EU)","type":"BEV","ac":"Type 1 (JP) / Type 2 (EU)","dc":"CHAdeMO","freq":"Массовый"},{"m":"Ariya (US)","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Редкий"},{"m":"Sakura","type":"BEV","ac":"Type 1","dc":"CHAdeMO","freq":"Средний"},{"m":"Ariya (JP)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Редкий"}],"Changan":[{"m":"Qiyuan A05 / A06 / A07","type":"EREV/BEV","ac":"GB/T AC","dc":"GB/T DC (уточнить)","freq":"Массовый"},{"m":"Qiyuan Q05 / Q06 / Q07","type":"PHEV","ac":"GB/T AC","dc":"— (уточнить)","freq":"Средний"},{"m":"Nevo E07","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Deepal":[{"m":"S07 (RU официальная)","type":"EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"},{"m":"L07 / S05 / S09","type":"EREV/BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"G318 (RU официальная)","type":"EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"}],"Hongqi":[{"m":"E-QM5","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"E-HS9","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"EH7 / HS7 EV / HS3 EV","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"VW":[{"m":"ID.3 / ID.4 / ID.5 / ID.Buzz","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Массовый"},{"m":"ID.6 (CN-версия)","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"},{"m":"Tayron L (CN, PHEV)","type":"PHEV","ac":"GB/T AC","dc":"—","freq":"Редкий"}],"Tesla":[{"m":"Model 3 / Y (EU)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Массовый"},{"m":"Model S / X (EU)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Редкий"},{"m":"Model 3 / Y / S / X (US)","type":"BEV","ac":"NACS / J1772 (AC)","dc":"NACS","freq":"Средний"}],"MG":[{"m":"ZS EV / MG5 (EU)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"},{"m":"4 (Mulan)","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Средний"},{"m":"HS PHEV / MG 07 (CN)","type":"PHEV","ac":"Type 2 (EU) / GB/T (CN)","dc":"—","freq":"Редкий"}],"Avatr":[{"m":"11 / 12 (официально RU)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Массовый"},{"m":"07 (параллельный)","type":"EREV/BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"AITO":[{"m":"M5 / M7","type":"EREV/BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"M9","type":"EREV/BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"}],"Xiaomi":[{"m":"SU7 / SU7 Ultra","type":"BEV","ac":"GB/T AC","dc":"GB/T DC (Max — 800V)","freq":"Массовый"},{"m":"YU7","type":"BEV","ac":"GB/T AC","dc":"GB/T DC 800V (Max)","freq":"Средний"}],"Xpeng":[{"m":"P7 / P5 / G3","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"},{"m":"G9 / G6","type":"BEV","ac":"GB/T AC","dc":"GB/T DC 800V","freq":"Средний"}],"Leapmotor":[{"m":"C10 / C11 / C01 / B10 / A05","type":"BEV/EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"},{"m":"T03","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Средний"}],"Ora":[{"m":"Good Cat / 03","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Средний"},{"m":"R1 / Black Cat / 07","type":"BEV","ac":"GB/T AC","dc":"GB/T DC (уточнить)","freq":"Редкий"}],"Lynk & Co":[{"m":"01 PHEV (EU-версия)","type":"PHEV","ac":"Type 2 AC","dc":"— (DC нет)","freq":"Редкий"},{"m":"08 / 900 (CN)","type":"EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Exeed":[{"m":"Exlantix ET / ES (Sterra)","type":"BEV","ac":"GB/T AC","dc":"GB/T DC 800V","freq":"Средний"},{"m":"RX PHEV","type":"PHEV","ac":"GB/T AC","dc":"—","freq":"Редкий"}],"Toyota":[{"m":"bZ4X (CN-версия)","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"},{"m":"bZ4X (JP)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Редкий"}],"Lexus":[{"m":"UX300e (CN-версия)","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"},{"m":"RZ (JP)","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Редкий"}],"BMW":[{"m":"i3 / i4 / iX / iX1","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Массовый"},{"m":"iX3 (CN-версия)","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"}],"Renault":[{"m":"Zoe","type":"BEV","ac":"Type 2","dc":"CCS2 (только фаза 2, ~50 кВт) / ранние без DC","freq":"Массовый"},{"m":"Megane e-Tech / Kangoo E-Tech","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Volvo":[{"m":"XC40 Recharge / C40 / EX40","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"},{"m":"XC90 / XC60 T8 (PHEV)","type":"PHEV","ac":"Type 2 AC","dc":"CCS2 (у части, ~50 кВт)","freq":"Средний"}],"Hyundai":[{"m":"Ioniq 5 / Ioniq 6 (KR)","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Массовый"},{"m":"Kona Electric (KR)","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Средний"}],"Mitsubishi":[{"m":"Outlander PHEV (JP / EU)","type":"PHEV","ac":"Type 1 (JP) / Type 2 (EU)","dc":"CHAdeMO","freq":"Массовый"},{"m":"i-MiEV","type":"BEV","ac":"Type 1","dc":"CHAdeMO","freq":"Редкий"}],"M-Hero":[{"m":"917 EV / EVR","type":"BEV/EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"FAW":[{"m":"Bestune NAT","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"}],"Denza (BYD)":[{"m":"D9 EV / D9 DM-i","type":"BEV/PHEV","ac":"GB/T AC","dc":"GB/T DC (только EV)","freq":"Средний"}],"Neta":[{"m":"U / V / X","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"}],"Livan":[{"m":"X3 Pro / S6 Pro","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"}],"Evolute":[{"m":"i-Jet / i-Pro / i-Space / i-Joy / i-JOA","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Массовый"}],"Moskvich":[{"m":"3e / 6","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Массовый"}],"JAC":[{"m":"e-JS1 / e-JS4 / iEVS4","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Skywell":[{"m":"ET5 / EL5","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"SWM":[{"m":"G01 EV и др.","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Kaiyi":[{"m":"E5 EV / X3 EV","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Wuling / Hongguang":[{"m":"Mini EV / Air EV","type":"BEV","ac":"GB/T AC","dc":"— (нет DC)","freq":"Средний"}],"Dongfeng":[{"m":"eπ 008 / Aeolus (Nami, Forthing)","type":"EREV/BEV","ac":"GB/T AC","dc":"GB/T DC (уточнить)","freq":"Средний"}],"GAC":[{"m":"Aion S Plus / Aion V","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Массовый"}],"Seres":[{"m":"5 / SF5","type":"BEV/EREV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"IM Motors":[{"m":"LS6 / L7","type":"BEV","ac":"GB/T AC","dc":"GB/T DC 800V","freq":"Редкий"}],"iCAR":[{"m":"03","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Средний"}],"Luxeed (Chery/Huawei)":[{"m":"R7","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Stelato (BAIC/Huawei)":[{"m":"S9","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Onvo (NIO)":[{"m":"L60","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Lotus":[{"m":"Eletre / Emeya","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Редкий"}],"HiPhi":[{"m":"X / Z","type":"BEV","ac":"GB/T (CN) / Type 2 (EU)","dc":"GB/T (CN) / CCS2 (EU)","freq":"Редкий"}],"Roewe":[{"m":"D7 и др.","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Honda":[{"m":"M-NV / e:NS1 / e:NP1","type":"BEV","ac":"GB/T AC","dc":"GB/T DC","freq":"Редкий"}],"Jetour":[{"m":"T1 / T2 PHEV","type":"PHEV","ac":"GB/T AC","dc":"— (уточнить)","freq":"Массовый"}],"Chery":[{"m":"Tiggo 7/8/9 C-DM PHEV","type":"PHEV","ac":"GB/T AC","dc":"— (уточнить)","freq":"Средний"}],"Jaecoo":[{"m":"7 PHEV","type":"PHEV","ac":"GB/T AC (уточнить RU-версию)","dc":"—","freq":"Средний"}],"Haval":[{"m":"H6 PHEV","type":"PHEV","ac":"GB/T AC","dc":"—","freq":"Средний"}],"Skoda":[{"m":"Enyaq","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Audi":[{"m":"e-tron / Q4 e-tron / Q8 e-tron","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Mercedes":[{"m":"EQC / EQA / EQB / EQE / EQS","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Mini":[{"m":"Cooper SE","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Редкий"}],"Peugeot":[{"m":"e-208 / e-2008 / e-3008","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Citroën":[{"m":"ë-C4 / ë-SpaceTourer","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Opel":[{"m":"Corsa-e / Mokka-e","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Fiat":[{"m":"500e","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Dacia":[{"m":"Spring","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Polestar":[{"m":"2 / 3 / 4","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Средний"}],"Cupra":[{"m":"Born","type":"BEV","ac":"Type 2","dc":"CCS2","freq":"Редкий"}],"Jaguar":[{"m":"I-Pace","type":"BEV","ac":"Type 2 (EU) / Type 1 (US)","dc":"CCS2 (EU) / CCS1 (US)","freq":"Редкий"}],"Porsche":[{"m":"Taycan","type":"BEV","ac":"Type 2 (EU) / Type 1 (US)","dc":"CCS2 (EU) / CCS1 (US)","freq":"Средний"}],"Smart":[{"m":"EQ fortwo / #1","type":"BEV","ac":"Type 2 (EU) / GB/T (CN)","dc":"CCS2 (EU) / GB/T (CN)","freq":"Редкий"}],"Genesis":[{"m":"GV60 / Electrified G80 / GV70","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Редкий"}],"Chevrolet":[{"m":"Bolt EV / EUV","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Редкий"}],"Ford":[{"m":"Mustang Mach-E (US) / F-150 Lightning","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Редкий"}],"Rivian":[{"m":"R1T / R1S","type":"BEV","ac":"Type 1 / NACS (новые)","dc":"CCS1 / NACS (новые)","freq":"Редкий"}],"Lucid":[{"m":"Air","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Редкий"}],"GMC":[{"m":"Hummer EV","type":"BEV","ac":"Type 1","dc":"CCS1","freq":"Редкий"}],"Mazda":[{"m":"MX-30","type":"BEV","ac":"Type 2","dc":"CCS2 (поздние) / CHAdeMO (ранние JP)","freq":"Редкий"}]},"order":["Zeekr","Geely","Voyah","Toyota","Changan","Li Auto","BYD","Avatr","Chery","Evolute","Tesla","VW","Nissan","MG","Deepal","Hongqi"]};
const QUIZ_BUNDLES=[{"id":"b-gbt","name":"Комплект GB/T: адаптер премиум + кабель 5 м + держатель + зимний набор","price":20190,"was":22190,"line":"gbt"},{"id":"b-eu","name":"Комплект Type 2 (Европа): портативка 7 кВт + кабель 5 м + держатель + зимний набор","price":26190,"was":28190,"line":"eu"},{"id":"b-phev","name":"Комплект для гибрида (PHEV): портативка 3,5 кВт + держатель + зимний набор","price":10790,"was":11690,"line":"phev"}];
const QUIZ_SITE='https://zapashoda-ev.ru/';

function openAppKb() {
  return { inline_keyboard: [[{ text: '🔋 Открыть «Запас хода»', web_app: { url: WEBAPP_URL } }]] };
}

/* ============ 1. Заявки из мини-аппа ============ */

function _leadDoPost(e) {
  try {
    const raw = (e && e.postData && e.postData.contents) || '';
    const d = JSON.parse(raw || '{}');

    if (d.update_id) { return out({ ok: true }); }
    // honeypot: поле заполняет бот — тихо игнорируем
    if (d.website !== undefined && String(d.website || '').length > 0) { return out({ ok: true }); }

    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sh = ss.getSheetByName(SHEET_NAME);
    if (!sh) {
      sh = ss.insertSheet(SHEET_NAME);
      sh.appendRow(['Дата', 'Тип', 'Модель', 'Город', 'Имя', 'Телефон', 'Позиций', 'Сумма ₽', 'Комментарий', 'Состав']);
    } else if (sh.getLastColumn() === 9) {
      sh.getRange(1, 10).setValue('Состав');
    }

    // OD v8: заявка из Конфигуратора ОД (промокод + кэшбэк менеджеру)
    if (String(d.t || '') === 'od_order') return _odDoOrder(d);

    // Формат модалки сайта (lead.js): t='lead', name/contact/city/carModel/product/price/source
    if (String(d.t || '') === 'lead') {
      sh.appendRow([
        new Date(),
        'Лид сайта · ' + (d.source || 'модалка'),
        d.carModel || '',
        d.city || '',
        d.name || '',
        d.contact || '',
        '',
        d.price || '',
        d.comment || '',
        (d.product ? ('Товар: ' + d.product + (d.price ? ' · ' + d.price : '')) : '') + (d.page ? ('\nСтраница: ' + d.page) : '')
      ]);
      // В ТГ НЕ дублируем: lead.js уже отправляет сообщение в канал напрямую.
      return out({ ok: true });
    }

    // Формат мини-аппа / корзины: t='miniapp', model/phone/items/total/comment — прежняя логика
    const itemsText = (d.items || [])
      .map(i => i.name + ' ×' + i.qty + ' — ' + (i.price * i.qty) + ' ₽')
      .join('\n');
    sh.appendRow([
      new Date(),
      d.t || '',
      d.model || '',
      d.city || '',
      d.name || '',
      d.phone || '',
      (d.items || []).length,
      d.total || 0,
      d.comment || '',
      itemsText
    ]);

    const items = (d.items || [])
      .map(i => '• ' + i.name + ' ×' + i.qty + ' — ' + (i.price * i.qty) + ' ₽')
      .join('\n');
    const msg =
      '🆕 ' + (d.t === 'miniapp' ? 'Заявка из мини-аппа ⚡️' : 'Заказ') + '\n' +
      '👤 ' + (d.name || '—') + '\n' +
      '📞 ' + (d.phone || '—') + '\n' +
      '📍 ' + (d.city || '—') + '\n' +
      '🚗 ' + (d.model || '—') + '\n' +
      (items ? items + '\n' : '') +
      '💰 Итого: ' + (d.total || 0) + ' ₽' +
      (d.comment ? '\n💬 ' + d.comment : '');
    tgSend(msg);

    return out({ ok: true });
  } catch (err) {
    try { tgSend('⚠️ Ошибка приёма заявки: ' + err); } catch (e2) {}
    return out({ ok: false, error: String(err) });
  }
}
function setupBotPolling() {
  // 1) Удалить вебхук — иначе Telegram не отдаёт апдейты через getUpdates
  const res = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/deleteWebhook', {
    method: 'post', payload: {}
  });
  Logger.log('deleteWebhook: ' + res.getContentText());

  // 2) Создать триггер «каждую минуту» (если ещё не создан)
  const trig = ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'checkUpdates');
  if (trig.length === 0) {
    ScriptApp.newTrigger('checkUpdates').timeBased().everyMinutes(1).create();
    Logger.log('Триггер checkUpdates создан');
  } else {
    Logger.log('Триггер уже существует');
  }

  // 3) Команды меню бота (кнопка ☰ рядом с полем ввода)
  setBotCommands();
}

/* ============ 2.5 Отложенный постинг в канал ============ */

function publishScheduledPosts(force) {
  const props = PropertiesService.getScriptProperties();
  const sent = JSON.parse(props.getProperty(POSTS_SENT_KEY) || '[]');
  const now = Date.now();
  for (const p of POST_QUEUE) {
    if (sent.indexOf(p.key) >= 0) continue;
    if (!force && Date.parse(p.at) > now) continue;
    let res;
    if (p.type === 'poll') {
      res = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendPoll', {
        method: 'post', payload: {
          chat_id: '@' + CHANNEL,
          question: p.question,
          options: JSON.stringify(p.options),
          is_anonymous: 'true'
        }, muteHttpExceptions: true
      });
    } else if (p.photo) {
      res = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendPhoto', {
        method: 'post', payload: {
          chat_id: '@' + CHANNEL,
          photo: p.photo,
          caption: String(p.text || '').slice(0, 1024),
          reply_markup: JSON.stringify({
            inline_keyboard: [[
              { text: '🔋 Открыть гид', url: 'https://t.me/zapashoda_ev_bot?startapp=' + p.key },
              { text: '🌐 Сайт zapashoda-ev.ru', url: 'https://zapashoda-ev.ru/' }
            ]]
          })
        }, muteHttpExceptions: true
      });
    } else {
      res = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage', {
        method: 'post', payload: {
          chat_id: '@' + CHANNEL,
          text: p.text,
          reply_markup: JSON.stringify({
            inline_keyboard: [[
              { text: '🔋 Открыть гид', url: 'https://t.me/zapashoda_ev_bot?startapp=' + p.key },
              { text: '🌐 Сайт zapashoda-ev.ru', url: 'https://zapashoda-ev.ru/' }
            ]]
          })
        }, muteHttpExceptions: true
      });
    }
    Logger.log('Post ' + p.key + ': ' + res.getContentText());
    sent.push(p.key);
    props.setProperty(POSTS_SENT_KEY, JSON.stringify(sent));
    Utilities.sleep(3000); // лимит Telegram: ~20 сообщений в минуту в канал
  }
}

// Разовая публикация всех постов очереди без ожидания времени (для теста)
function publishPostsNow() {
  publishScheduledPosts(true);
  Logger.log('Готово');
}

function setBotCommands() {
  const res = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/setMyCommands', {
    method: 'post',
    payload: { commands: JSON.stringify([
      { command: 'start', description: 'Открыть гид по электромобилю' },
      { command: 'quiz', description: 'Подобрать комплект за 30 секунд' },
      { command: 'app', description: 'Каталог и подбор аксессуаров' },
      { command: 'help', description: 'Что умеет бот' },
      { command: 'promo', description: 'Проверить промокод: /promo КОД' },
      { command: 'bonusweek', description: 'Бонус недели: итоги менеджеров' }
    ]) }
  });
  Logger.log('setMyCommands: ' + res.getContentText());
}

function checkUpdates() {
  const props = PropertiesService.getScriptProperties();
  const lastOffset = parseInt(props.getProperty(OFFSET_KEY) || '0', 10);
  try {
    publishScheduledPosts();
    const res = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN +
      '/getUpdates?timeout=0&limit=10&offset=' + (lastOffset + 1));
    const data = JSON.parse(res.getContentText());
    if (!data.ok) { Logger.log('getUpdates: ' + res.getContentText()); return; }
    let maxId = lastOffset;
    for (const u of data.result) {
      maxId = Math.max(maxId, u.update_id);
      if (u.callback_query) { handleCallback(u.callback_query); continue; }
      handleUpdate(u);
    }
    if (maxId > lastOffset) props.setProperty(OFFSET_KEY, String(maxId));
  } catch (err) {
    Logger.log('checkUpdates error: ' + err);
  }
}

/* ============ 3. Приветствие на /start ============ */

function handleUpdate(u) {
  try {
    const msg = u && u.message;
    if (!msg || !msg.text) return;
    const text = String(msg.text).trim();
    const from = msg.from || {};
    const uid = from.id;
    const name = (from.first_name || '').trim();

    // Кнопки reply-клавиатуры
    if (text === '🧩 Подбор') {
      startQuiz(msg.chat.id);
      return;
    }
    if (text === '🚗 Моя EV') {
      sendMessage(msg.chat.id,
        'Выбери модель в приложении — покажем разъёмы твоей машины, частые проблемы и что докупить 👇', openAppKb());
      return;
    }
    if (text === '🛍️ Каталог') {
      sendMessage(msg.chat.id,
        'Каталог аксессуаров для зарядки: адаптеры, удлинители, станции. Подбор — под твою модель 👇', openAppKb());
      return;
    }
    if (text === '📖 Справочник') {
      sendMessage(msg.chat.id,
        'Справочник разъёмов: Type 2, CCS2, GB/T — что есть у какой модели и чем заряжать 👇', openAppKb());
      return;
    }
    if (text === '💬 Поддержка') {
      sendMessage(msg.chat.id,
        'Напиши свой вопрос прямо в этот чат — ответим. А пока можешь открыть гид: 👇', openAppKb());
      return;
    }

    // Команды меню (учёт варианта /app@имя_бота)
    const cmd = text.split(' ')[0].split('@')[0];
    if (cmd === '/quiz') {
      startQuiz(msg.chat.id);
      return;
    }
    if (cmd === '/app') {
      sendMessage(msg.chat.id, 'Каталог и гид по твоей модели — в приложении 👇', openAppKb());
      return;
    }
    if (cmd === '/help') {
      sendMessage(msg.chat.id,
        'Что умеет бот:\n' +
        '/quiz — подобрать комплект под вашу модель\n' +
        '/app — открыть гид и каталог аксессуаров\n' +
        '/start — приветствие и подписка на канал\n\n' +
        'Быстрые кнопки разделов — под полем ввода. Вопрос — просто напиши в чат.\n' +
        'Открыть всё сразу: 👇', openAppKb());
      return;
    }
    if (cmd === '/promo') { odCmdPromo(text, msg.chat.id); return; }
    if (cmd === '/bonusweek') { odCmdBonusWeek(msg.chat.id); return; }

    if (text.indexOf('/start') !== 0) return;

    const status = getMemberStatus(uid);
    const isSub = status === 'member' || status === 'creator' || status === 'administrator';

    let text2;
    const kb = { inline_keyboard: [] };
    if (isSub) {
      text2 =
        'Привет' + (name ? ', ' + name : '') + '! 👋\n\n' +
        '🔋 «Запас хода» — твой гид по электромобилю:\n' +
        '• разъёмы твоей модели\n' +
        '• частые проблемы и решения\n' +
        '• что докупить — с доставкой через ближайший салон-дилера\n\n' +
        'Подбор за 30 секунд: жми «🧩 Подбор» под полем ввода или /quiz\n\n' +
        'Жми кнопку — откроется твой гид 👇';
      kb.inline_keyboard.push([{ text: '🔋 Открыть «Запас хода»', web_app: { url: WEBAPP_URL } }]);
    } else {
      text2 =
        'Привет' + (name ? ', ' + name : '') + '! 👋\n\n' +
        '🔋 «Запас хода» — гид по твоему электромобилю:\n' +
        '• разъёмы твоей модели\n' +
        '• частые проблемы и решения\n' +
        '• что докупить — с доставкой через салон-дилера\n\n' +
        'Полный гид открыт для подписчиков канала — он бесплатный, без спама.\n' +
        'Подпишись и нажми /start ещё раз 👇';
      kb.inline_keyboard.push([{ text: '📱 Подписаться на «Запас хода»', url: 'https://t.me/' + CHANNEL }]);
    }
    sendMessage(msg.chat.id, text2, kb);
    // Клавиатура разделов отправляется вторым сообщением (Telegram не совмещает два типа кнопок)
    sendMessage(msg.chat.id, 'Кнопки разделов всегда под рукой 👇', null, REPLY_KB);
  } catch (err) {
    // тихо: не роняем опросник
  }
}

function getMemberStatus(uid) {
  try {
    const res = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/getChatMember', {
      method: 'post',
      payload: { chat_id: '@' + CHANNEL, user_id: uid }
    });
    const r = JSON.parse(res.getContentText());
    if (r.ok) return r.result.status;
    return 'unknown';
  } catch (e) {
    return 'unknown';
  }
}

/* ============ 4. Квиз подбора (v3.6) ============ */

function startQuiz(chatId) {
  const rows = [];
  const top = QUIZ.order;
  for (let i = 0; i < top.length; i += 2) {
    const row = [];
    row.push({ text: '🚗 ' + top[i], callback_data: 'qb:' + top[i] + ':0' });
    if (i + 1 < top.length) row.push({ text: '🚗 ' + top[i + 1], callback_data: 'qb:' + top[i + 1] + ':0' });
    rows.push(row);
  }
  rows.push([{ text: '🌐 Полный список марок — на сайте', url: QUIZ_SITE + 'quiz/' }]);
  sendMessage(chatId, '🧩 Подбор за 30 секунд.\n\nВыберите марку — покажу разъёмы и что докупить под вашу модель:', rows);
}

function brandMenu(chatId, brand, page) {
  const models = (QUIZ.brands[brand] || []);
  if (!models.length) { startQuiz(chatId); return; }
  const per = 8;
  const from = page * per;
  const rows = [];
  for (let i = from; i < Math.min(from + per, models.length); i++) {
    rows.push([{ text: '• ' + models[i].m + ' (' + models[i].type + ')', callback_data: 'qm:' + brand + ':' + i }]);
  }
  const nav = [];
  if (page > 0) nav.push({ text: '⬅️ Назад', callback_data: 'qb:' + brand + ':' + (page - 1) });
  if (from + per < models.length) nav.push({ text: 'Ещё модели ➡️', callback_data: 'qb:' + brand + ':' + (page + 1) });
  if (nav.length) rows.push(nav);
  rows.push([{ text: '↩️ К маркам', callback_data: 'quiz:start' }]);
  let extra = '';
  if (models.length === 1) extra = '\n\nУ ' + brand + ' в базе одна модель — она же ниже.';
  else extra = '\n\nУ ' + brand + ' в базе ' + models.length + ' моделей (стр. ' + (page + 1) + ' из ' + Math.ceil(models.length / per) + ').';
  sendMessage(chatId, '🚗 ' + brand + '. Выберите модель:' + extra, rows);
}

function quizLineOf(m) {
  if (m.type === 'PHEV') return 'phev';
  return (String(m.ac || '').indexOf('GB/T') >= 0) ? 'gbt' : 'eu';
}

function showResult(chatId, brand, idx) {
  const m = (QUIZ.brands[brand] || [])[idx];
  if (!m) { startQuiz(chatId); return; }
  const line = quizLineOf(m);
  const b = QUIZ_BUNDLES.filter(x => x.line === line)[0];
  const slug = slugify(brand + ' ' + m.m);
  const modelUrl = QUIZ_SITE + 'models/' + slug + '.html';
  let txt =
    '🚗 ' + brand + ' ' + m.m + ' · ' + m.type + '\n' +
    '🔌 AC: ' + (m.ac || '—') + ' · DC: ' + (m.dc || '—') + '\n\n' +
    '📦 ' + (b ? b.name.split(':')[0] + ' — ' + b.price.toLocaleString('ru-RU') + ' ₽ (экономия ' + (b.was - b.price).toLocaleString('ru-RU') + ' ₽)' : '') + '\n\n' +
    'На странице модели — полный подбор с ценами, калькулятор зарядки и форма заявки (оплата — дилеру при получении):';
  const rows = [
    [{ text: '📄 Страница ' + brand + ' ' + m.m, url: modelUrl }],
    [{ text: '🛍️ Каталог с ценами', url: QUIZ_SITE + 'catalog/' }],
    [{ text: '↩️ Другая модель', callback_data: 'qb:' + brand + ':0' }]
  ];
  sendMessage(chatId, txt, rows);
  logQuiz(brand + ' ' + m.m);
}

function slugify(s) {
  const map = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',' ':'-','/':'-','.':'-','(':'',')':'',',':'','+':'','–':'-','—':'-'};
  let out = '';
  for (const ch of s.toLowerCase()) out += (map[ch] !== undefined ? map[ch] : ch);
  return out.replace(/[^a-z0-9\-]/g, '').replace(/-+/g, '-').replace(/^-|-$/g, '');
}

function handleCallback(cb) {
  try {
    const chatId = (cb.message && cb.message.chat && cb.message.chat.id) ? cb.message.chat.id : null;
    if (!chatId) return;
    const data = String(cb.data || '');
    if (data === 'quiz:start') { startQuiz(chatId); return; }
    const qb = data.match(/^qb:(.+):(\d+)$/);
    if (qb) { brandMenu(chatId, qb[1], parseInt(qb[2], 10) || 0); return; }
    const qm = data.match(/^qm:(.+?):(\d+)$/);
    if (qm) { showResult(chatId, qm[1], parseInt(qm[2], 10) || 0); return; }
  } catch (err) {
    // тихо: не роняем опросник
  }
}

function logQuiz(modelFull) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sh = ss.getSheetByName(SHEET_NAME);
    if (!sh) {
      sh = ss.insertSheet(SHEET_NAME);
      sh.appendRow(['Дата', 'Тип', 'Модель', 'Город', 'Имя', 'Телефон', 'Позиций', 'Сумма ₽', 'Комментарий', 'Состав']);
    } else if (sh.getLastColumn() === 9) {
      sh.getRange(1, 10).setValue('Состав');
    }
    sh.appendRow([new Date(), 'bot_quiz', modelFull, '—', 'из бота (квиз)', '—', 0, 0, '', '']);
    tgSend('🧩 Квиз в боте: ' + modelFull);
  } catch (err) {}
}

/* ============ Служебное ============ */

function tgSend(text) {
  UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage', {
    method: 'post',
    payload: { chat_id: CHAT_ID, text: text }
  });
}

function sendMessage(chatId, text, inlineKb, replyKb) {
  const payload = { chat_id: chatId, text: text };
  const markup = inlineKb || replyKb;
  if (markup) payload.reply_markup = JSON.stringify(markup);
  UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage', {
    method: 'post',
    payload: payload
  });
}

// Проверка приёмника: открой URL деплоя в браузере — должно ответить «работает»
function _leadDoGet(e) {
  return ContentService.createTextOutput('Запас хода: приёмник заявок работает');
}

function out(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// Разовая проверка вручную: выполнить checkUpdatesNow из редактора
function checkUpdatesNow() {
  checkUpdates();
  Logger.log('Готово');
}

/* ============================================================
   ФОРУМ (Forum.gs): живые темы и ответы на zapashoda-ev.ru/forum/
   Модерация: лист «Forum», столбец status: pending → ok
   Установка: вставить ВЕСЬ файл в GAS (заменить прежний Code.gs целиком!),
   затем один раз выполнить forumSetup() и разрешить права.
   ============================================================ */


/* ============ 3. Диспетчер входа: приёмник заявок ИЛИ форум ============ */
function doGet(e) {
  try {
    e = e || {};
    var p = e.parameter || {};
    if (p.shop_status) return _shopStatus(p.shop_status);
    if (p.t) return _shopDownload(p.t);
    var action = String(p.action || '');
    if (action === 'captcha') { var cap = _captchaIssue(); return _fJ(true, { captcha: cap }); }
    if (action === 'threads' || action === 'posts') return _forumDoGet(e);
    if (action === 'profile') return _userPublicProfile(p.u || '');
    if (action === 'me') return _userMe(p.token || '');
    return _leadDoGet(e);
  } catch (err) { return _leadDoGet(e); }
}

function doPost(e) {
  try {
    e = e || {};
    if (!e.postData || !e.postData.contents) return _leadDoPost(e);
    let d;
    const _pdC = String(e.postData.contents);
    if (_pdC.trim().indexOf('{') === 0) {
      d = JSON.parse(_pdC);
      if (String(d.t || '') === 'shop_init') return _shopInit(d);
    } else {
      d = {};
      _pdC.split('&').forEach(function (kv) {
        const j2 = kv.indexOf('=');
        if (j2 < 0) return;
        const k2 = decodeURIComponent(kv.slice(0, j2).replace(/\+/g, ' '));
        d[k2] = decodeURIComponent(kv.slice(j2 + 1).replace(/\+/g, ' '));
      });
      if (d.NotificationType || (d.OrderId && d.Status && d.TerminalKey && d.Token)) return _shopNotification(d);
      if (String(d.t || '') === 'shop_init') return _shopInit(d);
    }
    var act = String(d.action || '');
    if (act === 'register') return _userRegister(d);
    if (act === 'login') return _userLogin(d);
    if (d.thread !== undefined && d.thread !== null && String(d.thread) !== '') return _forumDoPost(e, d);
    return _leadDoPost(e);
  } catch (err) {
    return _leadDoPost(e);
  }
}

// ============================================================
// Форум zapashoda-ev.ru/forum/ — работает вместе с приёмником заявок выше.
// Установка: вставить ВЕСЬ этот файл в GAS-проект (вместо прежнего кода целиком),
// TELEGRAM_TOKEN/CHAT_ID/SPREADSHEET_ID — как раньше; один раз выполнить forumSetup().
// Модерация: в листе «Forum» менять status: pending → ok (или rejected).
// ============================================================

var FORUM_SHEET = 'Forum';
var FORUM_HEADERS = ['id', 'thread', 'section', 'title', 'name', 'tg', 'text', 'ts', 'status', 'ip', 'user'];
var FORUM_CLEAN_DAYS = 90;

function _forumSheet() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sh = ss.getSheetByName(FORUM_SHEET);
  if (!sh) sh = ss.insertSheet(FORUM_SHEET);
  if (sh.getLastRow() === 0) {
    sh.appendRow(FORUM_HEADERS);
    sh.setFrozenRows(1);
  }
  return sh;
}


function _fRows() {
  var sh = _forumSheet();
  var last = sh.getLastRow();
  if (last < 2) return [];
  var vals = sh.getRange(2, 1, last - 1, FORUM_HEADERS.length).getValues();
  var out = [];
  for (var i = 0; i < vals.length; i++) {
    if (!vals[i][0]) continue;
    out.push({
      id: String(vals[i][0]), thread: String(vals[i][1] || ''), section: String(vals[i][2] || ''),
      title: String(vals[i][3] || ''), name: String(vals[i][4] || ''), tg: String(vals[i][5] || ''),
      text: String(vals[i][6] || ''), ts: Number(vals[i][7]) || 0, status: String(vals[i][8] || 'pending'),
      user: String(vals[i][10] || '')
    });
  }
  return out;
}

function _fAppend(o) {
  var sh = _forumSheet();
  sh.appendRow([o.id, o.thread, o.section || '', o.title || '', o.name || '', o.tg || '', o.text || '', o.ts, o.status || 'pending', o.ip || '', o.user || '']);
}

function _fJ(ok, data, err) {
  var obj = ok ? Object.assign({ok: true}, data || {}) : {ok: false, error: String(err || 'ошибка')};
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function _fErr(e) { return _fJ(false, null, e); }

// Антиспам: не чаще 1 поста в минуту на тему, не больше 6 постов в час на тему
function _fRate(thread) {
  var c = CacheService.getScriptCache();
  var kMin = 'fr_' + thread;
  var kHr = 'frh_' + thread;
  if (c.get(kMin)) return false;
  var hr = Number(c.get(kHr) || 0);
  if (hr >= 6) return false;
  c.put(kMin, '1', 60);
  c.put(kHr, String(hr + 1), 3600);
  return true;
}

// Чистка: rejected и pending старше 90 дней
function forumCleanup() {
  var sh = _forumSheet();
  var last = sh.getLastRow();
  if (last < 2) return 'пусто';
  var vals = sh.getRange(2, 1, last - 1, FORUM_HEADERS.length).getValues();
  var cutoff = Date.now() - FORUM_CLEAN_DAYS * 86400000;
  var keep = [];
  var removed = 0;
  for (var i = 0; i < vals.length; i++) {
    var st = String(vals[i][8] || '');
    var ts = Number(vals[i][7]) || 0;
    if ((st === 'rejected' || st === 'pending') && ts && ts < cutoff) { removed++; continue; }
    keep.push(vals[i]);
  }
  if (removed > 0) {
    sh.getRange(2, 1, Math.max(1, last - 1), FORUM_HEADERS.length).clearContent();
    if (keep.length) sh.getRange(2, 1, keep.length, FORUM_HEADERS.length).setValues(keep);
  }
  return 'удалено: ' + removed;
}

function _forumDoGet(e) {
  try {
    e = e || {};
    var p = e.parameter || {};
    var action = String(p.action || 'posts');
    if (action === 'posts') {
      var thread = String(p.thread || '').trim();
      if (!thread) return _fErr('не указана тема');
      var posts = _fRows().filter(function(r) {
        return r.thread === thread && r.status === 'ok' && r.text;
      }).map(function(r) {
        return {name: r.name || 'Аноним', ts: r.ts, text: r.text};
      });
      return _fJ(true, {posts: posts});
    }
    if (action === 'threads') {
      var seen = {}, threads = [];
      _fRows().forEach(function(r) {
        if (!r.thread || r.status !== 'ok' || seen[r.thread]) return;
        if (r.thread === 'new') return;
        seen[r.thread] = 1;
        threads.push({thread: r.thread, section: r.section || 'general', title: r.title || r.thread, ts: r.ts});
      });
      threads.sort(function(a, b) { return (b.ts || 0) - (a.ts || 0); });
      return _fJ(true, {threads: threads.slice(0, 50)});
    }
    return _fErr('неизвестное действие');
  } catch (err) {
    return _fErr(err);
  }
}

/* ---------- ФОРУМ: POST (капча для гостей; юзеры — без премодерации) ---------- */
function _forumDoPost(e, d) {
  try {
    e = e || {};
    d = d || (e.postData ? JSON.parse(e.postData.contents) : {});
    var text = String(d.text || '').trim();
    var name = String(d.name || '').trim().substring(0, 40);
    var tg = String(d.tg || '').trim().replace(/^@+/, '').substring(0, 32);
    var thread = String(d.thread || '').trim();
    if (text.length < 5) return _fErr('Текст слишком короткий');
    if (text.length > 2000) return _fErr('Текст слишком длинный (до 2000)');
    var now = Date.now();
    var id = 'p' + now.toString(36) + Math.random().toString(36).substring(2, 6);
    var token = String(d.token || '');
    var userName = _tokenCheck(token);
    if (userName) {
      var uu = _userByName(userName);
      if (uu) { name = uu.name; tg = tg || uu.tg; }
    }
    if (!name) return _fErr('Укажите имя');
    if (!userName && REQUIRE_CAPTCHA) {
      if (!_captchaCheck(d.captcha_id, d.captcha_answer)) return _fErr('Капча неверна или устарела — обновите вопрос и попробуйте снова');
    }
    var status = userName ? 'ok' : 'pending';
    if (thread === 'new') {
      var title = String(d.title || '').trim();
      if (title.length < 8) return _fErr('Заголовок от 8 символов');
      if (title.length > 120) return _fErr('Заголовок слишком длинный');
      var sections = {general: 1, charging: 1, accessories: 1, problems: 1, market: 1};
      var section = sections[d.section] ? d.section : 'general';
      var newThread = 'f' + now.toString(36) + Math.random().toString(36).substring(2, 6);
      if (!_fRate(newThread)) return _fErr('Слишком часто, подождите минуту');
      _fAppend({id: 't' + id, thread: newThread, section: section, title: title, name: name, tg: tg, text: '', ts: now, status: status, user: userName || ''});
      _fAppend({id: id, thread: newThread, section: section, title: '', name: name, tg: tg, text: text, ts: now + 1, status: status, user: userName || ''});
      return _fJ(true, {thread: newThread});
    }
    if (!thread || thread.length > 80) return _fErr('Некорректная тема');
    if (!_fRate(thread)) return _fErr('Слишком часто, подождите минуту');
    _fAppend({id: id, thread: thread, section: String(d.section || ''), title: '', name: name, tg: tg, text: text, ts: now, status: status, user: userName || ''});
    return _fJ(true, {});
  } catch (err) {
    return _fErr(err);
  }
}

/* ============ ПОЛЬЗОВАТЕЛИ + КАПЧА (v5) ============ */

var USERS_SHEET = 'Users';
var USERS_HEADERS = ['id', 'name', 'pass_hash', 'tg', 'car', 'created', 'last_login', 'role'];
var SECRET_KEY = 'zs_secret_v5';

function _sec() {
  var props = PropertiesService.getScriptProperties();
  var s2 = props.getProperty(SECRET_KEY);
  if (!s2) { s2 = Utilities.getUuid() + Utilities.getUuid(); props.setProperty(SECRET_KEY, s2); }
  return s2;
}

function _hash(pass) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(pass) + '::zs-salt-v5')
    .map(function(b){ return ('0' + (b & 0xFF).toString(16)).slice(-2); }).join('');
}

function _sheetBy(name, headers) {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sh = ss.getSheetByName(name);
  if (!sh) sh = ss.insertSheet(name);
  if (sh.getLastRow() === 0) { sh.appendRow(headers); sh.setFrozenRows(1); }
  return sh;
}

function _usersSheet() { return _sheetBy(USERS_SHEET, USERS_HEADERS); }

function _uRows() {
  var sh = _usersSheet();
  var last = sh.getLastRow();
  if (last < 2) return [];
  var vals = sh.getRange(2, 1, last - 1, USERS_HEADERS.length).getValues();
  var out = [];
  for (var i = 0; i < vals.length; i++) {
    if (!vals[i][0]) continue;
    out.push({ id: String(vals[i][0]), name: String(vals[i][1] || ''), pass_hash: String(vals[i][2] || ''),
      tg: String(vals[i][3] || ''), car: String(vals[i][4] || ''), created: Number(vals[i][5]) || 0,
      last_login: Number(vals[i][6]) || 0, role: String(vals[i][7] || 'user') });
  }
  return out;
}

function _userByName(name) {
  var rows = _uRows();
  for (var i = 0; i < rows.length; i++) if (rows[i].name.toLowerCase() === String(name).toLowerCase()) return rows[i];
  return null;
}

function _tokenIssue(name) {
  var exp = Date.now() + 30 * 86400000;
  var raw = String(name) + '|' + exp;
  var sig = Utilities.computeHmacSignature(Utilities.DigestAlgorithm.HMAC_SHA_256, raw, _sec())
    .map(function(b){ return ('0' + (b & 0xFF).toString(16)).slice(-2); }).join('');
  return btoa(Utilities.newBlob(raw).getBytes()) + '.' + sig;
}

function _tokenCheck(token) {
  try {
    if (!token || String(token).indexOf('.') < 0) return null;
    var parts = String(token).split('.');
    var raw = Utilities.newBlob(Utilities.base64Decode(parts[0])).getDataAsString();
    var sig = Utilities.computeHmacSignature(Utilities.DigestAlgorithm.HMAC_SHA_256, raw, _sec())
      .map(function(b){ return ('0' + (b & 0xFF).toString(16)).slice(-2); }).join('');
    if (sig !== parts[1]) return null;
    var pair = raw.split('|');
    if (Number(pair[1]) < Date.now()) return null;
    return pair[0];
  } catch (e) { return null; }
}

function _captchaIssue() {
  var a = 2 + Math.floor(Math.random() * 8);
  var b = 2 + Math.floor(Math.random() * 8);
  var id = 'c' + Date.now().toString(36) + Math.random().toString(36).substring(2, 7);
  CacheService.getScriptCache().put('cap_' + id, String(a + b), 360);
  return { id: id, q: String(a) + ' + ' + String(b) };
}

function _captchaCheck(id, answer) {
  if (!id || !answer) return false;
  var c = CacheService.getScriptCache();
  var k = 'cap_' + String(id);
  var v = c.get(k);
  if (!v) return false;
  c.remove(k);
  return String(v) === String(answer).trim();
}

function _userRegister(d) {
  try {
    var name = String(d.name || '').trim();
    var pass = String(d.pass || '');
    var tg = String(d.tg || '').trim().replace(/^@+/, '').substring(0, 32);
    var car = String(d.car || '').trim().substring(0, 60);
    if (!/^[A-Za-zА-Яа-яЁё0-9_\.\\-]{3,20}$/.test(name)) return _fJ(false, null, 'Ник: 3–20 символов, буквы/цифры');
    if (pass.length < 6) return _fJ(false, null, 'Пароль от 6 символов');
    if (_userByName(name)) return _fJ(false, null, 'Этот ник уже занят');
    _usersSheet().appendRow(['u' + Date.now().toString(36), name, _hash(pass), tg, car, Date.now(), Date.now(), 'user']);
    tgSend('🆕 Регистрация на форуме: ' + name + (tg ? ' (@' + tg + ')' : '') + (car ? ' · ' + car : ''));
    return _fJ(true, { token: _tokenIssue(name), name: name });
  } catch (err) { return _fErr(err); }
}

function _userLogin(d) {
  try {
    var name = String(d.name || '').trim();
    var pass = String(d.pass || '');
    var u = _userByName(name);
    if (!u || u.pass_hash !== _hash(pass)) return _fJ(false, null, 'Неверный ник или пароль');
    var sh = _usersSheet();
    var last = sh.getLastRow();
    for (var i = 2; i <= last; i++) {
      if (String(sh.getRange(i, 2).getValue()).toLowerCase() === name.toLowerCase()) {
        sh.getRange(i, 7).setValue(Date.now());
        break;
      }
    }
    return _fJ(true, { token: _tokenIssue(u.name), name: u.name, car: u.car, tg: u.tg });
  } catch (err) { return _fErr(err); }
}

function _userPublicProfile(nick) {
  try {
    var u = _userByName(String(nick || '').trim());
    if (!u) return _fJ(false, null, 'Профиль не найден');
    var posts = _fRows().filter(function(r){ return r.name.toLowerCase() === u.name.toLowerCase() && r.status === 'ok'; })
      .slice(-20).reverse().map(function(r){ return {thread: r.thread, title: r.title, text: (r.text || '').substring(0, 160), ts: r.ts}; });
    return _fJ(true, { profile: {
      name: u.name, tg: u.tg, car: u.car, created: u.created,
      posts: posts
    }});
  } catch (err) { return _fErr(err); }
}

function _userMe(token) {
  try {
    var name = _tokenCheck(token);
    if (!name) return _fJ(false, null, 'Требуется вход');
    var u = _userByName(name);
    if (!u) return _fJ(false, null, 'Профиль не найден');
    var posts = _fRows().filter(function(r){ return r.name.toLowerCase() === u.name.toLowerCase(); })
      .slice(-30).reverse().map(function(r){ return {thread: r.thread, title: r.title, text: (r.text || '').substring(0, 200), ts: r.ts, status: r.status}; });
    return _fJ(true, { me: { name: u.name, tg: u.tg, car: u.car, created: u.created }, posts: posts });
  } catch (err) { return _fErr(err); }
}

/* forumSetup: создаёт Forum и Users */
function forumSetup() {
  var f = _forumSheet();
  var u = _usersSheet();
  return 'OK: листы «Forum» и «Users» готовы. Форумных записей: ' + Math.max(0, f.getLastRow() - 1) + ', юзеров: ' + Math.max(0, u.getLastRow() - 1);
}

/* ============================================================
 * OD v8 — КОНФИГУРАТОР ДЛЯ МЕНЕДЖЕРОВ ОД (B2B2C) · 03.11.2026
 * Ветка t='od_order' (фронтенд: zapashoda-ev.ru/app/, od v6).
 * Листы: «Менеджеры» (реестр, кэшбэк %) и «Промокоды» (реестр кодов).
 * Колонки «Менеджер» и «Промокод» добавляются в «Лиды» (odSetup).
 * Верификация initData: HMAC(bot_token, "WebAppData") → проверка hash;
 *   заявки по ?ref= помечаются «ref-link» (без подписи).
 * Команды: /promo КОД — статус промокода (+кнопка «Подтвердить продажу»
 *   для владельца), /bonusweek — пост «Бонус недели» в канал (без персональных
 *   данных: имя, город, салон, объём, бонус).
 * ============================================================ */

const OD_CB_SHEET = 'Менеджеры';
const OD_CB_HEADERS = ['tg_id', 'Имя', 'Город', 'Салон', 'Бренд', 'Кэшбэк %', 'Статус'];
const OD_PR_SHEET = 'Промокоды';
const OD_PR_HEADERS = ['Код', 'tg_id менеджера', 'Дата', 'Модель', 'Сценарий', 'Сумма ₽', 'Клиент', 'Телефон', 'Город', 'Статус', 'Дата использования'];
const OD_DEFAULT_CASHBACK = 5;
const OD_STALE_SEC = 48 * 3600; // свежесть initData
const OD_SEED_MANAGERS = [
  { tg_id: '123456789', name: 'Антон', city: 'МСК', salon: 'Zeekr Premium', brand: 'Zeekr' },
  { tg_id: '987654321', name: 'Дмитрий', city: 'Химки', salon: 'Рольф', brand: 'Li Auto' },
  { tg_id: '555666777', name: 'Игорь', city: '', salon: 'Авилон', brand: 'Voyah' }
];

function odSetup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(['Дата', 'Тип', 'Модель', 'Город', 'Имя', 'Телефон', 'Позиций', 'Сумма ₽', 'Комментарий', 'Состав']);
  }
  const cols = sh.getLastColumn();
  const headers = sh.getRange(1, 1, 1, cols).getValues()[0];
  ['Менеджер', 'Промокод'].forEach((w, i) => {
    if (headers.indexOf(w) < 0) sh.getRange(1, cols + 1 + i).setValue(w);
  });
  _odCbSheet();
  _odPrSheet();
  _odSeedManagers();
  try { setBotCommands(); } catch (e2) { Logger.log('setBotCommands: ' + e2); }
  Logger.log('OD v8 готов: листы созданы, реестр наполнен, команды обновлены');
}

function _odCbSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(OD_CB_SHEET);
  if (!sh) sh = ss.insertSheet(OD_CB_SHEET);
  if (sh.getLastRow() === 0) { sh.appendRow(OD_CB_HEADERS); sh.setFrozenRows(1); }
  return sh;
}

function _odPrSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(OD_PR_SHEET);
  if (!sh) sh = ss.insertSheet(OD_PR_SHEET);
  if (sh.getLastRow() === 0) { sh.appendRow(OD_PR_HEADERS); sh.setFrozenRows(1); }
  return sh;
}

function _odSeedManagers() {
  const sh = _odCbSheet();
  const vals = sh.getLastRow() > 1 ? sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues() : [];
  const have = new Set(vals.map(r => String(r[0])));
  OD_SEED_MANAGERS.forEach(m => {
    if (!have.has(String(m.tg_id))) {
      sh.appendRow([m.tg_id, m.name, m.city, m.salon, m.brand, OD_DEFAULT_CASHBACK, 'active']);
    }
  });
}

function _odManager(id) {
  id = String(id || '');
  if (!id) return null;
  const sh = _odCbSheet();
  const last = sh.getLastRow();
  if (last < 2) return null;
  const vals = sh.getRange(2, 1, last - 1, OD_CB_HEADERS.length).getValues();
  for (const r of vals) {
    if (String(r[0]) === id) {
      return { tg_id: id, name: r[1], city: r[2], salon: r[3], brand: r[4], pct: Number(r[5]) || OD_DEFAULT_CASHBACK, status: r[6] };
    }
  }
  return null;
}

function _odHex(bytes) {
  return bytes.map(b => (b < 0 ? b + 256 : b).toString(16).padStart(2, '0')).join('');
}

// Верификация Telegram initData (Mini App): secret = HMAC_SHA256(bot_token, "WebAppData")
function _odVerifyInitData(initData) {
  initData = String(initData || '');
  if (!initData || initData.indexOf('hash=') < 0) return { ok: false, reason: 'no-data' };
  try {
    const secret = Utilities.computeHmacSignature(
      Utilities.MacAlgorithm.HMAC_SHA_256, TELEGRAM_TOKEN, 'WebAppData', Utilities.Charset.UTF_8);
    let hash = '';
    const kvs = [];
    initData.split('&').forEach(p => {
      if (p.indexOf('hash=') === 0) hash = p.slice(5);
      else kvs.push(p);
    });
    if (!hash) return { ok: false, reason: 'no-hash' };
    kvs.sort();
    const sig = Utilities.computeHmacSignature(
      Utilities.MacAlgorithm.HMAC_SHA_256, Utilities.newBlob(kvs.join('\n')).getBytes(), secret);
    if (_odHex(sig) !== hash) return { ok: false, reason: 'bad-hash' };
    let uid = null, uname = '', authDate = null;
    kvs.forEach(p => {
      const i = p.indexOf('=');
      const k = p.slice(0, i), v = p.slice(i + 1);
      if (k === 'user') { try { const u = JSON.parse(decodeURIComponent(v)); uid = u.id; uname = (u.first_name || '') + (u.username ? ' (@' + u.username + ')' : ''); } catch (e) {} }
      if (k === 'auth_date') authDate = parseInt(v, 10) || null;
    });
    const fresh = !authDate || (Date.now() / 1000 - authDate) < OD_STALE_SEC;
    return { ok: true, user_id: uid, name: uname, fresh: fresh, reason: fresh ? 'ok' : 'stale-init-data' };
  } catch (err) {
    return { ok: false, reason: String(err) };
  }
}

function _odDoOrder(d) {
  try {
    const v = _odVerifyInitData(d.tg_init);
    let mid = String(d.manager_tg_id || '');
    const mode = v.ok && v.user_id ? 'init-verified' : (mid ? 'ref-link' : 'unattributed');
    if (v.ok && v.user_id) mid = String(v.user_id); // подписанный initData приоритетнее ?ref
    const mgr = _odManager(mid);
    const cbPct = mgr ? (Number(mgr.pct) || OD_DEFAULT_CASHBACK) : OD_DEFAULT_CASHBACK;
    const promo = String(d.promo || '');
    const pr = _odPrSheet();
    let existing = null;
    if (promo) {
      const last = pr.getLastRow();
      if (last > 1) {
        const codes = pr.getRange(2, 1, last - 1, 1).getValues();
        for (const r of codes) if (String(r[0]) === promo) { existing = true; break; }
      }
    }
    if (promo && !existing) {
      pr.appendRow([promo, mid, new Date(), d.model || '', d.scenario || '', d.total || 0,
        d.client_name || '', d.phone || '', d.city || '', 'open']);
    }
    // «Лиды»: колонки Менеджер/Промокод добавляем на ходу
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sh = ss.getSheetByName(SHEET_NAME);
    if (!sh) sh = ss.insertSheet(SHEET_NAME);
    const cols = sh.getLastColumn();
    const headers = sh.getRange(1, 1, 1, cols).getValues()[0];
    if (headers.indexOf('Менеджер') < 0) { cols; sh.getRange(1, cols + 1).setValue('Менеджер'); }
    const cols2 = sh.getLastColumn();
    if (sh.getRange(1, 1, 1, cols2).getValues()[0].indexOf('Промокод') < 0) sh.getRange(1, cols2 + 1).setValue('Промокод');
    const itemsText = (d.items || []).map(i => '• ' + i.name + ' ×' + i.qty + ' — ' + (i.price * i.qty) + ' ₽').join('\n');
    sh.appendRow([new Date(), 'Конфигуратор ОД', d.model || '', d.city || '', d.client_name || d.name || '',
      d.phone || '', (d.items || []).length, d.total || 0, d.comment || '', itemsText, mid, promo]);
    const cbFrom = Math.round((d.total || 0) * cbPct / 100);
    const cbTo = Math.round((d.total || 0) * 10 / 100);
    const msg =
      '🆕 Конфигуратор ОД ⚡️\n' +
      '👤 Клиент: ' + (d.client_name || '—') + '\n' +
      '📞 ' + (d.phone || '—') + '\n' +
      '📍 ' + (d.city || '—') + '\n' +
      '🚗 ' + (d.model || '—') + ' · ' + (d.scenario || '—') + '\n' +
      (itemsText ? itemsText + '\n' : '') +
      '💰 Итого: ' + (d.total || 0) + ' ₽\n' +
      '🎟 Промокод: ' + promo + ' (скидка 5% клиенту)\n' +
      '🎯 Менеджер: ' + (mgr ? (mgr.name + (mgr.salon ? ' · ' + mgr.salon : '') + ' [' + mid + ']') : (mid || 'не определён')) +
      ' · режим: ' + mode + (v.ok && !v.fresh ? ' (initData устарел)' : '') + '\n' +
      '💵 Кэшбэк ' + cbPct + '%: ' + cbFrom + ' ₽ (до ' + cbTo + ' ₽ при 10%)';
    tgSend(msg);
    return out({ ok: true, promo: promo, manager: mgr ? mgr.name : '', cashback_pct: cbPct, verify: mode });
  } catch (err) {
    try { tgSend('⚠️ Ошибка od_order: ' + err); } catch (e2) {}
    return out({ ok: false, error: String(err) });
  }
}

function _odFindByCode(code) {
  code = String(code || '').trim().toUpperCase();
  if (!code) return null;
  const sh = _odPrSheet();
  const last = sh.getLastRow();
  if (last < 2) return null;
  const vals = sh.getRange(2, 1, last - 1, OD_PR_HEADERS.length).getValues();
  for (const r of vals) {
    if (String(r[0]).trim().toUpperCase() === code) {
      return { code: r[0], tg_id: r[1], date: r[2], model: r[3], scenario: r[4], total: r[5],
        client: r[6], phone: r[7], city: r[8], status: String(r[9] || 'open') };
    }
  }
  return null;
}

function odCmdPromo(text, chatId) {
  const code = String(text || '').split(/\s+/)[1] || '';
  const p = _odFindByCode(code);
  if (!code || !p) {
    sendMessage(chatId, 'Промокод не найден. Формат: /promo ZSH-XXXXXX\nКоды выдаются в Конфигураторе: zapashoda-ev.ru/app/', openAppKb());
    return;
  }
  const mgr = _odManager(p.tg_id);
  let msg = '🎟 ' + p.code + '\n' +
    '🚗 ' + (p.model || '—') + ' · ' + (p.scenario || '—') + '\n' +
    '👤 Клиент: ' + (p.client || '—') + ' · ' + (p.phone || '—') + '\n' +
    '💰 Сумма: ' + (p.total || 0) + ' ₽\n' +
    '🎯 Менеджер: ' + (mgr ? (mgr.name + (mgr.salon ? ' · ' + mgr.salon : '')) : (p.tg_id || '—')) + '\n' +
    '📌 Статус: ' + (p.status === 'open' ? 'активен (скидка 5% клиенту)' : p.status);
  let kb = null;
  if (String(chatId) === String(CHAT_ID) && p.status === 'open') {
    kb = { inline_keyboard: [[{ text: '✅ Подтвердить продажу', callback_data: 'oduse:' + p.code }]] };
  }
  sendMessage(chatId, msg, kb);
}

function _odMarkUsed(code) {
  const sh = _odPrSheet();
  const last = sh.getLastRow();
  if (last < 2) return false;
  const vals = sh.getRange(2, 1, 1, OD_PR_HEADERS.length).getValues();
  for (let i = 0; i < last - 1; i++) {
    if (String(sh.getRange(2 + i, 1).getValue()).trim().toUpperCase() === String(code).trim().toUpperCase()) {
      sh.getRange(2 + i, 10).setValue('used');
      sh.getRange(2 + i, 11).setValue(new Date());
      return true;
    }
  }
  return false;
}

function _odBonusWeekText() {
  const sh = _odPrSheet();
  const last = sh.getLastRow();
  if (last < 2) return null;
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000;
  const per = {};
  const vals = sh.getRange(2, 1, last - 1, OD_PR_HEADERS.length).getValues();
  for (const r of vals) {
    const st = String(r[9] || 'open');
    if (st !== 'used') continue;
    const ts = (r[10] instanceof Date) ? r[10].getTime() : Date.parse(r[10] || 0) || 0;
    if (!ts || ts < weekAgo) continue;
    const mid = String(r[1] || '');
    if (!mid) continue;
    if (!per[mid]) per[mid] = { count: 0, total: 0 };
    per[mid].count += 1;
    per[mid].total += Number(r[5]) || 0;
  }
  const keys = Object.keys(per);
  if (!keys.length) return null;
  keys.sort((a, b) => per[b].total - per[a].total);
  const rows = keys.slice(0, 3).map((mid, i) => {
    const mgr = _odManager(mid);
    const name = mgr ? mgr.name : 'Менеджер';
    const city = mgr && mgr.city ? mgr.city : '';
    const salon = mgr && mgr.salon ? mgr.salon : '';
    const pct = mgr ? (Number(mgr.pct) || OD_DEFAULT_CASHBACK) : OD_DEFAULT_CASHBACK;
    const bonus = Math.round(per[mid].total * pct / 100);
    return (i + 1) + '. ' + name + (city ? ' из ' + city : '') + (salon ? ', салон ' + salon : '') +
      ' — продал ' + per[mid].count + ' комплект(ов) на ' + per[mid].total.toLocaleString('ru-RU') + ' ₽, бонус: ' + bonus.toLocaleString('ru-RU') + ' ₽';
  });
  return '🏆 Бонус недели\n\n' + rows.join('\n') +
    '\n\nКаждый комплект подобран в Конфигураторе за 30 секунд: у менеджера — промокод на скидку 5% для клиента и бонус 5–10% от чека.\n\n🔗 Стать партнёром: zapashoda-ev.ru/b2b/\n#бонус #дилеры';
}

function odCmdBonusWeek(chatId) {
  if (String(chatId) !== String(CHAT_ID)) {
    sendMessage(chatId, 'Команда доступна владельцу проекта.');
    return;
  }
  const text = _odBonusWeekText();
  if (!text) {
    sendMessage(chatId, 'За последние 7 дней подтверждённых продаж (статус used) нет. Отметьте продажи через /promo КОД → ✅ Подтвердить.');
    return;
  }
  try {
    sendMessage('@' + CHANNEL, text);
    sendMessage(chatId, 'Пост «Бонус недели» отправлен в канал 👍\n\n' + text);
  } catch (err) {
    sendMessage(chatId, 'Не удалось отправить в канал: ' + err + '\n\n' + text);
  }
}

// callback «Подтвердить продажу» — только владелец
(function () {
  const _origHandleCallback = handleCallback;
  handleCallback = function (cb) {
    try {
      const data = String((cb && cb.data) || '');
      if (data.indexOf('oduse:') === 0) {
        const chatId = (cb.message && cb.message.chat && cb.message.chat.id) || null;
        if (String(chatId) !== String(CHAT_ID)) return;
        const code = data.slice(6);
        const ok = _odMarkUsed(code);
        const p = _odFindByCode(code);
        if (ok && p) {
          const mgr = _odManager(p.tg_id);
          const pct = mgr ? (Number(mgr.pct) || OD_DEFAULT_CASHBACK) : OD_DEFAULT_CASHBACK;
          const bonus = Math.round((p.total || 0) * pct / 100);
          sendMessage(chatId, '✅ Продажа по промокоду ' + code + ' подтверждена.\n🎯 Менеджер: ' + (mgr ? mgr.name : p.tg_id) + '\n💵 Кэшбэк ' + pct + '%: ' + bonus.toLocaleString('ru-RU') + ' ₽ — зафиксирован.');
          tgSend('✅ Продажа подтверждена: ' + code + ' · менеджер ' + (mgr ? mgr.name : p.tg_id) + ' · кэшбэк ' + bonus + ' ₽');
        } else {
          sendMessage(chatId, 'Не нашёл промокод ' + code + ' — проверьте код.');
        }
        return;
      }
    } catch (e) { Logger.log('oduse: ' + e); }
    return _origHandleCallback(cb);
  };
})();

/* ============================================================
 * OD SELF-TEST — полный прогон тест-сценария B2B2C без Telegram.
 * Запустить ОДИН РАЗ из редактора ПОСЛЕ вставки файла (и после odSetup).
 * Прогоняет: odSetup → HMAC-подпись initData тест-менеджера → _odDoOrder →
 * → поиск промокода (аналог /promo) → перевод в used (аналог ✅) →
 * → сборка «Бонуса недели» (аналог /bonusweek) → чистка тестовых строк.
 * Результат — в лог (Ctrl+Enter) и возвращаемым значением.
 * ============================================================ */
function _odSelfTestCleanup(promo) {
  promo = String(promo || '');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const pr = ss.getSheetByName(OD_PR_SHEET);
  if (pr && pr.getLastRow() > 1) {
    for (let r = pr.getLastRow(); r >= 2; r--) {
      if (String(pr.getRange(r, 1).getValue()).trim().toUpperCase() === promo.toUpperCase()) pr.deleteRow(r);
    }
  }
  const sh = ss.getSheetByName(SHEET_NAME);
  if (sh && sh.getLastRow() > 1) {
    const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    const pi = headers.indexOf('Промокод') + 1;
    const ni = headers.indexOf('Имя') + 1;
    for (let r2 = sh.getLastRow(); r2 >= 2; r2--) {
      let hit = false;
      if (pi > 0 && String(sh.getRange(r2, pi).getValue()).trim().toUpperCase() === promo.toUpperCase()) hit = true;
      if (!hit && ni > 0 && String(sh.getRange(r2, ni).getValue()).indexOf('SELF-TEST') >= 0) hit = true;
      if (hit) sh.deleteRow(r2);
    }
  }
}

function odSelfTest() {
  const out = [];
  const ok = (name, cond) => out.push((cond ? '✅ ' : '❌ ') + name);
  const promo = 'ZSH-SELFTEST';
  try {
    odSetup();
    _odSelfTestCleanup(promo); // идемпотентность: убираем хвосты прошлых прогонов
    // 1. Строим валидный initData тест-менеджера №1 (подпись реальным токеном бота)
    const uid = OD_SEED_MANAGERS[0].tg_id;
    const params = [
      'auth_date=' + Math.floor(Date.now() / 1000),
      'query_id=AAAAselftest00000000000000',
      'user=' + encodeURIComponent(JSON.stringify({ id: Number(uid), first_name: 'Антон', username: 'selftest' }))
    ];
    params.sort();
    const secret = Utilities.computeHmacSignature(Utilities.MacAlgorithm.HMAC_SHA_256, TELEGRAM_TOKEN, 'WebAppData', Utilities.Charset.UTF_8);
    const sig = Utilities.computeHmacSignature(Utilities.MacAlgorithm.HMAC_SHA_256, Utilities.newBlob(params.join('\n')).getBytes(), secret);
    const initData = params.join('&') + '&hash=' + _odHex(sig);
    const v = _odVerifyInitData(initData);
    ok('1. Верификация initData (HMAC по реальному токену бота)', v.ok && String(v.user_id) === uid);
    ok('1a. init-режим определён как init-verified', (v.ok && String(v.user_id) === uid) ? _odVerifyInitData(initData).reason === 'ok' : false);
    // 2. Тестовая заявка od_order (Zeekr 001, дом, 2 позиции)
    const d = {
      t: 'od_order', promo: promo, manager_tg_id: uid, manager_name: 'Антон',
      tg_init: initData, brand: 'Zeekr', model: 'Zeekr 001 / 001 FR', scenario: 'house',
      items: [
        { id: 1, name: 'Адаптер Type 2 → GB/T, 22 кВт, премиум', qty: 1, price: 7000 },
        { id: 13, name: 'Настенная станция GB/T, 7 кВт', qty: 1, price: 39000 }
      ],
      total: 46000, client_name: 'SELF-TEST Алиса', name: 'SELF-TEST Алиса',
      phone: '+7 999 000-00-00', city: 'Тест-Сити',
      comment: 'odSelfTest — строки удаляются автоматически', website: '', source: 'tma_od'
    };
    const res = JSON.parse(_odDoOrder(d).getContentText());
    ok('2. _odDoOrder вернул ok=true', res.ok === true);
    ok('2a. Промокод в ответе: ' + promo, res.promo === promo);
    ok('2b. Кэшбэк по реестру = 5%', res.cashback_pct === 5);
    ok('2c. Режим атрибуции = init-verified', res.verify === 'init-verified');
    // 3. /promo: поиск кода
    const p = _odFindByCode(promo);
    ok('3. Промокод найден в «Промокодах» (/promo path)', !!p && String(p.model).indexOf('Zeekr') >= 0);
    // 3а. Строка в «Лидах»
    ok('3a. Строка «Конфигуратор ОД» в «Лидах»', (function () {
      const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
      const last = sh.getLastRow();
      if (last < 2) return false;
      const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
      const ti = headers.indexOf('Тип');
      const vals = sh.getRange(Math.max(2, last - 5), ti + 1, Math.min(5, last - 1), 1).getValues();
      return vals.some(r => String(r[0]).indexOf('Конфигуратор ОД') === 0);
    })());
    // 4. ✅ Подтвердить продажу
    ok('4. Промокод переведён в used', _odMarkUsed(promo) && String(_odFindByCode(promo).status) === 'used');
    // 5. /bonusweek
    const bw = _odBonusWeekText();
    ok('5. «Бонус недели» собрался с тестовой продажей', !!bw && bw.indexOf('Антон') >= 0);
    if (bw) out.push('   ↳ превью поста: ' + bw.split('\n')[0] + ' …');
    // 6. Чистка
    _odSelfTestCleanup(promo);
    ok('6. Тестовые строки удалены (Промокоды + Лиды)', !_odFindByCode(promo));
    out.push('');
    out.push('GAS-часть сценария B2B2C: ' + (out.every(l => l.indexOf('✅') === 0 || l.indexOf('   ') === 0 || l === '') ? 'ПОЛНОСТЬЮ ЗЕЛЁНАЯ' : 'ЕСТЬ СБОИ — смотри ❌'));
    Logger.log('===== OD SELF TEST =====\n' + out.join('\n'));
    return out.join('\n');
  } catch (err) {
    out.push('💥 Исключение: ' + err);
    try { _odSelfTestCleanup(promo); } catch (e2) {}
    Logger.log(out.join('\n'));
    return out.join('\n');
  }
}


/* ============================================================
 * SHOP v9 — Т-КАССА (интернет-эквайринг Т-Банка): продажа цифровых гайдов
 * Flow: POST t='shop_init' (email) → /v2/Init (Receipt 54-ФЗ) → PaymentURL →
 * оплата → webhook (AUTHORIZED/CONFIRMED) → лист «Заказы» → одноразовый токен →
 * письмо MailApp + выдача токена на success-странице → doGet?t= → PDF.
 * Секреты — только в Script Properties, в репозиторий не попадают.
 * ============================================================ */

const SHOP_PRICE_RUB = 490;
const SHOP_PRODUCT = 'm4don';
const SHOP_PRODUCT_TITLE = 'Цифровой путеводитель М-4 «Дон»';
const SHOP_SUCCESS_URL = 'https://zapashoda-ev.ru/shop/digital/success.html';
const SHOP_API_BASE = 'https://securepay.tinkoff.ru';
const SHOP_ORDERS_SHEET = 'Заказы';
const SHOP_ORDERS_HEADERS = ['OrderId', 'Дата', 'Продукт', 'Email', 'Сумма ₽', 'Статус', 'PaymentId', 'Токен', 'Скачиваний', 'Примечание'];
const SHOP_TAXATION = 'usn_income';
const SHOP_PAYMENT_OBJECT = 'commodity';
const SHOP_TOKEN_MAX_USES = 1;
const SHOP_FALLBACK_KEY = '';
const SHOP_FALLBACK_PWD = '';

function shopSetCreds(key, pwd) {
  PropertiesService.getScriptProperties().setProperties({
    SHOP_TERMINAL_KEY: String(key || ''),
    SHOP_TERMINAL_PWD: String(pwd || '')
  });
  Logger.log('SHOP: ключи терминала сохранены в Script Properties');
}

function shopSetPdf(product, fileId) {
  PropertiesService.getScriptProperties().setProperty(
    'SHOP_PDF_' + String(product || SHOP_PRODUCT).toUpperCase(), String(fileId || ''));
  Logger.log('SHOP: PDF привязан (' + String(product || SHOP_PRODUCT) + ')');
}

function _shopCreds() {
  const p = PropertiesService.getScriptProperties();
  return {
    key: p.getProperty('SHOP_TERMINAL_KEY') || SHOP_FALLBACK_KEY,
    pwd: p.getProperty('SHOP_TERMINAL_PWD') || SHOP_FALLBACK_PWD
  };
}

function _shopSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHOP_ORDERS_SHEET);
  if (!sh) sh = ss.insertSheet(SHOP_ORDERS_SHEET);
  if (sh.getLastRow() === 0) { sh.appendRow(SHOP_ORDERS_HEADERS); sh.setFrozenRows(1); }
  return sh;
}

// Token = SHA256 от конкатенации отсортированных key=value (без Token/Receipt/Receipts/Data и пустых) + Password
function _shopToken(obj, pwd) {
  const parts = [];
  Object.keys(obj).sort().forEach(function (k) {
    if (k === 'Token' || k === 'Receipt' || k === 'Receipts' || k === 'Data') return;
    let v = obj[k];
    if (typeof v === 'boolean') v = v ? 'true' : 'false';
    else if (v === null || typeof v === 'object') return;
    v = String(v);
    if (v === '') return;
    parts.push(k + '=' + v);
  });
  return _odHex(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, parts.join('') + pwd, Utilities.Charset.UTF_8));
}

function _shopInit(d) {
  try {
    const c = _shopCreds();
    if (!c.key || !c.pwd) return out({
      ok: false, error: 'terminal-not-configured',
      hint: 'Выполните shopSetCreds(TerminalKey, Password) — тестовый терминал выдаётся в ЛК Т-Бизнеса'
    });
    const email = String(d.email || '').trim().toLowerCase();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)) return out({ ok: false, error: 'bad-email' });
    const product = String(d.product || SHOP_PRODUCT);
    if (product !== SHOP_PRODUCT) return out({ ok: false, error: 'unknown-product' });
    const sh0 = _shopSheet();
    const last0 = sh0.getLastRow();
    let nSame = 0;
    if (last0 > 1) {
      const vals0 = sh0.getRange(2, 2, last0 - 1, 3).getValues();
      const hourAgo = Date.now() - 3600 * 1000;
      vals0.forEach(function (r) {
        const dt = (r[0] instanceof Date) ? r[0].getTime() : (Date.parse(r[0]) || 0);
        if (String(r[1]) === email && dt > hourAgo) nSame += 1;
      });
    }
    if (nSame >= 5) return out({ ok: false, error: 'too-many-requests' });
    const amount = SHOP_PRICE_RUB * 100;
    const oid = 'ZSD-' + new Date().toISOString().slice(2, 10).replace(/-/g, '') + '-' +
      Math.random().toString(36).slice(2, 8).toUpperCase();
    sh0.appendRow([oid, new Date(), product, email, SHOP_PRICE_RUB, 'pending', '', '', 0, 'Init запрошен']);
    const selfUrl = ScriptApp.getService().getUrl() ||
      PropertiesService.getScriptProperties().getProperty('SHOP_SELF_URL') || '';
    const payload = {
      TerminalKey: c.key,
      Amount: amount,
      OrderId: oid,
      Description: (SHOP_PRODUCT_TITLE + ' (заказ ' + oid + ')').slice(0, 140),
      SuccessURL: SHOP_SUCCESS_URL + '?oid=' + oid,
      FailURL: SHOP_SUCCESS_URL + '?oid=' + oid + '&fail=1',
      NotificationURL: selfUrl
    };
    payload.Token = _shopToken(payload, c.pwd);
    payload.Receipt = {
      Email: email,
      Taxation: SHOP_TAXATION,
      Items: [{ Name: SHOP_PRODUCT_TITLE, Price: amount, Quantity: 1, Amount: amount,
        Tax: 'none', PaymentMethod: 'full', PaymentObject: SHOP_PAYMENT_OBJECT }]
    };
    const r = UrlFetchApp.fetch(SHOP_API_BASE + '/v2/Init', {
      method: 'post', contentType: 'application/json',
      payload: JSON.stringify(payload), muteHttpExceptions: true
    });
    let res = {};
    try { res = JSON.parse(r.getContentText()); } catch (e2) {}
    const row = sh0.getLastRow();
    if (!res.Success) {
      sh0.getRange(row, 6).setValue('init-failed');
      sh0.getRange(row, 10).setValue(String(res.Message || '') + ' ' + String(res.Details || ''));
      return out({ ok: false, error: 'init-rejected', message: res.Message || '', details: res.Details || '' });
    }
    sh0.getRange(row, 6).setValue('created');
    if (res.PaymentId) sh0.getRange(row, 7).setValue(String(res.PaymentId));
    tgSend('🛍 Новый заказ на гайд: ' + SHOP_PRODUCT_TITLE + '\n📧 ' + email + '\n💰 ' + SHOP_PRICE_RUB + ' ₽\n🧾 ' + oid);
    return out({ ok: true, paymentUrl: res.PaymentURL, orderId: oid });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  }
}

function _shopNotification(d) {
  const c = _shopCreds();
  const expected = _shopToken(d, c.pwd);
  if (c.pwd && expected !== String(d.Token || '')) {
    tgSend('⚠️ SHOP: уведомление с неверной подписью (' + String(d.OrderId || '?') + ')');
    return out({ ok: false, error: 'bad-token-signature' });
  }
  const oid = String(d.OrderId || '');
  const status = String(d.Status || '');
  const sh = _shopSheet();
  const last = sh.getLastRow();
  let row = 0;
  if (last > 1) {
    const vals = sh.getRange(2, 1, last - 1, 1).getValues();
    for (let i = 0; i < vals.length; i++) if (String(vals[i][0]) === oid) { row = i + 2; break; }
  }
  if (!row) return out({ ok: true, note: 'unknown-order' });
  const success = (d.Success === true || d.Success === 'true');
  if (success && (status === 'AUTHORIZED' || status === 'CONFIRMED')) {
    const cur = String(sh.getRange(row, 6).getValue());
    if (cur !== 'paid') {
      const token = Utilities.getUuid().replace(/-/g, '');
      sh.getRange(row, 6).setValue('paid');
      sh.getRange(row, 7).setValue(String(d.PaymentId || ''));
      sh.getRange(row, 8).setValue(token);
      const email = String(sh.getRange(row, 4).getValue());
      const link = (ScriptApp.getService().getUrl() ||
        PropertiesService.getScriptProperties().getProperty('SHOP_SELF_URL') || '') + '?t=' + token;
      try {
        MailApp.sendEmail({
          to: email,
          subject: 'Гайд М-4 «Дон» — ссылка на скачивание (заказ ' + oid + ')',
          htmlBody: '<p>Спасибо за покупку!</p>'
            + '<p>Одноразовая ссылка на скачивание PDF:</p>'
            + '<p><a href="' + link + '">Скачать гайд М-4 «Дон»</a></p>'
            + '<p>Ссылка срабатывает один раз — так мы защищаем файл от копирования. '
            + 'Заказ: ' + oid + ', оплата: ' + SHOP_PRICE_RUB + ' ₽.</p>'
            + '<p>Если ссылка не открылась — напишите нам: zapashoda-ev.ru</p>'
        });
      } catch (e2) { sh.getRange(row, 10).setValue('mail-failed: ' + e2); }
      tgSend('💳 ОПЛАТА: ' + SHOP_PRODUCT_TITLE + '\n📧 ' + email + '\n💰 ' + SHOP_PRICE_RUB + ' ₽\n🧾 ' + oid + ' (' + status + ')\nОдноразовый токен выдан');
    } else {
      sh.getRange(row, 10).setValue('повторное уведомление ' + status);
    }
  } else if (!success) {
    sh.getRange(row, 6).setValue('failed:' + status);
  } else {
    sh.getRange(row, 10).setValue('уведомление: ' + status);
  }
  return out({ ok: true });
}

function _shopStatus(oid) {
  const sh = _shopSheet();
  const last = sh.getLastRow();
  let row = 0;
  if (last > 1) {
    const vals = sh.getRange(2, 1, last - 1, 1).getValues();
    for (let i = 0; i < vals.length; i++) if (String(vals[i][0]) === String(oid)) { row = i + 2; break; }
  }
  if (!row) return out({ ok: true, status: 'unknown' });
  const vals = sh.getRange(row, 1, 1, SHOP_ORDERS_HEADERS.length).getValues()[0];
  const status = String(vals[5] || '');
  const token = String(vals[7] || '');
  const uses = Number(vals[8]) || 0;
  const res = { ok: true, orderId: String(oid), status: status };
  if (status === 'paid' && token) {
    if (uses < SHOP_TOKEN_MAX_USES) { res.token = token; res.download_status = 'available'; }
    else res.download_status = 'used';
  }
  return out(res);
}

function _shopDownload(token) {
  token = String(token || '').trim();
  const sh = _shopSheet();
  const last = sh.getLastRow();
  let row = 0;
  if (last > 1) {
    const vals = sh.getRange(2, 1, last - 1, 1).getValues();
    for (let i = 0; i < vals.length; i++) if (String(vals[i][7] || '') === token) { row = i + 2; break; }
  }
  if (!row) return HtmlService.createHtmlOutput(
    '<h2>Ссылка недействительна</h2><p>Токен не найден. Запросите повторную выдачу в поддержке zapashoda-ev.ru.</p>').setTitle('Ссылка недействительна');
  const uses = Number(sh.getRange(row, 9).getValue()) || 0;
  if (uses >= SHOP_TOKEN_MAX_USES) return HtmlService.createHtmlOutput(
    '<h2>Ссылка уже использована</h2><p>Одноразовая ссылка уже сработала — PDF также отправлен на ваш email. Нужна повторная выдача: напишите нам.</p>').setTitle('Ссылка использована');
  const fileId = PropertiesService.getScriptProperties().getProperty('SHOP_PDF_M4DON');
  if (!fileId) return HtmlService.createHtmlOutput(
    '<h2>Файл ещё не подключён</h2><p>Токен жив, но файл гайда ещё не загружен — повторите попытку позже или напишите в поддержку.</p>').setTitle('Гайд готовится');
  const b64 = Utilities.base64Encode(DriveApp.getFileById(fileId).getBlob().getBytes());
  sh.getRange(row, 9).setValue(uses + 1);
  return HtmlService.createHtmlOutput(
    '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<title>Гайд М-4 «Дон» — скачивание</title></head>'
    + '<body style="font-family:system-ui,sans-serif;text-align:center;padding-top:48px">'
    + '<h2>Спасибо за покупку 🎉</h2><p>Файл скачивается автоматически. Если нет — нажмите кнопку.</p>'
    + '<a id="dl" download="guide-m4don.pdf" style="display:inline-block;margin:16px;padding:12px 22px;border-radius:12px;background:#1fbf75;color:#fff;text-decoration:none">⬇️ Скачать PDF</a>'
    + '<p style="color:#777;font-size:12px">Ссылка одноразовая — больше не сработает.</p>'
    + '<script>document.getElementById("dl").href="data:application/pdf;base64,' + b64 + '";'
    + 'var a=document.createElement("a");a.href=document.getElementById("dl").href;a.download="guide-m4don.pdf";document.body.appendChild(a);a.click();<\/script>'
    + '</body></html>').setTitle('Гайд М-4 «Дон»');
}

function shopSelfTest(live) {
  const res = [];
  const ok = function (n, c) { res.push((c ? '✅ ' : '❌ ') + n); };
  const c = _shopCreds();
  ok('1. Ключи терминала записаны (Script Properties или константы)', !!(c.key && c.pwd));
  ok('2. Лист «Заказы» доступен', !!_shopSheet());
  ok('3. PDF гайда привязан (shopSetPdf)', !!PropertiesService.getScriptProperties().getProperty('SHOP_PDF_M4DON'));
  const sample = { TerminalKey: 'X', Amount: 49000, OrderId: 'Z' };
  ok('4. Подпись детерминирована', _shopToken(sample, 'P') === _shopToken(sample, 'P'));
  ok('4a. Подпись зависит от пароля', _shopToken(sample, 'P') !== _shopToken(sample, 'Q'));
  if (live) {
    try {
      const r = JSON.parse(_shopInit({ t: 'shop_init', email: 'shop-selftest@example.com', product: SHOP_PRODUCT }).getContentText());
      ok('5. Живой Init к Т-Кассе', r.ok === true && !!r.paymentUrl);
      if (r.ok) res.push('   ↳ тест-заказ ' + r.orderId + ' создан — оплатите тестовой картой из ЛК Т-Банка');
      else res.push('   ↳ Init отклонён: ' + (r.message || r.error || '') + ' ' + (r.details || ''));
    } catch (e) { ok('5. Живой Init к Т-Кассе', false); res.push('   ↳ ' + e); }
  }
  Logger.log('===== SHOP SELF TEST =====\n' + res.join('\n'));
  return res.join('\n');
}
