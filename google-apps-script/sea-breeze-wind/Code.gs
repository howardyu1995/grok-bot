/**
 * 風的形成｜海風原理互動教學
 * Google Apps Script 網頁應用程式入口
 *
 * 部署後可把網址嵌入 Google 協作平台（Google Sites）。
 * 請務必設定 XFrameOptionsMode.ALLOWALL，否則 Sites 的 iframe 會被擋。
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('風的形成｜海風原理互動教學')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
