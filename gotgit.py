import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
import schedule
import time


class ReportSender:
    def __init__(self):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file"
        ]
        self.creds_file = "js.json"
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1IpV7hoUuOmbgEfr1YXNqRF2mXoV7s3eAEiltwB-Wn7c/edit"
        self.form_url = "https://docs.google.com/forms/d/e/1FAIpQLSe1vaEAthSHfjmQB51i-hAVPc6dBoCMAyi8sPAejrIhLz2tuw/formResponse"
        self.spreadsheet = None
        self.fbzx_value = None
        self.worksheet = None
        self.today = datetime.today().strftime("%d.%m.%Y")

    def authorize_google(self):
        print("🧐 Авторизация Google")
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, self.scope)
        client = gspread.authorize(creds)
        self.spreadsheet = client.open_by_url(self.sheet_url)

    def extract_form_token(self):
        print("📥 Получение токена формы")
        response = requests.get(self.form_url)
        if response.status_code != 200:
            raise Exception("Не удалось загрузить форму")
        soup = BeautifulSoup(response.text, 'html.parser')
        fbzx_input = soup.find("input", {"name": "fbzx"})
        if not fbzx_input:
            raise Exception("Не удалось найти fbzx")
        self.fbzx_value = fbzx_input["value"]

    def search_for_me(self, sheet, role="Зырянов Александр", column_index=1):
        table = sheet.get_all_values()
        return [row for row in table if row[0] == self.today and row[column_index] == role]

    def find_today_data(self):
        print("😤 Поиск нужного листа")
        for sheet_name in ['2', '3', '4']:
            sheet = self.spreadsheet.worksheet(sheet_name)
            matches = self.search_for_me(sheet)
            if matches:
                self.worksheet = sheet
                return matches
        raise Exception("🤪 Не найдено ни одного листа с данными")

    def prepare_data(self, rows):
        print("🛠 Подготовка данных")
        day, name_month, year = self.today.split(".")

        start_day = end_day = store = manager = cash = terminal = qr_code = \
            in_store_wallet = get_from_wallet = type_of_operation = who = ""
        terminal_in_1C = all_the_day = 0
        check = ""

        for row in rows:
            if str(row[1]) == "Зырянов Александр":
                check, start_day, end_day, store = str(row[3]).split(",")
                manager = row[1]
                cash = row[4].replace('\xa0', '').replace(' ', '').strip()
                terminal = row[7].replace('\xa0', '').replace(' ', '').strip()
                qr_code = row[9].replace('\xa0', '').replace(' ', '').strip()
                in_store_wallet = row[6].replace('\xa0', '').replace(' ', '').strip()
                all_the_day = int(terminal) + int(qr_code) + int(cash)
                terminal_in_1C = int(terminal) + int(qr_code)

        inkass = self.search_for_me(self.worksheet, role="Инкасс/Внесение", column_index=2)
        for row in inkass:
            get_from_wallet = row[5].replace('\xa0', '').replace(' ', '').strip()
            type_of_operation = row[3]
            who = row[1]

        store_report = {
            "крб3": "Соликамск Кр.Бульвар 3",
            "сев55": "Соликамск Северная 55",
            "мира83": "Березники Мира 110"
        }.get(store, "Неизвестно")

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
            "fbzx": self.fbzx_value,
            "pageHistory": "0,1,2,1,3,1,4,1,5,1,6,1,7,1,8,1,9,1,10,1,11,1,12,1,15,1,18,1,19",
            "fvv": "1",
        }

        print("Дата отчета: " + self.today)
        print("Начало смены: " + start_day + ":00 Закрытие смены: " + end_day + ":00")
        print("Магазин: " + store_report + " Консультант: " + manager)
        print("Наличные в 1С: " + cash + " Эквайринг 1С: " + str(terminal_in_1C))
        print("Сверка итогов: " + str(terminal) + " QR-код: " + str(qr_code))
        print("|||||ВСЕГО ЗА ДЕНЬ|||| " + str(all_the_day))
        print("Касса на конец смены: " + in_store_wallet)
        print("Инкассация сумма: " + get_from_wallet + " " + type_of_operation + " " + who)

        print("✅ Данные подготовлены")
        return check, data

    def send_form(self, data):
        print("👻 Отправка отчета!")
        response = requests.post(self.form_url, data=data)
        if response.status_code == 200:
            print("🙃 Форма успешно отправлена!")
        else:
            print(f"Ошибка при отправке формы: {response.status_code}")

    def job(self):
        print("=== Запуск отчета ===")
        self.authorize_google()
        self.extract_form_token()
        rows = self.find_today_data()
        check, data = self.prepare_data(rows)

        if check == "отправить":
            self.send_form(data)
        else:
            print("😫 Нет команды отправить")

sender = ReportSender()
schedule.every().day.at("17:28").do(sender.job)

print("Программа запущена. Ожидаем 17:28 каждый день...")
while True:
    schedule.run_pending()
    time.sleep(30)





