import json
import re
import datetime
import unicodedata


def get_name_object(text, loader_context):
    return _replace_chars(text)


def get_description(text, loader_context):
    fixed_text = re.sub(r'<.*?>', '', text).replace("'", '"').replace('₽', 'Руб')
    return _replace_chars(fixed_text)


def get_date_announcement(text, loader_context):
    date_time = _replace_chars(text).replace(' размещено ', '').replace(' в ', '')

    month = re.sub('[^а-я]', '', date_time)  # удалить все кроме названия месяца
    month_table = {'1': 'января', '2': 'февраля', '3': 'марта', '4': 'апреля', '5': 'мая', '6': 'июня',
                   '7': 'июля', '8': 'августа', '9': 'сентября', '10': 'октября', '11': 'ноября',
                   '12': 'декабря'}
    if month == 'сегодня':  # date_time[:7]
        # return datetime.datetime.now().strftime('%Y-%m-%d')
        return None
    elif month == 'вчера':  # date_time[:5]
        date_time_yesterday = datetime.date.today() - datetime.timedelta(1)
        date_time_yesterday = date_time_yesterday.strftime('%Y-%m-%d')
        # return date_time_yesterday
        return None
    else:
        for date_i in month_table.items():
            if month == date_i[1]:
                try:
                    current_date_month = re.sub(date_i[1], date_i[0], date_time)
                    if re.search('[0-9]{4}', date_time):
                        current_date = str(current_date_month).strip()
                        date_time_earlier = datetime.datetime.strptime(current_date, '%d %m %Y').strftime(
                            '%Y-%m-%d')
                        print('сформированная дата размещения за прошлый год: ', date_time_earlier)
                        return date_time_earlier
                    else:
                        current_date = str(datetime.datetime.now().strftime('%Y') + ' ' + current_date_month).strip()
                        date_time_earlier = datetime.datetime.strptime(current_date, '%Y %d %m').strftime(
                            '%Y-%m-%d')
                        print('сформированная дата размещения: ', date_time_earlier)
                        return date_time_earlier
                except Exception as e:
                    print('ошибка в формировании даты: ', e)
                    return None


# date for n30
def get_n30_date(text, loader_context):
    if loader_context:
        if loader_context.get("remove_date_chars"):
            date = re.findall(loader_context.get("remove_date_chars"), text)
            if len(date) > 1:
                date_time = datetime.datetime.strptime(date[0], '%d-%m-%Y').strftime(
                            '%Y-%m-%d')
                return date_time
    return None


def get_coord_point(text, loader_context):
    if len(text) > 3:
        return "POINT({0}, {1})".format(text[2], text[3])
    return None


# with special for domofond
def get_total_area(text, loader_context):
    # clear_text = re.findall('([0-9.,]+)', text)
    # print("===============================")
    # print(clear_text)
    # print(text)
    # print("===============================")
    # if len(clear_text) > 1:
    #     if loader_context:
    #         if loader_context.get('is_house') == 'False':
    #             return _area_to_square_meters(clear_text[0])
    #         elif loader_context.get('is_house') == 'True':
    #             return _area_to_square_meters(clear_text[1])
    #         else:
    #             return None
    return _area_to_square_meters(text)


#for domofond
def get_floor(text, loader_context):
    clear_text = re.findall('([0-9]+)', text)
    if len(clear_text) > 1:
        if loader_context:
            if loader_context.get('is_floor') == 'yes':
                return clear_text[0]
            elif loader_context.get('is_floor') == 'no':
                return clear_text[1]
    return clear_text[0]


def string_replace_chars(text, loader_context):
    return _replace_chars(text)


def _replace_chars(text):
    text.strip('; ')
    return unicodedata.normalize('NFKD', text)


def _area_to_square_meters(text):
    value = re.sub('[^0-9.,]', '', text).replace(",", ".").strip('.,; ')
    if re.search('сот\.', _replace_chars(text)):
        total_area = float(value) * 100
    elif re.search('га\.', text):
        total_area = float(value) * 10000
    else:
        total_area = float(value)
    return round(total_area, 2)


#for n30
def get_n30_address(text, loader_context):
    split_address = text.split(',')
    return _replace_chars(''.join(split_address[1:]))


# for consalting
def get_date_consalting(text, loader_context):
    fix_date_number = ''.join(text).replace('\n', '').replace('Добавлено: ', '').strip()
    month = re.sub('[^а-яА-Я]', '', fix_date_number)
    month_table = {'1': 'Января', '2': 'Февраля', '3': 'Марта', '4': 'Апреля', '5': 'Мая', '6': 'Июня', '7': 'Июля',
                   '8': 'Августа', '9': 'Сентября', '10': 'Октября', '11': 'Ноября', '12': 'Декабря'}
    for date_i in month_table.items():
        if month == date_i[1]:
            current_date_month = re.sub(date_i[1], date_i[0], fix_date_number)
            # current_date = datetime.datetime.now().strftime('%Y') + ' ' + current_date_month
            date_time_earlier = datetime.datetime.strptime(current_date_month, '%d %m %Y').strftime(
                '%Y-%m-%d')  # преобразование даты в форму
            return date_time_earlier
    return None


def get_consalting_cost_type(text, loader_context):
    if str(text).startswith("продажа"):
        return None
    return text

# на случай необходимости выборки из <script>:
# xpath = //head/script[contains(text(), "window.dataLayer")]/text()
# regExp = \[\{.+\}\]