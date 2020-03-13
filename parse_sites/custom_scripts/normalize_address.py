import re

import psycopg2
from pyproj import Proj


class normalizeAddress(object):
    # user_type_value = None
    # type_table = ''

    def __init__(self, type_table=None, id_object=None, cursor=None, connection=None):
        super(normalizeAddress, self).__init__()
        # self.connect_to_db()
        self.type_table = type_table
        self.id_object = id_object
        self.cur = cursor
        self.connection = connection

        if self.type_table:
            self.take_coordinate()
        else:
            print('не выбрана таблица для записи')

    def take_coordinate(self):  # сбор координат из базы данных
        self.cur.execute(
            "update {0} set cad_num = '{1}' where code = {2}".format(self.type_table, '', self.id_object))
        self.connection.commit()
        self.cur.execute('SELECT coord_point code FROM {0} WHERE code = {1}'.format(
            self.type_table, self.id_object))

        coordinate = self.cur.fetchone()
        if coordinate == ('', '', self.id_object):
            print('координата остутствует')
        elif coordinate is None:
            print('координата остутствует')
        elif coordinate == (None, None, self.id_object):
            print('координата остутствует')
        elif coordinate == ('Null', 'Null', self.id_object):
            self.cur.execute(
                """update {0} set (coordinate_latitude, coordinate_longitude) =
                ('{1}', '{2}') where id = {3}""".format(self.type_table, '', '', self.id_object))  # self.type_table
            self.connection.commit()
            print('изменено на пустое значение')
        else:
            self.modify_coordinate_to_utm(coordinate[0], self.id_object)

    def take_cad_num(self, coordinate_utm, id_item):  # изъятие кадастровых номеров из базы данных по координатам
        host = '192.168.50.70'
        user = 'postgres'
        password = '88005553535'
        datab = 'GKO_GIS_01'
        connection = psycopg2.connect(host=host, user=user, password=password, dbname=datab)
        cur = connection.cursor()  # (cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""with pad_meta as(select cad_num, ST_Within(
                        ST_GeomFromText('POINT{0}',3857),ST_SetSRID(ST_GEometryN(geom,1),3857)) 
                        from gis_land_cs) select * from pad_meta where ST_Within=True;""".format(coordinate_utm))
        coord = cur.fetchall()
        string_coord = ''.join(map(str, coord))
        self.fixed_coord = re.sub('[a-zA-Z,()\']', '', string_coord).strip()
        if not self.fixed_coord:
            cur.execute("""with pad_meta as(select cad_num, ST_Within(
                                       ST_GeomFromText('POINT{0}',3857),ST_SetSRID(ST_GEometryN(geom,1),3857)) 
                                       from gis_land_mzu_cs) select * from pad_meta where ST_Within=True;""".format(
                coordinate_utm))
            coord_land_mzu = cur.fetchall()
            if len(coord_land_mzu) > 1:  # при совпадении больше одного (создание массива)
                string_coord_kvartal = ''.join(map(str, coord_land_mzu[-1]))
            else:
                string_coord_kvartal = ''.join(map(str, coord_land_mzu))
            self.fixed_coord_kvartal = re.sub('[a-zA-Z,\s()\']|([\d]+\(\))', '', string_coord_kvartal)

            if not self.fixed_coord_kvartal:  # если нет кад номера, то брать номер квартала
                cur.execute("""with pad_meta as(select cad_num, ST_Within(
                                ST_GeomFromText('POINT{0}',3857),ST_SetSRID(ST_GEometryN(geom,1),3857)) 
                                from gis_kk_cs) select * from pad_meta where ST_Within=True;""".format(coordinate_utm))
                coord_kvartal = cur.fetchall()
                print(coord_kvartal)
                if len(coord_kvartal) > 1:  # при совпадении больше одного (создание массива)
                    for coord_one in coord_kvartal:
                        if not re.search(':000000$', coord_one[0]):  # исключить кад номера с окончанием :000000
                            string_coord_kvartal = ''.join(map(str, coord_one))
                else:
                    string_coord_kvartal = ''.join(map(str, coord_kvartal))

                self.fixed_coord_kvartal = re.sub('[a-zA-Z,\s()\']', '', string_coord_kvartal)
                self.save_to_DB(self.fixed_coord_kvartal, id_item)
                if not self.fixed_coord_kvartal:
                    print('нет в базе данных')
        else:
            self.save_to_DB(self.fixed_coord, id_item)
        cur.close()
        connection.close()

    def modify_coordinate_to_utm(self, coord, id_item):  # переопределение координат Яндекс карты в Меркатор
        # lonlat = Proj('+proj=merc +lon_0=0 +k=1 +x_0=30 +y_0=40 +ellps=WGS84 +datum=WGS84 +units=m +no_defs')
        # lonlat = Proj('+proj=utm +zone=42, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs')
        # lonlat = Proj(init='epsg:3395')
        # spherc = Proj(proj='utm', zone=39, ellps='WGS84', datum='WGS84', units='m', preserve_units=True)
        ellipse_mercator = Proj("epsg:3857")
        # lat, lon = float(coordinate[0]), float(coordinate[1])
        if coord:
            c = coord.replace("POINT(", "").replace(")", "").split(",")
        else:
            c = (0, 0,)

        try:
            utm = ellipse_mercator(c[0], c[1])
        except TypeError:
            print('error type coord')
            utm = ellipse_mercator(0, 0)

        # sm = transform(lonlat, spherc, lon, lat)
        self.fixed_utm = str(utm).replace(',', '')
        self.take_cad_num(self.fixed_utm, id_item)

    def save_to_DB(self, cad_number, id_item):  # запись кадастровых номеров в базу данных
        cad_status = self.get_status_cad_num()
        print('готовое значение: ', cad_number)

        request = "update {0} set (cad_num, cad_status) = ('{1}', {2}) WHERE code = {3}".format(self.type_table,
                                                                                                cad_number, cad_status,
                                                                                                id_item)
        # self.cur = self.connection.cursor()  # (cursor_factory=psycopg2.extras.DictCursor)

        self.cur.execute(request)
        self.connection.commit()

    def get_status_cad_num(self):
        """
            создание статуса для кадастрового номера:
            0 - все до дома
            1 - все до квартала
            2 - кадастровый номер взят из описания объекта (на этапе нормализации адресов для земельных участков)
            3 - нет кад номера
        """
        if self.fixed_coord:
            status = 0
        else:
            if len(self.fixed_coord_kvartal) > 1:
                if self.fixed_coord_kvartal[0]:
                    status = 1
                else:
                    status = 2
            else:
                status = 3
        return status


if __name__ == '__main__':
    normalizeAddress()

# групповое присваивание
# def take_coordinate(self):  # сбор координат из базы данных
#     self.cur.execute("SELECT id FROM {0} where id = '{1}';".format(self.type_table, self.id_object))  # SELECT id FROM {0} order by id;
#     ids = self.cur.fetchall()
#     print(ids)
#     for id in ids:
#         for id_num in id:
#             print(id_num)
#             self.cur.execute(
#                 "update {0} set cad_num = '{1}' where id = {2}".format(self.type_table, '', id_num))  # self.type_table
#             self.connection.commit()
#             self.cur.execute('SELECT coordinate_latitude, coordinate_longitude, id FROM {0} WHERE id = {1}'.format(self.type_table, id_num)) #self.type_table
#             coordinate = self.cur.fetchone()
#             print(coordinate)
#             if coordinate == ('', '', id_num):
#                 print('координата остутствует')
#             elif coordinate is None:
#                 print('координата остутствует')
#             elif coordinate == (None, None, id_num):
#                 print('координата остутствует')
#             elif coordinate == ('Null', 'Null', id_num):
#                 self.cur.execute(
#                     """update {0} set (coordinate_latitude, coordinate_longitude) =
#                     ('{1}', '{2}') where id = {3}""".format(self.type_table, '', '', id_num))  # self.type_table
#                 self.connection.commit()
#                 print('изменено на пустое значение')
#             else:
#                 print(coordinate)
#                 self.modify_coordinate_to_utm(coordinate[0], coordinate[1], id_num)
#     self.cur.close()
#     self.connection.close()
