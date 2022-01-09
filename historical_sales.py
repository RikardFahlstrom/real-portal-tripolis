import configparser
import time

import pandas as pd
import pandas_bokeh
from bokeh import models
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import load_config_file, remove_duplicates_from_string

pandas_bokeh.output_file("output_files/tripolis_sales.html")


def main_historical_sales(runs_local=False):
    configs = load_config_file()
    browser = setup_browser(configs, runs_local=runs_local)
    logged_in_browser = login_to_page(browser, configs)
    num_pages = get_num_pages_to_query(logged_in_browser, configs)
    raw_data = download_data(logged_in_browser, configs, num_pages)
    dropped_columns = remove_unneeded_rows(raw_data)
    transformed_data = transform_data(dropped_columns)

    structured_data, df_graph = create_dataframes_for_table_and_linegraph(
        transformed_data
    )
    create_graph(structured_data, df_graph)
    save_as_csv(structured_data)


def setup_browser(configs, runs_local=False) -> webdriver:
    options = Options()
    options.add_argument("--window-size=1920,1080")

    if runs_local:
        browser = webdriver.Chrome(
            executable_path=configs["selenium"]["local_executable_path"],
            options=options,
        )
    else:
        options.add_argument("--headless")
        browser = webdriver.Remote(
            "http://chrome:4444/wd/hub",
            webdriver.DesiredCapabilities.CHROME,
            options=options,
        )

    return browser


def login_to_page(chrome_browser, configs):
    chrome_browser.get(configs["abj_portal"]["login_url"])
    chrome_browser.execute_script("return onKlassiskInloggning()")

    username = chrome_browser.find_element_by_name("username")
    username.send_keys(configs["abj_portal"]["username"])

    password = chrome_browser.find_element_by_name("password")
    password.send_keys(configs["abj_portal"]["password"])

    chrome_browser.find_element_by_name("login").click()

    return chrome_browser


def get_num_pages_to_query(chrome_browser, configs):
    chrome_browser.get(
        configs["abj_portal"]["scrape_url"] + "1"
    )  # +1 to retrieve first pageno
    num_pages = chrome_browser.find_element_by_class_name("pagination").text

    return int(num_pages.split("\n")[-2])


def download_data(
    browser: webdriver, configs: configparser.ConfigParser, last_page_num
) -> pd.DataFrame:

    all_dfs = []

    for page in range(1, last_page_num + 1):
        browser.get(configs["abj_portal"]["scrape_url"] + str(page))
        df = pd.read_html(
            browser.find_element_by_xpath(
                "/html/body/div[2]/div[1]/div[2]/center/table"
            ).get_attribute("outerHTML"),
            header=0,
        )[0]
        all_dfs.append(df)
        time.sleep(2)

    browser.close()
    browser.quit()

    return pd.concat(all_dfs, ignore_index=True)


def remove_unneeded_rows(df: pd.DataFrame):
    df = df.iloc[:, :-1]
    df["Objekt"] = df["Objekt"].astype(str)
    df.drop(
        df[
            (df.Objekt.str.startswith("Namn"))
            | (df.Objekt.str.startswith("Information"))
            | (~df.Objekt.str.contains("0|1|2|3|4|5|6|7|8|9"))
        ].index,
        inplace=True,
    )

    return df


