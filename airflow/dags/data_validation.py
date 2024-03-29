import logging
import great_expectations as ge
import shutil
import os
import pandas as pd
from sqlalchemy import create_engine, Column, String, Integer, Text, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import smtplib
from email.mime.text import MIMEText

Base = declarative_base()


class DataProblemsStatistics(Base):
    __tablename__ = "data_problems_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String)
    column = Column(String)
    expectation_values = Column(String)
    unexpected_values = Column(Text)
    date_validation = Column(DateTime)


def read_and_validate_file(df):
    context = ge.DataContext("gx")
    expectation_suite_name = "external.table.warning"
    suite = context.get_expectation_suite(expectation_suite_name)

    if suite is None:
        suite = context.create_expectation_suite(expectation_suite_name)

    ge_df = ge.dataset.PandasDataset(df, expectation_suite=suite)

    ge_df.expect_column_values_to_be_in_set(
        column="CODE_GENDER",
        value_set=["F", "M"],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="FLAG_OWN_CAR",
        value_set=["Y", "N"],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="FLAG_OWN_REALTY",
        value_set=["Y", "N"],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="NAME_INCOME_TYPE",
        value_set=[
            "Working",
            "Commercial associate",
            "State servant",
            "Student",
            "Pensioner",
        ],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="NAME_EDUCATION_TYPE",
        value_set=[
            "Higher education",
            "Secondary / secondary special",
            "Incomplete higher",
            "Lower secondary",
            "Academic degree",
        ],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="NAME_FAMILY_STATUS",
        value_set=[
            "Civil marriage",
            "Married",
            "Single / not married",
            "Separated",
            "Widow",
        ],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="NAME_HOUSING_TYPE",
        value_set=[
            "Rented apartment",
            "House / apartment",
            "Municipal apartment",
            "With parents",
            "Co-op apartment",
            "Office apartment",
        ],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_between(
        column="CNT_CHILDREN",
        min_value=0,
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_between(
        column="AMT_INCOME_TOTAL",
        min_value=0,
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_between(
        column="DAYS_BIRTH",
        max_value=0,
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_between(
        column="DAYS_EMPLOYED",
        max_value=0,
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="FLAG_MOBIL",
        value_set=[0, 1],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="FLAG_WORK_PHONE",
        value_set=[0, 1],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="FLAG_PHONE",
        value_set=[0, 1],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_in_set(
        column="FLAG_EMAIL",
        value_set=[0, 1],
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_between(
        column="CNT_FAM_MEMBERS",
        min_value=0,
        result_format={"result_format": "COMPLETE"},
    )
    ge_df.expect_column_values_to_be_between(
        column="CNT_FAM_MEMBERS",
        min_value=0,
        parse_strings_as_datetimes=True,
        result_format={"result_format": "COMPLETE"},
    )
    validation_result = ge_df.validate()

    return validation_result


def process_file(file_path, folder_b, folder_c):
    df = pd.read_csv(file_path)
    validation_result = read_and_validate_file(df)
    if validation_result["success"]:
        store_file_in_folder(file_path, folder_c)
    else:
        if all(
            result["success"] is False
            for result in validation_result["results"]
        ):
            store_file_in_folder(file_path, folder_b)

        else:
            split_file_and_save_problems(
                file_path, folder_b, folder_c, validation_result
            )
    os.rename(
        file_path,
        os.path.dirname(file_path)
        + "/validated_"
        + os.path.basename(file_path),
    )


def store_file_in_folder(file_path, destination_folder):
    shutil.copy(
        file_path,
        os.path.join(destination_folder, os.path.basename(file_path)),
    )


def save_data_problems_statistics(validation_result, file_path):
    db_url = "postgresql://postgres:121199@172.21.240.1/dsp"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for result in validation_result["results"]:
        if not result["success"]:
            column = result["expectation_config"]["kwargs"]["column"]
            try:
                expectation_values = result["expectation_config"]["kwargs"][
                    "value_set"
                ]
            except:
                expectation_values = "greater than " + str(
                    result["expectation_config"]["kwargs"]["min_value"]
                )
            unexpected_values = str(
                result["result"]["partial_unexpected_list"]
            )

            stat = DataProblemsStatistics(
                file_name=file_path,
                column=column,
                expectation_values=expectation_values,
                unexpected_values=unexpected_values,
                date_validation=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            data_problems = [column, expectation_values, unexpected_values]
            alert_user_with_email_notification(file_path, data_problems)
            session.add(stat)

    session.commit()
    session.close()


def split_file_and_save_problems(
    file_path, folder_b, folder_c, validation_result
):
    df = pd.read_csv(file_path)

    problematic_rows = []
    for result in validation_result["results"]:
        if not result["success"]:
            problematic_rows.extend(result["result"]["unexpected_index_list"])

    if problematic_rows:
        df_problems = df.loc[problematic_rows]
        df_no_problems = df.drop(problematic_rows)

        problems_file_path = os.path.join(
            folder_b, f"file_with_data_problems_{os.path.basename(file_path)}"
        )

        save_data_problems_statistics(validation_result, problems_file_path)
        df_problems.to_csv(problems_file_path, index=False)

        no_problems_file_path = os.path.join(
            folder_c,
            f"file_without_data_problems_{os.path.basename(file_path)}",
        )
        df_no_problems.to_csv(no_problems_file_path, index=False)


def send_email_notification(sender, recipient, subject, message):
    # Create the message
    message = MIMEText(message)
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    # Establish a connection with the SMTP server
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("ducminhvu2022@gmail.com", "otqt hqpw wqwo hhvm")
        server.sendmail(sender, recipient, message.as_string())


def alert_user_with_email_notification(file_path, val_rs):
    sender = "ducminhvu2022@gmail.com"
    recipient = "minhducvu1211@gmail.com"
    subject = "Data Quality Issues"
    message = (
        f"File: {file_path} have problems\n"
        + f"Detail: \n"
        + f"Column          |   Expected value  |   True Value \n"
        + f"{val_rs[0]}     |   {val_rs[1]}     |   {val_rs[2]}"
    )

    send_email_notification(sender, recipient, subject, message)
