import decimal

import pytest

from yadm import fields
from yadm.fields.money import DEFAULT_CURRENCY_STORAGE
from yadm.documents import Document


class TestMoney:
    def test_general(self):
        assert str(fields.Money(1, 'USD')) == '1.00 USD'
        assert str(fields.Money('1.2345', 840)) == '1.24 USD'
        assert str(fields.Money(10, 'RUB')) == '10.00 RUB'
        assert str(fields.Money('99', 'CHF')) == '99.00 CHF'

        assert str(fields.Money(5, 840)) == '5.00 USD'
        assert str(fields.Money(7, 826)) == '7.00 GBP'

        r1 = fields.Money(10, 'RUB')
        r2 = fields.Money(r1)
        assert r1 == r2
        assert r1 is not r2

        with pytest.raises(TypeError):
            fields.Money(r1, 'RUB')

    def test_from_string(self):
        assert fields.Money.from_string('1.00 USD') == fields.Money(1, 'USD')
        assert fields.Money.from_string('  1.2345  USD') == fields.Money('1.2345', 'USD')
        assert fields.Money.from_string('1\tUSD\n') == fields.Money(1, 'USD')
        assert fields.Money.from_string('1 840') == fields.Money(1, 'USD')

        with pytest.raises(decimal.InvalidOperation):
            fields.Money.from_string('one USD')

        with pytest.raises(ValueError):
            fields.Money.from_string('1 A01')

    def test_arithmetic_operations(self):
        r10 = fields.Money(10, 'RUB')
        r1 = fields.Money('1', 'RUB')
        u10 = fields.Money('10', 'USD')
        u1 = fields.Money(1, 'USD')

        assert r10 + r1 == fields.Money(11, 'RUB')
        assert r1 + r10 == fields.Money(11, 'RUB')
        assert r10 - r1 == fields.Money(9, 'RUB')
        assert r1 - r10 == fields.Money(-9, 'RUB')
        assert u10 + u1 == fields.Money(11, 'USD')
        assert u1 + u10 == fields.Money(11, 'USD')
        assert u10 - u1 == fields.Money(9, 'USD')
        assert u1 - u10 == fields.Money(-9, 'USD')

        assert r10 * 10 == fields.Money(100, 'RUB')
        assert 10 * r10 == fields.Money(100, 'RUB')
        assert r10 / 10 == fields.Money(1, 'RUB')
        assert u1 * 10 == fields.Money(10, 'USD')
        assert 10 * u1 == fields.Money(10, 'USD')
        assert u1 / 10 == fields.Money('0.1', 'USD')

    def test_is_methods(self):
        r0 = fields.Money(0, 'RUB')
        r1 = fields.Money(1, 'RUB')
        r_1 = fields.Money(-1, 'RUB')

        assert r0.is_zero()
        assert r1.is_positive()
        assert r_1.is_negative()

    def test_cmp(self):
        r0 = fields.Money(0, 'RUB')
        r1 = fields.Money(1, 'RUB')
        r_1 = fields.Money(-1, 'RUB')
        r10 = fields.Money(10, 'RUB')
        u1 = fields.Money(1, 'USD')

        assert r10 > r1
        assert not r10 < r1
        assert r1 < r10
        assert not r1 > r10
        assert r10 >= r1
        assert not r10 <= r1
        assert r1 <= r10
        assert not r1 >= r10

        assert r1 > 0
        assert not r1 < 0
        assert r_1 < 0
        assert not r_1 > 0

        assert not bool(r0)
        assert bool(r1)

        assert r0 == 0
        assert not r0 != 0

        with pytest.raises(ValueError) as e:
            r10 > u1

        with pytest.raises(TypeError) as e:
            r0 > 1
        assert 'unorderable types: Money() > int()' in str(e.value)

    def test_forbidden_operations(self):
        r1 = fields.Money('1', 'RUB')
        u1 = fields.Money(1, 'USD')

        with pytest.raises(ValueError) as e:
            u1 + r1

        s = "Money '1.00 USD' and '1.00 RUB' must be with the same currencies"
        assert s in str(e.value)

        with pytest.raises(TypeError) as e:
            u1 * r1

        s = "unsupported operand type(s) for *: 'Money' and 'Money'"
        assert s in str(e.value)

        with pytest.raises(TypeError) as e:
            u1 + 10

        s = "unsupported operand type(s) for +: 'Money' and 'int'"
        assert s in str(e.value)

        with pytest.raises(TypeError) as e:
            10 + u1

        s = "unsupported operand type(s) for +: 'int' and 'Money'"
        assert s in str(e.value)

    @pytest.mark.parametrize('iv, ov', [
        ('3.14', '3.14'),
        ('0.14', '0.14'),
        ('30.14', '30.14'),
        ('3.1', '3.10'),
        ('0.1', '0.10'),
    ])
    @pytest.mark.parametrize('cur', ['RUB', 'EUR', 'USD'])
    def test_money_str(self, iv, cur, ov):
        assert str(fields.Money(iv, cur)) == '{} {}'.format(ov, cur)

    @pytest.mark.parametrize('iv, ov', [
        ('3.14', 314),
        ('0.14', 14),
        ('30.14', 3014),
        ('3.1', 310),
        ('0.1', 10),
    ])
    @pytest.mark.parametrize('cur', ['RUB', 'EUR', 'USD'])
    @pytest.mark.parametrize('func', [
        lambda money: money.total_cents,
        lambda money: money.to_mongo()['v'],  # b/c function, for coverage
    ])
    def test_money_cents(self, func, iv, cur, ov):
        assert func(fields.Money(iv, cur)) == ov


