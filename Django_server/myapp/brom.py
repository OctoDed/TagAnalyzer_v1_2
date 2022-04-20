'''
Модуль Бром
Клиентский интеграционный модуль для 1С:Предприятие.

Правообладатель: ООО "ИТВОРКС"
Автор исходного кода: Антон Шаганов (ООО "ИТВОРКС")
Описание и документация: https://brom.itworks.group
По всем вопросам: info@itworks.group; a.shaganov@itworks.group
'''

from abc import ABCMeta
from abc import abstractmethod
from datetime import date, datetime
from enum import Enum, auto
from hashlib import md5
from hashlib import sha1
from requests import Session
from requests.auth import HTTPBasicAuth
from uuid import UUID
from uuid import uuid4
from weakref import WeakKeyDictionary, WeakValueDictionary
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
import os
import re


class ВидГраницы(Enum):
    Включая = auto()
    Исключая = auto()

    Including = Включая
    Excluding = Исключая

class ВидДвиженияБухгалтерии(Enum):
    Дебет = auto()
    Кредит = auto()

    Debit = Дебет
    Credit = Кредит

class ВидДвиженияНакопления(Enum):
    Приход = auto()
    Расход = auto()

    Receipt = Приход
    Expense = Расход

class ВидСчета(Enum):
    АктивноПассивный = auto()
    Активный = auto()
    Пассивный = auto()

    ActivePassive = АктивноПассивный
    Active = Активный
    Passive = Пассивный

class ДопустимаяДлина(Enum):
    Переменная = auto()
    Фиксированная = auto()

    Variable = Переменная
    Fixed = Фиксированная

class ДопустимыЗнак(Enum):
    Любой = auto()
    Неотрицательный = auto()

    Any = Любой
    Nonnegative = Неотрицательный

class ЧастиДаты(Enum):
    Время = auto()
    Дата = auto()
    ДатаВремя = auto()

    Time = Время
    Date = Дата
    DateTime = ДатаВремя

class ВидСравнения(Enum):
    Равно = auto()
    НеРавно = auto()
    Больше = auto()
    БольшеИлиРавно = auto()
    Меньше = auto()
    МеньшеИлиРавно = auto()
    Содержит = auto()
    НеСодержит = auto()
    ВСписке = auto()
    НеВСписке = auto()
    ВИерархии = auto()
    НеВИерархии = auto()

    Equal = Равно
    NotEqual = НеРавно
    Greater = Больше
    GreaterOrEqual = БольшеИлиРавно
    Less = Меньше
    LessOrEqual = МеньшеИлиРавно
    Contains = Содержит
    NotContains = НеСодержит
    InList = ВСписке
    NotInList = НеВСписке
    InHierarchy = ВИерархии
    NotInHierarchy = НеВИерархии

class НаправлениеСортировки(Enum):
    Возрастание = auto()
    Убывание = auto()

    Ascending = Возрастание
    Descending = Убывание

class ОбходРезультатаЗапроса(Enum):
    Прямой = auto()
    ПоГруппировкам = auto()
    ПоГруппировкамСИерархией = auto()

    Linear = Прямой
    ByGroups = ПоГруппировкам
    ByGroupsWithHierarchy = ПоГруппировкамСИерархией

class РежимЗаписиДокумента(Enum):
    Запись = auto()
    ОтменаПроведения = auto()
    Проведение = auto()

    Write = Запись
    UndoPosting = ОтменаПроведения
    Posting = Проведение

class РежимПроведенияДокумента(Enum):
    Неоперативный = auto()
    Оперативный = auto()

    Regular = Неоперативный
    RealTime = Оперативный

class ТипКоллекции(Enum):
    Справочник = auto()
    Документ = auto()
    Перечисление = auto()
    ПланВидовХарактеристик = auto()
    ПланСчетов = auto()
    ПланВидовРасчета = auto()
    Задача = auto()
    БизнесПроцесс = auto()

    Catalog = Справочник
    Document = Документ
    Enum = Перечисление
    ChartOfCharacteristicTypes = ПланВидовХарактеристик
    ChartOfAccounts = ПланСчетов
    ChartOfCalculationTypes = ПланВидовРасчета
    Task = Задача
    BusinessProcess = БизнесПроцесс

class КешМетаданных(metaclass=ABCMeta):

    @abstractmethod
    def ПолучитьЗначение(self, ключ):
        raise NotImplementedError()

    @abstractmethod
    def УстановитьЗначение(self, ключ, значение):
        raise NotImplementedError()

    @abstractmethod
    def Очистить(self):
        raise NotImplementedError()

    @abstractmethod
    def СодержитКлюч(self, ключ):
        raise NotImplementedError()

class УзелМетаданных(metaclass=ABCMeta):
    def __init__(self, корень, родитель, имя, полноеИмя, синоним):
        self.__root = корень
        self.__name = имя
        self.__fullName = полноеИмя
        self.__title = синоним if синоним.strip() else имя
        self.__parent = родитель

        self.__children = Структура()

        if родитель:
            родитель.__children.Вставить(self.__name, self)

        if self.Корень():
            self.Корень().ЗарегистрироватьУзел(self)


    def _clear(self):
        self.__children.Очистить()

    def НайтиПодчиненный(self, имя):
        if self.__children.СвойствоОпределено(имя):
            return self.__children[имя]
        else:
            return None

    def Имя(self):
        return self.__name

    def ПолноеИмя(self):
        return self.__fullName

    def Синоним(self):
        return self.__title

    def Родитель(self):
        return self.__parent

    def Корень(self):
        if not self.__parent:
            return self
        return self.__root

    def Путь(self):
        if not self.Родитель():
            return ""
        if not self.Родитель().Путь().strip():
            return self.Имя()
        return self.Родитель().Путь() + "." + self.Имя()

    def Клиент(self):
        return self.Корень().Клиент()

    def _addNode(self, узел):
        self.__children.Вставить(узел.Имя(), узел)
        self.Корень().ЗарегистрироватьУзел(узел)

    def Найти(self, имя):
        имена = имя.split(".")
        результат = self;
        for текИмя in имена:
            узел = результат.НайтиПодчиненный(текИмя)
            if узел:
                результат = узел
            else:
                return None
        return результат

    def Содержит(self, имя):
        return bool(self.Найти(имя))

    def __iter__(self):
        for key, value in self.__children:
            yield key, value

    def _tryget(self, name):
        return self.НайтиПодчиненный(name)

    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

    def ИменаПодчиненных(self):
        имена = []
        for имя in self.__children.keys():
            имена.append(имя)
        return имена

    def __str__(self):
        return self.__fullName

class ДвумернаяКоллекцияЗначений(metaclass=ABCMeta):
    def __init__(self):
        self.__columns = КоллекцияКолонок(self)

    @property
    def Колонки(self):
        return self.__columns

    @abstractmethod
    def _onColumnRemoved(self, column):
        raise NotImplementedError()

class КонтекстОбъекта:
    a =0

class Ссылка(metaclass=ABCMeta):
    def __init__(self, клиент, типКоллекции, имяКоллекции):
        self.__dict__["_bromClient"] = клиент
        self.__dict__["_collectionType"] = типКоллекции
        self.__dict__["_collectionName"] = имяКоллекции

    @staticmethod
    def ПоПолномуИмениКоллекции(клиент, полноеИмяТипа):
        фрагментыИмени = полноеИмяТипа.strip().split(".")
        if len(фрагментыИмени) == 2:
            raise Exception('Переданный параметр "полноеИмяТип" не соответствует шаблону {ТипКоллекции.ИмяКоллекции}')

        super().__init__(клиент, ТипКоллекции[фрагментыИмени[0]], фрагментыИмени[1])

    def ТипКоллекции(self):
        return self.__dict__["_collectionType"]

    def ИмяКоллекции(self):
        return self.__dict__["_collectionName"]

    def Клиент(self):
        return self.__dict__["_bromClient"]

    def ПолноеИмяТипа(self):
        return self.ТипКоллекции().name + "." + self.ИмяКоллекции()

    def Метаданные(self):
        return self.Клиент().Метаданные.Получить(self.ПолноеИмяТипа())

    def Пустая(self):
        raise NotImplementedError()

    def __eq__(self, other):
        return self.Клиент() == other.Клиент() and self.ТипКоллекции() == other.ТипКоллекции() and self.ИмяКоллекции() == other.ИмяКоллекции()

    def __hash__(self):
        return hash((self.Клиент(), self.ТипКоллекции(), self.ИмяКоллекции()))

class СтрокаДвумернойКоллекцииЗначений(metaclass=ABCMeta):
    def __init__(self, коллекция):
        self.__dict__["__parent"] = коллекция

        self.__dict__["__values"] = {}

    def _onColumnRemove(self, column):
        del(self.__dict__["__values"][column])

    def _tryget(self, name):
        if isinstance(name, КолонкаКоллекцииЗначений):
            return self.__dict__["__values"].get(name)

        column = self.__dict__["__parent"].Колонки.Найти(name)
        if column:
            return self.__dict__["__values"].get(column)
        return None

    def _tryset(self, name, value):
        if isinstance(name, КолонкаКоллекцииЗначений):
            self.__dict__["__values"][name] = value
            return

        column = self.__dict__["__parent"].Колонки.Найти(name)
        if column:
            self.__dict__["__values"][column] = value

    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

    def __setattr__(self, key, value):
        self._tryset(key, value)

    def __setitem__(self, key, value):
        self._tryset(key, value)

    def __iter__(self):
        for column in self.__dict__["__parent"].Колонки:
            yield column.Имя, self.__dict__["__values"].get(column)

class КонтекстОбъекта:
    def __init__(self, ссылка):
        self.__dict__["__reference"] = ссылка
        self.__dict__["__data"] = {}
        self.__dict__["__modifiedFields"] = []
        self.__dict__["__additionalProperties"] = Структура()
        self.__dict__["__isExchangeLoadMode"] = False

    def __getTableSection(self, метаданные):
        времИмя = метаданные.Имя().lower()
        таблЧасть = self.__dict__["__data"].get(времИмя)
        if not таблЧасть:
            таблЧасть = ТабличнаяЧастьКонтекст(self, метаданные)
            self.__dict__["__data"][времИмя] = таблЧасть
        return таблЧасть

    def __addModifiedField(self, name):
        if not name in self.__dict__["__modifiedFields"]:
            self.__dict__["__modifiedFields"].append(name)

    def __установитьЗначенияИзСвойствSOAP(self, properties):
        if properties == None:
            return

        метаданные = self.Метаданные()

        реквизиты = метаданные.Реквизиты
        таблЧасти = метаданные.ТабличныеЧасти

        for property in properties:
            реквизит = реквизиты.НайтиПодчиненный(property.Name)
            if реквизит:
                значение = self.__dict__["__reference"].Клиент().Сериализатор().ИзЗначенияБром(property)
                self.__dict__["__data"][реквизит.Имя().lower()] = значение
                continue

            таблЧастьМета = таблЧасти.НайтиПодчиненный(property.Name)
            if таблЧастьМета:
                значение = self.__dict__["__reference"].Клиент().Сериализатор().ИзЗначенияБром(property)
                табличнаяЧасть = self.__getTableSection(таблЧастьМета)
                if isinstance(значение, ТаблицаЗначений):
                    табличнаяЧасть.Загрузить(значение)
                else:
                    табличнаяЧасть.Очистить()

                табличнаяЧасть._ТабличнаяЧастьКонтекст__setIsModified(True)


    def _записатьДанные(self, режимЗаписиДокумента = РежимЗаписиДокумента.Запись, режимПроведенияДокумента = РежимПроведенияДокумента.Неоперативный):
        сериализатор = self.Клиент().Сериализатор()
        tempObject = сериализатор.ВЗначениеБром(self.__dict__["__reference"])
        tempObject.Property = []
        for key in self.__dict__["__modifiedFields"]:
            значение = self.__dict__["__data"].get(key.lower())
            property = сериализатор.ВЗначениеБром(значение)
            property.Name = key
            tempObject.Property.append(property)

        settings = сериализатор.Фабрика.PostObject_Settings(
            AdditionalProperties=сериализатор.ВЗначениеБром(self.__dict__["__additionalProperties"]),
            ExchangeLoadMode=self.__dict__["__isExchangeLoadMode"],
            DocumentWriteMode=режимЗаписиДокумента.name,
            DocumentPostingMode=режимПроведенияДокумента.name
        )

        returnObject = self.Клиент().SoapКлиент.service.PostObject(tempObject, settings)
        ссылка = сериализатор.ИзЗначенияБром(returnObject)

        self.УстановитьСсылку(ссылка)
        self.__установитьЗначенияИзСвойствSOAP(returnObject.Property)

        self.__dict__["__modifiedFields"].clear()

    @property
    def ДополнительныеСвойства(self):
        return self.__dict__["__additionalProperties"]

    @property
    def РежимЗагрузки(self):
        return self.__dict__["__isExchangeLoadMode"]

    @РежимЗагрузки.setter
    def РежимЗагрузки(self, value):
        self.__dict__["__isExchangeLoadMode"] = bool(value)

    def Клиент(self):
        return self.__dict__["__reference"].Клиент()

    def Метаданные(self):
        return self.__dict__["__reference"].Метаданные()

    def ЭтоНовый(self):
        return self.__dict__["__reference"].Пустая()

    def ТипКоллекции(self):
        return self.__dict__["__reference"].ТипКоллекции()

    def ИмяКоллекции(self):
        return self.__dict__["__reference"].ИмяКоллекции()

    def УстановитьСсылку(self, ссылка):
        if self.__dict__["__reference"] == ссылка:
            return

        if self.ТипКоллекции() != ссылка.ТипКоллекции() or self.ИмяКоллекции() != ссылка.ИмяКоллекции():
            raise ValueError('Тип аргумента "ссылка" не соответствует требуемому типу "{0}".'.format(self.__dict__["__reference"].ПолноеИмяТипа()))

        self.__dict__["__reference"] = ссылка

    def УстановитьПометкуУдаления(self, значение):
        self.ПометкаУдаления = bool(значение)

    def __str__(self):
        return "{0}.{1}".format(super().__str__(), self.ИмяКоллекции())

    def ЗагрузитьДанные(self):
        сериализатор = self.Клиент().Сериализатор()

        settings = сериализатор.Фабрика.GetObject_Settings(
            FieldAutoinclusion=сериализатор.Фабрика.RequestFieldAutoinclusionSettings(
                DefaultFields=True,
                CustomFields=True,
                Tables=True
            )
        )

        refSoap = self.Клиент().SoapКлиент.service.GetObject(
            сериализатор.ВЗначениеБром(self.__dict__["__reference"]),
            settings
        )

        self.Клиент().Контекст()._КонтекстДанных__установитьПредставлениеОбъекта(self.__dict__["__reference"], refSoap.Presentation)
        self.Клиент().Контекст()._КонтекстДанных__установитьЗначенияИзСвойствSOAP(self.__dict__["__reference"], refSoap.Property)

        self.__установитьЗначенияИзСвойствSOAP(refSoap.Property)

        self.__dict__["__modifiedFields"].clear()

    def Записать(self):
        self._записатьДанные()

    def Удалить(self):
        if self.ЭтоНовый():
            raise Exception("Не возможно удалить объект, который является новым.")

        self.Клиент().SoapКлиент.service.DeleteObject(self.Клиент().Сериализатор().ВЗначениеБром(self.__dict__["__reference"]))

        self.Клиент().Контекст().ОчиститьДанныеОбъекта(self.__dict__["__reference"])

    def _tryget(self, name):
        tempName = name.lower()
        if tempName in ["ссылка", "ref"]:
            return self.__dict__["__reference"]

        текМета = self.__dict__["__reference"].Метаданные().Реквизиты.НайтиПодчиненный(name)
        if текМета:
            return self.__dict__["__data"].get(tempName)

        текМета = self.__dict__["__reference"].Метаданные().ТабличныеЧасти.НайтиПодчиненный(name)
        if текМета:
            return self.__getTableSection(текМета)

        return None

    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

    def _tryset(self, name, value):
        tempName = name.lower()
        if tempName in ["ссылка", "ref"]:
            raise Exception('Реквизит "Ссылка" доступен только для чтения.')

        метаданные = self.Метаданные()

        реквизит = метаданные.ТабличныеЧасти.НайтиПодчиненный(name)
        if реквизит:
            raise Exception('Реквизит "{0}" доступен только для чтения.'.format(реквизит.Имя()))

        реквизит = метаданные.Реквизиты.НайтиПодчиненный(name)
        if реквизит:
            self.__dict__["__data"][tempName] = value
            self.__addModifiedField(реквизит.Имя())
            return

        raise Exception('Поле "{0}" не определено.'.format(name))

    def __setattr__(self, key, value):
        self._tryset(key, value)

    def __setitem__(self, key, value):
        self._tryset(key, value)

    def __iter__(self):
        метаданные = self.Метаданные()
        for name in метаданные.Реквизиты.ИменаПодчиненных():
            yield name, self[name]

        for name in метаданные.ТабличныеЧасти.ИменаПодчиненных():
            yield name, self[name]

    def __len__(self):
        метаданные = self.Метаданные()
        return len(метаданные.Реквизиты) + len(метаданные.ТабличныеЧасти)



    @staticmethod
    def ПолучитьКонтекстОбъекта(ссылка):
        if ссылка == None:
            raise ValueError()

        if ссылка.ТипКоллекции() == ТипКоллекции.Справочник:
            return СправочникОбъект(ссылка)
        if ссылка.ТипКоллекции() == ТипКоллекции.Документ:
            return ДокументОбъект(ссылка)
        if ссылка.ТипКоллекции() == ТипКоллекции.ПланВидовХарактеристик:
            return ПланВидовХарактеристикОбъект(ссылка)
        if ссылка.ТипКоллекции() == ТипКоллекции.ПланСчетов:
            return ПланСчетовОбъект(ссылка)
        if ссылка.ТипКоллекции() == ТипКоллекции.ПланВидовРасчета:
            return ПланВидовРасчетаОбъект(ссылка)
        if ссылка.ТипКоллекции() == ТипКоллекции.БизнесПроцесс:
            return БизнесПроцессОбъект(ссылка)
        if ссылка.ТипКоллекции() == ТипКоллекции.Задача:
            return ЗадачаОбъект(ссылка)

        raise Exception()

