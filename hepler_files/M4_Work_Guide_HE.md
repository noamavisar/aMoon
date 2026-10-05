# מדריך ביצוע M4 לדמו המצומצם

חילוץ טקסט מ PDF ובדיקת ציטוטים

השלב הנוכחי שלך הוא M4. המטרה היא שהמערכת תוכל לקרוא את הדק שכבר מגיע מ־Gmail, לשמור את מספרי העמודים ולבדוק אם ציטוט מופיע במקור. זה הבסיס למנתח היחיד שנוסיף בשלב הבא.

בסיום יהיה לך כלי שעובד מקומית: PDF נכנס, מתקבלים טקסט עמודים ואזהרות, וציטוטים אמיתיים ומומצאים מקבלים תוצאות שונות. M4 אינו מפיק עדיין תדריך השקעה. החיבור למנתח ולדוח הטקסט נעשה בשלב הבא בתוכנית המצומצמת.

## 1 מה כבר ידוע על הפרויקט שלך

לפי דיווחך, M0–M3 הושלמו. ב־Workflow שצירפת קיימים Gmail Trigger, Get Full Message, Normalize Gmail Message, POST Triage, Route by Action, Select PDF Attachment, If, Prepare PDF for API ו־POST Analyze.

Gmail כבר מוריד את הקובץ ל־binary. Prepare PDF for API ממיר את הקובץ ל־base64 ושולח אותו אל /opportunities/{id}/analyze. אין צורך בהורדה נוספת או ב־OAuth נוסף.

אני לא מחזיק את קוד ה־API הנוכחי שלך. כדי לא להסתמך על שמות של מחלקות או על מימושים שלא נבדקו, המדריך מוסיף מודול נפרד בשם app/m4_pdf.py. הוא אינו מחליף את schemas.py, main.py או parsing.py. בשלב הבא נחבר אותו לשרת הקיים.

תקציב העבודה המוצע הוא 45–60 דקות כאשר סביבת Python מוכנה. זו מסגרת עבודה ולא הבטחת זמן. ההיקף כאן הוא PDF אחד עם טקסט, עד 25 עמודים ועד 10 MiB.

## 2 המושגים שתצטרך להכיר

**PDF עם שכבת טקסט:** המילים קיימות בקובץ כטקסט שהקוד יכול לקרוא. בדק שמור כתמונות בלבד, העין רואה מילים אך חילוץ רגיל אינו רואה אותן. OCR הוא מנגנון נפרד לזיהוי טקסט מתמונה, והוא מחוץ להיקף הדמו.

**bytes:** תוכן הקובץ בפורמט שהמחשב קורא. **base64:** ייצוג של התוכן הזה כמחרוזת כדי להעבירו ב־JSON. M4 מקבל bytes לאחר פענוח ה־base64. בבדיקה המקומית קוראים את הקובץ ישירות, ולכן אין צורך לעבוד עם base64.

**parser:** קוד שפותח את הקובץ ומחלץ ממנו תוכן. נשתמש ב־PyMuPDF, הספרייה שנבחרה בתוכנית המקורית.

**עמוד מקור:** העמוד הראשון בקובץ PDF הוא 1, השני הוא 2 וכו'. אם בשקופית מודפס מספר אחר, הוא אינו קובע את מספור המקור שלנו. לא מוחקים עמודים ריקים, כדי שהפניות לעמודים יישארו נכונות.

**אזהרה לעומת שגיאה:** אזהרה אומרת שחלק מהחילוץ דל אך אפשר להמשיך עם הסבר. שגיאה צפויה אומרת שהקלט אינו מתאים למסלול האוטומטי, למשל PDF ללא טקסט. תקלה בקוד או בסביבה היא חסימת פיתוח שצריך לתקן.

**אימות ציטוט:** בדיקה שהמילים מופיעות במייל או בעמוד PDF מסוים. זו אינה בדיקה שטענת החברה נכונה. למשל, מציאת סכום בדק מוכיחה שהדק מציג את הסכום.

**נרמול whitespace:** החלפת רצפים של רווחים, ירידות שורה וטאבים ברווח אחד, לצורך ההשוואה בלבד. לא משנים מספרים, מטבע, אותיות או סימני פיסוק.

**SHA-256:** מזהה שמחושב מתוכן הקובץ. הוא עוזר לוודא שאתה בודק את אותו קובץ. הוא אינו מדד איכות או אמינות.

**Terminal:** החלון שבו מריצים פקודות. פקודה מתחילה רק כשלוחצים Enter. קוד Python שייך לקובצי .py; פקודות PowerShell שייכות ל־Terminal.

## 3 מה נמצא בחבילת M4

פתח את M4_Starter.zip באמצעות לחיצה ימנית ואז Extract All. בחבילה יש:

```text
M4_Work_Guide_HE.md                 המדריך הזה
app/
  m4_pdf.py                        חילוץ PDF ובדיקת ציטוטים
scripts/
  inspect_m4_pdf.py                 הרצה על PDF אחד ושמירת תוצאת בדיקה
tests/
  test_m4_pdf.py                    בדיקות אוטומטיות ממוקדות
fixtures/m4/
  agilerpm_text_reference.pdf       דוגמה חיובית
  agilerpm_image_only.pdf           דוגמה שלילית
FIXTURE_PROVENANCE.txt              תיאור מקורות קובצי הדמו
```

ה־PDF החיובי הוא תמלול טקסט שכבר נוצר מתוך פסקאות מצגת AgileRPM. הוא שומר 21 עמודי מקור, אך אינו ייצוא שמשמר את עיצוב המצגת. אפשר להשתמש בו כדי לחסוך זמן בפיתוח ולציין את סוג הקלט בהצגת הדמו. הדוגמה השלילית היא ה־PDF המקורי שבמקורות הפרויקט.

אם כבר ייצאת מ־PowerPoint PDF בעל שכבת טקסט, תוכל לבדוק גם אותו בהמשך. לא צריך לעצור את המימוש כדי ליצור ייצוא מושלם.

## 4 פתח את תיקיית הפרויקט הנכונה

1. פתח את VS Code או את עורך הקוד שבו ביצעת M1–M3.
2. בחר File ואז Open Folder.
3. פתח את התיקייה שבה נמצאות app, requirements.txt וקובץ compose.yaml או docker-compose.yml. זו תיקיית השורש של פרויקט הפיתוח שלך, ולא בהכרח תיקיית הצ'אט של Codex או תיקיית Downloads.
4. בחר Terminal ואז New Terminal. ב־Windows ההוראות בהמשך מניחות PowerShell.
5. הרץ:

```powershell
Get-Location
Get-ChildItem -Name
```

Get-Location מציג את התיקייה הנוכחית. ב־Get-ChildItem אתה צריך לראות את app ואת קובץ התלויות של הפרויקט. אם אינך רואה אותם, פתח מחדש Terminal מתוך תיקיית הפרויקט.

אל תריץ פקודות כשמופיע הסימן >>>; זה מסך Python אינטראקטיבי. הקלד exit() ולחץ Enter כדי לחזור ל־Terminal.

## 5 העתק רק את קובצי M4

באמצעות סייר הקבצים, העתק מתוך החבילה אל תיקיית הפרויקט:

| קובץ בחבילה | המקום בפרויקט |
|---|---|
| app/m4_pdf.py | בתוך app |
| scripts/inspect_m4_pdf.py | בתוך scripts |
| tests/test_m4_pdf.py | בתוך tests |
| fixtures/m4 וכל התוכן שלה | בתוך fixtures/m4 |

אם scripts, tests או fixtures אינם קיימים, צור אותם. אין להחליף תיקיית app שלמה: מוסיפים לתוכה את הקובץ החדש בלבד. קבצים קיימים כגון main.py ו־schemas.py נשארים כפי שהם.

אם אחד משלושת קובצי M4 כבר קיים מהתנסות קודמת, שמור עותק שלו לפני החלפה. לדוגמה, שנה את שם העותק ל־m4_pdf_before_update.py.

הקוד המלא מופיע גם בנספחים בסוף המדריך. הדרך המהירה היא להעתיק את הקבצים המוכנים. אם אתה מעתיק קוד מהנספח, העתק רק את התוכן שבין סימוני הקוד, ושמור בשם המדויק עם סיומת .py.

## 6 בחר את Python של הפרויקט

סביבה וירטואלית היא תיקייה שמחזיקה את Python ואת הספריות של הפרויקט. אנחנו מפנים אל Python שלה ישירות, כדי לא להסתבך בהפעלת סביבה או בהגדרות PowerShell.

העתק את הבלוק הבא ל־Terminal. הוא בוחר .venv או venv אם הם קיימים, ויוצר .venv רק אם אין אף אחד מהם:

```powershell
if (Test-Path '.\.venv\Scripts\python.exe') {
    $M4Python = (Resolve-Path '.\.venv\Scripts\python.exe').Path
} elseif (Test-Path '.\venv\Scripts\python.exe') {
    $M4Python = (Resolve-Path '.\venv\Scripts\python.exe').Path
} else {
    py -3 -m venv .venv
    $M4Python = (Resolve-Path '.\.venv\Scripts\python.exe').Path
}
& $M4Python --version
```

התוצאה צריכה להיות Python 3.11 או חדש יותר, בהתאם לתכנון המקורי. המשתנה M4Python הוא קיצור לנתיב Python שבחרת. הסימן & אומר ל־PowerShell להריץ את הקובץ שבנתיב הזה. המשתנה תקף בחלון ה־Terminal הנוכחי; אם סגרת אותו, הרץ שוב את בלוק הבחירה.

אם py אינו מזוהה אבל python כן עובד, צור את הסביבה כך ואז הרץ שוב את בלוק הבחירה:

```powershell
python -m venv .venv
```

אם הפרויקט שלך רץ רק בתוך Docker, אפשר להשתמש במקום זאת במסלול Docker שבסעיף 14. בחר מסלול אחד והישאר בו בזמן הבדיקות.

