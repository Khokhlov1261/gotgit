import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
import schedule
import time


def job():
    print("=== Запуск отчета ===")

    print("🧐 Авторизация Google")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("js.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1IpV7hoUuOmbgEfr1YXNqRF2mXoV7s3eAEiltwB-Wn7c/edit?gid=1161211803#gid=1161211803")

    url = "https://docs.google.com/forms/d/e/1FAIpQLSe1vaEAthSHfjmQB51i-hAVPc6dBoCMAyi8sPAejrIhLz2tuw/formResponse"
    response = requests.get(url)
    if response.status_code != 200:
        print("Не удалось загрузить форму")
        exit()

    soup = BeautifulSoup(response.text, 'html.parser')
    fbzx_input = soup.find("input", {"name": "fbzx"})
    if not fbzx_input:
        print("Не удалось найти fbzx")
        exit()
    fbzx_value = fbzx_input["value"]




    print("😤 поиск нужного листа")
    def search_for_me(sheet, role = "Зырянов Александр",column_index = 1):
        today_for_search = datetime.today().strftime("%d.%m.%Y")
        table_1 = sheet.get_all_values()
        matching = [col for col in table_1 if col[0] == today_for_search and col[column_index] == role]
        return matching

    worksheet = spreadsheet.worksheet('2')
    searching_today = search_for_me(worksheet, role= 'Зырянов Александр', column_index=1)

    if not searching_today:
        print("🥸 Ищу другой лист!")
        worksheet = spreadsheet.worksheet('3')
        searching_today = search_for_me(worksheet)

    if not searching_today:
        print("🥸 Ищу другой лист!")
        worksheet = spreadsheet.worksheet('4')
        print("🥸 Ищу другой лист!")
        searching_today = search_for_me(worksheet)

    if not searching_today:
        print("🤪 ни одного листа не найдено!")
        exit()

    print("🤑 Лист найден, собираю данные!")
    today = datetime.today().strftime("%d.%m.%Y")
    searching_today = [row for row in searching_today if row[0] == today]

    day, name_month, year = today.split(".")

    start_day = end_day = store = manager = cash = terminal = qr_code = \
        in_store_wallet = get_from_wallet = type_of_operation = who  = ""
    terminal_in_1C = all_the_day = 0

    for row in searching_today:
        if str(row[1]) == "Зырянов Александр":
            match = row[3]
            check, start_day, end_day, store = str(match).split(",")
            manager = row[1]
            cash = str(row[4]).replace('\xa0', '').replace(' ', '').strip()
            terminal = str(row[7]).replace('\xa0', '').replace(' ', '').strip()
            qr_code = str(row[9]).replace('\xa0', '').replace(' ', '').strip()
            in_store_wallet = str(row[6]).replace('\xa0', '').replace(' ', '').strip()
            all_the_day = int(terminal) + int(qr_code) + int(cash)
            terminal_in_1C = int(terminal) + int(qr_code)

    inkass = search_for_me(worksheet, role = "Инкасс/Внесение", column_index= 2)
    for row in inkass:
        get_from_wallet = str(row[5]).replace('\xa0', '').replace(' ', '').strip()
        type_of_operation = str(row[3])
        who = str(row[1])

    store_report = "Неизвестно"

    if store == "крб3":
        store_report = "Соликамск Кр.Бульвар 3"
    elif store == "сев55":
        store_report = "Соликамск Северная 55"
    elif store == "мира83":
        store_report = "Березники Мира 110"
    else:
        print("😬 Не удалась распознать магазин!")


    data = {
            "entry.1834620662_day": day,
            "entry.1834620662_month": name_month,
            "entry.1834620662_year": year,
            "entry.1390867807_hour": start_day,
            "entry.1390867807_minute": "00",
            "entry.948603546_hour": end_day,
            "entry.948603546_minute": "00",
            "entry.62903313": store_report,
            "entry.1314851336": manager,
            "entry.417024138": cash,
            "entry.1622716671": cash,
            "entry.898291640": terminal_in_1C,
            "entry.1691390490": terminal,
            "entry.53970266": in_store_wallet,
            "entry.1408529044": qr_code,
            "entry.1488218029": get_from_wallet,
            "entry.527465824": type_of_operation,
            "entry.536482182": who,
            "fbzx": fbzx_value,
            "pageHistory": "0,1,2,1,3,1,4,1,5,1,6,1,7,1,8,1,9,1,10,1,11,1,12,1,15,1,18,1,19",
            "fvv": "1",
        }


    print("Дата отчета: " + today)
    print("Начало смены: " + start_day + ":00 Закрытие смены: " + end_day + ":00")
    print("Магазин: " + store_report + " Консультант: " + manager)
    print("Наличные в 1С: " + cash + " Эквайринг 1С: " + str(terminal_in_1C))
    print("Сверка итогов: " + str(terminal) + " QR-код: " + str(qr_code))
    print("|||||ВСЕГО ЗА ДЕНЬ|||| " + str(all_the_day))
    print("Касса на конец смены: " + in_store_wallet)
    print("Инкассация сумма: " + get_from_wallet + " " + type_of_operation + " " + who)



    if check == "отправить":
        print("👻 Отправка отчета!")
        send_response = requests.post(url, data=data)
        if send_response.status_code == 200:
            print("🙃 Форма успешно отправлена!")
        else:
            print(f"Ошибка при отправке формы: {send_response.status_code}")

    else:
        print("😫 Нет команды отправить")

schedule.every().day.at("17:28").do(job)
print("Программа запущена. Ожидаем 22:28 (17:28pm по UTC) каждый день...")
while True:
    schedule.run_pending()
    time.sleep(30)