class ПрограммныйМодуль(metaclass=ABCMeta):
    def __init__(self, клиент, метаданныеМодуля):
        self._bromClient = клиент
        self._moduleMetadata = метаданныеМодуля

class ТабличнаяЧасть:
    def __init__(self, метаданные):
        self.__metadata = метаданные
        self.__rows = []

    def Метаданные(self):
        return self.__metadata

    def Количество(self):
        return len(self.__rows)

    def _addRow(self):
        стр = СтрокаТабличнойЧасти(self)
        self.__rows.append(стр)
        return стр

    def _removeRow(self, row):
        if isinstance(row, int):
            del(self.__rows[row])
        else:
            self.__rows.remove(row)

    def _clear(self):
        self.__rows.clear()

    def _loadData(self, table):
        поляТаблица = table.Колонки.Наименования()
        поляТаблЧасть = self.__metadata.Реквизиты.ИменаПодчиненных()
        общиеПоля = []
        for имя in поляТаблица:
            for имя2 in поляТаблЧасть:
                if имя.lower() == имя2.lower():
                    общиеПоля.append(имя2)

        self.__rows.clear()
        for row in table:
            стр = self._addRow()
            for имя in общиеПоля:
                стр._СтрокаТабличнойЧасти__setValue(имя, row[имя])

    def Выгрузить(self):
        таблица = ТаблицаЗначений()

        именаПолей = self.__metadata.Реквизиты.ИменаПодчиненных()
        for имяПоля in именаПолей:
            таблица.Колонки.Добавить(имяПоля)

        for стр in self.__rows:
            новСтр = таблица.Добавить()
            for колонка in таблица.Колонки:
                новСтр[колонка] = стр[колонка.Имя]

        return таблица

    def __len__(self):
        return len(self.__rows)

    def __getitem__(self, item):
        return self.__rows[item]

    def __contains__(self, item):
        return item in self.__rows

    def __iter__(self):
        for row in self.__rows:
            yield row

    def __str__(self):
        return self.__metadata.ПолноеИмя()

class ОбъектСсылка(Ссылка):
    def __init__(self, клиент, типКоллекции, имяКоллекци, идентификатор):
        super().__init__(клиент, типКоллекции, имяКоллекци)
        self.__dict__["__guid"] = идентификатор

    def УникальныйИдентификатор(self):
        return self.__dict__["__guid"]

    def Пустая(self):
        return self.__dict__["__guid"] == UUID('00000000-0000-0000-0000-000000000000')

    def ПолучитьОбъект(self):
        if self.Пустая():
            raise Exception('Невозможно получить объект пустой ссылки. Воспользуйтесь методом "СоздатьОбъект" модуля менеджера коллекции.')

        контекст = КонтекстОбъекта.ПолучитьКонтекстОбъекта(self)
        контекст.ЗагрузитьДанные()
        return контекст

    def __str__(self):
        представление = self.Клиент().Контекст().ПолучитьПредставлениеОбъекта(self)
        return представление if представление else "{0}: ({1})".format(self.ПолноеИмяТипа(), self.__dict__["__guid"])

    def __eq__(self, other):
        if not isinstance(other, ОбъектСсылка):
            return False

        return self.Клиент() == other.Клиент() and \
               self.ТипКоллекции() == other.ТипКоллекции() and \
               self.ИмяКоллекции() == other.ИмяКоллекции() and \
               self.УникальныйИдентификатор() == other.УникальныйИдентификатор()

    def __hash__(self):
        return hash((self.ТипКоллекции(), self.ИмяКоллекции(), self.УникальныйИдентификатор()))

    def _tryget(self, name):
        return self.Клиент().Контекст().ПолучитьЗначение(self, name)

    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

    def _tryset(self, key, value):
        raise Exception("Поля ссылки доступны только на чтение.")

    def __setattr__(self, key, value):
        self._tryset(key, value)

    def __setitem__(self, key, value):
        self._tryset(key, value)

    def __iter__(self):
        метаданные = self.Метаданные()
        for name in метаданные.Реквизиты.ИменаПодчиненных():
            yield name, self[name]

        for name, meta in метаданные.ТабличныеЧасти.ИменаПодчиненных():
            yield name, self[name]

class КоллекцияМенеджер(ПрограммныйМодуль):
    def __init__(self, клиент, метаданныеМодуля):
        super().__init__(клиент, метаданныеМодуля)

    def __tryget(self, name):
        метаданные = self._moduleMetadata.Найти(name)
        if метаданные:
            return МодульМенеджер(self._bromClient, метаданные)
        return None

    def __getattr__(self, item):
        return self.__tryget(item)

    def __getitem__(self, item):
        return self.__tryget(item)

class МодульМенеджер(ПрограммныйМодуль):
    def __init__(self, клиент, метаданныеМодуля):
        super().__init__(клиент, метаданныеМодуля)

    def _tryget(self, name):
        return lambda *args: self._trycall(name, args)

    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

    def _trycall(self, name, args):
        return self.__dict__["_bromClient"].ВызватьМетодСМассивомПараметров(self._moduleMetadata.Путь(), name, args)

    def __str__(self):
        return "{0}.{1}".format(super().__str__(), self.__dict__["_moduleMetadata"].Имя())

class ОбщийМодуль(ПрограммныйМодуль):
    def __init__(self, клиент, метаданныеМодуля):
        super().__init__(клиент, метаданныеМодуля)

    def __getattr__(self, item):
        return lambda *args: self.__trycall(item, args)

    def __trycall(self, name, args):
        return self._bromClient.ВызватьМетодСМассивомПараметров(self._moduleMetadata.Имя(), name, args)

    def __str__(self):
        return "{0}.{1}".format(super().__str__(), self._moduleMetadata.Имя())

class ОбъектМенеджер(МодульМенеджер):
    def __init__(self, клиент, метаданные, типКоллекции):
        super().__init__(клиент, метаданные)
        self.__dict__["_collectionType"] = типКоллекции

    def СоздатьСелектор(self):
        селектор = Селектор(self.__dict__["_bromClient"])
        селектор.УстановитьКоллекцию(self.__dict__["_moduleMetadata"].ПолноеИмя())
        return селектор

    def ПолучитьСсылку(self, идентификатор):
        return self.__dict__["_bromClient"].Контекст().ПолучитьОбъектСсылку(
            self.__dict__["_moduleMetadata"].ПолноеИмя(),
            идентификатор
        )

    def ПустаяСсылка(self):
        return self.__dict__["_bromClient"].Контекст().ПолучитьОбъектСсылку(
            self.__dict__["_moduleMetadata"].ПолноеИмя(),
            УникальныйИдентификатор.Пустой()
        )

    def СоздатьОбъект(self):
        return КонтекстОбъекта.ПолучитьКонтекстОбъекта(
            self.ПустаяСсылка()
        )

    def _tryget(self, name):
        предопределенные = self.__dict__["_moduleMetadata"].Предопределенные
        if предопределенные and предопределенные.СвойствоОпределено(name):
            return предопределенные[name]

        return super()._tryget(name)


    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

class МетаданныеКоллекция(УзелМетаданных):
    def __init__(self, корень, родитель, имя, полноеИмя, синоним, проверятьКеш = False):
        super().__init__(корень, родитель, имя, полноеИмя, синоним)
        self.__checkCache = проверятьКеш
        self.__childrenNames = None

    def ИменаПодчиненных(self):
        if not self.__checkCache:
            return super().ИменаПодчиненных()

        if not self.__childrenNames == None:
            return self.__childrenNames

        кеш = self.Корень().Кеш
        if кеш:
            имена = кеш.ПолучитьЗначение("#list." + self.Путь())
            if имена != None:
                self.__childrenNames = имена
                return self.__childrenNames

        картаИмен = self.Корень().ПолучитьИменаОбъектовКоллекций(self.Путь())
        имена = картаИмен[self.Путь()]
        if not имена == None:
            self.__childrenNames = []
            for имя in имена:
                self.__childrenNames.append(имя)
            if кеш:
                кеш.УстановитьЗначение("#list." + self.Путь(), self.__childrenNames)
            return self.__childrenNames

        raise Exception('Не удалось получить имена подчиненых узлов для коллекции "{0}"'.format(self.Путь()))

    def НайтиПодчиненный(self, имя):
        узел = super().НайтиПодчиненный(имя)
        if узел:
            return узел

        if self.__checkCache:
            кеш = self.Корень().Кеш
            if кеш:
                node = кеш.ПолучитьЗначение(self.Путь() + "." + имя)
                if node != None:
                    return ПостроительМетаданных.ПолучитьУзелИзSOAP(node, self)

            именаПодчиненных = self.ИменаПодчиненных()
            for текИмя in именаПодчиненных:
                if текИмя.lower() == имя.lower():
                    self.Корень().Загрузить("{0}.{1}".format(self.Путь(), имя))
                    return self.НайтиПодчиненный(имя)
                    break

        return None

    def __iter__(self):
        if self.__checkCache:
            names = self.ИменаПодчиненных()
            for name in names:
                yield name, self.НайтиПодчиненный(name)
        else:
            baseIter = super().__iter__()
            for key, val in baseIter:
                yield key, val

