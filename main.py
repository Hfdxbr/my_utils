# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 12:09:28 2021

@author: l_knyazev
"""
#
# Программа для вывода данных из rpt файлов
#
# Для корректной работы программы необходимо указать путь к папке в переменной
# dest и имя репорт файла в переменной file, или перетащить файл с 
# исходными данными на исполняемый файл.
#
# Кроме того в папке с репорт можно поместить config.txt,
# который задает обозначения для элементов пары:
# "название" - "номер элемента" (через " - ")
#
# В файле config.txt можно указать порядок вывода результатов. Для этого config.txt
# должен содержать строку print_order, за которой на следующей строке,
# через запятую, должен быть указан порядок в котором должны выводиться результаты.
# Если параметр print_order не задан результаты буду выведены в порядке добавления.
#
# Пример структуры файла config.txt:
# ---------------------------------
#    # Номер узла навески:
#    ots1 - 53113
#    ots2 - 53086
#    ots3 - 53081
#
#    # Номер подкоса:
#
#    vsu1 - 66936
#    vsu2 - 66937
#    vsu3 - 66938
#
#    print_order:
#    vsu1,vsu2,vsu3,ots1,ots2,ots3
# ----------------------------------

import re
import sys, os
from report_classes import Job, Loadcase
from datetime import datetime as dt
from pathlib import Path

import logging

logging.basicConfig()
logger = logging.getLogger('JobProcessor')
logger.setLevel(logging.INFO)

# =============================================================================
# Введите путь и имя файла с исходными данными
# =============================================================================
dest = Path(r'D:\Program Files\WPy\_py_projects\__work_scripts\report_reader\check_data\patran_XXX.rpt')

if len(sys.argv) > 1:
    dest = Path(sys.argv[1])
    print('\n')
# =============================================================================

current_date = dt.today().strftime('%d.%m.%y_%H.%M')
logger.info(f'Current date: {current_date}')

def read_config(path: Path):
    '''Чтение файла конфигурации config.txt'''
    config_data = {}
    prt_order = []
    if path.exists():
        logger.info(f'Путь {path} существует')
        print_order_flag = 0
        for line in path.read_text().split():
            if line.strip() and not '#' in line:
                if 'print' in line and 'order' in line:
                    print_order_flag = 1
                elif print_order_flag == 1:
                    prt_order = [i.strip() for i in line.strip().split(',')]
                    print_order_flag = 0
                elif line.strip().split():
                    line = line.strip().split('-')
                    line = [i.strip() for i in line]
                    config_data[line[0]] = line[1]
        if prt_order:
            for i in prt_order:
                if i not in config_data.keys():
                    logger.warn("Имена указанные в списке print order не совпадают с таблицей обозначений.\n"
                                "Дальнейший вывод будет производиться в порядке заданным таблицей обозначений")
                    break
            else:
                logger.info('Параметр print_order обнаружен.\nприменяем print_order')
                config_data = {i: config_data[i] for i in prt_order}
                logger.info(f"Новый порядок вывода:\n{',\n'.join(config_data.keys())}")
        logger.info('Чтение файла конфигурации завершено\n')
    else:
        logger.warn('Файл конфигурации не найден\n')
    return config_data

def read_input_data(file: Path):
# Чтение входного файла
    logger.info(f"Открываю файл входных данных: {file.name}\nиз дирректории: {file.parent}")
    ratio_dict = {}
    rezalts_NL = {}
    for line in file.read_text().split():
        line = line.strip()
        if 'Result Sources' in line:   #конец чтения rpt файла
            break
# Структура словаря        
        if 'Load Case' in line:
            lc_ = re.match(r'(Load Case: )(.+)(, )(A[0-9]*:)(Non-linear|Static Subcase)(.*)', line)
            lc_type = lc_.group(5)
            lc_name = lc_.group(2)            
            if lc_type == 'Static Subcase':
                lc_job = lc_.group(4)[:-1]  #имя джоба просто буква с порядковым номером
                lc_percent = 100
            if lc_type == 'Non-linear':
#               если нелинейный тогда в имени будет процент нагрузки
                percent = re.match(r'(: )([.0-9]+)(.+)',lc_.group(6))
                lc_percent = float(percent.group(2))
#               если в конце заголовка есть '_' и число за ним, то считываем его как процент нагрузки в данном лоадкейсе
#               в конце вместо точки может быть использована буква Р
                name_flag = re.match(r'(.+:)?(.*)(_[0-9Pp]+$)', lc_.group(2))
                if name_flag:
                    lc_job = lc_.group(4)[:-1] + ' ' + name_flag.group(2)
                else:
#                  если числа в конце имени не обнаружено, тогда берем номер джоба и добавляем к нему имя лоадкейса
                    nf = re.match(r'(.+:)?(.*)', lc_.group(2))
                    lc_job = lc_.group(4)[:-1] + ' ' + nf.group(2)  # срез [:-1] отбрасывает ':' после А 
#------------------------------------------------------------------------------
# Изменился формат ratio_dict.
# Ключи:
#     ratios - содержит имена сабкейсов данного джоба и процент нагрузки в них
#     output_type - тип выводимых результатов
#     header - заголовки данных
#     type - тип сабкейса
#------------------------------------------------------------------------------
            if lc_job not in ratio_dict.keys():
                ratio_dict[lc_job]={}
                keys = ['ratios', 'output_type', 'header', 'type']
                _data_type = [{}, '', [], lc_type]
                for key, _type in zip(keys, _data_type):
                    ratio_dict[lc_job][key]=_type
            if lc_name not in ratio_dict[lc_job]['ratios'].keys():
                ratio_dict[lc_job]['ratios'][lc_name]=[]
            if lc_type =='Static Subcase':
                ratio_dict[lc_job]['ratios'][lc_name] = 100    
            else:
                if name_flag:
                    ratio_dict[lc_job]['ratios'][lc_name] = float(name_flag.group(3)[1:].replace('P', '.').replace('p','.'))
                else:
                    ratio_dict[lc_job]['ratios'][lc_name] = None
            if lc_job not in rezalts_NL.keys():
                rezalts_NL[lc_job] = {}
            if lc_name not in rezalts_NL[lc_job].keys():                    
                rezalts_NL[lc_job][lc_name] = {}
            if lc_percent not in rezalts_NL[lc_job][lc_name].keys():
                rezalts_NL[lc_job][lc_name][lc_percent] = {}
        if 'Result' in line:
            res = re.match(r'(Result )(.+$)', line)
            if res:
                if lc_job in ratio_dict.keys():
                    ratio_dict[lc_job]['output_type'] = res.group(2)
        if line.startswith('-Entity ID'):
            if lc_job in ratio_dict.keys():
                res = re.sub(r'[-]+','-',line[10:])
                ratio_dict[lc_job]['header'] = res.strip('-').split('-')
# Считывание данных
        line = line.split()
        if line:
# Пробуем строку превратить в числа, если в строке хоть одна буква - строка не является строкой с результами, omit
            try:
                line = [float(i) for i in line]
                rezalts_NL[lc_job][lc_name][lc_percent][str(int(line[0]))] = line[1:]
            except ValueError:
                pass            

    jobs = []
    loadcases = []
    for job in rezalts_NL.keys():
        loadcases=[]
        for lc, pc in rezalts_NL[job].items():
            loadcases.append(Loadcase(name = lc,
                                      output_type = ratio_dict[job]['output_type'],
                                      header = ratio_dict[job]['header'],
                                      percents = list(pc.keys()),
                                      max_load = ratio_dict[job]['ratios'][lc],
                                      data = pc))
        jobs.append(Job(job, ratio_dict[job]['type'], loadcases))
    return jobs


path = dest_file.parent / 'config.txt'
logger.info(f'Чтение файла конфигурации вывода {path}...')    
config_data = read_config(path)
logger.info(f'Чтение входных данных')
jobs = read_input_data(dest_file)

out_file = dest.parent / f'output_{current_date}.txt'
out_lines = []
for j in jobs:
    logger.info(f'Обработка {j.name}\n')
    out_lines.append(j.printout(config_data))
out_file.write_text(''.join(out_lines))
logger.info(f'\nФайл {out_file} сохранен')
input('Press Enter to Exit')
