import configparser
import yagmail
from datetime import date


def load_config_file() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read('config.ini')

    return config


def remove_duplicates_from_string(string_to_be_changed: str):
    string_as_list = string_to_be_changed.split(',')
    only_unique_values = set(string_as_list)

    return ','.join(only_unique_values)


def send_mail(send_mail_to_addresses, from_adress, from_adress_pw):
    receiver = send_mail_to_addresses
    body = "Se bifogad information om historiska och aktuella försäljning för Brf Tripolis"
    excel_hist_sale = "output_files/tripolis_historical_sales.xlsx"
    excel_for_sale = "output_files/tripolis_for_sale.xlsx"
    html_table = "output_files/tripolis_sales.html"

    yag = yagmail.SMTP(from_adress, from_adress_pw)
    date_today = date.today().strftime("%Y-%m-%d")

    yag.send(
        to=receiver,
        subject=f"Brf Tripolis försäljningsinformation uppdaterat {date_today}",
        contents=body,
        attachments=[excel_hist_sale, excel_for_sale, html_table],
    )
