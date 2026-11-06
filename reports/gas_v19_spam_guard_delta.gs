/**
 * ════════════════════════════════════════════════════════════════
 *  GAS v19 DELTA — «ОХРАНА» (анти-спам в канале и комментариях)
 *  Задача: удалять рекламный спам (пробив-боты и т.п.) в канале
 *  @zapashoda_ev и в связанном чате комментариев, и докладывать
 *  владельцу в личку. Больше никак не меняет поведение бота.
 *
 *  КАК ВСТАВИТЬ (1 минута):
 *  1) Telegram: в боте @BotFather нет прав не нужно; бот должен быть
 *     АДМИНОМ канала (уже есть — публикует тизеры) и, чтобы чистить
 *     комментарии, — админом связанного чата обсуждения
 *     (Управление каналом → Обсуждение → добавить админом с правом
 *     «Удаление сообщений»).
 *  2) Открой проект GAS бота (расширения → Apps Script).
 *  3) Создай новый файл «ОХРАНА.gs» и вставь ВЕСЬ этот файл.
 *  4) В существующем файле найди функцию checkUpdates() и цикл:
 *         if (u.callback_query) { handleCallback(u.callback_query); continue; }
 *         handleUpdate(u);
 *     замени на:
 *         if (u.callback_query) { handleCallback(u.callback_query); continue; }
 *         spamGuard(u);
 *         handleUpdate(u);
 *  5) Сохрани (Ctrl+S). Всё — охрана работает на ежеминутном опросе.
 * ════════════════════════════════════════════════════════════════
 */

var SPAM_RE = /(пробив[аыу]?\b|пробить\s+(?:чел|человека|номер)|поиск\s+человека\s+по\s+фото|телефон.{0,6}(?:фио|по\s+номеру)|(?:новый|рабочий)\s+бот\s+(?:для\s+)?(?:пробива|пробит)|слив\s+баз)/i;
var SPAM_ALERT_COOLDOWN_MS = 10 * 60 * 1000; // не чаще 1 алерта в 10 минут

function spamGuard(u) {
  try {
    var post = u.channel_post;        // посты в самом канале
    var msg  = u.message;             // сообщения в чатах (вкл. комментарии/группу)
    var m = post || msg;
    if (!m) return;
    var chatType = (m.chat && m.chat.type) || '';
    if (!post && chatType.indexOf('group') === -1) return; // личку не трогаем
    var text = (m.text || m.caption || '') + '';
    if (!text) return;
    if (!SPAM_RE.test(text)) return;

    var chatId = m.chat.id;
    var msgId = m.message_id;
    var who = (m.from && (m.from.username ? '@' + m.from.username : m.from.first_name)) || (post ? 'автор канала' : '?');
    var snippet = text.replace(/\s+/g, ' ').slice(0, 120);

    // удалить
    var del = UrlFetchApp.fetch('https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/deleteMessage', {
      method: 'post', payload: { chat_id: String(chatId), message_id: String(msgId) }
    });

    // доклад владельцу (не чаще, чем раз в 10 минут)
    var props = PropertiesService.getScriptProperties();
    var last = parseInt(props.getProperty('SPAM_LAST_ALERT') || '0', 10);
    var now = Date.now();
    if (now - last > SPAM_ALERT_COOLDOWN_MS) {
      props.setProperty('SPAM_LAST_ALERT', String(now));
      var where = post ? 'КАНАЛ @' + CHANNEL : 'комментарии/чат (' + chatType + ')';
      sendMessage(CHAT_ID,
        '🛡 ОХРАНА: удалён спам (' + where + ')\n' +
        'От: ' + who + '\nФрагмент: «' + snippet + '»\n' +
        'Ответ бота: ' + del.getContentText() + '\n' +
        'Если удалять не хотел — проверь слово в спам-списке ОХРАНА.gs (SPAM_RE).');
    }
    Logger.log('[ОХРАНА] удалено ' + where + ' от ' + who + ': ' + snippet);
  } catch (err) {
    Logger.log('[ОХРАНА] error: ' + err);
  }
}

/* Тест: в редакторе GAS запусти spamGuardTest() — уведомление в личку значит, что охрана жива. */
function spamGuardTest() {
  sendMessage(CHAT_ID, '🛡 ОХРАНА v19 установлена и запущена. Спам в канале и комментариях будет удаляться автоматически.');
}
