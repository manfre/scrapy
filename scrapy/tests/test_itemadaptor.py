import unittest
import string
from scrapy.contrib_exp.newitem.adaptors import adaptor, ItemAdaptor
from scrapy.contrib_exp.newitem import * 


class BaseItem(Item):
    name = StringField()


class TestItem(BaseItem):
    url = StringField()
    summary = StringField()


class BaseAdaptor(ItemAdaptor):
    item_class = TestItem


class TestAdaptor(BaseAdaptor):
    name = lambda v: v.title()


class DefaultedAdaptor(BaseAdaptor):
    default_adaptor = lambda v: v[:-1]


class InheritDefaultAdaptor(DefaultedAdaptor):
    pass


class MultiValuedTestItem(Item):
    names = MultiValuedField(StringField)


class MultiValuedItemAdaptor(ItemAdaptor):
    item_class = MultiValuedTestItem

    names = adaptor(lambda v: v.title())


class ItemAdaptorTest(unittest.TestCase):

    def test_basic(self):
        ia = TestAdaptor()
        ia.name = 'marta'
        self.assertEqual(ia.item_instance.name, 'Marta')
        self.assertEqual(ia.name, 'Marta')

    def test_defaultadaptor(self):
        dta = DefaultedAdaptor()
        assert dta.default_adaptor
        dta.name = 'marta'
        self.assertEqual(dta.name, 'mart')

    def test_inheritdefaultadaptor(self):
        ida = InheritDefaultAdaptor()
        ida.name = 'marta'
        assert ida.name == 'mart'

    def test_inheritance(self):
        class ChildTestAdaptor(TestAdaptor):
            url = lambda v: v.lower()

        ia = ChildTestAdaptor()
        assert 'url' in ia._field_adaptors
        assert 'name' in ia._field_adaptors

        ia.url = 'HTTP://scrapy.ORG'
        self.assertEqual(ia.url, 'http://scrapy.org')

        ia.name = 'marta'
        self.assertEqual(ia.name, 'Marta')

        class ChildChildTestAdaptor(ChildTestAdaptor):
            url = lambda v: v.upper()
            summary = lambda v: v

        ia = ChildChildTestAdaptor()
        assert 'url' in ia._field_adaptors
        assert 'name' in ia._field_adaptors
        assert 'summary' in ia._field_adaptors

        ia.url = 'HTTP://scrapy.ORG'
        self.assertEqual(ia.url, 'HTTP://SCRAPY.ORG')

        ia.name = 'marta'
        self.assertEqual(ia.name, 'Marta')

    def test_staticmethods(self):
        class ChildAdaptor(TestAdaptor):
            name = adaptor(TestAdaptor.name, string.swapcase)

        ia = ChildAdaptor()
        ia.name = 'Marta'
        self.assertEqual(ia.name, 'mARTA')

    def test_staticdefaults(self):
        class ChildAdaptorDefaulted(DefaultedAdaptor):
            name = adaptor(DefaultedAdaptor.name, string.swapcase)

        dia = ChildAdaptorDefaulted()
        dia.name = 'marta'
        self.assertEqual(dia.name, 'MART')

    def test_multiplevaluedadaptor(self):
        ma = MultiValuedItemAdaptor()
        ma.names = ['name1', 'name2']
        assert ma.names == ['Name1', 'Name2']


class TreeadaptTest(unittest.TestCase):

    def test_1_passtrough(self):
        ad = adaptor()
        self.assertEqual(ad('string'), ['string'])

    def test_2_composing(self):
        addone = lambda v: v+1
        ad = adaptor(addone)
        self.assertEqual(ad(0), [1])

        addtwo = lambda v: v+2
        ad2 = adaptor(addone, addtwo)
        self.assertEqual(ad2(0), [3])

        ad3 = adaptor(ad, ad2)
        self.assertEqual(ad3(0), [4])

    def test_3_adaptor_args(self):
        addn = lambda v, adaptor_args: v + adaptor_args.get('add_value', 0)

        ad = adaptor(addn)
        self.assertEqual(ad(0), [0])
        self.assertEqual(ad(0, {'add_value': 3}), [3])
        self.assertEqual(ad(0), [0])

        ad = adaptor(addn, add_value=5)
        self.assertEqual(ad(0), [5])
        self.assertEqual(ad(0, {'add_value': 3}), [3])
        self.assertEqual(ad(0), [5])

    def test_4_treelogic(self):
        split1 = lambda v: v.split('&')
        split2 = lambda v: v.split('=')
        ad = adaptor(split1, split2)
        self.assertEqual(ad('name=joe&job=joker'), ['name', 'joe', 'job', 'joker'])