def transform_data(raw_data: pd.DataFrame) -> pd.DataFrame:

    raw_data["Area"] = raw_data["Area"].astype(float)
    raw_data["Area"] = raw_data["Area"] / 100
    raw_data["Pris"] = raw_data["Pris"].str.replace("-", "0")
    raw_data["Pris"] = raw_data["Pris"].str.replace(" ", "")
    raw_data["Pris"].fillna(0, inplace=True)

    raw_data["transaction_id"] = raw_data["Objekt"] + ";" + raw_data["Överlåtelse"]

    raw_data_grouped = raw_data.groupby("transaction_id").agg(
        {
            "Area": "max",
            "Lokaltyp": lambda x: ",".join(x),
            "Adress": lambda x: ",".join(x),
            "Pris": "max",
        }
    )
    raw_data_grouped = raw_data_grouped.reset_index()
    raw_data_grouped["id"] = raw_data_grouped["transaction_id"]
    raw_data_grouped[["transaction_id", "överlåtelse"]] = raw_data_grouped[
        "transaction_id"
    ].str.split(";", expand=True)
    raw_data_grouped[["Pris", "Pris_leftovers"]] = raw_data_grouped["Pris"].str.split(
        ",", expand=True
    )
    raw_data_grouped["Lokaltyp"] = raw_data_grouped.apply(
        lambda row: remove_duplicates_from_string(row["Lokaltyp"]), axis=1
    )
    raw_data_grouped["Adress"] = raw_data_grouped.apply(
        lambda row: remove_duplicates_from_string(row["Adress"]), axis=1
    )

    raw_data_grouped["Pris"] = pd.to_numeric(raw_data_grouped["Pris"])
    raw_data_grouped["Area"] = pd.to_numeric(raw_data_grouped["Area"])
    raw_data_grouped["överlåtelse"] = pd.to_datetime(raw_data_grouped["överlåtelse"])
    raw_data_grouped["overlatelse_date"] = raw_data_grouped["överlåtelse"].dt.date

    raw_data_grouped["överlåtelse_yearmonth"] = raw_data_grouped[
        "överlåtelse"
    ].dt.to_period("M")
    raw_data_grouped["overlatelse_year"] = raw_data_grouped["överlåtelse"].dt.to_period(
        "Y"
    )
    raw_data_grouped["överlåtelse_quarter"] = raw_data_grouped["överlåtelse"].dt.quarter
    raw_data_grouped["pris_kvm"] = raw_data_grouped["Pris"] / raw_data_grouped["Area"]
    raw_data_grouped = raw_data_grouped.round({"pris_kvm": 0})

    raw_data_grouped.rename(columns={"transaction_id": "lgh"}, inplace=True)
    raw_data_grouped.drop(columns=["Pris_leftovers", "överlåtelse"], inplace=True)
    raw_data_grouped.sort_values(by=["overlatelse_date"], ascending=True, inplace=True)

    raw_data_grouped = raw_data_grouped[
        (raw_data_grouped["Pris"] != 0)
        & (~raw_data_grouped["Lokaltyp"].isin(["Egen lokal", "Lokal"]))
        & (raw_data_grouped["pris_kvm"] >= 10000)
    ]

    return raw_data_grouped


def create_dataframes_for_table_and_linegraph(transformed_data):

    df_table = transformed_data[["overlatelse_date", "lgh", "Area", "Pris", "pris_kvm"]]

    df_graph = (
        transformed_data.groupby(["overlatelse_year"])
        .agg({"Pris": "sum", "Area": "sum", "overlatelse_date": "count"})
        .reset_index()
    )
    df_graph["pris_per_kvm"] = df_graph["Pris"] / df_graph["Area"]
    df_graph.drop(columns=["Pris", "Area"], inplace=True)

    return df_table, df_graph


def create_graph(structured_sales_data, df_for_line_graph):
    hfmt = models.NumberFormatter(format="0,0")
    columns = [
        TableColumn(
            field="overlatelse_date",
            title="Överlåtelsedatum",
            formatter=models.DateFormatter(format="%Y-%m-%d"),
        ),
        TableColumn(field="lgh", title="Lgh"),
        TableColumn(field="Area", title="m2"),
        TableColumn(field="Pris", title="Pris", formatter=hfmt),
        TableColumn(field="pris_kvm", title="Pris per kvm", formatter=hfmt),
    ]

    data_table = DataTable(
        columns=columns, source=ColumnDataSource(structured_sales_data), height=600
    )

    p = figure(x_axis_type="datetime")
    source = ColumnDataSource(df_for_line_graph)
    p.line(x="overlatelse_year", y="pris_per_kvm", source=source)
    p.title.text = "Brf Tripolis"
    p.xaxis.axis_label = "Överlåtelseår"
    p.yaxis.axis_label = "Genomsnittligt pris per kvadrat"

    hover = HoverTool(
        tooltips=[
            ("År", "@overlatelse_year{%Y}"),
            ("Pris", "@pris_per_kvm{%0.0000000f}"),
            ("Antalet sålda lägenheter", "@overlatelse_date"),
        ],
        formatters={"@overlatelse_year": "datetime", "@pris_per_kvm": "printf"},
    )

    p.add_tools(hover)

    pandas_bokeh.plot_grid([[data_table, p]], width=600, height=550)


def save_as_csv(formatted_sales_data: pd.DataFrame):
    formatted_sales_data.to_excel(
        "output_files/tripolis_historical_sales.xlsx", index=False, freeze_panes=(1, 0)
    )


if __name__ == "__main__":
    main_historical_sales(runs_local=True)