## 7 בדוק את הספרייה והשלם התקנה רק אם צריך

הרץ:

```powershell
& $M4Python -c "import pymupdf; print('PyMuPDF import: OK'); print(pymupdf.VersionBind)"
```

אם מתקבל PyMuPDF import: OK ואחריו מספר גרסה, המשך לסעיף 8. אם מתקבל No module named pymupdf, התקן:

```powershell
& $M4Python -m pip install --only-binary=:all: PyMuPDF
```

הרץ שוב את בדיקת ה־import. אם אצלך מותקנת גרסה ישנה שאינה תומכת ב־import pymupdf, עדכן רק את הספרייה הזאת:

```powershell
& $M4Python -m pip install --upgrade --only-binary=:all: PyMuPDF
```

שימוש ב־only-binary מבקש חבילה מוכנה ומונע כניסה לבניית C/C++ שאינה מתאימה לתקציב הדמו. לא מתקינים חבילה בשם fitz; זה שם של חבילה אחרת שאפשר להתבלבל איתה.

אם PyMuPDF כבר מופיע ב־requirements.txt, אין צורך בשורה נוספת. אם הוא חסר, הוסף שורה אחת:

```text
PyMuPDF
```

אם קובץ התלויות שלך מקבע גרסאות, השתמש בגרסה שהרצת בהצלחה, למשל PyMuPDF==ואחריו מספר הגרסה שהודפס. לא מעתיקים את הטקסט העברי הזה לקובץ; צריך מספר אמיתי. אין צורך להתקין מחדש את כל ספריות הפרויקט או לשנות את ה־SDK של המודל.

תיעוד ההתקנה הרשמי: https://pymupdf.readthedocs.io/en/latest/installation.html

## 8 הרץ את הבדיקות האוטומטיות

מתיקיית השורש של הפרויקט הרץ:

```powershell
& $M4Python -m unittest discover -s tests -p test_m4_pdf.py -v
```

unittest מגיע עם Python. אין צורך להוסיף pytest לצורך הבדיקות האלה. יש בחבילה 16 בדיקות: ציטוט אמיתי, ציטוט מומצא, עמוד שגוי, ציטוט ריק, שינוי פיסוק, מקור מייל, גבולות קלט, חילוץ טקסט, מספור עמודים, PDF ללא טקסט, הצפנה ומגבלת העמודים.

בתחתית הפלט צריך להופיע:

```text
Ran 16 tests in ...
OK
```

אין לדלג על השורה skipped. אם מתקבל OK (skipped=8), ספריית PyMuPDF לא זמינה לאותו Python, וחילוץ PDF לא נבדק. חזור לסעיף 7 והריץ את שתי הפקודות עם אותו M4Python.

אם מופיע FAILED או ERROR, אל תסמן שהשלב הושלם. חפש את שם הבדיקה שנכשלה ואת השורה האחרונה של השגיאה. בסעיף 15 יש פתרונות לתקלות נפוצות.

## 9 הרץ את הדוגמה החיובית

הרץ:

```powershell
& $M4Python -m scripts.inspect_m4_pdf fixtures/m4/agilerpm_text_reference.pdf --agilerpm
```

צריך לקבל פלט מהצורה:

```text
PARSED: 21 pages
Warnings: 0
SHA-256: ...
21_pages: PASS
round_target_on_page_9: PASS
fund_check_on_page_9: PASS
invented_amount_rejected: PASS
wrong_page_rejected: PASS
Text: work\m4\pages.txt
Report: work\m4\inspection.json
```

זה פלט צפוי לדוגמת התמלול המצורפת, ולא תוצאה שאני טוען שהורצה אצלך. מספר האזהרות תלוי בקובץ ובחילוץ בפועל. אם יש אזהרות, בדוק אילו עמודים גרמו להן; הן אינן בהכרח שגיאה.

שתי בדיקות הסכומים מכוונות לעמוד 9: יעד הסבב הוא 12 מיליון דולר, והסכום המבוקש מהקרן הוא 3 מיליון דולר, לפי טקסט דק הדמו. ציטוט של 13 מיליון דולר צריך להידחות. גם ציטוט אמיתי עם עמוד שגוי צריך להידחות.

האפשרות agilerpm בודקת את דוגמת הדמו המסוימת הזאת. אם אתה בודק PDF אחר, השמט אותה:

```powershell
& $M4Python -m scripts.inspect_m4_pdf 'fixtures/my_other_deck.pdf'
```

## 10 פתח את תוצאת החילוץ והשווה למקור

בסייר הקבצים של VS Code פתח work ואז m4 ואז pages.txt. אפשר גם לפתוח כך:

```powershell
notepad .\work\m4\pages.txt
```

חפש באמצעות Ctrl+F את [PAGE 9]. צריך לראות את הנתונים שהגיעו מהעמוד התשיעי. פתח במקביל את PDF התמלול בעמוד 9 והשווה את יעד הסבב ואת הבקשה מהקרן.