class МетаданныеКонфигурация(УзелМетаданных):
    def __init__(self, клиент):
        super().__init__(None, None, "", "", "")

        self.__bromClient = клиент

        self.__cache = None

        self.__metadataMap = {}

        self.__fullNameToPathMap = {}

        self.__init()

    def __init(self):
        self._clear()
        self.__metadataMap.clear()

        self.__fullNameToPathMap = {
            "Справочник": "Справочники",
            "Документ": "Документы",
            "Перечисление": "Перечисления",
            "ПланВидовХарактеристик": "ПланыВидовХарактеристик",
            "ПланСчетов": "ПланыСчетов",
            "ПланВидовРасчета": "ПланыВидовРасчета",
            "БизнесПроцесс": "БизнесПроцессы",
            "Задача": "Задачи",
            "Константа": "Константы",
            "ОбщийМодуль": "ОбщиеМодули",
            "ПараметрСеанса": "ПараметрыСеанса",
            "КритерийОтбора": "КритерииОтбора",
            "Обработка": "Обработки",
            "Отчет": "Отчеты",
            "ЖурналДокументов": "ЖурналыДокументов",

            "РегистрСведений": "РегистрыСведений",
            "РегистрНакопления": "РегистрыНакопления",
            "РегистрБухгалтерии": "РегистрыБухгалтерии",
            "РегистрРасчета": "РегистрыРасчета",

            "Последовательность": "Последовательности",

            "Реквизит": "Реквизиты",
            "ТабличнаяЧасть": "ТабличныеЧасти"
        }

        МетаданныеКоллекция(self, self, "ПараметрыСеанса", "ПараметрыСеанса", "ПараметрыСеанса", True)
        МетаданныеКоллекция(self, self, "КритерииОтбора", "КритерииОтбора", "Критерии отбора", True)
        МетаданныеКоллекция(self, self, "Константы", "Константы", "Константы", True)
        МетаданныеКоллекция(self, self, "Справочники", "Справочники", "Справочники", True)
        МетаданныеКоллекция(self, self, "Документы", "Документы", "Документы", True)
        МетаданныеКоллекция(self, self, "Перечисления", "Перечисления", "Перечисления", True)
        МетаданныеКоллекция(self, self, "ПланыВидовХарактеристик", "ПланыВидовХарактеристик", "Планы видов характеристик", True)
        МетаданныеКоллекция(self, self, "ПланыСчетов", "ПланыСчетов", "Планы счетов", True)
        МетаданныеКоллекция(self, self, "ПланыВидовРасчета", "ПланыВидовРасчета", "Планы видов расчета", True)
        МетаданныеКоллекция(self, self, "БизнесПроцессы", "БизнесПроцессы", "Бизнес-процессы", True)
        МетаданныеКоллекция(self, self, "Задачи", "Задачи", "Задачи", True)
        МетаданныеКоллекция(self, self, "ЖурналыДокументов", "ЖурналыДокументов", "Журналы документов", True)
        МетаданныеКоллекция(self, self, "Обработки", "Обработки", "Обработки", True)
        МетаданныеКоллекция(self, self, "Отчеты", "Отчеты", "Отчеты", True)
        МетаданныеКоллекция(self, self, "РегистрыСведений", "РегистрыСведений", "Регистры сведений", True)
        МетаданныеКоллекция(self, self, "РегистрыНакопления", "РегистрыНакопления", "Регистры накопления", True)
        МетаданныеКоллекция(self, self, "РегистрыБухгалтерии", "РегистрыБухгалтерии", "Регистры бухгалтерии", True)
        МетаданныеКоллекция(self, self, "РегистрыРасчета", "РегистрыРасчета", "Регистры расчета", True)
        МетаданныеКоллекция(self, self, "Последовательности", "Последовательности", "Последовательности", True)
        МетаданныеКоллекция(self, self, "ОбщиеМодули", "ОбщиеМодули", "Общие модули", True)

    @property
    def Кеш(self):
        return self.__cache

    @Кеш.setter
    def Кеш(self, value):
        self.__cache = value

    def Клиент(self):
        return self.__bromClient

    def ЗарегистрироватьУзел(self, узел):
        if not self.__metadataMap == None:
            self.__metadataMap[узел.ПолноеИмя()] = узел

    def Загрузить(self, состав, размерПакета = 0):
        индексПакета = 0
        while True:
            soapMetadataPack = self._получитьМетаданныеSOAP(состав, размерПакета, индексПакета)
            self.__заполнитьМетаданныеИзПакетаSOAP(soapMetadataPack)
            запрошеноПакетов = soapMetadataPack.RequestedObjectsCount
            текРазмерПакета = soapMetadataPack.PackSize
            всегоПакетов = (запрошеноПакетов + текРазмерПакета - 1) // текРазмерПакета if текРазмерПакета > 0 else 0
            if индексПакета >= всегоПакетов - 1:
                break
            индексПакета += 1

    def __заполнитьМетаданныеИзПакетаSOAP(self, soapMetadataPack):
        if not soapMetadataPack.Collection:
            return
        for collection in soapMetadataPack.Collection:
            узелКоллекции = self.НайтиПодчиненный(collection.Name)
            if узелКоллекции:
                if collection.Item:
                    for node in collection.Item:
                        узел = ПостроительМетаданных.ПолучитьУзелИзSOAP(node, узелКоллекции)
                        self.__закешироватьЭлементКоллекции(узел, node)

    def _получитьМетаданныеSOAP(self, состав, размерПакета, индексПакета):
        return self.__bromClient.SoapКлиент.service.GetMetadata(состав, размерПакета, индексПакета)

    def ПолучитьИменаОбъектовКоллекций(self, коллекции):
        result = self.__bromClient.SoapКлиент.service.GetMetadaChildrenNames(коллекции)
        return self.__bromClient.Сериализатор().ИзЗначенияБром(result)

    def __закешироватьЭлементКоллекции(self, узелМетаданных, node):
        if self.__cache:
            self.__cache.УстановитьЗначение(узелМетаданных.Путь(), node)

    def Получить(self, полноеИмя):
        узел = self.__metadataMap.get(полноеИмя)
        if узел:
            return узел

        фрагменты = полноеИмя.split(".")
        if len(фрагменты) >= 1:
            новФрагмент = self.__fullNameToPathMap.get(фрагменты[0])
            if новФрагмент:
                фрагменты[0] = новФрагмент

        if len(фрагменты) >= 3:
            новФрагмент = self.__fullNameToPathMap.get(фрагменты[2])
            if новФрагмент:
                фрагменты[2] = новФрагмент

        путь = str.join('.', фрагменты)

        return self.Найти(путь)

class МетаданныеМодуль(УзелМетаданных):
    def __init__(self, родитель, metadata):
        super().__init__(
            родитель.Корень(),
            родитель,
            metadata.Name,
            metadata.FullName,
            metadata.Title
        )

class МетаданныеОбъект(УзелМетаданных):
    def __init__(self, родитель, metadata):
        super().__init__(
            родитель.Корень(),
            родитель,
            metadata.Name,
            metadata.FullName,
            metadata.Title
        )

        self.__collectionType = ТипКоллекции[metadata.CollectionType]

        ПостроительМетаданных.ЗагрузитьРеквизиты(родитель.Корень(), self, metadata.Attribute)
        ПостроительМетаданных.ЗагрузитьТабличныеЧасти(родитель.Корень(), self, metadata.TableSection)

        self.__predefinedValues = self.Клиент().Сериализатор().ИзЗначенияБром(metadata.Predefined) if metadata.Predefined else Структура()


    def ТипКоллекции(self):
        return self.__collectionType

    @property
    def Предопределенные(self):
        return self.__predefinedValues

class МетаданныеРеквизит(УзелМетаданных):
    def __init__(self, родитель, metadata):
        super().__init__(
            родитель.Корень(),
            родитель,
            metadata.Name,
            "{0}.Реквизит.{1}".format(родитель.ПолноеИмя(), metadata.Name),
            metadata.Title
        )

class МетаданныеТабличнаяЧасть(УзелМетаданных):
    def __init__(self, родитель, metadata):
        super().__init__(
            родитель.Корень(),
            родитель,
            metadata.Name,
            "{0}.ТабличнаяЧасть.{1}".format(родитель.ПолноеИмя(), metadata.Name),
            metadata.Title
        )
        ПостроительМетаданных.ЗагрузитьРеквизиты(родитель.Корень(), self, metadata.Attribute)

class ПостроительМетаданных:
    @staticmethod
    def ЗагрузитьРеквизиты(корень, узелРодитель, attributesSOAP):
        реквизиты = МетаданныеКоллекция(
            корень,
            узелРодитель,
            "Реквизиты",
            "{0}.Реквизиты".format(узелРодитель.ПолноеИмя()),
            "Реквизиты"
        )
        if attributesSOAP:
            for attribute in attributesSOAP:
                МетаданныеРеквизит(реквизиты, attribute)

    @staticmethod
    def ЗагрузитьТабличныеЧасти(корень, узелРодитель, tablesSOAP):
        табличныеЧасти = МетаданныеКоллекция(
            корень,
            узелРодитель,
            "ТабличныеЧасти",
            "{0}.ТабличныеЧасти".format(узелРодитель.ПолноеИмя()),
            "ТабличныеЧасти"
        )
        if tablesSOAP:
            for table in tablesSOAP:
                МетаданныеТабличнаяЧасть(табличныеЧасти, table)

    @staticmethod
    def ПолучитьУзелИзSOAP(soapОбъект, родитель):
        имяКласса = soapОбъект.__class__.__name__

        if имяКласса == "MetadataAttribute":
            return МетаданныеРеквизит(родитель, soapОбъект)
        if имяКласса == "MetadataTableSection":
            return МетаданныеТабличнаяЧасть(родитель, soapОбъект)
        if имяКласса == "MetadataModule":
            return МетаданныеМодуль(родитель, soapОбъект)
        if имяКласса == "MetadataObject":
            return МетаданныеОбъект(родитель, soapОбъект)

        return None

import os
import pickle



