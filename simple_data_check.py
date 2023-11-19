#!/usr/bin/python3
"""
This script performs data checks according to
the specification: https://github.com/tradingview-pine-seeds/pine-seeds-docs/blob/main/data.md
"""

from __future__ import annotations
import glob
import json
import os
from os.path import exists, isfile
from sys import exit as sys_exit, argv
from datetime import datetime
from re import Pattern, compile as re_compile
from typing import Any, Dict, List, Tuple


TODAY: str = datetime.now().strftime("%Y%m%dT")
FLOAT_RE: Pattern[str] = re_compile(r'^[+-]?([0-9]*[.])?[0-9]+$')
SYMBOL_RE: Pattern[str] = re_compile(r'^[_.0-9A-Z]+$')
DESCRIPTION_RE: Pattern[str] = re_compile(r'^.+$')
PRICESCALE_RE: Pattern[str] = re_compile(r'^1(0){0,22}$')
MAX_ERRORS_IN_MSG: int = int(os.getenv("MAX_ERRORS_IN_MSG", 50))   # max show errors in console, file or PR message
THRESHOLD_ERR: int = int(os.getenv('THRESHOLD_ERR', 10))
REPORTS_PATH: str = argv[1] if len(argv) > 1 else "."


def check_type(values: Any, val_type: type) -> bool:
    """ check that values is list of types or single type value """
    if isinstance(values, list):
        for val in values:
            if not isinstance(val, val_type):
                return False
        return True
    else:
        return isinstance(values, val_type)


def check_length(values: Any, max_length: int) -> bool:
    """ check length of each element in values. Return True only when all elements have length less or equal to max_length."""
    if isinstance(values, list):
        for val in values:
            if len(val) > max_length:
                return False
    else:
        return len(values) <= max_length
    return True


def check_regexp(values: Any, regexp: Pattern[str]) -> bool:
    """ check that str() of each element in values match to provided regexp """
    if isinstance(values, list):
        for val in values:
            if regexp.match(str(val)) is None:
                return False
    else:
        return regexp.match(str(values)) is not None
    return True


def check_field_data(name: str, values: Any, val_type: type, regexp: Pattern[str], max_length: int, quantity: int, sym_file: str) -> List[str]:
    """ check the field data according type, max_length and quantity of elements """
    errors = []
    if not check_type(values, val_type):
        s_type = F'{"string" if val_type.__name__ == "str" else "integer"}'
        errors.append(F'The {name} type specified in {sym_file} must be a {s_type} or an array of {s_type}s')
        return errors
    if max_length > 0 and not check_length(values, max_length):
        errors.append(F'The {name} field in {sym_file} contains elements whose length exceeds the maximum allowed length: ({max_length})')
    if regexp is not None and not check_regexp(values, regexp):
        if name == "symbol":
            errors.append(F'The {sym_file} file contains invalid characters for the "symbol" field')
        elif name == "description":
            errors.append(F'The {sym_file} file contains empty "description" fields')
        else:  # "pricescale"
            errors.append(F'The {sym_file} file contains invalid values for the "pricescale" field. The value should be a power of 10: 1, 10, …, 10000000000000000000000. ' +
                          'The number of zeros represents the number of decimal places.')
    if quantity > 0 and (len(values) != quantity if isinstance(values, list) else quantity != 1):
        errors.append(F'The number of the {name} fields does not match the number of symbols in {sym_file}')
    return errors


def get_duplicates(items: List[Any]) -> set:
    """ Returns the set of duplicated items in list """
    existing = set()
    dup = set()
    for item in items:
        if item in existing:
            dup.add(item)
        else:
            existing.add(item)
    return dup


def check_symbol_info(sym_file: str) -> Tuple[List[str], List[str]]:
    """ check symbol file """
    errors: List[str] = []
    with open(sym_file) as file:
        sym_data: Dict[str, Any] = json.load(file)
    expected_fields = set(("symbol", "description", "pricescale"))
    exists_fields = set(sym_data.keys())
    if exists_fields != expected_fields:
        if expected_fields.issubset(exists_fields):
            errors.append(F"The {sym_file} file contains unexpected fields: {', '.join(exists_fields.difference(expected_fields))}")
        else:
            errors.append(F"The {sym_file} file doesn't have required fields: {', '.join(i for i in expected_fields.difference(exists_fields))}")
        return [], errors
    symbols: List[str] = sym_data["symbol"]
    errors = check_field_data("symbol", symbols, str, SYMBOL_RE, 42, 0, sym_file)
    if len(set(symbols)) != len(symbols):
        errors.append(F"The {sym_file} file contain duplicated symbols: {', '.join(get_duplicates(symbols))}. All symbols must have unique names.")
    if len(errors) > 0:
        return [], errors
    length = len(symbols) if isinstance(symbols, list) else 1
    descriptions = sym_data["description"]
    errors += check_field_data("description", descriptions, str, DESCRIPTION_RE, 128, length, sym_file)
    pricescale = sym_data["pricescale"]
    errors += check_field_data("pricescale", pricescale, int, PRICESCALE_RE, 0, length, sym_file)
    return symbols, errors