class TestCurrencyStorage:
    @pytest.mark.parametrize('key, code, string, precision', [
        (643, 643, 'RUB', 2),
        ('RUB', 643, 'RUB', 2),
        (840, 840, 'USD', 2),
        ('USD', 840, 'USD', 2),
        (368, 368, 'IQD', 3),
        ('IQD', 368, 'IQD', 3),
    ])
    def test_currency_storage(self, key, code, string, precision):
        assert DEFAULT_CURRENCY_STORAGE[key].code == code
        assert DEFAULT_CURRENCY_STORAGE[key].string == string
        assert DEFAULT_CURRENCY_STORAGE[key].precision == precision

    @pytest.mark.parametrize('key', ['BLABLABLA', 100500])
    def test_currency_storage__key_error(self, key):
        with pytest.raises(KeyError):
            DEFAULT_CURRENCY_STORAGE[key]


class TestMoneyField:
    class Doc(Document):
        __collection__ = 'testdocs'
        money = fields.MoneyField(bbc='RUB')

    @pytest.mark.parametrize('value, currency, v, c', [
        ('3.14', 'USD', 314, 840),
        (1, 'CLF', 10000, 990),
        (1, 'BYR', 1, 974),
    ])
    def test_save(self, db, value, currency, v, c):
        doc = self.Doc()
        doc.money = fields.Money(value, currency)
        db.save(doc)

        data = db.db.testdocs.find_one()

        assert 'money' in data
        assert isinstance(data['money'], dict)
        assert data['money'] == {'c': c, 'v': v}

    @pytest.mark.parametrize('value, currency, v, c', [
        ('3.14', 'USD', 314, 840),
        (1, 'CLF', 10000, 990),
        (1, 'BYR', 1, 974),
    ])
    def test_load(self, db, value, currency, v, c):
        db.db.testdocs.insert({'money': {'c': c, 'v': v}})

        doc = db(self.Doc).find_one()

        assert hasattr(doc, 'money')
        assert isinstance(doc.money, fields.Money)
        assert doc.money == fields.Money(value, currency)

    def test_load_and_save(self, db):
        db.db.testdocs.insert({'money': {'v': 999, 'c': 840}})

        doc = db(self.Doc).find_one()
        doc.money = fields.Money('10.5', 'RUB')
        db.save(doc)

        assert hasattr(doc, 'money')
        assert isinstance(doc.money, fields.Money)
        assert doc.money == fields.Money('10.5', 'RUB')

        data = db.db.testdocs.find_one()

        assert 'money' in data
        assert isinstance(data['money'], dict)
        assert data['money'] == {'v': 1050, 'c': 643}

    def test_load_and_save_bbc(self, db):
        db.db.testdocs.insert({'money': 1234})

        doc = db(self.Doc).find_one()

        assert hasattr(doc, 'money')
        assert isinstance(doc.money, fields.Money)
        assert doc.money == fields.Money('12.34', 'RUB')