בדוק גם את עמוד 1: שם החברה והמוצר צריכים להופיע באופן קריא. ודא שלא נמחקו או הוחלפו תווים בתוך הסכומים. שני עמודים ושתי טענות מרכזיות מספיקים לבדיקת הקבלה הידנית כאן.

פתח גם work/m4/inspection.json. תראה status של parsed, מספר עמודים, SHA-256, רשימת pages ורשימת warnings. JSON הוא פורמט נתונים מסודר; אין צורך לערוך את הקובץ ידנית.

pages.txt ו־inspection.json הם פלטי בדיקה זמניים. הם אינם brief.txt העסקי או record.json הסופי, שיתווספו בהמשך.

חילוץ טקסט אינו מבטיח שגרפים, צילומים וטבלאות מורכבות נקראו נכון. גם כאשר אין אזהרות, הסיכום העתידי חייב להציג את גבולות הקריאה הזאת. הסף של 40 תווים לעמוד הוא כלל דמו לזיהוי טקסט דל, ולא מדד לשלמות הדק.

## 11 הרץ את הדוגמה השלילית

לפני הבדיקה אפשר לשמור עותק של פלטי ההצלחה לשם השוואה. הסקריפט כותב מחדש את פלטי work/m4 בכל בדיקה שבוצע בה parsing.

הרץ:

```powershell
& $M4Python -m scripts.inspect_m4_pdf fixtures/m4/agilerpm_image_only.pdf
```

הפלט הצפוי הוא:

```text
REVIEW MANUAL: pdf_no_usable_text
No usable text layer found. This demo does not use OCR.
Report: work\m4\inspection.json
```

הפקודה מסתיימת בקוד יציאה 2 משום שאין תוצאת חילוץ. זהו מקרה שלילי צפוי, והוא מראה שהמערכת לא ממשיכה כאילו קראה את הדק. במצב הזה inspection.json מכיל review_manual, סיבת העצירה ושם קובץ הבדיקה. pages.txt נכתב מחדש עם הסיבה במקום להשאיר טקסט מההרצה הקודמת.

זה עדיין מצב בסקריפט המקומי. שמירה של אותו מצב ברשומת הזדמנות ב־API וחיבור מסלול n8n ייעשו בחיבור השלב הבא.

לסיום, הרץ שוב את הדוגמה החיובית, כדי שהפלט האחרון בתיקיית העבודה יהיה טקסט שניתן להעביר למנתח:

```powershell
& $M4Python -m scripts.inspect_m4_pdf fixtures/m4/agilerpm_text_reference.pdf --agilerpm
```

## 12 הבן מה כל פונקציה עושה

| פונקציה | קלט | פלט ותפקיד |
|---|---|---|
| parse_pdf | bytes של PDF | ParsedPdf עם עמודים, אזהרות ומזהה תוכן |
| format_pages_for_llm | ParsedPdf | טקסט עם [PAGE 1], [PAGE 2] וכו' |
| verify_deck_quote | ParsedPdf, מספר עמוד וציטוט | True כשהציטוט נמצא באותו עמוד |
| verify_email_quote | גוף מייל וציטוט | True כשהציטוט נמצא בגוף המייל |

הפלטים הם dataclasses, מבני נתונים פשוטים שמגיעים עם Python. הם נשארים בתוך מודול M4 כדי שלא יהיה צורך לשנות את סכמות Pydantic שבנית. to_dict הופך את תוצאת החילוץ למילון שניתן לשמור כ־JSON.

verify_deck_quote ו־verify_email_quote אינם פונים למודל ואינם עולים כסף. הם בודקים התאמה לטקסט בלבד. המנתח שנוסיף יקבל את הטקסט של format_pages_for_llm ויצטרך להחזיר ציטוטים מתוכו. הקוד יקבע אחר כך את validation_status של הראיות הקיימות.

אם ציטוט אינו נמצא, לא מתקנים את המספרים כדי לגרום לו להתאים ולא מחפשים בעמוד אחר בלי לציין זאת. משאירים את הממצא כלא נתמך, בהתאם לתוכנית הדמו.

## 13 נקודת החיבור לשלב הבא

אחרי שהבדיקות המקומיות עברו, הקוד שהשרת יצטרך להפעיל לאחר קבלת ה־PDF הוא:

```python
from app.m4_pdf import parse_pdf, format_pages_for_llm

parsed = parse_pdf(pdf_bytes)
deck_text = format_pages_for_llm(parsed)
```

זהו הסבר על נקודת החיבור, ולא הוראה להדביק שורות במקום לא ידוע בתוך main.py. pdf_bytes הם ה־bytes שכבר מפוענחים מבקשת analyze. בשלב הבא נחבר את deck_text ואת גוף המייל למנתח היחיד.

כשל PdfParsingError נותן code ו־message שאפשר לשמור ולהציג. כשל פיתוח בלתי צפוי נשאר כשל שצריך לתקן; אין להפוך אותו למייל רגיל או להצלחה מדומה.

ה־Workflow שלך כרגע מסתיים ב־POST Analyze. אין להוסיף כעת מסווג חדש, מחקר אינטרנטי, דשבורד או אישור במייל. גם חיבור יציאת false של If, מסלול skip ושמירת ההקשר של המייל נשארים למשימת החיבור בתוכנית המצומצמת.

