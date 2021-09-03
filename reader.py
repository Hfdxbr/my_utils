# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 17:25:46 2021

@author: l_knyazev
"""
class Job():
    def __init__(self,                  
                 name: str ='test', 
                 jtype: str = 'None type', 
                 loadcases: list = []):
        self.name = name
        self.jtype = jtype
        self.loadcases = loadcases
        if self.jtype == 'Non-linear' and self.__max_loads_check:
            self.true_pc()

    @property
    def lc_names(self):
        return [lc.lc_name for lc in self.loadcases]
    
    @property
    def j_percents(self):
        jpercents = []
        for lc in self.loadcases:
            jpercents += lc.percents
        return jpercents
    
    @property
    def j_max_loads(self):
        return [lc.max_load for lc in self.loadcases]
    
    @property
    def __max_loads_check(self):
        return all(self.j_max_loads)

    @property
    def all_elements(self):
        all_elements = []
        for l in self.loadcases:
            for k, v in l.data.items():
                for item in v.keys():
                    if item not in all_elements:
                        all_elements.append(item)
        return all_elements
                
    def data_by_lc_name(self, lc_name:str = ''):
        for lc in self.loadcases:
            if lc.lc_name == lc_name:
                return lc.data
        else:
            print('LC not found')
        
    def data_by_node_id(self, node_id = None):
        if node_id:
            for lc in self.loadcases:
                for pc in lc.percents:
                    print(pc, lc.data[pc][node_id])
        else:
            print('Node not found')
    
    def true_pc(self, start = 0):
#        start = 0                                 # Старт джоба принимается от 0 максимальной нагрузки
        for lc in self.loadcases:
            tp_list = []                          # Список с реальными процентами внутри лоадкейса
            lc_load = (lc.max_load - start)/100   # Шаг лоадкейса от максимальной нагрузки
            sub_control = lc.percents[0]//100     # Параметр для отслеживания 100% данного лоадкейса
            for percent in lc.percents:                # Для каждого процента данного лоадкейса
                if percent // 100 == sub_control:      # Если не достигнут последний элемент добавляем в список
                    tp_list.append(start + lc_load * (percent % 100))  # начальное значение плюс процент помноженный на шаг лоадкейса от максимальной нагрузки
                else:
                    tp_list.append(lc.max_load)        # Если достигнут последний элемент добавляем значение максимальной нагрузки в лоадкейсе
            start = lc.max_load                        # Старт нового лоадкейса от максимума предыдущего  
            tp_list = sorted(tp_list)                  # Строка не нужна, но пусть будет
            for i in range(len(tp_list)):
                x = len(str(lc.percents[i]).split('.')[1])
                tp_list[i] = f"{tp_list[i]:.{x}f}"
            lc.update_true(tp_list)                    # Обновление для лоадкейса - список строк
    
    def printout(self, print_order: dict = {}):
        _prt_output = ''
        _prt_output += f"JOB: {self.name}\nType: {self.jtype}\n"
# Если параметр print_order отсутствует, тогда проверяем тип джоба и печатаем его целиком.
        if not print_order:
            print("Порядок вывода на печать не задан")
            print(f"Тип работы для вывода результатов: {self.jtype}")
            if self.jtype == 'Static Subcase':
                _prt_output += self.__print_static_all()
            elif self.jtype == 'Non-linear':
                _prt_output += self.__print_nonlinear_all()
        else:
            print("Задан порядок вывода на печать!")
#            print(f"Количество элементов для вывода в print_order: {len(print_order)}")
            _print_order = self.__print_order_check(print_order.copy())
            elements_to_output = len(_print_order)
#            print(f"Количество совпадений с элементами в базе: {elements_to_output}")
            if elements_to_output:
                if self.jtype == 'Static Subcase':
                    _prt_output += self.__print_static_with_order(_print_order)
                if self.jtype == 'Non-linear':
                    _prt_output += self.__print_nonlinear_with_order(_print_order)
            else:
                print("В порядке вывода результатов нет элементов находящихся в базе\n")
                _prt_output += "\n\nNo data to out put\n\n"
                answer = input("Вывести все результаты? y/n\n")
                if answer in ['y', 'Y']:
                    _prt_output = self.printout()
                else:
                    _prt_output += "\n\nNo data to out put\n\n"
        return _prt_output

    def __print_nonlinear_with_order(self, print_order: dict):
        _prt_output = ''
        _prt_output += f"Results: {self.loadcases[0].lc_otype}\n\n"
        for title, element in print_order.items():
            _prt_output += f"{title}: {element}\n"
            _prt_output += f"{'lc%':<16}"
            if self.loadcases[0].true_percents:
                _prt_output += f"{'true %':<16}"
            _prt_output += f"{self.loadcases[0].lc_header}\n"
            for lc in self.loadcases:
                for index, percent in enumerate(lc.percents):
                    _prt_output += f"{str(percent).replace('.',','):<16}"
                    if lc.true_percents:
                        _prt_output += f"{str(lc.true_percents[index]).replace('.',','):<16}"
                    for i in lc.data[percent][element]:
                        _prt_output += f"{str(i).replace('.',','):<16}"
                    _prt_output += '\n'
            _prt_output += '\n'
        return _prt_output
        
    def __print_static_with_order(self, print_order: dict):
        _prt_output = ''
        for lc in self.loadcases:
            _prt_output += f"Loadcase: {lc.lc_name}\n"
            _prt_output += f'Results: {lc.lc_otype}\n\n'
            _prt_output += f"{'Named output':<16}{'Entity ID':<16}{lc.lc_header}\n"
            for k, v in print_order.items():
                for _perc, _data in lc.data.items():           #Перебираем data лоадкейса по процентам
                    _prt_output += f"{k+':':<16}{v:<16}"
                    for i in _data[v]:
                        _prt_output += f"{str(i).replace('.',','):<16}"                        
                _prt_output += '\n'
            _prt_output += '\n'
        return _prt_output
        
    def __print_nonlinear_all(self):
        _prt_output = ''
        _prt_output += f"Results: {self.loadcases[0].lc_otype}\n\n"
        for element in self.all_elements:
            _prt_output += f"Entity ID: {element}\n"
            _prt_output += f"{'lc%':<16}"
            if self.loadcases[0].true_percents:
                _prt_output += f"{'true %':<16}"
            _prt_output += f"{self.loadcases[0].lc_header}\n"
            for lc in self.loadcases:
                for index, percent in enumerate(lc.percents):
                    _prt_output += f"{str(percent).replace('.',','):<16}"
                    if lc.true_percents:
                        _prt_output += f"{str(lc.true_percents[index]).replace('.',','):<16}"
                    for i in lc.data[percent][element]:
                        _prt_output += f"{str(i).replace('.',','):<16}"
                    _prt_output += '\n'
            _prt_output += '\n'
        return _prt_output

    def __print_static_all(self):
        _prt_output = ''
        for lc in self.loadcases:
            _prt_output += f"Loadcase: {lc.lc_name}\n"
            _prt_output += f'Results: {lc.lc_otype}\n\n'
            _prt_output += f"{'Entity ID':<16}{lc.lc_header}\n"
            for _perc, _data in lc.data.items():           #Перебираем data лоадкейса по процентам
                for _elm, _rez in _data.items():
                    _prt_output += f"{_elm:<16}"
                    for i in _rez:
                        _prt_output += f"{str(i).replace('.',','):<16}"
                    _prt_output += '\n'
            _prt_output += '\n'
        return _prt_output
        
    def __print_order_check(self, print_order):
        to_remove = []
        for k, v in print_order.items():
            if v not in self.all_elements:
                to_remove.append(k)
        for i in to_remove:
            print_order.pop(i)
        return print_order
                        
class Loadcase():
    def __init__(self, 
                 name: str = '',
                 output_type: str = '', 
                 header: list = [],
                 percents: list = [],
                 max_load: float = 0,
                 data: dict = {}):
        self.lc_name = name
        self.lc_header = ''.join([f"{i:<16}" for i in header]) #список заголовков результатов объединяем в строку
        self.lc_otype = output_type
        self.max_load = max_load
        self.percents = sorted(percents)
        self.data = data
        self.true_percents = []
        
    def update_true(self, tp_list):
        self.true_percents = tp_list    