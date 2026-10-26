# GOLD V9 — GitHub Actions + Biquote + Telegram (bepul prototip)

## Nima qiladi?
- Biquote `/api/XAUUSD/ohlc?interval=5m&limit=250` orqali M5 OHLC oladi.
- Yopilgan shamda EMA100 + oldingi 10 sham high/low breakoutni tekshiradi.
- ATR14 × 1.8 bo'yicha taxminiy SL va RR3 TP hisoblaydi.
- Kuniga 2 tadan ortiq kirish xabarini bermaydi (UTC).
- Oxirgi tekshirilgan sham va virtual pozitsiya holatini `state.json` orqali saqlaydi.
- Birinchi ishga tushganda eski signal yubormaydi.

## 0 so'm bilan ishga tushirish
1. GitHub'da bepul akkaunt yarating.
2. YANGI **public** repository yarating (masalan `gold-v9-telegram`). Public GitHub Actions standart runnerlari bepul. Public repo ichida kod va state.json ko'rinadi, lekin tokenlar ko'rinmaydi.
3. ZIP ichidagi fayllarni repositoryga yuklang. **`.github/workflows/gold-v9.yml` yo'li aynan shunday saqlansin.** GitHub veb interfeysi yashirin `.github` papkasini ko'rsatishi mumkin.
4. Telegram @BotFather orqali bot yarating. Tokenni hech kimga yubormang. Botga `/start` yozing.
5. Chat ID ni olish uchun `https://api.telegram.org/botTOKEN/getUpdates` manzilidan `message.chat.id` ni toping. Bu URLni hech kim bilan bo'lishmang.
6. GitHub repository → Settings → Secrets and variables → Actions → New repository secret:
   - `TELEGRAM_BOT_TOKEN` = BotFather token
   - `TELEGRAM_CHAT_ID` = chat ID
7. Repository → Settings → Actions → General → Workflow permissions → **Read and write permissions** ni tanlang va saqlang (agar mavjud bo'lsa).
8. Actions → GOLD V9 Telegram Signals → Run workflow tugmasini bosing. Birinchi ishga tushish `state.json` yaratadi, tarixiy signal yubormaydi.
9. Actions loglarida `Initialized without historical alert` yoki `Processed` yozuvini tekshiring. Keyingi ishga tushishlar cron bo'yicha bo'ladi.

## Jiddiy cheklovlar
- GitHub Actions cron **aniq har 5 daqiqada** ishga tushishini kafolatlamaydi, ayrim ishlar kechikishi yoki o'tkazib yuborilishi mumkin.
- Biquote XAUUSD ma'lumotlari XM Standard narxlari emas. Uning OHLC tarixi ham broker, sessiya va sham vaqtiga qarab TradingView'dan farq qilishi mumkin.
- Bu **signal prototipi**, XM'ga order yubormaydi va Pine V9 strategiyasini 100% takrorlamaydi. Signal shami yopilgandan keyin keyingi sham ochilishidagi real fill va stop/target ketma-ketligi kafolatlanmaydi.
- 24 shamlik virtual pozitsiya, stop/target tekshiruvi faqat tekshirilgan so'nggi shamda bajariladi. GitHub kechiksa, ayrim exitlar o'tib ketadi. Uzoq uzilishda virtual pozitsiya bekor qilinadi.
- Biquote ma'lumotlari eskirganida yoki bozor yopiq bo'lsa, xabar yuborilmaydi.
- `state.json` public repo'da ko'rinadi; u token saqlamaydi. Tokenni hech qachon faylga yoki chatga yozmang.
- Bepul xizmatlarning shartlari o'zgarishi mumkin; GitHub Actions limitlari va xizmatning mavjudligini kuzating.
- Real pulda ishlatishdan oldin XM demo hisobida kamida 30–50 signalni solishtiring.