M4 הושלם מקומית כאשר החילוץ והאימות עובדים. הוא אינו מוכיח עדיין שה־API מפעיל אותם על מייל חי, שהתקבל תדריך או שהדוח נשמר. אלה תנאי הסיום של השלבים הבאים.

## 14 אם אתה בוחר להריץ בתוך Docker

ה־Workflow פונה לשירות api. אם גם בקובץ Compose שלך זה שם השירות, אפשר להשתמש בפקודות הבאות מתוך תיקיית הפרויקט, אחרי העתקת הקבצים:

```powershell
docker compose config --services
```

ודא שמופיע api. לאחר שהוספת PyMuPDF לקובץ התלויות, הרץ:

```powershell
docker compose up -d --build api
docker compose exec api python -c "import pymupdf; print(pymupdf.VersionBind)"
docker compose exec api python -m unittest discover -s tests -p test_m4_pdf.py -v
docker compose exec api python -m scripts.inspect_m4_pdf fixtures/m4/agilerpm_text_reference.pdf --agilerpm
docker compose exec api python -m scripts.inspect_m4_pdf fixtures/m4/agilerpm_image_only.pdf
```

הפקודות מניחות שה־Dockerfile שלך מתקין את קובץ התלויות, מעתיק את app, scripts, tests ו־fixtures ומגדיר תיקיית עבודה בשורש הפרויקט בתוך הקונטיינר. אלה הנחות שצריך לבדוק בקובץ שלך; קוד ה־Dockerfile אינו זמין כאן. אם מופיע No module named scripts או שה־fixtures לא נמצאים, אל תשנה תשתית רק לצורך M4: השתמש במסלול המקומי והשלם את התאמת Docker בשלב החיבור.

פלט work/m4 שנכתב בתוך Docker לא בהכרח נגיש מהמחשב. אפשר לקרוא אותו כך:

```powershell
docker compose exec api python -c "from pathlib import Path; print(Path('work/m4/pages.txt').read_text(encoding='utf-8'))"
```

הדוגמה השלילית מחזירה קוד יציאה 2 בכוונה. לכן הרץ את הפקודות אחת בכל פעם, ולא בשרשרת שתעצור בלי הסבר אחרי בדיקה שלילית.

## 15 פתרון תקלות נפוצות

| מה אתה רואה | מה זה אומר | מה לעשות |
|---|---|---|
| No module named pymupdf | הספרייה אינה מותקנת ל־Python שמריץ את הפקודה | חזור לסעיף 7 והשתמש באותו M4Python |
| No module named app.m4_pdf | תיקייה שגויה או קובץ במקום שגוי | בדוק שאתה בשורש ושיש app/m4_pdf.py |
| No module named scripts.inspect_m4_pdf | קובץ הסקריפט חסר או שהפקודה רצה מתיקייה אחרת | בדוק את שם הקובץ ואת Get-Location |
| File not found | נתיב הקלט שגוי | ודא שה־PDF נמצא ב־fixtures/m4 ושלא שונה שמו |
| pdf_no_usable_text בדוגמה החיובית | נבחר PDF בלי טקסט או שטקסט החילוץ דל | בדוק שזו דוגמת התמלול ולא ה־PDF המקורי |
| pdf_invalid | תוכן הקובץ אינו PDF שניתן לפתוח | פתח את הקובץ ידנית ובחר קובץ תקין |
| pdf_encrypted | ה־PDF מוצפן | השתמש בדוגמת התמלול או בייצוא ללא הצפנה |
| FAIL בבדיקת עמוד 9 | הסכום לא מופיע בטקסט שחולץ בעמוד הצפוי | פתח pages.txt בעמוד 9 והשווה למקור; אל תשנה סכום כדי להעביר בדיקה |
| OK (skipped=8) | בדיקות הקריאה לא בוצעו | התקן PyMuPDF והריץ שוב |
| אין התאמה גלויה של טבלה לטקסט | סדר חילוץ עשוי להשתנות לעומת העיצוב | השתמש בציטוט שמופיע בטקסט שנשלח למודל ובדוק ידנית משמעות |

אם התקנת PyMuPDF מציעה לבנות קוד C/C++, עצור את הניסיון והשתמש ב־only-binary עם Python נתמך. התקלה אינה סיבה להוסיף OCR או להחליף את כל הסביבה.

אם פקודה נכשלת בגלל נתיב או ספרייה חסרה לפני פתיחת PDF, ייתכן שקובץ בדיקה ישן עדיין קיים. תוצאת פקודה שנכשלה אינה הצלחה, גם אם pages.txt מהרצה קודמת נפתח.

## 16 תעד את ההשלמה

פתח PROGRESS.md והוסף רק לאחר שהבדיקות שלך באמת עברו:

```text
M4 lean PDF parsing
Status: completed locally

Added app/m4_pdf.py, scripts/inspect_m4_pdf.py and tests/test_m4_pdf.py.
Positive fixture: fixtures/m4/agilerpm_text_reference.pdf.
Fixture is a text transcript of the source slides, not a layout-preserving export.
Negative fixture: fixtures/m4/agilerpm_image_only.pdf.

Checked: 16 tests pass with no skipped tests.
Positive fixture: 21 pages; two amounts on page 9 matched.
Invented amount and incorrect page were rejected.
Negative fixture: pdf_no_usable_text.
Manually compared pages 1 and 9 with the PDF.

Python version: [fill with actual value]
PyMuPDF version: [fill with actual value]
PDF SHA-256: [copy from the successful inspection]
Actual time spent: [fill with actual value]
Known blockers: [fill with actual value]

Next: one LLM analyst receiving the email and the parsed deck.
API/workflow integration and final brief storage are pending.
```

מלא את הסוגריים בתוצאות שלך. אם בדיקה נכשלה, רשום in progress ואת הכשל במקום completed. אין צורך לשמור מפתחות או תוכן .env במדריך או בתוצאות.

## 17 תנאי הסיום המדויקים

- 16 בדיקות הסתיימו ללא כשל וללא skipped.
- דוגמת AgileRPM החיובית נקראה ונוצר טקסט עם 21 מספרי עמודים נכונים.
- שני הסכומים בעמוד 9 נמצאו; סכום מומצא ועמוד שגוי נדחו.
- ה־PDF השלילי נעצר עם pdf_no_usable_text.
- בדקת ידנית את עמודים 1 ו־9 ואת משמעות שני הסכומים.
- גרסת הספרייה והמצב האמיתי תועדו ב־PROGRESS.md.

לאחר מכן המשימה הבאה היא מנתח LLM יחיד. אין צורך להמתין למחקר רגולציה, לדשבורד או לארבעה סוכנים.

## 18 מה נבדק בהכנת החבילה

בדיקת התחביר של שלושת קובצי Python עברה. שמונה בדיקות של ציטוטים, עיצוב קלט וגבולות קלט עברו בסביבת ההכנה. שמונה בדיקות שדורשות PyMuPDF לא הורצו כאן משום שהספרייה אינה מותקנת בסביבה זו. לכן החבילה אינה מוצגת כמימוש שנבדק במלואו אצלך; סעיפים 7–11 הם חלק מתנאי הקבלה שעליך לבצע.

המידע על שני קובצי הדמו מגיע מבדיקת המקורות הקודמת בפרויקט. ה־PDF החיובי נוצר מתוכן המצגת ונבדק שם באמצעות pypdf; זה אינו תחליף להרצת PyMuPDF בפרויקט שלך.

## 19 מקורות טכניים