class ФайловыйКешМетаданных(КешМетаданных):
    def __init__(self, адресДиректории):
        self.__rootDirectoryPath = os.path.abspath(адресДиректории)
        self.__dataDirectoryPath = os.path.join(self.__rootDirectoryPath, "data")

    def __getKeyHash(self, key):
        hash = md5(key.lower().encode('utf-8'))
        return hash.hexdigest()

    def __getFilePath(self, key):
        hash = self.__getKeyHash(key)
        return os.path.join(self.__dataDirectoryPath, hash)

    def __addDir(self, dirName):
        if not os.path.exists(dirName):
            os.makedirs(dirName)

    def __removeDir(self, dirName):
        if os.path.exists(dirName):
            for root, dirs, files in os.walk(dirName, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

            os.rmdir(dirName)

    @property
    def АдресДиректории(self):
        return self.__rootDirectoryPath

    def ПолучитьЗначение(self, ключ):
        filePath = self.__getFilePath(ключ)

        if os.path.isfile(filePath):
            with open(filePath, 'rb') as file:
                value = pickle.load(file)
                return value

        return None

    def УстановитьЗначение(self, ключ, значение):
        self.__addDir(self.__dataDirectoryPath)

        filePath = self.__getFilePath(ключ)

        with open(filePath, 'wb') as file:
            pickle.dump(значение, file)

    def Очистить(self):
        self.__removeDir(self.__dataDirectoryPath)

    def СодержитКлюч(self, ключ):
        filePath = self.__getFilePath(ключ)

        return os.path.isfile(filePath)

class DBNull:
    def __init__(self):
        return

class БизнесПроцессСсылка(ОбъектСсылка):
    def __init__(self, клиент, имяКоллекци, идентификатор):
        super().__init__(клиент, ТипКоллекции.БизнесПроцесс, имяКоллекци, идентификатор)

class Граница:
    def __init__(self, моментВремени, видГраницы = ВидГраницы.Включая):
        self.__value = моментВремени
        self.__boundaryType = видГраницы

    @property
    def Значение(self):
        return self.__value

    @property
    def ВидГраницы(self):
        return self.__boundaryType

class ДвоичныеДанные:
    __data = None

    def __init__(self, данные):
        if isinstance(данные, str):
            with open(данные, "rb") as binary_file:
                self.__data = binary_file.read()
        else:
            self.__data = bytes(данные)

    @property
    def Данные(self):
        return self.__data

    def Размер(self):
        return len(self.__data)

    def Записать(self, имяФайла):
        with open(имяФайла, "wb") as binary_file:
            binary_file.write(self.__data)

    def __str__(self):
        return str(self.__data)

    def __getitem__(self, item):
        return self.__data[item]

    def __len__(self):
        return len(self.__data)

class ДеревоЗначений(ДвумернаяКоллекцияЗначений):
    def __init__(self):
        super().__init__()
        self.__rows = КоллекцияСтрокДереваЗначений(self)

    def Строки(self):
        return self.__rows

    def _onColumnRemoved(self, column):
        self.__removeColumnFromRow(self, column)

    def __removeColumnFromRow(self, parent, column):
        rows = parent.Строки()
        for row in rows:
            row._onColumnRemove(column)
            self.__removeColumnFromRow(row, column)

class ДокументСсылка(ОбъектСсылка):
    def __init__(self, клиент, имяКоллекци, идентификатор):
        super().__init__(клиент, ТипКоллекции.Документ, имяКоллекци, идентификатор)

class ЗадачаСсылка(ОбъектСсылка):
    def __init__(self, клиент, имяКоллекци, идентификатор):
        super().__init__(клиент, ТипКоллекции.Задача, имяКоллекци, идентификатор)

class КвалификаторыДаты:
    def __init__(self, частиДаты = ЧастиДаты.ДатаВремя):
        self.__dateFractions = частиДаты


    @property
    def ЧастиДаты(self):
        return self.__dateFractions

class КвалификаторыДвоичныхДанных:
    def __init__(self, длина = 0, допустимаяДлина = ДопустимаяДлина.Переменная):
        self.__length = длина
        self.__allowedLength = допустимаяДлина


    @property
    def Длина(self):
        return self.__length

    @property
    def ДопустимаяДлина(self):
        return self.__allowedLength

class КвалификаторыСтроки:
    def __init__(self, длинаСтроки = 0, допустимаяДлина = ДопустимаяДлина.Переменная):
        self.__length = длинаСтроки
        self.__allowedLength = допустимаяДлина


    @property
    def Длина(self):
        return self.__length

    @property
    def ДопустимаяДлина(self):
        return self.__allowedLength

class КвалификаторыЧисла:
    def __init__(self, числоРазрядов = 0, числоРазрядовДробнойЧасти = 0, допустимыйЗнак = ДопустимыЗнак.Любой):
        self.__digits = числоРазрядов
        self.__fractionDigits = числоРазрядовДробнойЧасти
        self.__allowedSign = допустимыйЗнак


    @property
    def Разрядность(self):
        return self.__digits

    @property
    def РазрядностьДробнойЧасти(self):
        return self.__fractionDigits

    @property
    def ДопустимыйЗнак(self):
        return self.__allowedSign

class КоллекцияКолонок:
    def __init__(self, коллекция):
        self.__parent = коллекция
        self.__columns = []

    @property
    def Родиель(self):
        return self.__parent

    def Добавить(self, имя, заголовок = ""):
        if self.Найти(имя):
            raise ValueError('Колонка с именем "{0}" уже присутствует в таблице.'.format(имя))

        column = КолонкаКоллекцииЗначений(self, имя, заголовок)
        self.__columns.append(column)

    def Наименования(self):
        return list(map(lambda x : x.Имя, self.__columns))

    def Количество(self):
        return len(self.__columns)

    def Вставить(self, индекс, имя, заголовок = ""):
        if self.Найти(имя):
            raise ValueError('Колонка с именем "{0}" уже присутствует в таблице.'.format(имя))

        column = КолонкаКоллекцииЗначений(self, имя, заголовок)
        self.__columns.insert(индекс, column)

    def Найти(self, имя):
        текИмя = имя.lower()
        for column in self.__columns:
            if column.Имя.lower() == текИмя:
                return column
        return None

    def Удалить(self, индекс):
        if isinstance(индекс, int):
            column = self.__columns[индекс]
            if column:
                del(self.__columns[индекс])
                self.__parent._onColumnRemoved(column)
        elif isinstance(индекс, str):
            column = self.Найти(индекс)
            if column:
                self.__columns.remove(column)
                self.__parent._onColumnRemoved(column)
        elif isinstance(индекс, КолонкаКоллекцииЗначений):
            if индекс in self.__columns:
                self.__columns.remove(индекс)
                self.__parent._onColumnRemoved(индекс)

    def __len__(self):
        return len(self.__columns)

    def __getitem__(self, item):
        return self.__columns[item]

    def __iter__(self):
        for column in self.__columns:
            yield column

    def __contains__(self, item):
        return item in self.__columns

class КоллекцияСтрокДереваЗначений:
    def __init__(self, коллекция):
        self.__parent = коллекция
        self.__rows = []

    def Количество(self):
        return len(self.__rows)

    def Добавить(self):
        строка = СтрокаДереваЗначений(self.__parent)
        self.__rows.append(строка)
        return строка

    def Вставить(self, индекс):
        строка = СтрокаДереваЗначений(self.__parent)
        self.__rows.insert(индекс, строка)
        return строка

    def Удалить(self, строка):
        if isinstance(строка, СтрокаДереваЗначений):
            self.__rows.remove(строка)
        elif isinstance(строка, int):
            del(self.__rows[строка])

    def Очистить(self):
        self.__rows.clear()

    def Получить(self, индекс):
        return self.__rows[индекс]

    def __len__(self):
        return len(self.__rows)

    def __getitem__(self, item):
        return self.__rows[item]

    def __contains__(self, item):
        return item in self.__rows

    def __iter__(self):
        for row in self.__rows:
            yield row

import re

class КолонкаКоллекцииЗначений:
    def __init__(self, родитель, имя, заголовок):
        if not КолонкаКоллекцииЗначений.__isValidKey(имя):
            raise ValueError("Недопустимое имя колонки. Имя должно быть корректным идентификатором.")

        self.__parent = родитель
        self.__name = имя
        self.__title = заголовок if заголовок.strip() else имя

    @staticmethod
    def __isValidKey(key):
        return isinstance(key, str) and bool(re.match("^[A-Za-zА-Яа-я_]{1}[A-Za-zА-Яа-я_0-9]*$", key))

    @property
    def Имя(self):
        return self.__name

    @Имя.setter
    def Имя(self, value):
        if not КолонкаКоллекцииЗначений.__isValidKey(value):
            raise ValueError("Недопустимое имя колонки. Имя должно быть корректным идентификатором.")

        if value.lower() == self.__name.lower():
            self.__name = value
            return

        if self.__parent.Найти(value):
            raise ValueError('Колонка с именем "{0}" уже присутствует в таблице.'.format(value))

        self.__name = value


    def __str__(self):
        return self.__name

class Массив(list):
    def __init__(self, *items):
        for item in items:
            self.append(item)

    def Добавить(self, значение):
        self.append(значение)

    def Вставить(self, индекс, значение):
        self.insert(индекс, значение)

    def Удалить(self, индекс):
        self.pop(индекс)

    def Очистить(self):
        self.clear()

    def Получить(self, индекс):
        return self[индекс]

    def Установить(self, индекс, значение):
        self[индекс] = значение

    def Количество(self):
        return len(self)

    def Найти(self, значение):
        return self.index(значение)

class МоментВремени:
    def __init__(self, дата, ссылка):
        self.__date = дата
        self.__reference = ссылка

    @property
    def Дата(self):
        return self.__date

    @property
    def Ссылка(self):
        return self.__reference

    def __str__(self):
        return str(self.__date) + "; " + str(self.__reference)

    def __eq__(self, other):
        return isinstance(other, МоментВремени) and self.Дата == other.Дата and self.Ссылка == other.Ссылка

    def __hash__(self):
        return hash((self.__date, self.__reference))

class НесериализуемыеДанные:
    pass

class ОписаниеТипов:
    def __init__(self, типы, квалификаторыЧисла = None, квалификаторыСтроки = None, квалификаторыДаты = None, квалификаторыДвоичныхДанных = None):
        self.__types = типы

        self.__numberQualifiers = квалификаторыЧисла
        self.__stringQualifiers = квалификаторыСтроки
        self.__dateQualifiers = квалификаторыДаты
        self.__binaryDataQualifiers = квалификаторыДвоичныхДанных

    @property
    def КвалификаторыЧисла(self):
        return self.__numberQualifiers

    @property
    def КвалификаторыСтроки(self):
        return self.__stringQualifiers

    @property
    def КвалификаторыДаты(self):
        return self.__dateQualifiers

    @property
    def КвалификаторыДвоичныхДанных(self):
        return self.__binaryDataQualifiers

    def Типы(self):
        return self.__types.copy()

    def СодержитТип(self, тип):
        return тип in self.__types

    def __iter__(self):
        for type in self.__types:
            yield type

    def __len__(self):
        return len(self.__types)

    def __str__(self):
        return str(self.__types)

    def __getitem__(self, item):
        return self.__types[item]

    def __contains__(self, item):
        return item in self.__types

class ПеречислениеСсылка(Ссылка):
    def __init__(self, клиент, имяКоллекци, имя, синоним = ""):
        super().__init__(клиент, ТипКоллекции.Перечисление, имяКоллекци)
        self.__name = имя if str(имя).strip() else ""
        self.__presentation = синоним if синоним else имя

    def Имя(self):
        return self.__name

    def Синоним(self):
        return self.__presentation

    def __Пустая(self):
        return not bool(self.__name)

    def __str__(self):
        return self.__presentation

    def __eq__(self, other):
        if not isinstance(other, ПеречислениеСсылка):
            return False

        return self.Клиент() == other.Клиент() and \
               self.ИмяКоллекции() == other.ИмяКоллекции() and \
               self.Имя() == other.Имя()

    def __hash__(self):
        return hash((self.ИмяКоллекции(), self.Имя()))

class ПланВидовРасчетаСсылка(ОбъектСсылка):
    def __init__(self, клиент, имяКоллекци, идентификатор):
        super().__init__(клиент, ТипКоллекции.ПланВидовРасчета, имяКоллекци, идентификатор)

class ПланВидовХарактеристикСсылка(ОбъектСсылка):
    def __init__(self, клиент, имяКоллекци, идентификатор):
        super().__init__(клиент, ТипКоллекции.ПланВидовХарактеристик, имяКоллекци, идентификатор)

class ПланСчетовСсылка(ОбъектСсылка):
    def __init__(self, клиент, имяКоллекци, идентификатор):
        super().__init__(клиент, ТипКоллекции.ПланСчетов, имяКоллекци, идентификатор)

class Сериализатор:
    def __init__(self, клиент):
        self.__bromClient = клиент
        self.__factory = клиент.SoapКлиент.type_factory('ns0')

    @property
    def Фабрика(self):
        return self.__factory;


    # Упаковка -------------------------------------------

    def ВЗначениеБром(self, значение):
        тип = type(значение)

        # NULL
        if значение is None:
            return self.__factory.ValueNull()
        # String
        elif тип == str:
            return self.__factory.ValueString(Value=значение)
        # Number
        elif тип in [int, float]:
            return self.__factory.ValueNumber(Value=значение)
        # Boolean
        elif тип == bool:
            return self.__factory.ValueBoolean(Value=значение)
        # Date
        elif тип in [datetime, date]:
            return self.__factory.ValueDate(Value=значение)
        # ValueEnumRef
        elif isinstance(значение, ПеречислениеСсылка):
            return self.__ВЗначениеБром_ПеречислениеСсылка(значение)
        # ValueObjectRef
        elif isinstance(значение, ОбъектСсылка):
            return self.__ВЗначениеБром_ОбъектСсылка(значение)
        # Array
        elif isinstance(значение, list) or isinstance(значение, tuple) or isinstance(значение, set):
            return self.__ВЗначениеБром_Массив(значение)
        # Struct
        elif isinstance(значение, Структура):
            return self.__ВЗначениеБром_Структура(значение)
        # Map
        elif isinstance(значение, dict):
            return self.__ВЗначениеБром_Соответствие(значение)
        # ValueTable
        elif isinstance(значение, ТаблицаЗначений):
            return self.__ВЗначениеБром_ТаблицаЗначений(значение)
        elif isinstance(значение, ТабличнаяЧасть):
            return self.__ВЗначениеБром_ТаблицаЗначений(значение.Выгрузить())
        # ValueTable
        elif isinstance(значение, ДеревоЗначений):
            return self.__ВЗначениеБром_ДеревоЗначений(значение)
        # GUID
        elif isinstance(значение, UUID):
            return self.__factory.ValueGuid(Value=str(значение))
        # DBNUll
        elif isinstance(значение, DBNull):
            return self.__factory.ValueDBNull()
        # ValueStorage
        elif isinstance(значение, ХранилищеЗначения):
            return self.__factory.ValueStorage(Data=self.ВЗначениеБром(значение.Получить()))
        # ValueBinaryData
        elif isinstance(значение, bytes):
            return self.__factory.ValueBinaryData(Value=значение)
        elif isinstance(значение, ДвоичныеДанные):
            return self.__factory.ValueBinaryData(Value=значение.Данные)
        # ValueType
        elif isinstance(значение, Тип):
            return self.__ВЗначениеБром_Тип(значение)
        # ValueTypeDescription
        elif isinstance(значение, ОписаниеТипов):
            return self.__ВЗначениеБром_ОписаниеТипов(значение)
        # ValueBoundary
        elif isinstance(значение, Граница):
            return self.__ВЗначениеБром_Граница(значение)
        # ValueBoundary
        elif isinstance(значение, МоментВремени):
            return self.__ВЗначениеБром_МоментВремени(значение)

        # ValueAccountingRecordType
        elif isinstance(значение, ВидДвиженияБухгалтерии):
            return self.__factory.ValueAccountingRecordType(Value=значение.name)
        # ValueAccumulationRecordType
        elif isinstance(значение, ВидДвиженияНакопления):
            return self.__factory.ValueAccumulationRecordType(Value=значение.name)
        # ValueAccountType
        elif isinstance(значение, ВидСчета):
            return self.__factory.ValueAccountType(Value=значение.name)

        raise ValueError("Не удается сериализовать указанное значение.")

    def __ВЗначениеБром_Массив(self, значение):
        items = []
        for item in значение:
            items.append(self.ВЗначениеБром(item))
        return self.__factory.ValueArray(Item=items)

    def __ВЗначениеБром_Структура(self, значение):
        properties = []
        for key, value in значение:
            property = self.ВЗначениеБром(value)
            property.Name = key
            properties.append(property)
        return self.__factory.ValueStruct(Property=properties)

    def __ВЗначениеБром_Соответствие(self, значение):
        keyValues = []
        for key, value in значение.items():
            keyValues.append(
                self.__factory.ValueKeyValue(
                    Key=self.ВЗначениеБром(key),
                    Value=self.ВЗначениеБром(value)
                )
            )
        return self.__factory.ValueMap(KeyValue=keyValues)

    def __ВЗначениеБром_ПеречислениеСсылка(self, значение):
        return self.__factory.ValueEnumRef(
            Type=значение.ПолноеИмяТипа(),
            Value=значение.Имя()
        )

    def __ВЗначениеБром_ОбъектСсылка(self, значение):
        return self.__factory.ValueObjectRef(
            Type=значение.ПолноеИмяТипа(),
            Value=str(значение.УникальныйИдентификатор())
        )

    def __ВЗначениеБром_Тип(self, значение):
        xmlПространствоИмен = значение.XmlПространствоИмен;
        if xmlПространствоИмен.lower() == "http://www.w3.org/2001/XMLSchema":
            xmlПространствоИмен = Тип.XMLПространствоИменXmlSchema()
        elif xmlПространствоИмен.lower() == "http://v8.1c.ru/data":
            xmlПространствоИмен = Тип.XMLПространствоИмен1C()

        return self.__factory.ValueType(Value=значение.XmlИмя, Namespace=xmlПространствоИмен)

    def __ВЗначениеБром_ОписаниеТипов(self, значение):
        types = []
        for type in значение:
            types.append(self.__ВЗначениеБром_Тип(type))

        return self.__factory.ValueTypeDescription(
            Item=types,
            NumberQualifiers = None if not значение.КвалификаторыЧисла else self.__factory.NumberQualifiers(
                Digits=значение.КвалификаторыЧисла.Разрядность,
                FractionDigits=значение.КвалификаторыЧисла.РазрядностьДробнойЧасти,
                OnlyPositive=(значение.КвалификаторыЧисла.ДопустимыйЗнак == ДопустимыЗнак.Неотрицательный)
            ),
            StringQualifiers=None if not значение.КвалификаторыСтроки else self.__factory.StringQualifiers(
                Length=значение.КвалификаторыСтроки.Длина,
                AllowedLength=значение.КвалификаторыСтроки.ДопустимаяДлина.name
            ),
            DateQualifiers=None if not значение.КвалификаторыДаты else self.__factory.DateQualifiers(
                DateFractions=значение.КвалификаторыДаты.ЧастиДаты.name,
            ),
            BinaryDataQualifiers=None if not значение.КвалификаторыДвоичныхДанных else self.__factory.BinaryDataQualifiers(
                Length=значение.КвалификаторыДвоичныхДанных.Длина,
                AllowedLength=значение.КвалификаторыДвоичныхДанных.ДопустимаяДлина.name
            )
        )

    def __ВЗначениеБром_Граница(self, значение):
        return self.__factory.ValueBoundary(
            Value=self.ВЗначениеБром(значение.Значение),
            Type=значение.ВидГраницы.name
        )

    def __ВЗначениеБром_МоментВремени(self, значение):
        return self.__factory.ValuePointInTime(
            Date=значение.Дата,
            Ref=self.ВЗначениеБром(значение.Ссылка)
        )

    def __ВЗначениеБром_ТаблицаЗначений(self, значение):
        columns = []
        for колонка in значение.Колонки:
            columns.append(self.__factory.DataTableColumn(Name=колонка.Имя))

        rows = []
        for стр in значение:
            props = []
            for колонка in значение.Колонки:
                prop = self.ВЗначениеБром(стр[колонка])
                prop.Name = колонка.Имя
                props.append(prop)
            rows.append(self.__factory.DataTableRow(Property=props))

        return self.__factory.ValueTable(
            Column=columns,
            Row=rows
        )

    def __ВЗначениеБром_ДеревоЗначений(self, значение):
        columns = []
        for колонка in значение.Колонки:
            columns.append(self.__factory.DataTableColumn(Name=колонка.Имя))

        rows = []
        self.__ВЗначениеБром_ДеревоЗначений_Строка(значение, rows, значение.Строки())

        return self.__factory.ValueTree(
            Column=columns,
            Row=rows
        )

    def __ВЗначениеБром_ДеревоЗначений_Строка(self, дерево, rows, строки):
        for стр in строки:
            props = []
            for колонка in дерево.Колонки:
                prop = self.ВЗначениеБром(стр[колонка])
                prop.Name = колонка.Имя
                props.append(prop)

                newRows = []
                self.__ВЗначениеБром_ДеревоЗначений_Строка(дерево, newRows, стр.Строки())
            rows.append(
                self.__factory.DataTableRow(
                    Property=props,
                    Row=newRows
                )
            )


    # Распаковка -------------------------------------------

    def ИзЗначенияБром(self, значение):
        имяКласса = значение.__class__.__name__

        if имяКласса == "ValueNull":
            return None
        if имяКласса == "ValueString":
            return str(значение.Value)
        if имяКласса == "ValueNumber":
            return float(значение.Value)
        if имяКласса == "ValueBoolean":
            return bool(значение.Value)
        if имяКласса == "ValueDate":
            return значение.Value
        if имяКласса == "ValueEnumRef":
            return self.__ИзЗначенияБром_ПеречислениеСсылка(значение)
        if имяКласса == "ValueObjectRef":
            return self.__ИзЗначенияБром_ОбъектСсылка(значение)
        if имяКласса == "ValueArray":
            return self.__ИзЗначенияБром_Массив(значение)
        if имяКласса == "ValueStruct":
            return self.__ИзЗначенияБром_Структура(значение)
        if имяКласса == "ValueMap":
            return self.__ИзЗначенияБром_Соответствие(значение)
        if имяКласса == "ValueTable":
            return self.__ИзЗначенияБром_ТаблицаЗначений(значение)
        if имяКласса == "ValueTree":
            return self.__ИзЗначенияБром_ДеревоЗначений(значение)
        if имяКласса == "ValueGuid":
            return УникальныйИдентификатор(значение.Value)
        if имяКласса == "ValueDBNull":
            return DBNull()
        if имяКласса == "ValueType":
            return self.__ИзЗначенияБром_Тип(значение)
        if имяКласса == "ValueTypeDescription":
            return self.__ИзЗначенияБром_ОписаниеТипов(значение)
        if имяКласса == "ValueBinaryData":
            return ДвоичныеДанные(значение.Value)
        if имяКласса == "ValueStorage":
            return ХранилищеЗначения(self.ИзЗначенияБром(значение.Data))
        if имяКласса == "ValueBoundary":
            return self.__ИзЗначенияБром_Граница(значение)
        if имяКласса == "ValuePointInTime":
            return self.__ИзЗначенияБром_МоментВремени(значение)

        if имяКласса == "ValueAccountingRecordType":
            return ВидДвиженияБухгалтерии[значение.Value]
        if имяКласса == "ValueAccumulationRecordType":
            return ВидДвиженияНакопления[значение.Value]
        if имяКласса == "ValueAccountType":
            return ВидСчета[значение.Value]

        if имяКласса == "ValueNonserializable":
            return НесериализуемыеДанные()

        raise ValueError("Не удается десериализовать полученное значение.")

    def __ИзЗначенияБром_Массив(self, значение):
        result = Массив()
        if значение.Item:
            for item in значение.Item:
                result.append(self.ИзЗначенияБром(item))
        return result

    def __ИзЗначенияБром_Структура(self, значение):
        result = Структура()
        if значение.Property:
            for property in значение.Property:
                result.Вставить(property.Name, self.ИзЗначенияБром(property))
        return result

    def __ИзЗначенияБром_Соответствие(self, значение):
        result = Соответствие()
        if значение.KeyValue:
            for keyValue in значение.KeyValue:
                result.Вставить(self.ИзЗначенияБром(keyValue.Key), self.ИзЗначенияБром(keyValue.Value))
        return result

    def __ИзЗначенияБром_ПеречислениеСсылка(self, значение):
        return self.__bromClient.Контекст().ПолучитьПеречислениеСсылку(значение.Type, значение.Value, значение.Presentation)

    def __ИзЗначенияБром_ОбъектСсылка(self, значение):
        reference = self.__bromClient.Контекст().ПолучитьОбъектСсылку(значение.Type, значение.Value)

        if значение.Presentation != None:
            self.__bromClient.Контекст()._КонтекстДанных__установитьПредставлениеОбъекта(reference, значение.Presentation)

        if значение.Property != None:
            self.__bromClient.Контекст()._КонтекстДанных__установитьЗначенияИзСвойствSOAP(reference, значение.Property)

        return reference

    def __ИзЗначенияБром_Тип(self, значение):
        ns = значение.Namespace
        if ns == Тип.XMLПространствоИменXmlSchema():
            ns = "http://www.w3.org/2001/XMLSchema"
        elif ns == Тип.XMLПространствоИмен1C():
            ns = "http://v8.1c.ru/data"
        return Тип(значение.Value, ns)

    def __ИзЗначенияБром_ОписаниеТипов(self, значение):
        типы = []
        for type in значение.Item:
            типы.append(self.__ИзЗначенияБром_Тип(type))

        return ОписаниеТипов(
            типы=типы,
            квалификаторыЧисла=None if not значение.NumberQualifiers else КвалификаторыЧисла(
                значение.NumberQualifiers.Digits,
                значение.NumberQualifiers.FractionDigits,
                ДопустимыЗнак.Неотрицательный if значение.NumberQualifiers.OnlyPositive else ДопустимыЗнак.Любой
            ),
            квалификаторыСтроки=None if not значение.StringQualifiers else КвалификаторыСтроки(
                значение.StringQualifiers.Length,
                ДопустимаяДлина[значение.StringQualifiers.AllowedLength]
            ),
            квалификаторыДаты=None if not значение.DateQualifiers else КвалификаторыДаты(
                ЧастиДаты[значение.DateQualifiers.DateFractions]
            ),
            квалификаторыДвоичныхДанных=None if not значение.BinaryDataQualifiers else КвалификаторыДвоичныхДанных(
                значение.BinaryDataQualifiers.Length,
                ДопустимаяДлина[значение.BinaryDataQualifiers.AllowedLength]
            )
        )

    def __ИзЗначенияБром_Граница(self, значение):
        return Граница(
            self.ИзЗначенияБром(значение.Value),
            ВидГраницы[значение.Type]
        )

    def __ИзЗначенияБром_МоментВремени(self, значение):
        return МоментВремени(
            значение.Date,
            self.ИзЗначенияБром(значение.Ref)
        )

    def __ИзЗначенияБром_ТаблицаЗначений(self, значение):
        табл = ТаблицаЗначений()

        if значение.Column:
            for column in значение.Column:
                табл.Колонки.Добавить(column.Name)

        if значение.Row:
            for row in значение.Row:
                стр = табл.Добавить()
                if row.Property:
                    for prop in row.Property:
                        стр[prop.Name] = self.ИзЗначенияБром(prop)

        return табл

    def __ИзЗначенияБром_ДеревоЗначений(self, значение):
        дерево = ДеревоЗначений()

        if значение.Column:
            for column in значение.Column:
                дерево.Колонки.Добавить(column.Name)

        self.__ИзЗначенияБром_ДеревоЗначений_Строка(дерево.Строки(), значение.Row)

        return дерево

    def __ИзЗначенияБром_ДеревоЗначений_Строка(self, сроки, rows):
        if not rows:
            return

        for row in rows:
            стр = сроки.Добавить()
            if row.Property:
                for prop in row.Property:
                    стр[prop.Name] = self.ИзЗначенияБром(prop)

            self.__ИзЗначенияБром_ДеревоЗначений_Строка(стр.Строки(), row.Row)



    def ИзЗначенияБромВСтруктуру(self, значение):
        результат = Структура()
        if значение.Property:
            for prop in значение.Property:
                результат.Вставить(prop.Name, self.ИзЗначенияБром(prop))

        return результат

    def ИзЗначенияБромВДерево(self, значение):
        дерево = ДеревоЗначений()
        дерево.Колонки.Добавить("Ключ")
        дерево.Колонки.Добавить("Значение")

        self.__ИзЗначенияБромВДерево_Строка(значение.Property, дерево.Строки())

        return дерево

    def __ИзЗначенияБромВДерево_Строка(self, properties, строки):
        if properties:
            for prop in properties:
                стр = строки.Добавить()
                стр.Ключ = prop.Name
                стр.Значение = self.ИзЗначенияБром(prop)

                if hasattr(prop, "Property"):
                    self.__ИзЗначенияБромВДерево_Строка(prop.Property, стр.Строки())

class Соответствие(dict):
    def __init__(self, *args):
        super().__init__(args)

    def Вставить(self, ключ, значение):
        self[ключ] = значение

    def Количество(self):
        return len(self)

    def Очистить(self):
        self.clear()

    def Получить(self, ключ):
        return self[ключ]

    def Удалить(self, ключ):
        self.pop(ключ)

    def __iter__(self):
        return self.items().__iter__()

class СправочникСсылка(ОбъектСсылка):
    def __init__(self, клиент, имяКоллекци, идентификатор):
        super().__init__(клиент, ТипКоллекции.Справочник, имяКоллекци, идентификатор)

class СтрокаДереваЗначений(СтрокаДвумернойКоллекцииЗначений):
    def __init__(self, коллекция):
        super().__init__(коллекция)

        self.__dict__["__rows"] = КоллекцияСтрокДереваЗначений(self.__dict__["__parent"])

    def Строки(self):
        return self.__dict__["__rows"]

class СтрокаТаблицыЗначений(СтрокаДвумернойКоллекцииЗначений):
    def __init__(self, коллекция):
        super().__init__(коллекция)

import re

class Структура:
    def __init__(self, ключи = '', *значения):
        self.__dict__["__values"] = {}

        списокКлючей = ключи.split(',')
        минДлина = min(len(списокКлючей), len(значения))
        for i in range(минДлина):
            ключ = списокКлючей[i].strip()
            self.Вставить(ключ, значения[i])

    @staticmethod
    def __isValidKey(key):
        return isinstance(key, str) and bool(re.match("^[A-Za-zА-Яа-я_]{1}[A-Za-zА-Яа-я_0-9]*$", key))


    def Вставить(self, ключ, значение = None):
        if not(Структура.__isValidKey(ключ)):
            raise Exception("Недопустимый ключ. Ключ должен быть корректным идентификатором.")

        self.__dict__["__values"][ключ.lower()] = (ключ, значение)

    def Свойство(self, ключ):
        времКлюч = ключ.lower()
        if self.СвойствоОпределено(времКлюч):
            return self.__dict__["__values"][времКлюч][1]
        return None

    def СвойствоОпределено(self, ключ):
        времКлюч = ключ.lower()
        return времКлюч in self.__dict__["__values"]

    def Очистить(self):
        self.__dict__["__values"].clear()

    def Количество(self):
        return len(self.__dict__["__values"])

    def Удалить(self, ключ):
        времКлюч = ключ.lower()
        self.__dict__["__values"].pop(времКлюч)

    def __len__(self):
        return len(self.__dict__["__values"])

    def __getitem__(self, key):
        if not(self.СвойствоОпределено(key)):
            raise Exception('Свойство "{0}" не определено.'.format(key))
        return self.Свойство(key)

    def __setitem__(self, key, value):
        if not(self.СвойствоОпределено(key)):
            raise Exception('Свойство "{0}" не определено.'.format(key))
        self.Вставить(key, value)

    def __iter__(self):
        for value in self.__dict__["__values"].values():
            yield value[0], value[1]

    def keys(self):
        for item in self.__dict__["__values"].values():
            yield item[0]

    def values(self):
        for item in self.__dict__["__values"].values():
            yield item[1]

    def __contains__(self, item):
        return item.lower() in self.__dict__["__values"]

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

class ТаблицаЗначений(ДвумернаяКоллекцияЗначений):
    def __init__(self):
        super().__init__()
        self.__rows = []

    def Количество(self):
        return len(self.__rows)

    def Добавить(self):
        строка = СтрокаТаблицыЗначений(self)
        self.__rows.append(строка)
        return строка

    def Вставить(self, индекс):
        строка = СтрокаТаблицыЗначений(self)
        self.__rows.insert(индекс, строка)
        return строка

    def Удалить(self, строка):
        if isinstance(строка, СтрокаТаблицыЗначений):
            self.__rows.remove(строка)
        elif isinstance(строка, int):
            del(self.__rows[строка])

    def Очистить(self):
        self.__rows.clear()

    def Получить(self, индекс):
        return self.__rows[индекс]

    def __len__(self):
        return len(self.__rows)

    def __getitem__(self, item):
        return self.__rows[item]

    def __contains__(self, item):
        return item in self.__rows

    def __iter__(self):
        for row in self.__rows:
            yield row

    def _onColumnRemoved(self, column):
        for row in self.__rows:
            row._onColumnRemove(column)

class Тип():
    def __init__(self, xmlИмяТипа, xmlПространствоИмен):
        self.__name = xmlИмяТипа
        self.__nameSpace = xmlПространствоИмен

    @property
    def XmlИмя(self):
        return self.__name

    @property
    def XmlПространствоИмен(self):
        return self.__nameSpace

    def __str__(self):
        return self.__name

    @staticmethod
    def XMLПространствоИменXmlSchema():
        return "#xs"

    @staticmethod
    def XMLПространствоИмен1C():
        return "#1c"

    @staticmethod
    def Строка():
        return Тип("string", Тип.XMLПространствоИменXmlSchema())

    @staticmethod
    def Число():
        return Тип("decimal", Тип.XMLПространствоИменXmlSchema())

    @staticmethod
    def Дата():
        return Тип("dateTime", Тип.XMLПространствоИменXmlSchema())

    @staticmethod
    def Булево():
        return Тип("boolean", Тип.XMLПространствоИменXmlSchema())

    @staticmethod
    def ДвоичныеДанные():
        return Тип("base64Binary", Тип.XMLПространствоИменXmlSchema())

    @staticmethod
    def ХранилищеЗначения():
        return Тип("ValueStorage", Тип.XMLПространствоИмен1C())

    @staticmethod
    def УникальныйИдентификатор():
        return Тип("UUID", Тип.XMLПространствоИмен1C())

    @staticmethod
    def ВидДвиженияНакопления():
        return Тип("AccumulationMovementType", Тип.XMLПространствоИмен1C())

    @staticmethod
    def ВидДвиженияБухгалтерии():
        return Тип("AccountingMovementType", Тип.XMLПространствоИмен1C())

    @staticmethod
    def ВидСчета():
        return Тип("AccountType", Тип.XMLПространствоИмен1C())

    @staticmethod
    def СправочникСсылка(имя):
        return Тип("CatalogRef." + имя, "")

    @staticmethod
    def ДокументСсылка(имя):
        return Тип("DocumentRef." + имя, "")

    @staticmethod
    def ПеречислениеСсылка(имя):
        return Тип("EnumRef." + имя, "")

    @staticmethod
    def ПланВидовХарактеристикСсылка(имя):
        return Тип("ChartOfCharacteristicTypesRef." + имя, "")

    @staticmethod
    def ПланСчетовСсылка(имя):
        return Тип("ChartOfAccountsRef." + имя, "")

    @staticmethod
    def ПланВидовРасчетаСсылка(имя):
        return Тип("ChartOfCalculationTypesRef." + имя, "")

    @staticmethod
    def БизнесПроцессСсылка(имя):
        return Тип("BusinessProcessRef." + имя, "")

    @staticmethod
    def ЗадачаСсылка(имя):
        return Тип("TaskRef." + имя, "")

    def __eq__(self, other):
        if not isinstance(other, Тип):
            return NotImplemented

        return self.__name.lower() == other.__name.lower() and self.__nameSpace.lower() == other.__nameSpace.lower()

    def __hash__(self):
        return hash((self.__nameSpace.lower(), self.__name.lower()))

class УникальныйИдентификатор(UUID):
    def __init__(self, идентификатор = None):
        if идентификатор:
            super().__init__(идентификатор)
        else:
            super().__init__(bytes=uuid4().bytes)

    def Пустой(self):
        return self == УникальныйИдентификатор.Пустой()

    @staticmethod
    def Пустой():
        return УникальныйИдентификатор('00000000-0000-0000-0000-000000000000')

class ХранилищеЗначения:
    __value = None

    def __init__(self, значение):
        self.__value = значение

    def Получить(self):
        return self.__value;

class АвтозагрузкаПолейОбъектов:
    def __init__(self, загружатьСтандартныеРеквизиты, загружатьПользовательскиеРеквизиты, загружатьТабличныеЧасти):
        self.__loadDefaultAttributes = bool(загружатьСтандартныеРеквизиты)
        self.__loadCustomAttributes = bool(загружатьПользовательскиеРеквизиты)
        self.__loadTableSections = bool(загружатьТабличныеЧасти)

    @property
    def ЗагружатьСтандартныеРеквизиты(self):
        return self.__loadDefaultAttributes

    @property
    def ЗагружатьПользовательскиеРеквизиты(self):
        return self.__loadCustomAttributes

    @property
    def ЗагружатьТабличныеЧасти(self):
        return self.__loadTableSections

    @staticmethod
    def Ничего():
        return АвтозагрузкаПолейОбъектов(False, False, False)

    @staticmethod
    def ВсеПоля():
        return АвтозагрузкаПолейОбъектов(True, True, True)

    @staticmethod
    def ТолькоСтандартныеРеквизиты():
        return АвтозагрузкаПолейОбъектов(True, False, False)

    @staticmethod
    def ТолькоПользовательскиеРеквизиты():
        return АвтозагрузкаПолейОбъектов(False, True, False)

    @staticmethod
    def ТолькоРеквизиты():
        return АвтозагрузкаПолейОбъектов(True, True, False)

    @staticmethod
    def ТолькоТабличныеЧасти():
        return АвтозагрузкаПолейОбъектов(False, False, True)

class БизнесПроцессМенеджер(ОбъектМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные, ТипКоллекции.БизнесПроцесс)

    def СоздатьБизнесПроцесс(self):
        return self.СоздатьОбъект()

class БизнесПроцессОбъект(КонтекстОбъекта):
    def __init__(self, ссылка):
        super().__init__(ссылка)

class БромКлиент:
    def __init__(self, публикация = "", пользователь = "", пароль = "", строкаПодключения = ""):
        if строкаПодключения:
            параметры = {}
            фрагменты = строкаПодключения.split(';')
            for фрагмент in фрагменты:
                разбивка = фрагмент.split('=')
                if len(разбивка) == 2:
                    параметры[разбивка[0].strip().lower()] = разбивка[1].strip()

            if "публикация" in параметры:
                публикация = параметры["публикация"]
            if "publication" in параметры:
                публикация = параметры["publication"]

            if "пользователь" in параметры:
                пользователь = параметры["пользователь"]
            if "user" in параметры:
                пользователь = параметры["user"]

            if "пароль" in параметры:
                пароль = параметры["пароль"]
            if "password" in параметры:
                пароль = параметры["password"]


        self.__connectionSettings = НастройкиПодключения(публикация, пользователь, пароль)
        self.__metadata = МетаданныеКонфигурация(self)
        self.__dataContext = КонтекстДанных(self)


        session = Session()
        session.auth = HTTPBasicAuth(
            username=пользователь,
            password=пароль
        )

        self.__soapClient = Client(
            wsdl=публикация.rstrip('/') + "/ws/brom_api?wsdl",
            transport=Transport(
                session=session,
                cache=SqliteCache()
            )
        )

        self.__serializer = Сериализатор(self)

    @property
    def Метаданные(self):
        return self.__metadata

    @property
    def SoapКлиент(self):
        return self.__soapClient

    def НастройкиПодключения(self):
        return self.__connectionSettings

    def Контекст(self):
        return self.__dataContext

    def Сериализатор(self):
        return self.__serializer

    def ЗагрузитьМетаданные(self, состав = "", размерПакета = 0):
        self.Метаданные.Загрузить(состав, размерПакета)

    def ПолучитьИнформациюОСистеме(self):
        info =  self.SoapКлиент.service.GetSystemInfo()
        return self.Сериализатор().ИзЗначенияБром(info)

    def ВызватьМетод(self, имяМодуля, имяМетода, *параметры):
        self.ВызватьМетодСМассивомПараметров(имяМодуля, имяМетода, параметры)

    def ВызватьМетодСМассивомПараметров(self, имяМодуля, имяМетода, параметры):
        paramArray = self.__serializer.ВЗначениеБром(параметры)
        value = self.__soapClient.service.ExecuteMethod(имяМодуля, имяМетода, paramArray)
        return self.__serializer.ИзЗначенияБром(value)

    def ПолучитьЗначениеПараметраСеанса(self, имяПараметраСеанса):
        value = self.__soapClient.service.GetSessionParameter(имяПараметраСеанса)
        return self.__serializer.ИзЗначенияБром(value)

    def ПолучитьЗначениеКонстанты(self, имяКонстанты):
        value = self.__soapClient.service.GetConstant(имяКонстанты, None)
        return self.__serializer.ИзЗначенияБром(value)

    def УстановитьЗначениеКонстанты(self, имяКонстанты, значение):
        self.__soapClient.service.SetConstant(имяКонстанты, self.__serializer.ВЗначениеБром(значение))

    def СоздатьСелектор(self):
        return Селектор(self)

    def СоздатьЗапрос(self, текст = ""):
        return Запрос(self, текст)


    def __executeQuery(self, текстЗапроса, параметры = None, отбор = None, поля = None, порядок = None, пакетный = False, типОбхода = ОбходРезультатаЗапроса.Прямой, включатьВременныеДанные = False):
        фабрика = self.Сериализатор().Фабрика

        params = []
        if параметры:
            for ключ, значение in параметры.items():
                params.append(фабрика.RequestParameter(
                    Key=ключ,
                    Value=self.Сериализатор().ВЗначениеБром(значение)
                ))

        filters = []
        if отбор:
            for условиеОтбора in отбор:
                filters.append(фабрика.RequestFilter(
                    Key=условиеОтбора.Ключ,
                    Value=self.Сериализатор().ВЗначениеБром(условиеОтбора.Значение),
                    ComparisonType=условиеОтбора.ВидСравнения.name
                ))

        fields = []
        if поля:
            for поле in поля:
                fields.append(фабрика.RequestField(
                    Key=поле.Ключ,
                    Name=поле.Псевдоним
                ))

        sort = []
        if порядок:
            for сортировка in sort:
                sort.append(фабрика.RequestSort(
                    Key=сортировка.Ключ,
                    Direction= "Убыв" if сортировка.Направление == НаправлениеСортировки.Убывание else "Возр"
                ))

        settings = фабрика.ExecuteRequest_Settings(
            Parameter=params,
            Filter=filters,
            Field=fields,
            Sort=sort,
            QueryResultIteration=типОбхода.name,
            IncludeTemporalData=включатьВременныеДанные
        )

        if not пакетный:
            result = self.__soapClient.service.ExecuteRequest(текстЗапроса, settings)
        else:
            result = self.__soapClient.service.ExecuteRequestBatch(текстЗапроса, settings)

        return self.Сериализатор().ИзЗначенияБром(result)

    def ВыполнитьЗапрос(self, текстЗапроса, параметры = None, отборы = None, поля = None, порядок = None, типОбхода = ОбходРезультатаЗапроса.Прямой):
        return self.__executeQuery(текстЗапроса, параметры, отборы, поля, порядок, False, типОбхода)

    def ВыполнитьПакетныйЗапрос(self, текстЗапроса, параметры = None, отборы = None, поля = None, порядок = None, типОбхода = ОбходРезультатаЗапроса.Прямой, включатьВременныеДанные = False):
        return self.__executeQuery(текстЗапроса, параметры, отборы, поля, порядок, True, типОбхода, включатьВременныеДанные)

    def ПолучитьДанныеОбъекта(self, ссылка, поля = None, автозагрузкаПолей = None):
        if not автозагрузкаПолей:
            автозагрузкаПолей = АвтозагрузкаПолейОбъектов.Ничего()

        фабрика = self.Сериализатор().Фабрика

        fields = []
        if поля:
            for поле in поля:
                fields.append(фабрика.RequestField(
                    Key=поле
                ))

        settings = фабрика.GetObject_Settings(
            Field=fields,
            AddSkippedProperties=True,
            PropertiesHierarchyType="Hierarchy",
            FieldAutoinclusion=фабрика.RequestFieldAutoinclusionSettings(
                DefaultFields=автозагрузкаПолей.ЗагружатьСтандартныеРеквизиты,
                CustomFields=автозагрузкаПолей.ЗагружатьПользовательскиеРеквизиты,
                Tables=автозагрузкаПолей.ЗагружатьТабличныеЧасти
            )
        )

        result = self.__soapClient.service.GetObject(self.Сериализатор().ВЗначениеБром (ссылка), settings)

        return self.Сериализатор().ИзЗначенияБромВДерево(result)


    # Методы для отладки
    def Ping(self):
        return self.SoapКлиент.service.DebugPing()

    def Эхо(self, значение):
        значениеБром = self.Сериализатор().ВЗначениеБром(значение)
        ответ = self.SoapКлиент.service.DebugEcho(значениеБром)
        return self.Сериализатор().ИзЗначенияБром(ответ)


    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

    def _tryget(self, name):
        текМетаданные = self.Метаданные.Найти(name)
        if текМетаданные:
            имяМетаданных = текМетаданные.Имя()
            if имяМетаданных == "ПараметрыСеанса":
                return ПараметрыСеансаМенеджер(self)
            if имяМетаданных == "КритерииОтбора":
                return КритерииОтбораМенеджер(self)
            if имяМетаданных == "Константы":
                return КонстантыМенеджер(self)
            if имяМетаданных == "Справочники":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.Справочник)
            if имяМетаданных == "Документы":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.Документ)
            if имяМетаданных == "Перечисления":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.Перечисление)
            if имяМетаданных == "ПланыВидовХарактеристик":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.ПланВидовХарактеристик)
            if имяМетаданных == "ПланыСчетов":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.ПланСчетов)
            if имяМетаданных == "ПланыВидовРасчета":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.ПланВидовРасчета)
            if имяМетаданных == "БизнесПроцессы":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.БизнесПроцесс)
            if имяМетаданных == "Задачи":
                return ОбъектыМенеджер(self, текМетаданные, ТипКоллекции.Задача)
            if имяМетаданных == "ЖуралыДокументов":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "Обработки":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "Отчеты":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "РегистрыСведений":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "РегистрыНакопления":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "РегистрыБухгалтерии":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "РегистрыРасчета":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "Последовательности":
                return КоллекцияМенеджер(self, текМетаданные)
            if имяМетаданных == "ОбщиеМодули":
                return None

        текМетаданные = self.Метаданные.Найти("ОбщиеМодули." + name)
        if текМетаданные:
            return ОбщийМодуль(self, текМетаданные)

        return lambda *args: self._trycall(name, args)

    def _trycall(self, name, args):
        return self.ВызватьМетодСМассивомПараметров("", name, args)

