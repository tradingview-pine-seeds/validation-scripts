#!/usr/bin/python3
"""
This script performs data checks according to
the specification: https://github.com/tradingview-pine-seeds/pine-seeds-docs/blob/main/data.md
"""


import json
import os
from os import getenv
from os.path import exists, isfile
from sys import exit as sys_exit, argv
from datetime import datetime
from re import compile as re_compile


TODAY = datetime.now().strftime("%Y%m%dT")
FLOAT_RE = re_compile(r'^[+-]?([0-9]*[.])?[0-9]+$')
SYMBOL_RE = re_compile(r'^[_.0-9A-Z]+$')
CURRENCY_RE = re_compile(r'^[0-9A-Z]*$')
PRICESCALE_RE = re_compile(r'^1(0){0,18}$')
REPORTS_PATH = argv[1] if len(argv) > 1 else "."


def fail(msg):
    """ report about fail and exit with non-zero exit code"""
    with open(os.path.join(REPORTS_PATH, "report.txt"), "a") as file:
        file.write(msg)
    sys_exit(0)


def check_type(values, val_type):
    """ check that values is list of types or single type value """
    if isinstance(values, list):
        for val in values:
            if not isinstance(val, val_type):
                return False
        return True
    else:
        return isinstance(values, val_type)


def check_length(values: any, max_length: int):
    """ check length of each element in values. Return True only when all elements have length less or equal to max_length."""
    if isinstance(values, list):
        for val in values:
            if len(val) > max_length:
                return False
    else:
        return len(values) <= max_length
    return True


def check_regexp(values, regexp):
    """ check that str() of each element in values match to provided regexp """
    if isinstance(values, list):
        for val in values:
            if regexp.match(str(val)) is None:
                return False
    else:
        return regexp.match(str(values)) is not None
    return True


def check_field_data(name, values, val_type, regexp, max_length, quantity, sym_file):
    """ check the field data according type, max_length and quantity of elements """
    errors = []
    if not check_type(values, val_type):
        s_type = F'{"string" if val_type.__name__ == "str" else "integer"}'
        errors.append(F'The type of {name} filed must be {s_type} or array of {s_type}s in the {sym_file} file')
        return errors
    if max_length > 0 and not check_length(values, max_length):
        errors.append(F'The length of some elements in {name} field exceeds maximum allowed length in the {sym_file} file')
    if regexp is not None and not check_regexp(values, regexp):
        errors.append(F'Some elements in {name} field contains not allowed characters in the {sym_file} file')
    if quantity > 0 and isinstance(values, list) and len(values) != quantity:
        errors.append(F'The number of {name} field does not match the number of symbol in the {sym_file} file')
    return errors


def get_duplicates(items: list):
    """ Returns the set of duplicated items in list """
    existing = set()
    dup = set()
    for item in items:
        if item in existing:
            dup.add(item)
        else:
            existing.add(item)
    return dup


def check_symbol_info(sym_file):
    """ check symbol file """
    errors = []
    with open(sym_file) as file:
        sym_data = json.load(file)
    expected_fields = set(("symbol", "description", "pricescale", "currency"))
    exists_fields = set(sym_data.keys())
    if exists_fields != expected_fields:
        if expected_fields.issubset(exists_fields):
            errors.append(F"The {sym_file} file contains unexpected fields: {', '.join(exists_fields.difference(expected_fields))}")
        else:
            errors.append(F"The {sym_file} file doesn't have required fields: {', '.join(i for i in expected_fields.difference(exists_fields))}")
        return [], errors
    symbols = sym_data["symbol"]
    errors = check_field_data("symbol", symbols, str, SYMBOL_RE, 128, 0, sym_file)
    if len(set(symbols)) != len(symbols):
        errors.append(F"The {sym_file} file contain duplicated symbols: {', '.join(get_duplicates(symbols))}. All symbols must have unique names.")
    if len(errors) > 0:
        return [], errors
    length = len(symbols) if isinstance(symbols, list) else 1
    descriptions = sym_data["description"]
    errors += check_field_data("description", descriptions, str, None, 128, length, sym_file)
    desc_length = len(descriptions) if isinstance(descriptions, list) else 1
    if desc_length != length:  # strictly check descriptions length
        errors.append(F'The number of symbol descriptions does not much the number of symbols in {sym_file} file')
    pricescale = sym_data["pricescale"]
    errors += check_field_data("pricescale", pricescale, int, PRICESCALE_RE, 0, length, sym_file)
    currency = sym_data["currency"]
    errors += check_field_data("currency", currency, str, CURRENCY_RE, 128, length, sym_file)
    return symbols, errors


