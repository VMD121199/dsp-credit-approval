import os
import pandas as pd
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, OneHotEncoder
import pickle

onehot_cols = [
    "NAME_FAMILY_STATUS",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
]
scale_cols = [
    "AMT_INCOME_TOTAL",
    "DAYS_EMPLOYED",
    "DAYS_BIRTH",
    "CNT_FAM_MEMBERS",
]


def select_core_columns(data: pd.DataFrame) -> pd.DataFrame:
    core_columns = [
        "FLAG_OWN_CAR",
        "FLAG_OWN_REALTY",
        "AMT_INCOME_TOTAL",
        "NAME_FAMILY_STATUS",
        "NAME_INCOME_TYPE",
        "NAME_EDUCATION_TYPE",
        "NAME_HOUSING_TYPE",
        "DAYS_BIRTH",
        "DAYS_EMPLOYED",
        "OCCUPATION_TYPE",
        "CNT_FAM_MEMBERS",
    ]
    if "APPROVED" in data.columns:
        core_columns.append("APPROVED")
    return data[core_columns]


def load_or_fit_encoder(
    encoder_name: str,
    data: pd.DataFrame,
    columns: list,
    encoder_type,
    fit_params={},
) -> any:
    filename = f"../output_model/{encoder_name}.pkl"
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            encoder = pickle.load(file)
    else:
        encoder = encoder_type(**fit_params)
        encoder.fit(data[columns])
        with open(filename, "wb") as file:
            pickle.dump(encoder, file)
    return encoder


def load_or_fit_onehot_encoder(data: pd.DataFrame) -> OneHotEncoder:
    params = {"handle_unknown": "ignore"}
    return load_or_fit_encoder(
        "onehot_encoder", data, onehot_cols, OneHotEncoder, params
    )


def load_or_fit_scaler(data: pd.DataFrame) -> StandardScaler:
    return load_or_fit_encoder("scaler", data, scale_cols, StandardScaler)


def load_encoder_scaler(data: pd.DataFrame) -> tuple:
    # ordinal_encoder = load_or_fit_ordinal_encoder(data)
    onehot_encoder = load_or_fit_onehot_encoder(data)
    scaler = load_or_fit_scaler(data)
    return onehot_encoder, scaler


def encode_ordinal(
    data: pd.DataFrame, column: str, encoder: OrdinalEncoder
) -> pd.DataFrame:
    encoded_data = encoder.transform(data[[column]])
    data[column] = encoded_data
    return data


def encode_onehot(
    data: pd.DataFrame, columns: list, encoder: OneHotEncoder
) -> pd.DataFrame:
    transformed_data = encoder.transform(data[columns]).toarray()
    column_names = encoder.get_feature_names_out(columns)
    encoded_df = pd.DataFrame(
        transformed_data, columns=column_names, index=data.index
    )
    data = pd.concat([data, encoded_df], axis=1)
    data.drop(columns=columns, inplace=True)
    return data


def scale_features(
    data: pd.DataFrame, columns: list, scaler: StandardScaler
) -> pd.DataFrame:
    scaled_data = scaler.transform(data[columns])
    data[columns] = scaled_data
    return data


def map_values(
    data: pd.DataFrame, columns: list, mapping: dict
) -> pd.DataFrame:
    return data.replace({col: mapping for col in columns})


def transform_data(data: pd.DataFrame, onehot_encoder, scaler) -> pd.DataFrame:
    data = encode_onehot(data, onehot_cols, onehot_encoder)

    data = scale_features(data, scale_cols, scaler)
    return data


def features_preprocessing(data: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    data = select_core_columns(data)
    onehot_encoder, scaler = load_encoder_scaler(data)
    data = transform_data(data, onehot_encoder, scaler)
    if "APPROVED" in data.columns:
        features = data.drop("APPROVED", axis=1)
        target = data[["APPROVED"]]
        return features, target
    else:
        return data, pd.DataFrame([])