class ДокументМенеджер(ОбъектМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные, ТипКоллекции.Документ)

    def СоздатьДокумент(self):
        return self.СоздатьОбъект()

class ДокументОбъект(КонтекстОбъекта):
    def __init__(self, ссылка):
        super().__init__(ссылка)

    def Записать(self, режимЗаписиДокумента = РежимЗаписиДокумента.Запись, режимПроведенияДокумента = РежимПроведенияДокумента.Неоперативный):
        self._записатьДанные(режимЗаписиДокумента, режимПроведенияДокумента)

class ЗадачаМенеджер(ОбъектМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные, ТипКоллекции.Задача)

    def СоздатьЗадачу(self):
        return self.СоздатьОбъект()

class ЗадачаОбъект(КонтекстОбъекта):
    def __init__(self, ссылка):
        super().__init__(ссылка)

class Запрос:
    def __init__(self, клиент, текст = ""):
        self.__bromClient = клиент
        self.__parameters = {}
        self.__filters = []
        self.__fields = []
        self.__sort = []

        self.__text = текст

    @property
    def Клиент(self):
        return self.__bromClient

    @property
    def Текст(self):
        return self.__text

    @Текст.setter
    def Текст(self, value):
        self.__text = value

    @property
    def Параметры(self):
        return self.__parameters

    @property
    def ВыбранныеПоля(self):
        return self.__fields

    @property
    def Порядок(self):
        return self.__sort

    @property
    def Отбор(self):
        return self.__filters

    def УстановитьПараметр(self, имя, значение):
        self.__parameters[имя] = значение

    def ДобавитьУсловиеОтбора(self, путьКДанным, значение, видСравнения = ВидСравнения.Равно):
        условие = УсловиеОтбора(путьКДанным, значение, видСравнения)
        self.__filters.append(условие)
        return условие

    def ДобавитьУпорядочение(self, путьКДанным, направление = НаправлениеСортировки.Возрастание):
        self.__sort.append(Сортировка(путьКДанным, направление))

    def ДобавитьПоле(self, путьКДанным, псевдоним = None):
        self.__fields.append(ПолеДанных(путьКДанным, псевдоним))

    def Выполнить(self, типОбхода = ОбходРезультатаЗапроса.Прямой):
        return self.__bromClient.ВыполнитьЗапрос(
            self.__text,
            self.__parameters,
            self.__filters,
            self.__fields,
            self.__sort, типОбхода
        )

    def ВыполнитьПакет(self, типОбхода = ОбходРезультатаЗапроса.Прямой, включатьВременныеДанные = False):
        return self.__bromClient.ВыполнитьПакетныйЗапрос(
            self.__text,
            self.__parameters,
            self.__filters,
            self.__fields,
            self.__sort, типОбхода,
            включатьВременныеДанные
        )