def check_data_line(data_line, file_path, i):
    """ check values of data file's line """
    messages = []
    date = None
    if data_line.startswith("#"):
        messages.append(F'{file_path} has comment in line {i}')
        return messages, date
    if len(data_line.strip()) == 0:
        messages.append(F'{file_path} contains empty line {i}')
        return messages, date
    vals = data_line.split(',')
    if len([i for i in vals if len(i) != len(i.strip())]) > 0:
        messages.append(F'{file_path} contains spaces in line {i}')
    if len(vals) != 6:  # YYYYMMDDT, o, h, l, c, v
        messages.append(F'{file_path}:{i} contains incorrect number of elements (expected: 6, actual: {len(vals)})')
        return messages, date
    try:
        for val in (vals[i] for i in range(1, 6)):
            if FLOAT_RE.match(val) is None:
                raise ValueError
        if len(vals[0]) != 9:  # value '202291T' is considered as correct date 2022/09/01 by datetime.strptime but specification require zero-padded values
            raise ValueError
        open_price, high_price, low_price, close_price = float(vals[1]), float(vals[2]), float(vals[3]), float(vals[4])
        _, volume = datetime.strptime(vals[0], '%Y%m%dT'), float(vals[5])
    except (ValueError, TypeError):
        messages.append(F'{file_path}:{i} contains invalid value types. Types must be: string(YYYYMMDDT), float, float, float, float, float. The float can\'t be NAN/+INF/-INF')
    else:
        date = vals[0]
        if not (open_price <= high_price >= close_price >= low_price <= open_price and high_price >= low_price):
            messages.append(F'{file_path}:{i} contains invalid OHLC values. Values must comply with the rules: h >= o, h >= l, h >= c, l <= o, l <= c).')
        if volume < 0:
            messages.append(F'{file_path}:{i} contains invalid volume value. The value must be positive.')
        if date > TODAY:
            messages.append(F'{file_path}:{i} contains date in future. The date must be today or before today.')
        if date < "19000101T":
            messages.append(F'{file_path}:{i} contains too old date. The date must be 1 Jan 1900 or after.')
    return messages, date


def check_datafile(file_path, problems):
    """ Check data file """
    dates = set()
    last_date = ""
    double_dates = False
    unordered_dates = False
    with open(file_path) as file:
        for i, line in enumerate(l.rstrip('\n') for l in file):
            wrong, date = check_data_line(line, file_path, i+1)
            problems["errors"].extend(wrong)
            if date is not None:
                if not double_dates and (date in dates):
                    double_dates = True
                    problems["errors"].append(F'{file_path} contains duplicate dates. First duplicate: {date} in line {i+1}.')
                if not unordered_dates and (date < last_date):
                    unordered_dates = True
                    problems["errors"].append(F'{file_path} has unordered dates. First unordered date: {date} in line {i+1}.')
                last_date = date
                dates.add(date)


def main():
    """ main routine """
    group = getenv("GROUP")
    if group == "":
        fail("ERROR: the GROUP environment variable is not set")
    sym_file_path = F"symbol_info/{group}.json"
    problems = {"errors": [], "missed_files": []}
    if not (exists(sym_file_path) and isfile(sym_file_path)):
        problems["errors"] = [F'The symbol info file "{sym_file_path}" does not exist']
        symbols = []
    else:
        symbols, sym_errors = check_symbol_info(sym_file_path)
        problems["errors"] = sym_errors
    for symbol in symbols:
        file_path = F'data/{symbol}.csv'
        if not (exists(file_path) and isfile(file_path)):
            problems["missed_files"].append(symbol)
            continue
        check_datafile(file_path, problems)
    if len(problems["missed_files"]) > 0:
        warning = F'WARNING: the following symbols have no corresponding CSV files in the data folder: {", ".join(problems["missed_files"])}\n'
        with open(os.path.join(REPORTS_PATH, "warnings.txt"), "a") as file:
            file.write(warning)
    if len(problems["errors"]) > 0:
        problems_list = "\n ".join(problems["errors"])
        fail(F'ERROR: the following issues were found in the repository files:\n {problems_list}\n')


if __name__ == "__main__":
    main()