- [התקנה ו־import של PyMuPDF](https://pymupdf.readthedocs.io/en/latest/installation.html)
- [חילוץ טקסט וסדר הקריאה](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)
- [פתיחת מסמך, הצפנה ומטא־מידע](https://pymupdf.readthedocs.io/en/latest/document.html)

הקוד משתמש ב־get_text("text", sort=True), שמנסה לסדר טקסט לפי מיקום. הוא אינו משמר את עיצוב המצגת. בדיקת ההצפנה כוללת גם מידע metadata, משום ש־needs_pass לבדו אינו מספיק לזיהוי PDF מוצפן שנפתח ללא בקשת סיסמה.

## נספחים הקוד המלא להעתקה

הקבצים האלה כבר נמצאים בחבילה. אין צורך להקליד אותם מחדש אם העתקת את הקבצים.

### app/m4_pdf.py

```python
"""Small PDF reader and literal quote checks for the lean M4 demo."""

from dataclasses import asdict, dataclass, field
import hashlib
import re


MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 25
MIN_USEFUL_PAGE_CHARS = 40


@dataclass
class PdfPage:
    page_number: int
    text: str


@dataclass
class PdfWarning:
    code: str
    page: int | None
    message: str


@dataclass
class ParsedPdf:
    sha256: str
    page_count: int
    pages: list[PdfPage]
    warnings: list[PdfWarning] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class PdfParsingError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_pdf(pdf_bytes: bytes) -> ParsedPdf:
    if not isinstance(pdf_bytes, (bytes, bytearray)):
        raise PdfParsingError("pdf_invalid_input", "Expected PDF bytes.")
    if not pdf_bytes:
        raise PdfParsingError("pdf_empty", "The PDF is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise PdfParsingError("pdf_too_large", "The PDF exceeds 10 MiB.")

    # Only PDF reading needs the external package.
    import pymupdf

    try:
        document = pymupdf.open(stream=bytes(pdf_bytes), filetype="pdf")
    except pymupdf.FileDataError as exc:
        raise PdfParsingError("pdf_invalid", "Cannot open this PDF.") from exc

    with document:
        if document.needs_pass:
            raise PdfParsingError("pdf_encrypted", "Encrypted PDFs are unsupported.")
        encryption = (document.metadata or {}).get("encryption")
        if encryption and str(encryption).lower() != "none":
            raise PdfParsingError("pdf_encrypted", "Encrypted PDFs are unsupported.")
        if document.page_count == 0:
            raise PdfParsingError("pdf_no_pages", "The PDF has no pages.")
        if document.page_count > MAX_PDF_PAGES:
            raise PdfParsingError("pdf_too_many_pages", "The PDF exceeds 25 pages.")

        pages = []
        warnings = []
        useful_pages = 0

        for index in range(document.page_count):
            page_number = index + 1
            try:
                text = document[index].get_text("text", sort=True).strip()
            except RuntimeError as exc:
                raise PdfParsingError(
                    "pdf_extraction_failed", f"Cannot read PDF page {page_number}."
                ) from exc

            pages.append(PdfPage(page_number=page_number, text=text))
            normalized = normalize_whitespace(text)
            if not normalized:
                warnings.append(PdfWarning("empty_page", page_number, "No text extracted."))
            elif len(normalized) < MIN_USEFUL_PAGE_CHARS:
                warnings.append(PdfWarning("short_page", page_number, "Very little text extracted."))
            else:
                useful_pages += 1

        if useful_pages == 0:
            raise PdfParsingError(
                "pdf_no_usable_text",
                "No usable text layer found. This demo does not use OCR.",
            )
        if useful_pages < document.page_count:
            warnings.append(PdfWarning(
                "partial_text_coverage", None,
                f"Useful text extracted on {useful_pages} of {document.page_count} pages.",
            ))

        return ParsedPdf(
            sha256=hashlib.sha256(pdf_bytes).hexdigest(),
            page_count=document.page_count,
            pages=pages,
            warnings=warnings,
        )


def format_pages_for_llm(parsed: ParsedPdf) -> str:
    return "\n\n".join(
        f"[PAGE {page.page_number}]\n{page.text}" for page in parsed.pages
    )


def verify_deck_quote(parsed: ParsedPdf, page_number: int | None, quote: str | None) -> bool:
    if type(page_number) is not int or not isinstance(quote, str):
        return False
    normalized_quote = normalize_whitespace(quote)
    if not normalized_quote:
        return False
    for page in parsed.pages:
        if page.page_number == page_number:
            return normalized_quote in normalize_whitespace(page.text)
    return False


def verify_email_quote(email_body: str, quote: str | None) -> bool:
    if not isinstance(quote, str):
        return False
    normalized_quote = normalize_whitespace(quote)
    return bool(normalized_quote) and normalized_quote in normalize_whitespace(email_body)
```

### scripts/inspect_m4_pdf.py

```python
"""Run from the project root: python -m scripts.inspect_m4_pdf PDF_PATH."""

import argparse
import json
from pathlib import Path

from app.m4_pdf import (
    PdfParsingError, format_pages_for_llm, parse_pdf, verify_deck_quote,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect one PDF for the lean M4 demo.")
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--agilerpm", action="store_true", help="Check the supplied AgileRPM fixture.")
    args = parser.parse_args()

    output_dir = Path("work/m4")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "inspection.json"
    text_path = output_dir / "pages.txt"

    try:
        parsed = parse_pdf(args.pdf_path.read_bytes())
    except FileNotFoundError:
        print(f"File not found: {args.pdf_path}")
        return 2
    except ModuleNotFoundError as exc:
        if exc.name != "pymupdf":
            raise
        print("Missing dependency: install PyMuPDF in the Python environment used for this command.")
        return 2
    except PdfParsingError as exc:
        report = {
            "status": "review_manual", "input_file": str(args.pdf_path),
            "error_code": exc.code, "message": exc.message,
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        text_path.write_text(f"No extracted text: {exc.code}\n{exc.message}\n", encoding="utf-8")
        print(f"REVIEW MANUAL: {exc.code}")
        print(exc.message)
        print(f"Report: {report_path}")
        return 2

    report = {"status": "parsed", "input_file": str(args.pdf_path), **parsed.to_dict()}
    checks = {}
    if args.agilerpm:
        checks = {
            "21_pages": parsed.page_count == 21,
            "round_target_on_page_9": verify_deck_quote(parsed, 9, "$12,000,000 USD"),
            "fund_check_on_page_9": verify_deck_quote(parsed, 9, "$3,000,000 USD"),
            "invented_amount_rejected": not verify_deck_quote(parsed, 9, "$13,000,000 USD"),
            "wrong_page_rejected": not verify_deck_quote(parsed, 8, "$12,000,000 USD"),
        }
        report["fixture_checks"] = checks

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    text_path.write_text(format_pages_for_llm(parsed), encoding="utf-8")
    print(f"PARSED: {parsed.page_count} pages")
    print(f"Warnings: {len(parsed.warnings)}")
    print(f"SHA-256: {parsed.sha256}")
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"Text: {text_path}")
    print(f"Report: {report_path}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

### tests/test_m4_pdf.py

```python
import hashlib
import importlib.util
import unittest

from app.m4_pdf import (
    MAX_PDF_BYTES, ParsedPdf, PdfPage, PdfParsingError,
    format_pages_for_llm, parse_pdf, verify_deck_quote, verify_email_quote,
)


class QuoteChecks(unittest.TestCase):
    def setUp(self):
        self.parsed = ParsedPdf("example", 2, [
            PdfPage(1, "Total Round Target\n$12,000,000 USD"),
            PdfPage(2, "Requested Fund Check $3,000,000 USD"),
        ])

    def test_real_quote_with_different_whitespace(self):
        self.assertTrue(verify_deck_quote(self.parsed, 1, "Total Round Target   $12,000,000 USD"))

    def test_invented_amount_is_rejected(self):
        self.assertFalse(verify_deck_quote(self.parsed, 1, "$13,000,000 USD"))

    def test_real_quote_on_wrong_page_is_rejected(self):
        self.assertFalse(verify_deck_quote(self.parsed, 2, "$12,000,000 USD"))

    def test_empty_quote_and_invalid_page_are_rejected(self):
        for page, quote in [(1, "  "), (1, None), (None, "Target"), (0, "Target"),
                            (99, "Target"), (True, "Target")]:
            with self.subTest(page=page, quote=quote):
                self.assertFalse(verify_deck_quote(self.parsed, page, quote))

    def test_case_and_punctuation_are_preserved(self):
        self.assertFalse(verify_deck_quote(self.parsed, 1, "total round target"))
        self.assertFalse(verify_deck_quote(self.parsed, 1, "$12.000.000 USD"))

    def test_email_quote_is_checked_against_email(self):
        self.assertTrue(verify_email_quote("We seek\n$3M.", "We seek $3M."))
        self.assertFalse(verify_email_quote("We seek $3M.", "We seek $4M."))
        self.assertFalse(verify_email_quote("We seek $3M.", ""))

    def test_format_keeps_original_page_numbers(self):
        text = format_pages_for_llm(self.parsed)
        self.assertIn("[PAGE 1]", text)
        self.assertIn("[PAGE 2]", text)


class InputChecks(unittest.TestCase):
    def test_empty_wrong_type_and_large_input(self):
        for data, expected_code in [(b"", "pdf_empty"), ("not bytes", "pdf_invalid_input"),
                                    (b"x" * (MAX_PDF_BYTES + 1), "pdf_too_large")]:
            with self.subTest(code=expected_code):
                with self.assertRaises(PdfParsingError) as error:
                    parse_pdf(data)
                self.assertEqual(error.exception.code, expected_code)


HAS_PYMUPDF = importlib.util.find_spec("pymupdf") is not None


@unittest.skipUnless(HAS_PYMUPDF, "PyMuPDF is missing; PDF reading has NOT been tested.")
class PdfReadingChecks(unittest.TestCase):
    def make_pdf(self, texts, *, user_password=None):
        import pymupdf
        with pymupdf.open() as document:
            for text in texts:
                page = document.new_page()
                if text:
                    page.insert_text((50, 70), text)
            options = {}
            if user_password is not None:
                options = {"encryption": pymupdf.PDF_ENCRYPT_AES_256,
                           "owner_pw": "owner-test-only", "user_pw": user_password}
            return document.tobytes(**options)

    def test_text_pdf_and_hash(self):
        data = self.make_pdf(["A company is raising a twelve million dollar Series A round."])
        parsed = parse_pdf(data)
        self.assertEqual(parsed.page_count, 1)
        self.assertIn("twelve million", parsed.pages[0].text)
        self.assertEqual(parsed.sha256, hashlib.sha256(data).hexdigest())

    def test_blank_middle_page_keeps_numbering(self):
        data = self.make_pdf(["First page contains enough useful company information to extract.", "",
                              "Third page contains enough useful financing information to extract."])
        parsed = parse_pdf(data)
        self.assertEqual([page.page_number for page in parsed.pages], [1, 2, 3])
        self.assertEqual(parsed.pages[1].text, "")
        self.assertTrue(any(w.code == "partial_text_coverage" for w in parsed.warnings))

    def test_no_text_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf([""]))
        self.assertEqual(error.exception.code, "pdf_no_usable_text")

    def test_title_only_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf(["Title"]))
        self.assertEqual(error.exception.code, "pdf_no_usable_text")

    def test_invalid_pdf_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(b"This is not a PDF.")
        self.assertEqual(error.exception.code, "pdf_invalid")

    def test_25_pages_accepted_and_26_rejected(self):
        text = "This page contains useful text about a company and its financing round."
        self.assertEqual(parse_pdf(self.make_pdf([text] * 25)).page_count, 25)
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf([text] * 26))
        self.assertEqual(error.exception.code, "pdf_too_many_pages")

    def test_encrypted_pdf_with_user_password_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf(["Enough useful company text for a normal parsing result."],
                                    user_password="user-test-only"))
        self.assertEqual(error.exception.code, "pdf_encrypted")

    def test_encrypted_pdf_with_empty_user_password_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf(["Enough useful company text for a normal parsing result."],
                                    user_password=""))
        self.assertEqual(error.exception.code, "pdf_encrypted")


if __name__ == "__main__":
    unittest.main()
```
