import re
import sys

import psycopg2
import requests

import parse_sites.custom_scripts.list_of_values as list_of_values
import parse_sites.custom_scripts.normalize_address as normalize_address
from parse_sites.parse_sites.settings import DATABASES


class AddressAnalizeObjectsData(object):
    hostname = DATABASES['default']['HOST']
    username = DATABASES['default']['USER']
    password = DATABASES['default']['PASSWORD']
    database = DATABASES['default']['NAME']
    connection = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)
    connection.autocommit = True
    cur = connection.cursor()

    def __init__(self, parce_table, parce_date):
        super(AddressAnalizeObjectsData, self).__init__()
        if parce_table and parce_date:
            self.table = parce_table
            self.parse_date = parce_date
            self.main_requests()
        else:
            sys.exit('нет входных данных')

    def main_requests(self):
        request = """select address, code, description, cost_object, total_area from {0} 
                                                where parse_date >= '{1}' and code >= 4824 order by code"""

        self.cur.execute(request.format(self.table, self.parse_date))
        self.address_list = self.cur.fetchall()
        self.cur.execute('select locality_name, district from address_book.locality_names order by code')
        self.locality_list = self.cur.fetchall()
        self.cur.execute('select street_name, type_street from address_book.streets_names order by code')
        self.streets_list = self.cur.fetchall()
        self.cur.execute('select city_name, district_code from address_book.cities_names order by code')
        self.cities_list = self.cur.fetchall()
        self.main_analize()

    def request_for_take_coordinates(self, fix_address_for_api, item_house, id_object):
        """
            функция для получения координат из сформированного адреса, сначала через яндекс АПИ, если не обнаружен,
            то передать на Google API, если не обнаружено, то вернуть пустую строку.
        """
        if fix_address_for_api:
            self.cur.execute(
                'select coordinate_latitude, coordinate_longitude from {0} where id = {1}'.format(self.table,
                                                                                                  id_object))
            coordinates = self.cur.fetchone()
            longitude = coordinates[1]
            latitude = coordinates[0]
            if longitude and latitude:
                return (latitude, longitude)

            api_url = 'https://geocode-maps.yandex.ru/1.x/?'  # формирование УРЛ геокодера
            params = dict(  # указание параметров с которыми вернется ответ
                format='json',
                geocode=fix_address_for_api
            )
            try:
                request = requests.get(api_url, params=params).json()  # получение ответа и преобразование его в json
                # data = json.loads(request)
                if request['response']['GeoObjectCollection']['featureMember']:
                    data = (request['response']['GeoObjectCollection']['featureMember'][0])
                    if data:
                        coordinates = ''.join(data['GeoObject']['Point']['pos']).split(' ')
                        if not item_house:
                            longitude = coordinates[0]
                            latitude = coordinates[1]
                        else:
                            longitude = coordinates[0]
                            latitude = coordinates[1]
                    else:
                        api_url = 'https://maps.googleapis.com/maps/api/geocode/json?'  # формирование УРЛ геокодера
                        params = dict(  # указание параметров с которыми вернется ответ
                            address=fix_address_for_api,
                            key='AIzaSyBXww-W_CJma2rTgJjtCqglSkf8NHnv-k4',
                            language='ru'
                        )
                        request = requests.get(api_url,
                                               params=params).json()  # получение ответа и преобразование его в json
                        if request['results'] == []:
                            print('nobody')
                        else:
                            if request['results'][0]['geometry']['location']:
                                # print(request['results'][0]['geometry']['location'])
                                formated_address = (request['results'][0]['formatted_address'])
                                if not item_house:
                                    longitude = request['results'][0]['geometry']['location']['lng']
                                    latitude = request['results'][0]['geometry']['location']['lat']
                                else:
                                    longitude = request['results'][0]['geometry']['location']['lng']
                                    latitude = request['results'][0]['geometry']['location']['lat']
                                    # print('долгота: ', longitude, 'широта: ', latitude)
                                    print('сформированный адрес google: ', formated_address)
            except:
                print('ошибка данных')
            return (latitude, longitude)

    def address_normalization(self, address):
        """
            проверка условий на наличие городского района в запросе (чтобы избежать его как название улицы),
            также удаление ненужной информации, мешающей разбору адреса
        """
        # сравнение и преобразование сопадений символов русской и английской раскладок
        translating = str.maketrans(list_of_values.maketrans_eng, list_of_values.maketrans_rus)
        fix_address_rus = str(address[0]).translate(translating)

        fix_address = re.sub('\\bном\\b|\\bномер\\b', '№', fix_address_rus, flags=re.IGNORECASE)
        fix_address = fix_address.replace('  ', ' ')  # бывают двойные пробелы

        for problem in list_of_values.list_problem_names:
            fix_address = re.sub('\\b{}\\b'.format(problem), ' ', fix_address, flags=re.IGNORECASE)  # экранировал . , /

        "преобразование ориентиров в названия близлежащих улиц(по словарю)"
        for list_reference_values in list_of_values.list_values_from_coordinated.items():
            for reference in list_reference_values[1]:
                if re.search('\\b{}\\b'.format(reference), fix_address, flags=re.IGNORECASE):
                    fix_address = re.sub('\\b{}\\b'.format(reference), list_reference_values[0], fix_address,
                                         flags=re.IGNORECASE)
                    break

        "проверка на неправильное название улиц(по словарю)"
        for list_error_in_street in list_of_values.list_errors_in_street.items():
            for error_in_street in list_error_in_street[1]:
                if re.search('\\b{}\\b'.format(error_in_street), fix_address, flags=re.IGNORECASE):
                    fix_address = re.sub('\\b{}\\b'.format(error_in_street), list_error_in_street[0], fix_address,
                                         flags=re.IGNORECASE)
                    break

        "проверка на ошибки в названиях (по словарю), если есть совпадение, то заменить ошибочно написанное на правильное"
        for list_error_in_word in list_of_values.list_errors_in_words.items():
            for error_in_word in list_error_in_word[1]:
                if re.search('\\b{}\\b'.format(error_in_word), fix_address, flags=re.IGNORECASE):
                    fix_address = re.sub('\\b{}\\b'.format(error_in_word), list_error_in_word[0], fix_address,
                                         flags=re.IGNORECASE)
                    break

        fix_address = re.sub('\([^()]*\)', '', fix_address)

        search_addr = re.findall('(?<=\d){1,2}\s?[аяийь]{1,2}\s?(?=[А-Яа-я]{3,})', fix_address, flags=re.IGNORECASE)
        if search_addr:
            fix_address = re.sub('(?<=\d)[аяийь]{1,2}', '-' + search_addr[0].strip(), fix_address, flags=re.IGNORECASE)

        for urban_area in list_of_values.urban_areas:
            if re.search('\\b{}\\b'.format(urban_area), fix_address, flags=re.IGNORECASE):
                """
                    реверс строки по наличию городского района:
                    пример ул. Дарвина 3/16/55 КИРОВСКИЙ Астрахань', 29 преобразуется в список с делением по району, 
                    затем меняется местами: астрахань ул. дарвина 3/16/55
                """
                if re.search('\\bАстрахань$', fix_address, flags=re.IGNORECASE):
                    string_list = str(fix_address.lower()).split(urban_area.lower())[::-1]
                    string_reverse = ' '.join(string_list)
                    return string_reverse, False
                fix_address = re.sub('\\b{}\\b'.format(urban_area), '', fix_address, flags=re.IGNORECASE)
                return fix_address, urban_area

        return fix_address, False

    def split_address(self, address, locality):
        """
            деление адреса на 2 части: до названия населенного пункта и после
        """
        fix_address_split = self.address_normalization(address)  # передача на нормализацию
        lst = re.split('\\b%s\\b' % locality[0], fix_address_split[0], flags=re.IGNORECASE)
        if len(lst) > 1:
            value = lst[1]
        else:
            value = lst[0]
        return value

    def take_address_locality(self, addr, loc):
        """
            получение названия населенного пункта и передача на обрезку, если названия нет
            или название содержит городской район, то вернуть False
            (при наличии городского района происходит передача с поиска нас. пунктов на поиск городов)
        """
        fixed_address = self.address_normalization(addr)
        for urban in list_of_values.urban_areas:
            if urban.lower() in str(addr[0]).lower():
                return False

        if re.search('\\b%s\\b' % loc[0], fixed_address[0], flags=re.IGNORECASE):
            locality_value = self.split_address(addr, loc)
            self.cur.execute('select district_name from address_book.districts_names where code = {0}'.format(loc[1]))
            district_name = self.cur.fetchone()
            return [loc[0], locality_value, district_name, ]
        return False

    def take_street(self, street, street_value_search):
        """
            поиск названия улицы. Если название найдено и оно имеет значение из словарей list_of_prefix_street
            и list_of_words_in_prefix_street (списки сокращений для первый, второй и т.д.), то происходит
            обработка и преобразование названия улицы с учетом этих сокращений, иначе просто вернуть название улицы
        """
        # if 'бабаевского' in str(value).lower():  # иправление Бабаевского как улицы
        #     return False
        if re.search('\\b{0}\\b|\\b{0}\d+\w'.format(street[0]), street_value_search, flags=re.IGNORECASE):
            fixed_street = street[0]
            if re.search('\\b%s\\b' % street[1], street_value_search, flags=re.IGNORECASE) and street[1] != 'улица':
                fixed_street = street[0] + ' ' + street[1]
            """
                разделение на 2 части, до названия улицы и после, 
                с передачей второй половины для определения номера дома
            """
            value_after_street = street_value_search.lower().split(str(street[0]).lower())
            """
                проверка на содержание префиксов: первый, 1-ый и преобразование их в 1-й...
            """
            for prefix_street in list_of_values.list_of_prefix_street:
                for item_prefix in list_of_values.list_of_words_in_prefix_street.keys():
                    value_of_list_items_prefix = list_of_values.list_of_words_in_prefix_street.get(item_prefix)
                    if re.search('\\b{0}\\b {1}\\b'.format(item_prefix + prefix_street, fixed_street),
                                 street_value_search, flags=re.IGNORECASE) \
                            or re.search('\\b{1} \\b[а-яА-Я]{{3,7}}{0}\\b'.format(prefix_street, fixed_street),
                                         street_value_search, flags=re.IGNORECASE) \
                            or re.search(
                        '\\b{0} {1}\\b'.format(value_of_list_items_prefix + '-' + prefix_street[1:], fixed_street),
                        street_value_search, flags=re.IGNORECASE):
                        street = value_of_list_items_prefix + '-' + prefix_street[1] + ' ' + fixed_street
                        return street, value_after_street[1]

                    value_street = re.search('\\b\d{1,2}-%s' % prefix_street, street_value_search, flags=re.IGNORECASE)
                    if value_street:
                        """
                         если значение длиннее 4х симолов (пример 22-ая Пархоменко), то по перебору символов в строке
                         искать каждый 4ый символ и удалять (для преобразования в 22-я Пархоменко) иначе удалять 
                         каждый 3ий символ для аналогичного преобразования
                        """
                        if len(value_street.group(0)) > 4:
                            fixed_street_group = ''.join(
                                value_street.group(0)[i:i + 3] for i in range(0, len(value_street.group(0)), 4))
                            street = fixed_street_group + ' ' + fixed_street
                            return street, value_after_street[1]
                        else:
                            fixed_street_group = ''.join(
                                value_street.group(0)[i:i + 2] for i in range(0, len(value_street.group(0)), 3))
                            street = fixed_street_group + ' ' + fixed_street
                            return street, value_after_street[1]
            if len(value_after_street) > 1:
                return fixed_street, value_after_street[1]
            else:
                return fixed_street, value_after_street[0]

    def take_address_city(self, addr):
        """
            получение названия города (сравнение со списком городов области)
        """
        city_found = ''
        value = ''
        fix_address_city = self.address_normalization(addr)
        district_name = ('',)

        for city in self.cities_list:
            if re.search('\\b%s\\b' % city[0], fix_address_city[0], flags=re.IGNORECASE):
                if city[1]:
                    self.cur.execute(
                        'select district_name from address_book.districts_names where code = {0}'.format(city[1]))
                    district_name = self.cur.fetchone()
                lst = str(fix_address_city[0]).lower().split(city[0].lower())
                city_found = city[0]
                if len(lst) > 1:
                    if len(lst) > 2:
                        if lst[2]:
                            value = lst[2]
                    else:
                        if lst[1]:
                            value = lst[1]
                else:
                    value = lst[0]
        return city_found, value, (district_name[0],)  # вернуть нас пункт, срез после нас пункта, областной район

    def take_house_address(self, street_address):
        """
            поиск номера дома по переданному значению, отсеченному после названия улицы,
            если найдено совпадение, вплоть до корпуса, то передать значение найденной группы
            в основную функцию, т.к. проверка на наличие адреса есть в основной функции после проверки на
            наличие улицы, то проверять возвращаемое значение нет необходимости
        """
        house_search = re.compile(
            '\\b\d+\s?[корпус]{1,6}\s?\s?\d+|\\b\d+\s?[а-яА-Я]{1}$|\\b\d+$|\\b\d+\\b|\\b[Дд]\.?\s?\d+\\b')
        house_address = house_search.search(str(street_address).strip())  # \\b\d+\s?[корпус]{1, 7}\s?\d{1,2}$
        if house_address:
            if re.search('\d+ \d+', str(street_address).strip()):
                fix_house = re.search('\d+ \d+', str(street_address).strip())
                fix_house = str(fix_house.group(0)).split(' ')
                return fix_house[0].lower().replace(' ', '').replace('д', '')
            else:
                return house_address.group(0).lower().replace(' ', '').replace('д', '')
        return ''

    def create_status_from_address(self, value_address, street, house):
        """
            статусы для состояния адресов:
            0 - до дома
            1 - до улицы
            2 - до нас. пункта/города
            3 - нет совпадений
        """
        if value_address[0]:
            if street:
                if house:
                    return 0
                return 1
            return 2
        return 3

    def formatted_address_for_api_request(self, district, locality, street, house):
        if district and locality:
            district = '{0} район'.format(district)
            address_for_api = [district, locality.strip(), street.strip(), str(house).strip(), ]
            formatted_list_for_api = list(filter(None, address_for_api))
            formatted_address_for_api = 'Астраханская область, ' + ', '.join(formatted_list_for_api)
            return formatted_address_for_api
        else:
            for city in list_of_values.list_of_cities:
                if locality == city:
                    if street:
                        address_for_api = [district, locality.strip(), street.strip(), str(house).strip(), ]
                        formatted_list_for_api = list(filter(None, address_for_api))
                        formatted_address_for_api = 'Астраханская область, ' + ', '.join(formatted_list_for_api)
                        return formatted_address_for_api
                    return None
            return None

    def description_address(self, description, address):
        """
            поиск названия населенного пункта в детальном описании если не обнаружен в адресе
        """
        if description:
            description_list = (description,)
            for locality in self.locality_list:
                problem_item = False
                fix_value_description = self.take_address_locality(description_list, locality)
                if fix_value_description:
                    for problem in list_of_values.list_problem_names:
                        if fix_value_description[0] == problem:
                            problem_item = True
                            break
                    if problem_item:
                        continue  # пропуск итерации
                    else:
                        "удаление из списка элемента с описанием, т.к. будет пытаться искать в нем улицу"
                        fix_address_from_city = self.take_address_city(address)  # для получения улицы из адреса объекта
                        fix_value_description.pop(1)
                        if len(fix_address_from_city) > 1:
                            fix_value_description.insert(1, fix_address_from_city[1])
                        else:
                            fix_value_description.insert(1, '')
                        "вернуть откорректированный список"
                        return fix_value_description
        return False

    def cad_num_from_description(self, description):
        """
            поиск кадастрового номера в детальном описании объекта
        """

        cad_num_f = re.search('\\b\d{2}\s?:\s?\d{1,2}\s?:\s?\d{6}\s?:\s?\d+\\b', str(description), flags=re.IGNORECASE)
        if cad_num_f:
            fixed_cad_num = cad_num_f.group(0).replace(' ', '')
            return fixed_cad_num
        else:
            return None

    def area_calculation(self, cost, total_area):
        """
         функция по вычислению стоимости за вкадратный метр и присвоению статуса:
         0 - все в порядке
         1 - нет цены
         2 - нет площади
         3 - нет обоих значений
         4 - ошибка в вычислении
         5 - аномально высокая стоимость за кв. метр
        """
        if not cost and not total_area:
            status_area = 3
            return status_area, 0

        if cost:
            if not total_area or total_area == '':
                status_area = 2
                return status_area, 0

        if total_area:
            if not cost or cost == '':
                status_area = 1
                return status_area, 0
        try:
            cost = float(re.sub('[^0-9.,]', '', str(cost)).replace(' ', '').strip())
            area = float(re.sub('[^0-9.,]', '', str(total_area)).replace(' ', '').strip())
            analog_1price = float(cost) / float(area)
            if len(str(round(analog_1price, 2))) >= 10:
                status_area = 5
                return status_area, 0
            status_area = 0
        except:
            status_area = 4
            print('не соответствует формату')
            return status_area, 0
        return status_area, round(analog_1price, 2)

    def update_to_db(self, id_object, district, locality, street, house, status, cad_num_from_description, status_area,
                     analog_1price):
        """
            сохранение в базу данных
        """
        # создание статуса для кадастрового номера если он взят из описания объекта
        cad_status = 3
        if cad_num_from_description:
            cad_status = 2  # кадастровый номер взят из объекта

        update_request = """update {0} set (region, locality, street, house,
                            cad_status, analog_1price) = 
                            ('{1}', '{2}', '{3}', '{4}', {5}, {6}) where code = '{7}'
                        """.format(self.table, district, locality, street, house, cad_status, analog_1price, id_object)

        update_request_without_coordinate = """update {0} set (region, locality, street, house, 
                                                cad_status, analog_1price) = 
                            ('{1}', '{2}', '{3}', '{4}', {5}, {6}) where id = '{7}'
                        """.format(self.table, district, locality, street, house,
                                   cad_status, analog_1price, id_object)

        self.cur.execute(update_request)
        self.connection.commit()

    def main_analize(self):
        """
            если нас.пункт есть в списке то обработать и вернуть из функции
            иначе если значение вернулось нулевым, то искать название города,
            если город обнаружен то передать управление на установку названия города, затем поиск улицы...
            если передается в locality то возвращает, также, номер областного района из каталога (value_address > 2)
        """
        count = 0
        for address in self.address_list:
            address = [addr for addr in address]  # преобразование из кортежа в список
            value_address = ''
            street_value = ''
            house = ''
            district = ''
            coordinates = ('', '')
            cad_num = self.cad_num_from_description(address[2])

            for locality in self.locality_list:
                problem_item = False  # ключ для проблемных наименований
                if re.search('\\b%s [раийон-]{3,6}\\b' % str(locality[0]), str(address[0]),
                             flags=re.IGNORECASE):  # исключение района типа Володарский в попадание в нас пункт
                    without_district_address = str(address[0]).lower().replace(str(locality[0]).lower(), '')
                    address.pop(0)
                    address.insert(0, without_district_address)
                fix_value = self.take_address_locality(address, locality)
                if fix_value:
                    """
                    проверка на совпадение со списком проблемных названий, если есть совпадение, то ключ problem_item
                    переходит в True и итерация locality пропускается
                    """
                    for problem in list_of_values.list_problem_names:
                        if fix_value[0] == problem:
                            problem_item = True
                            break
                    if problem_item:
                        continue  # пропуск итерации
                    else:
                        value_address = fix_value
                        break

            "если нет в адресе, то искать в детальном описании объекта (для земельных участков)"
            if self.table == 'land_plot':
                if not value_address:
                    value_address = self.description_address(address[2], address)

            "если не найден выше, то искать в списке городов"
            if not value_address:
                value_address = self.take_address_city(address)
            "если после split_address есть вторая половина, то искать в ней улицу по каталогу"
            if value_address[1]:
                fix_street_value = value_address[1].replace(',', ' ').strip()
                for street_val in self.streets_list:
                    street_address = self.take_street(street_val, fix_street_value)
                    if street_address:
                        street_value = street_address[0]
                        "если после split_address есть вторая половина, то искать в ней номер дома"
                        if street_address[1]:
                            house = self.take_house_address(street_address[1])
                            break
                        else:
                            break
            if len(value_address) > 2:
                district = value_address[2][0]

            status = self.create_status_from_address(value_address, street_value, house)  # присвоение статуса по адресу
            print('-----------------------------------------------------------------')
            print('статус: ', status, 'id:', address[1], 'район: ', district, 'нас пункт: ', value_address[0].strip(),
                  'улица: ', street_value.strip(), 'дом: ', str(house).strip())
            print(address[0])
            formatted_address_for_api = self.formatted_address_for_api_request(district, value_address[0].strip(),
                                                                               street_value.strip(), str(house).strip())

            # if formatted_address_for_api:
            #     coordinates = self.request_for_take_coordinates(formatted_address_for_api, str(house).strip(), address[1])
            list_area = self.area_calculation(address[3], address[4])  # формат (статус_площади, стоимость за кв метр)
            self.update_to_db(address[1], district, value_address[0], street_value, house, status, cad_num,
                              # coordinates
                              list_area[0], list_area[1])
            if not cad_num:
                normalize_address.normalizeAddress(self.table, address[1], self.cur,
                                                   self.connection)  # присвоение кадастрового номера из базы
            count += 1
        print(count)


if __name__ == '__main__':
    table = 'main_parser_datamodel'
    if table:
        AddressAnalizeObjectsData(table, '2019-01-01')
    else:
        print('не выбрана таблица для работы')