def check_data_line(data_line: str, file_path: str, i: int) -> Tuple[List[str], str|None]:
    """ check values of data file's line """
    messages: List[str] = []
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
    
    check_ok = True
    # validate float
    open_price, high_price, low_price, close_price, volume = 0.0, 0.0, 0.0, 0.0, 0.0
    try:
        for val in (vals[i] for i in range(1, 6)):
            if FLOAT_RE.match(val) is None:
                raise ValueError
        open_price, high_price, low_price, close_price, volume = float(vals[1]), float(vals[2]), float(vals[3]), float(vals[4]), float(vals[5])
    except ValueError:
        check_ok = False
        messages.append(F'{file_path}:{i} float values validation error. The float value can\'t be NAN/+INF/-INF') 
    # validate date
    try:
        if len(vals[0]) != 9:  # value '202291T' is considered as correct date 2022/09/01 by datetime.strptime but specification require zero-padded values
            raise ValueError
        _ = datetime.strptime(vals[0], '%Y%m%dT')
    except (ValueError, TypeError):
        check_ok = False
        messages.append(F'{file_path}:{i} date validation error, date format have to be YYYYMMDDT, for example: 20230101T')
    
    if check_ok:
        date = vals[0]
        if not (open_price <= high_price >= close_price >= low_price <= open_price and high_price >= low_price):
            messages.append(F'{file_path}:{i} contains invalid OHLC values. Values must comply with the rules: h >= o, h >= l, h >= c, l <= o, l <= c).')
        if volume < 0:
            messages.append(F'{file_path}:{i} contains invalid volume value. The value must be positive.')
        if date > TODAY:
            messages.append(F'{file_path}:{i} contains a date in the future. The date must be today or earlier.')
        if date < "19000101T":
            messages.append(F'{file_path}:{i} contains a date that is too old. The date must be January 1, 1900 or later.')
    return messages, date


def check_datafile(file_path: str, problems: Dict[str, List[Any]]) -> None:
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

def check_data_files(sym_file_path: str, symbols: List[str], problems: Dict[str, List[Any]]) -> None:
    """ check all files into data/ folder """
    sym_set = set(symbols)
    for file in glob.glob("data/*"):
        parts = file.split("/")[1].split(".")
        if len(parts) != 2:
            problems["errors"].append(F'Invalid file name. Check that {file} has a valid name and extension.')
            continue
        if parts[1] not in ("csv", "CSV"):
            problems["errors"].append(F'Invalid file extension. The {file} file format must be CSV.')
            continue
        if parts[0] not in sym_set:
            problems["errors"].append(F'There is no corresponding symbol for {file} in {sym_file_path}.')
            continue
        sym_set.discard(parts[0])
        check_datafile(file, problems)
    for symbol in sym_set:
        problems["missed_files"].append(symbol)


def fail(msg: str) -> None:
    """ report about fail and exit with non-zero exit code"""
    if REPORTS_PATH is None:
        print(msg)
        sys_exit(1)
    with open(os.path.join(REPORTS_PATH, "report.txt"), "a") as file:
        file.write(msg)
    sys_exit(0)


def main() -> None:
    """ main routine """
    group = os.getenv("GROUP")
    if group == "":
        fail("ERROR: the GROUP environment variable is not set")
    sym_file_path = F"symbol_info/{group}.json"
    problems = {"errors": [], "missed_files": []}
    if not (exists(sym_file_path) and isfile(sym_file_path)):
        problems["errors"] = [F'The "{sym_file_path}" file does not exist. Check that you have not deleted the file or modified its name/path']
    else:
        symbols, sym_errors = check_symbol_info(sym_file_path)
        problems["errors"] = sym_errors
        if len(symbols) > 0:
            check_data_files(sym_file_path, symbols, problems)

    # report warnings
    len_problems_missed_files = len(problems["missed_files"])
    if len_problems_missed_files > 0:
        if len_problems_missed_files > MAX_ERRORS_IN_MSG + THRESHOLD_ERR:
            warning = F'WARNING: the following symbols have no corresponding CSV files in the data folder: {", ".join(problems["missed_files"][:MAX_ERRORS_IN_MSG])} and {len_problems_missed_files - MAX_ERRORS_IN_MSG} other CSV files.\n'
        else:       
            warning = F'WARNING: the following symbols have no corresponding CSV files in the data folder: {", ".join(problems["missed_files"])}\n'
        
        if REPORTS_PATH is None:
            print(warning)
        else:
            with open(os.path.join(REPORTS_PATH, "warnings.txt"), "a") as file:
                file.write(warning)
    
    # report errors
    len_problems_errors = len(problems["errors"])
    if len_problems_errors > 0:
        if len_problems_errors > MAX_ERRORS_IN_MSG + THRESHOLD_ERR:
            problems_list = "\n ".join(problems["errors"][:MAX_ERRORS_IN_MSG])
            error_msg = F'ERROR: the following issues were found in the repository files:\n {problems_list} and {len_problems_errors - MAX_ERRORS_IN_MSG} other errors. \n'
        else:
            problems_list = "\n ".join(problems["errors"])
            error_msg = F'ERROR: the following issues were found in the repository files:\n {problems_list}\n'
        
        fail(error_msg)


if __name__ == "__main__":
    main()
