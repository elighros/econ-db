# ====================================================================================
# Author:David Ding
# Date:2023/02/17
# Purpose:
#
# ====================================================================================

# =========IMPORT PACKAGES==========
from bokeh.models import Select, ColumnDataSource
import pandas as pd
import numpy as np
from datetime import timedelta as td
import warnings
from bokeh.models.css import InlineStyleSheet
import os
warnings.filterwarnings(action='ignore')


# =========DEFINE CLASS==========
class Tool:
    
    def __init__(self):
        self.mapping_dict = None
        self.general_mapping = None
        self.matched_columns = None
        self.setting = Setting()
        self.source_backup = pd.DataFrame()
        self.data_setting_backup = pd.DataFrame()
        self.data_setting_backup.index.name = "name"
    
    def create_mapping_dict(self, df, keys, values, result=None, prefix=""):
        if result is None:
            result = {}
            
        if len(keys) == 1:
            for val in df[keys[0]].unique():
                result[str(prefix) + str(val)] = df[df[keys[0]] == val][values].unique().tolist()
        else:
            key = keys[0]
            for val in df[key].unique():
                new_prefix = str(prefix) + str(val)
                sub_df = df[df[key] == val]
                result[new_prefix] = sub_df[keys[1]].unique().tolist()
                self.create_mapping_dict(df=sub_df, keys=keys[1:], values=values, result=result, prefix=new_prefix)
        
        self.mapping_dict = result
        return result
    
    def create_matched_columns_and_general_mapping(self, df, country, length):
        
        self.matched_columns = df[country].tolist()
        self.general_mapping = pd.concat([df[df.columns[:length]], df[[country]]], axis=1)
    
    def create_selects(self):
        
        structure = self.setting.structure
        category_structure = self.setting.category_structure
        
        country_select_options = list(structure.keys())
        country_select = Select(value=country_select_options[0], options=country_select_options,
                                width=self.setting.select_width, title="Country")
        # print(f"Country select : {country_select.value}")
        
        category_select_options = list(structure[country_select.value].keys())
        category_select = Select(value=category_select_options[0], options=category_select_options,
                                 width=self.setting.select_width, title="Category")
        # print(f"Category select : {category_select.value}")
        
        mapping = pd.read_csv(category_structure[category_select.value]["path"])
        mapping = mapping[~mapping[country_select.value].isna()].replace(np.nan, "")
        mapping_dict = self.create_mapping_dict(df=mapping,
                                                keys=mapping.columns[: category_structure[category_select.value]["length"] - 1],
                                                values=mapping.columns[category_structure[category_select.value]["length"] - 1])
        # print(mapping_dict["NGDP QLCUBy expenditure"])
        self.create_matched_columns_and_general_mapping(df=mapping, country=country_select.value, length=category_structure[category_select.value]["length"])
        
        freq_select_options = sorted(mapping[mapping.columns[0]].unique().tolist())
        freq_select = Select(value="NGDP Q", options=freq_select_options,
                             width=self.setting.select_width, title="Frequency")
        # print(f"freq select : {freq_select.value}")
        
        unit_select_options = sorted(mapping_dict[freq_select.value])
        unit_select = Select(value="LCU", options=unit_select_options,
                             width=self.setting.select_width, title="Unit")
        # print(f"Unit select : {unit_select.value}")
        
        type_select_options = sorted(mapping_dict[freq_select.value + unit_select.value])
        type_select = Select(value="By expenditure", options=type_select_options,
                             width=self.setting.select_width, title="Type")
        
        cat1_select_options = sorted(mapping_dict[freq_select.value + unit_select.value + type_select.value])
        cat1_select = Select(value="GDP", options=cat1_select_options, width=self.setting.select_width,
                             title="Data category 1")
        
        cat2_select_options = sorted(mapping_dict[freq_select.value + unit_select.value + type_select.value + cat1_select.value])
        cat2_select = Select(value="", options=cat2_select_options, width=self.setting.select_width,
                             title="Data category 2")
        
        cat3_select_options = sorted(mapping_dict[freq_select.value + unit_select.value + type_select.value + cat1_select.value + cat2_select.value])
        cat3_select = Select(value=cat3_select_options[0], options=cat3_select_options, width=self.setting.select_width,
                             title="Data category 3")
        
        cat4_select_options = sorted(mapping_dict[freq_select.value + unit_select.value + type_select.value + cat1_select.value + cat2_select.value + cat3_select.value])
        cat4_select = Select(value=cat4_select_options[0], options=cat4_select_options, width=self.setting.select_width,
                             title="Data category 4")
        cat5_select_options = sorted(mapping_dict[
                                         freq_select.value + unit_select.value + type_select.value + cat1_select.value + cat2_select.value + cat3_select.value + cat4_select.value])
        cat5_select = Select(value=cat5_select_options[0], options=cat4_select_options, width=self.setting.select_width,
                             title="Data category 5")
        
        return country_select, category_select, freq_select, unit_select, type_select, cat1_select, cat2_select, cat3_select, cat4_select, cat5_select

    def get_column_by_selects(self, country_select, freq_select, unit_select, type_select, cat1_select, cat2_select, cat3_select, cat4_select, cat5_select, category_len):
        
        select_value_list = [i.value for i in [freq_select, unit_select, type_select, cat1_select, cat2_select, cat3_select, cat4_select, cat5_select]]
        
        dummy = (self.general_mapping.loc[:, [str(i) for i in range(category_len)]] == select_value_list[:category_len]).all(axis=1)
        col_name = self.general_mapping.loc[dummy, country_select.value].values[0]
        
        return col_name
    
    def read_data(self, setting_path, data_path, matched_columns=None):
        self.data_setting = pd.read_csv(setting_path, index_col=[0])
        
        data = pd.read_csv(data_path, index_col=[0]).dropna(how='all', axis=0).fillna(method="ffill")
        self.data = data[matched_columns] if matched_columns is not None else data
        self.data.index = pd.to_datetime(self.data.index)
        
        for index, row in self.data_setting.iterrows():
            try:
                if row['data_type'] == "p":
                    self.data.loc[:, index] = self.data[index].values / 100
                else:
                    self.data.loc[:, index] = self.data[index].values * 1000000000
            
            except Exception as e:
                pass
                
        return self.data, self.data_setting
    
    def create_data_setting_object(self, data_setting, col_name):
        data_setting_backup_cols = ['display_name', "data_type", "chart_type"]
        data_col_name = col_name = "_".join(col_name.split("_")[:-1])
        try:
            self.data_setting_backup.loc[col_name, data_setting_backup_cols] = data_setting.loc[data_col_name].tolist()
        except Exception as e:
            pass
        data_setting_object = self.data_setting_backup.loc[[col_name]].reset_index().loc[0].to_dict()
        
        return data_setting_object
    
    def add_source_column(self, source, col_name, new=True):
        
        source_df = pd.DataFrame(source.data)
        col_name = "_".join(col_name.split("_")[:-1])
        
        if len(source_df) == 0:
            source_df = self.data[[col_name]]
            self.source_backup = self.data[[col_name]]
        else:
            try:
                source_df = pd.concat([source_df.set_index("Date"), self.data[[col_name]]], axis=1)
                self.source_backup = pd.concat([self.source_backup, self.data[[col_name]]], axis=1)
            except Exception as e:
                source_df = pd.concat([source_df.set_index("Date"), self.source_backup[[col_name]]], axis=1)
            
        source = ColumnDataSource(source_df)
    
        return source


