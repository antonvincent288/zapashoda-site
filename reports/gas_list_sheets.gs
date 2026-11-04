/**
 * ЗАПАС ХОДА — фонарик: показывает, к какой таблице привязан GAS и какие в ней листы.
 * Ничего не меняет, только читает и пишет в журнал.
 */
function listSheets() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    Logger.log('СКРИПТ НЕ ПРИВЯЗАН К ТАБЛИЦЕ (standalone). Каталог ищем через Диск.');
    return;
  }
  Logger.log('Таблица: ' + ss.getName());
  Logger.log('URL: ' + ss.getUrl());
  ss.getSheets().forEach(function(s) {
    Logger.log('лист: ' + s.getName() + ' | строк: ' + s.getLastRow());
  });
}