class КонстантаМенеджер(МодульМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные)

class КонстантыМенеджер(КоллекцияМенеджер):
    def __init__(self, клиент):
        super().__init__(клиент, клиент.Метаданные.Найти("Константы"))

    def __tryget(self, name):
        метаданные = self._moduleMetadata.Найти(name)
        if метаданные:
            return КонстантаМенеджер(self._bromClient, метаданные)
        return None


    def __getattr__(self, item):
        return self.__tryget(item)

    def __getitem__(self, item):
        return self.__tryget(item)

class КонтекстДанных:
    def __init__(self, клиент):
        self.__bromClient = клиент
        self.__data = WeakKeyDictionary()
        self.__references = WeakValueDictionary()

    @property
    def Клиент(self):
        return self.__bromClient

    def __получитьУзелДанныхОбъекта(self, ссылка):
        node = self.__data.get(ссылка)
        if not node:
            node = {}
            self.__data[ссылка] = node
        return node

    def __удалитьУзелДанныхОбъекта(self, ссылка):
        if ссылка in self.__data:
            self.__data.pop(ссылка)

    def __инициализироватьДанныеОбъекта(self, ссылка):
        данныеОбъекта = self.__получитьУзелДанныхОбъекта(ссылка)
        данныеОбъекта.clear()

        реквизиты = ссылка.Метаданные().НайтиПодчиненный("Реквизиты")
        for key in реквизиты.ИменаПодчиненных():
            данныеОбъекта[key.lower()] = None
        данныеОбъекта["#"] = None

    def __получитьТабличнуюЧасть(self, ссылка, метаданные):
        данныеОбъекта = self.__получитьУзелДанныхОбъекта(ссылка)
        таблЧасть = данныеОбъекта.get(метаданные.Имя())
        if таблЧасть == None or not isinstance(таблЧасть, ТабличнаяЧасть):
            таблЧасть = ТабличнаяЧасть(метаданные)
            self.__установитьЗначениеПоляОбъекта(ссылка, метаданные.Имя(), таблЧасть)
        return таблЧасть

    def __установитьЗначениеПоляОбъекта(self, ссылка, имяПоля, значение):
        данныеОбъекта = self.__получитьУзелДанныхОбъекта(ссылка)
        данныеОбъекта[имяПоля.lower()] = значение

    def __установитьПредставлениеОбъекта(self, ссылка, представление):
        if представление == None:
            return

        данныеОбъекта = self.__получитьУзелДанныхОбъекта(ссылка)
        данныеОбъекта["#"] = представление

    def __установитьЗначенияИзСвойствSOAP(self, ссылка, properties):
        if properties == None:
            return

        реквизиты = ссылка.Метаданные().НайтиПодчиненный("Реквизиты")
        таблЧасти = ссылка.Метаданные().НайтиПодчиненный("ТабличныеЧасти")

        for property in properties:
            текМета = реквизиты.НайтиПодчиненный(property.Name)
            if текМета:
                значение = self.Клиент.Сериализатор().ИзЗначенияБром(property)
                self.__установитьЗначениеПоляОбъекта(ссылка, текМета.Имя(), значение)
                continue

            текМета = таблЧасти.НайтиПодчиненный(property.Name)
            if текМета:
                значение = self.Клиент.Сериализатор().ИзЗначенияБром(property)
                if isinstance(значение, ТаблицаЗначений):
                    таблЧасть = self.__получитьТабличнуюЧасть(ссылка, текМета)
                    таблЧасть._loadData(значение)

    def УничтожитьСсылку(self, ссылка):
        указатель = ссылка.УникальныйИдентификатор() if isinstance(ссылка, ОбъектСсылка) else ссылка.Имя()
        идСсылки = КонтекстДанных.__получитьОбобщенныйИдентификаторСсылки(ссылка.ПолноеИмяТипа(), указатель)

        if isinstance(ссылка, ОбъектСсылка):
            self.ОчиститьДанныеОбъекта(ссылка)
        if идСсылки in self.__references:
            self.__references.pop(идСсылки)

    def ПолучитьЗначение(self, ссылка, имяПоля):
        if not isinstance(ссылка, ОбъектСсылка):
            raise ValueError()

        текИмяПоля = имяПоля.lower()
        if текИмяПоля == "ссылка" or текИмяПоля == "ref":
            return ссылка

        реквизит = ссылка.Метаданные().Реквизиты.НайтиПодчиненный(имяПоля)
        if (реквизит):
            if ссылка.Пустая():
                return None

            данныеОбъекта = self.__получитьУзелДанныхОбъекта(ссылка)
            if текИмяПоля in данныеОбъекта:
                return данныеОбъекта[текИмяПоля]

            self.ЗагрузитьДанныеОбъекта(ссылка)
            return self.ПолучитьЗначение(ссылка, имяПоля)

        реквизит = ссылка.Метаданные().ТабличныеЧасти.НайтиПодчиненный(имяПоля)
        if (реквизит):
            if ссылка.Пустая():
                return None

            данныеОбъекта = self.__получитьУзелДанныхОбъекта(ссылка)
            if текИмяПоля in данныеОбъекта:
                таблЧасть = данныеОбъекта.get(текИмяПоля)
                if таблЧасть == None:
                    таблЧасть = self.__получитьТабличнуюЧасть(ссылка, реквизит)
                    данныеОбъекта[текИмяПоля] = таблЧасть
                return таблЧасть

            self.ЗагрузитьДанныеОбъекта(ссылка)
            return self.ПолучитьЗначение(ссылка, имяПоля)

        raise Exception('Поле "{0}" не определено.'.format(имяПоля))

    def ПолучитьПредставлениеОбъекта(self, ссылка):
        if ссылка.Пустая():
            return ""

        данныеОбъекта = self.__получитьУзелДанныхОбъекта(ссылка)
        представление = данныеОбъекта.get("#")
        if not представление == None:
            return представление

        self.ЗагрузитьДанныеОбъекта(ссылка)
        return self.ПолучитьПредставлениеОбъекта(ссылка)

    def ОчиститьДанныеОбъекта(self, ссылка):
        self.__удалитьУзелДанныхОбъекта(ссылка)

    def ЗагрузитьДанныеОбъекта(self, ссылка):
        фабрика = self.Клиент.Сериализатор().Фабрика;

        settings = фабрика.GetObject_Settings(
            AddSkippedProperties=True,
            FieldAutoinclusion = фабрика.RequestFieldAutoinclusionSettings(
                DefaultFields=True,
                CustomFields=True,
                Tables=True
            )
        )

        refSoap = self.Клиент.SoapКлиент.service.GetObject(self.Клиент.Сериализатор().ВЗначениеБром(ссылка), settings)

        self.__инициализироватьДанныеОбъекта(ссылка)

        self.__установитьПредставлениеОбъекта(ссылка, refSoap.Presentation)
        self.__установитьЗначенияИзСвойствSOAP(ссылка, refSoap.Property)


    def ПолучитьОбъектСсылку(self, полноеИмяТипа, указатель):
        узелМетаданных = self.Клиент.Метаданные.Получить(полноеИмяТипа)
        if not узелМетаданных:
            raise 'Ошибка при получении ссылки на объект. Не удалось обнаружить объект метаданных "{0}".'.format(полноеИмяТипа)

        идСсылки = КонтекстДанных.__получитьОбобщенныйИдентификаторСсылки(полноеИмяТипа, str(указатель))

        ссылка = self.__references.get(идСсылки)
        if ссылка:
            return ссылка

        типКоллекции = узелМетаданных.ТипКоллекции()
        if типКоллекции == ТипКоллекции.Справочник:
            ссылка = СправочникСсылка(self.__bromClient, узелМетаданных.Имя(), указатель)
        elif типКоллекции == ТипКоллекции.Документ:
            ссылка = ДокументСсылка(self.__bromClient, узелМетаданных.Имя(), указатель)
        elif типКоллекции == ТипКоллекции.ПланВидовХарактеристик:
            ссылка = ПланВидовХарактеристикСсылка(self.__bromClient, узелМетаданных.Имя(), указатель)
        elif типКоллекции == ТипКоллекции.ПланСчетов:
            ссылка = ПланСчетовСсылка(self.__bromClient, узелМетаданных.Имя(), указатель)
        elif типКоллекции == ТипКоллекции.ПланВидовРасчета:
            ссылка = ПланВидовРасчетаСсылка(self.__bromClient, узелМетаданных.Имя(), указатель)
        elif типКоллекции == ТипКоллекции.Задача:
            ссылка = ЗадачаСсылка(self.__bromClient, узелМетаданных.Имя(), указатель)
        elif типКоллекции == ТипКоллекции.БизнесПроцесс:
            ссылка = БизнесПроцессСсылка(self.__bromClient, узелМетаданных.Имя(), указатель)
        else:
            raise Exception("Указан неверный тип коллекции.")

        self.__references[идСсылки] = ссылка

        return ссылка

    def ПолучитьПеречислениеСсылку(self, полноеИмяТипа, указатель, синоним = ""):
        узелМетаданных = self.Клиент.Метаданные.Получить(полноеИмяТипа)
        if not узелМетаданных:
            raise 'Ошибка при получении ссылки на объект. Не удалось обнаружить объект метаданных "{0}".'.format(полноеИмяТипа)

        if узелМетаданных.ТипКоллекции() != ТипКоллекции.Перечисление:
            raise Exception('Указан неверный тип коллекции.')

        идСсылки = КонтекстДанных.__получитьОбобщенныйИдентификаторСсылки(полноеИмяТипа, указатель)

        ссылка = self.__references.get(идСсылки)
        if ссылка:
            return ссылка

        ссылка = ПеречислениеСсылка(self.__bromClient, узелМетаданных.Имя(), указатель, синоним)

        self.__references[идСсылки] = ссылка

        return ссылка

    @staticmethod
    def __получитьОбобщенныйИдентификаторСсылки(полноеИмяТипа, указатель):
        representation = (полноеИмяТипа + "#" + str(указатель)).lower()
        return sha1(representation.encode('utf-8')).hexdigest()

