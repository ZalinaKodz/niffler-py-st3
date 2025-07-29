import pytest
from datetime import datetime, date

from sqlmodel import Session


from models.spend import Category, Spend

from databases.spend_db import SpendDb


class TestSpendDb:
    @pytest.fixture
    def spend_db(self, settings):
        return SpendDb(settings.SPEND_DB_URL)

    @pytest.fixture
    def test_category(self, spend_db, fake_name, random_category):
        """Фикстура создает и возвращает тестовую категорию, удаляет после теста"""
        category = Category(
            name=random_category,
            username=fake_name,
            archived=False
        )
        with Session(spend_db.engine) as session:
            session.add(category)
            session.commit()
            session.refresh(category)
        yield category
        spend_db.delete_category(category.id)

    @pytest.fixture
    def test_spend(self, spend_db, test_category, new_spending_data, fake_name):
        """Фикстура создает и возвращает тестовый расход, удаляет после теста"""
        spend = Spend(
            amount=float(new_spending_data["amount"]),
            currency="USD",
            spend_date=datetime.now().date(),
            description="Test spend",
            category_id=test_category.id,
            username=fake_name
        )
        with Session(spend_db.engine) as session:
            session.add(spend)
            session.commit()
            session.refresh(spend)
        yield spend
        spend_db.delete_spend(spend.id)

    def test_category_crud(self, test_category, spend_db, fake_name, random_category):
        """Тест CRUD операций с категориями"""
        # Read проверки
        categories = spend_db.get_categories(fake_name)
        assert len(categories) >= 1
        assert any(c.id == test_category.id for c in categories)

        category = spend_db.get_category_by_id(test_category.id)
        assert category is not None
        assert category.name == random_category
        assert category.username == fake_name
        assert not category.archived

    def test_spend_operations(self, test_spend, spend_db, test_category, new_spending_data):
        """Тест операций с расходами"""
        spend = spend_db.get_spend_by_id(test_spend.id)
        assert spend is not None
        assert spend.amount == float(new_spending_data["amount"])
        assert spend.category_id == test_category.id
        assert isinstance(spend.spend_date, date)

    def test_update_category(self, test_category, spend_db):
        """Тест обновления категории"""
        new_name = "Updated " + test_category.name
        spend_db.update_category(test_category.id, new_name=new_name)

        updated = spend_db.get_category_by_id(test_category.id)
        assert updated.name == new_name

    def test_delete_category_by_name(self, spend_db, fake_name, random_category):
        """Тест удаления категории по имени"""
        # Создаем временную категорию
        temp_category = Category(
            name=random_category,
            username=fake_name,
            archived=False
        )
        with Session(spend_db.engine) as session:
            session.add(temp_category)
            session.commit()

        # Удаляем и проверяем
        spend_db.delete_category_by_name(random_category)
        assert spend_db.get_category_by_name(random_category) is None