class Setting:
    def __init__(self):
        self.create_styles()
        self.theme_file_path = "lib/theme/theme.yml"
        self.curdoc_name = "ECON DB"
        
        self.line_width = 2
        self.bar_width = td(days=60)
        self.figure_width = 1000
        self.figure_height = 500
        self.range_height = 100
        self.select_width = 500
        self.button_width = 100
        self.datatable_column_width = 500

        self.multichoice_width = int(self.figure_width + self.datatable_column_width - 3 * self.button_width)
        
        # color setting
        self.bar_border_color = "#000000"
        self.colors = [
            {"id": 0, "color": "#191970", "used": False, "label": "midnightblue"},
            {"id": 1, "color": "#006400", "used": False, "label": "darkgreen"},
            {"id": 2, "color": "#8b0000", "used": False, "label": "darkred"},
            {"id": 3, "color": "#4b0082", "used": False, "label": "indigo"},
        ]
        
        self.data_freq_lookup_table = {
            "Quarterly": ["NGDP Q", "RGDP Q"],
            "Monthly": ["Monthly"]
        }
        
        # first three selects setting
        self.structure = {
            "JP": {
                "National accounts": {
                    "Q": True,
                    "Quarterly_data_path": "db/jp/data/gdp/jp_gdp_q.csv",
                    "Quarterly_setting_path": "db/jp/setting/gdp/jp_gdp_q_setting.csv",
    
                    "A": False,
                    "Annual_data_path": "db/jp/data/gdp/jp_gdp_a.csv",
                    "Annual_setting_path": "db/jp/setting/gdp/jp_gdp_a_setting.csv",
                    
                }
            },
            
            "TW": {
                "National accounts": {
                    "Q": True,
                    "Quarterly_data_path": "db/tw/data/gdp/tw_gdp_q.csv",
                    "Quarterly_setting_path": "db/tw/setting/gdp/tw_gdp_q_setting.csv",
                    
                    "A": False,
                    "Annual_data_path": "db/tw/data/gdp/tw_gdp_a.csv",
                    "Annual_setting_path": "db/tw/setting/gdp/tw_gdp_a_setting.csv",
                },
                "Foreign trade":{
                    "M": True,
                    "Monthly_data_path": "db/tw/data/export/tw_export_m.csv",
                    "Monthly_setting_path": "db/tw/setting/export/tw_export_m_setting.csv",
                }
            },
            
            "KR": {
                "National accounts": {
                    "Q": True,
                    "Quarterly_data_path": "db/kr/data/gdp/kr_gdp_q.csv",
                    "Quarterly_setting_path": "db/kr/setting/gdp/kr_gdp_q_setting.csv",
                    
                    "A": False,
                    "Annual_data_path": "db/kr/data/gdp/kr_gdp_a.csv",
                    "Annual_setting_path": "db/kr/setting/gdp/kr_gdp_a_setting.csv",
                },
                "Foreign trade": {
                    "M": True,
                    "Monthly_data_path": "db/kr/data/export/kr_export_m.csv",
                    "Monthly_setting_path": "db/kr/setting/export/kr_export_m_setting.csv",
                }
            },
        }
        
        self.category_structure = {
            "National accounts": {
                "input_path": "db/mapping/gdp/gdp_mapping_template.xlsx",
                "path": "db/mapping/gdp/gdp_mapping.csv",
                "length": 8
            },
            
            "Foreign trade": {
                "input_path": "db/mapping/export/export_mapping_template.xlsx",
                "path": "db/mapping/export/export_mapping.csv",
                "length": 6
            }
            
        }
        
        self.download_button_path = "lib/js_code/download_button_callback.js"

    def create_styles(self):
        
        
        button_style_path = "lib/style/button_styles.css"
        self.button_stylesheet = InlineStyleSheet(css=open(button_style_path).read())
    
        select_style_path = "lib/style/select_styles.css"
        self.select_stylesheet = InlineStyleSheet(css=open(select_style_path).read())
    
        datatable_style_path = "lib/style/datatable_styles.css"
        self.datatable_stylesheet = InlineStyleSheet(css=open(datatable_style_path).read())