class КритерииОтбораМенеджер(КоллекцияМенеджер):
    def __init__(self, клиент):
        super().__init__(клиент, клиент.Метаданные.Найти("КритерииОтбора"))

    def __tryget(self, name):
        метаданные = self._moduleMetadata.Найти(name)
        if метаданные:
            return КритерийОтбораМенеджер(self._bromClient, метаданные)
        return None


    def __getattr__(self, item):
        return self.__tryget(item)

    def __getitem__(self, item):
        return self.__tryget(item)

class КритерийОтбораМенеджер(МодульМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные)

class НаблюдаемыйСписок(list):
    def __init__(self, наблюдатель):
        super().__init__()

        self.__observer = наблюдатель
        self.__observer_method = "_" + self.__observer.__class__.__name__ + "__onMemberChanged"

    def __notifyObserver(self):
        getattr(self.__observer, self.__observer_method)()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.__notifyObserver()

    def append(self, object):
        super().append(object)
        self.__notifyObserver()

    def remove(self, object):
        super().remove(object)
        self.__observer.__onMemberChanged()

    def insert(self, index, object):
        super().insert(index, object)
        self.__notifyObserver()

    def sort(self, *, key = ..., reverse = ...):
        super().sort(key, reverse)
        self.__notifyObserver()

    def reverse(self):
        super().reverse()
        self.__notifyObserver()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.__notifyObserver()

class НастройкиПодключения:
    def __init__(self, адресПубликации, имяПользователя, пароль):
        self.__publicationAddress = адресПубликации
        self.__userName = имяПользователя
        self.__password = пароль

    @property
    def АдресПубликации(self):
        return self.__publicationAddress

    @property
    def ИмяПользователя(self):
        return self.__userName

    @property
    def Пароль(self):
        return self.__password

