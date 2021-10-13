from current_sales import main_current_sales
from historical_sales import main_historical_sales
from utils import send_mail, load_config_file
import yagmail


def main():
    main_historical_sales()
    main_current_sales()
    configs = load_config_file()
    send_mail(
        configs["mail"]["to_address"],
        configs["mail"]["from_address"],
        configs["mail"]["from_address_pw"])


if __name__ == "__main__":
    main()