class ОбъектыМенеджер(КоллекцияМенеджер):
    def __init__(self, клиент, метаданныеКоллекции, типКоллекции):
        super().__init__(клиент, метаданныеКоллекции)
        self.__collectionType = типКоллекции

    def __tryget(self, name):
        метаданные = self._moduleMetadata.Найти(name)
        if метаданные:
            if self.__collectionType == ТипКоллекции.Справочник:
                return СправочникМенеджер(self._bromClient, метаданные)
            if self.__collectionType == ТипКоллекции.Документ:
                return ДокументМенеджер(self._bromClient, метаданные)
            if self.__collectionType == ТипКоллекции.Перечисление:
                return ПеречислениеМенеджер(self._bromClient, метаданные)
            if self.__collectionType == ТипКоллекции.ПланВидовХарактеристик:
                return ПланВидовХарактеристикМенеджер(self._bromClient, метаданные)
            if self.__collectionType == ТипКоллекции.ПланСчетов:
                return ПланСчетовМенеджер(self._bromClient, метаданные)
            if self.__collectionType == ТипКоллекции.ПланВидовРасчета:
                return ПланВидовРасчетаМенеджер(self._bromClient, метаданные)
            if self.__collectionType == ТипКоллекции.БизнесПроцесс:
                return БизнесПроцессМенеджер(self._bromClient, метаданные)
            if self.__collectionType == ТипКоллекции.Задача:
                return ЗадачаМенеджер(self._bromClient, метаданные)
        return None


    def __getattr__(self, item):
        return self.__tryget(item)

    def __getitem__(self, item):
        return self.__tryget(item)

class ПараметрыСеансаМенеджер(КоллекцияМенеджер):
    def __init__(self, клиент):
        super().__init__(клиент, клиент.Метаданные.Найти("ПараметрыСеанса"))

    def __tryget(self, name):
        метаданные = self._moduleMetadata.Найти(name)
        if метаданные:
            return self._bromClient.ПолучитьЗначениеПараметраСеанса(метаданные.Имя())
        return None


    def __getattr__(self, item):
        return self.__tryget(item)

    def __getitem__(self, item):
        return self.__tryget(item)

class ПеречислениеМенеджер(МодульМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные)

    def СоздатьСелектор(self):
        селектор = Селектор(self.__dict__["_bromClient"])
        селектор.УстановитьКоллекцию(ТипКоллекции.Перечисление, self.__dict__["_moduleMetadata"].Имя())
        return селектор

    def ПустаяСсылка(self):
        return self.__dict__["_bromClient"].Контекст().ПолучитьПеречислениеСсылку(
            self.__dict__["_moduleMetadata"].ПолноеИмя(),
            ""
        )

    def _tryget(self, name):
        предопределенные = self.__dict__["_moduleMetadata"].Предопределенные
        if предопределенные and предопределенные.СвойствоОпределено(name):
            return предопределенные[name]

        return None

    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)

class ПланВидовРасчетаМенеджер(ОбъектМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные, ТипКоллекции.ПланВидовРасчета)

    def СоздатьВидРасчета(self):
        return self.СоздатьОбъект()

class ПланВидовРасчетаОбъект(КонтекстОбъекта):
    def __init__(self, ссылка):
        super().__init__(ссылка)

class ПланВидовХарактеристикМенеджер(ОбъектМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные, ТипКоллекции.ПланВидовХарактеристик)

    def СоздатьЭлемент(self):
        объект = self.СоздатьОбъект()
        if self.__dict__["_moduleMetadata"].Метаданные.Найти("Реквизиты.ЭтоГруппа"):
            объект.ЭтоГруппа = False
        return объект

    def СоздатьГруппу(self):
        объект = self.СоздатьОбъект()
        if self.__dict__["_moduleMetadata"].Найти("Реквизиты.ЭтоГруппа"):
            объект.ЭтоГруппа = True
        return объект

class ПланВидовХарактеристикОбъект(КонтекстОбъекта):
    def __init__(self, ссылка):
        super().__init__(ссылка)

class ПланСчетовМенеджер(ОбъектМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные, ТипКоллекции.ПланСчетов)

    def СоздатьСчет(self):
        return self.СоздатьОбъект()

class ПланСчетовОбъект(КонтекстОбъекта):
    def __init__(self, ссылка):
        super().__init__(ссылка)

class ПолеДанных:
    def __init__(self, ключ, псевдоним = None):
        self.__key = ключ
        self.__name = псевдоним

    @property
    def Ключ(self):
        return self.__key

    @property
    def Псевдоним(self):
        return self.__name

class Селектор:
    def __init__(self, клиент):
        self.__bromClient = клиент

        self.__collectionType = None
        self.__collectionName = ""
        self.__collectionMetadata = None

        self.__limit = 0;

        self.__fields = НаблюдаемыйСписок(self)
        self.__filters = НаблюдаемыйСписок(self)
        self.__sort = НаблюдаемыйСписок(self)

        self.__fieldsAutoloadSettings = АвтозагрузкаПолейОбъектов.Ничего()

        self.__items = []

        self.__isModified = False

    @property
    def Клиент(self):
        return self.__bromClient

    @property
    def ТипКоллекции(self):
        return self.__collectionType

    @property
    def ИмяКоллекции(self):
        return self.__collectionName

    @property
    def Лимит(self):
        return int(self.__limit)

    @Лимит.setter
    def Лимит(self, value):
        self.__limit = int(value) if value > 0 else 0;
        self.__isModified = True

    @property
    def МетаданныеКоллекции(self):
        return self.__collectionMetadata

    def Количество(self):
        return len(self.__items)

    @property
    def АвтозагрузкаПолей(self):
        return self.__fieldsAutoloadSettings

    @АвтозагрузкаПолей.setter
    def АвтозагрузкаПолей(self, value):
        self.__fieldsAutoloadSettings = value if isinstance(value, АвтозагрузкаПолейОбъектов) else АвтозагрузкаПолейОбъектов.Ничего()
        self.__isModified = True

    @property
    def Поля(self):
        return self.__fields

    @property
    def Отбор(self):
        return self.__filters

    @property
    def Порядок(self):
        return self.__sort

    def ВыгрузитьРезультат(self):
        if self.__isModified:
            self.Выполнить()

        return self.__items.copy()

    def УстановитьКоллекцию(self, полноеИмяКоллекции):
        if not полноеИмяКоллекции.strip():
            raise ValueError("Указано некорректное полноеИмяКоллекции коллекции.")

        фрагментыИмени = полноеИмяКоллекции.split(".")
        if len(фрагментыИмени) != 2:
            raise ValueError("Указано некорректное полноеИмяКоллекции коллекции.")

        типКоллекции = ТипКоллекции[фрагментыИмени[0]]

        метаданные = self.__bromClient.Метаданные.Получить(полноеИмяКоллекции)
        if not метаданные:
            raise Exception('Коллекция с именем "{0}" не определена.'.format(полноеИмяКоллекции))

        self.__collectionType = типКоллекции
        self.__collectionName = метаданные.Имя()
        self.__collectionMetadata = метаданные

        self.__isModified = True

    def __addFields(self, именаПолей):
        поля = []
        if isinstance(именаПолей, str):
            поля = поля + именаПолей.split(",")
        elif isinstance(именаПолей, list):
            поля = поля + именаПолей
        elif isinstance(именаПолей, tuple):
            поля = поля + list(именаПолей)

        for поле in поля:
            self.__fields.append(поле.strip())

        self.__isModified = True


    def ДобавитьПоля(self, *ключиПолей):
        for времПоля in ключиПолей:
            self.__addFields(времПоля)

    def ДобавитьСортировку(self, ключПоля, направлениеСортировки = НаправлениеСортировки.Возрастание):
        self.__sort.append(Сортировка(ключПоля, направлениеСортировки))

        self.__isModified = True

    def ДобавитьОтбор(self, ключПоля, значение, видСравнения = ВидСравнения.Равно):
        self.__filters.append(УсловиеОтбора(ключПоля, значение, видСравнения))

        self.__isModified = True

    def Выполнить(self):
        if not self.__collectionMetadata:
            raise Exception("Не установлена коллекция для получения выборки.")

        фабрика = self.Клиент.Сериализатор().Фабрика

        fields = []
        for field in self.Поля:
            fields.append(фабрика.RequestField(Key=field))

        filters = []
        for filter in self.Отбор:
            filters.append(фабрика.RequestFilter(
                Key=filter.Ключ,
                Value=self.Клиент.Сериализатор().ВЗначениеБром(filter.Значение),
                ComparisonType=filter.ВидСравнения.name
            ))

        sorts = []
        for sort in self.Порядок:
            sorts.append(фабрика.RequestSort(
                Key=sort.Ключ,
                Direction= "Убыв" if sort.Направление == НаправлениеСортировки.Убывание else "Возр"
            ))


        settings = фабрика.GetObjectList_Settings(
            AddSkippedProperties=True,
            PropertiesHierarchyType="Hierarchy",
            FieldAutoinclusion=фабрика.RequestFieldAutoinclusionSettings(
                DefaultFields=self.АвтозагрузкаПолей.ЗагружатьСтандартныеРеквизиты,
                CustomFields=self.АвтозагрузкаПолей.ЗагружатьПользовательскиеРеквизиты,
                Tables=self.АвтозагрузкаПолей.ЗагружатьТабличныеЧасти
            ),
            Limit=self.__limit,
            Field=fields,
            Filter=filters,
            Sort=sorts
        )

        objectList = self.Клиент.SoapКлиент.service.GetObjectList(
            self.ТипКоллекции.name,
            self.ИмяКоллекции,
            settings
        )

        self.__items.clear()

        if objectList.Item:
            for item in objectList.Item:
                self.__items.append(self.Клиент.Сериализатор().ИзЗначенияБром(item))

        self.__isModified = False

        return self

    def Сбросить(self):
        self.__items.clear()
        self.__fields.clear()
        self.__filters.clear()
        self.__sort.clear()

        self.__limit = 0
        self.__collectionMetadata = None
        self.__collectionName = ""

        self.__isModified = False

        return self

    def Выбрать(self, *ключиПолей):
        for времПоля in ключиПолей:
            self.__addFields(времПоля)
        return self

    def Первые(self, лимит):
        self.Лимит = лимит
        return self

    def Из(self, полноеИмяКоллекции):
        self.УстановитьКоллекцию(полноеИмяКоллекции)
        return self

    def Где(self, ключПоля, значение, видСравнения = ВидСравнения.Равно):
        self.ДобавитьОтбор(ключПоля, значение, видСравнения)
        return self

    def Упорядочить(self, ключПоля, направлениеСортировки = НаправлениеСортировки.Возрастание):
        self.ДобавитьСортировку(ключПоля, направлениеСортировки)
        return self

    def __len__(self):
        return len(self.__items)

    def __getitem__(self, item):
        return self.__items[item]

    def __iter__(self):
        if self.__isModified:
            self.Выполнить()

        for item in self.__items:
            yield item

    def __contains__(self, item):
        return item in self.__items

    def __bool__(self):
        return bool(self.__items)

    def __onMemberChanged(self):
        self.__isModified = True

class Сортировка:
    def __init__(self, ключ, направлениеСортировки = НаправлениеСортировки.Возрастание):
        self.__key = ключ
        self.__sortDirection = направлениеСортировки

    @property
    def Ключ(self):
        return self.__key

    @property
    def Направление(self):
        return self.__sortDirection

class СправочникМенеджер(ОбъектМенеджер):
    def __init__(self, клиент, метаданные):
        super().__init__(клиент, метаданные, ТипКоллекции.Справочник)

    def СоздатьЭлемент(self):
        объект = self.СоздатьОбъект()
        if self.__dict__["_moduleMetadata"].Метаданные.Найти("Реквизиты.ЭтоГруппа"):
            объект.ЭтоГруппа = False
        return объект

    def СоздатьГруппу(self):
        объект = self.СоздатьОбъект()
        if self.__dict__["_moduleMetadata"].Найти("Реквизиты.ЭтоГруппа"):
            объект.ЭтоГруппа = True
        return объект

class СправочникОбъект(КонтекстОбъекта):
    def __init__(self, ссылка):
        super().__init__(ссылка)

class СтрокаТабличнойЧасти:
    def __init__(self, таблЧасть):
        self.__dict__["__tableSection"] = таблЧасть
        self.__dict__["__values"] = {}

    def __ismutable(self):
        return isinstance(self.__dict__["__tableSection"], ТабличнаяЧастьКонтекст)

    def __setValue(self, имяПоля, значение):
        self.__dict__["__values"][имяПоля] = значение

    def _tryget(self, name):
        реквизит = self.__dict__["__tableSection"].Метаданные().Реквизиты.НайтиПодчиненный(name)
        if реквизит:
            return self.__dict__["__values"].get(реквизит.Имя())
        return None

    def __getattr__(self, item):
        return self._tryget(item)

    def __getitem__(self, item):
        return self._tryget(item)


    def _tryset(self, name, value):
        if self.__ismutable():
            реквизит = self.__dict__["__tableSection"].Метаданные().Реквизиты.НайтиПодчиненный(name)
            if реквизит:
                self.__dict__["__values"][реквизит.Имя()] = value
                self.__dict__["__tableSection"]._ТабличнаяЧастьКонтекст__setIsModified(True)

    def __setattr__(self, key, value):
        self._tryset(key, value)

    def __setitem__(self, key, value):
        self._tryset(key, value)

    def __iter__(self):
        ts = self.__dict__["__tableSection"]
        for реквизит in ts.Метаданные():
            yield реквизит.Имя(), self.__dict__["__values"].get(реквизит.Имя())

class ТабличнаяЧастьКонтекст(ТабличнаяЧасть):
    def __init__(self, родитель, метаданные):
        super().__init__(метаданные)
        self.__parent = родитель
        self.__isModified = False

    def __setIsModified(self, value):
        if not(self.__isModified) and value:
            self.__parent._КонтекстОбъекта__addModifiedField(self.Метаданные().Имя())
        self.__isModified = value

    def Добавить(self):
        стр = super()._addRow()
        self.__setIsModified(True)
        return стр

    def Удалить(self, строка):
        super()._removeRow(строка)
        self.__setIsModified(True)

    def Очистить(self):
        super()._clear()
        self.__setIsModified(True)

    def Загрузить(self, таблица):
        super()._loadData(таблица)
        self.__setIsModified(True)

class УсловиеОтбора:
    def __init__(self, ключ, значение, видСравнения = ВидСравнения.Равно):
        self.__key = ключ
        self.__value = значение
        self.__comparationType = видСравнения

    @property
    def Ключ(self):
        return self.__key

    @property
    def Значение(self):
        return self.__value

    @property
    def ВидСравнения(self):
        return self.__comparationType