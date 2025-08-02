import allure
import pytest
from datetime import datetime, date

from sqlmodel import Session


from models.spend import Category, Spend

from databases.spend_db import SpendDb


@allure.epic("Spend Management System")
@allure.feature("Database Operations")
class TestSpendDb:
    @pytest.fixture
    def spend_db(self, settings):
        with allure.step("Initialize SpendDB client"):
            return SpendDb(settings.SPEND_DB_URL)

    @pytest.fixture
    def test_category(self, spend_db, fake_name, random_category):
        with allure.step(f"Create test category '{random_category}' for user '{fake_name}'"):
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

            with allure.step(f"Cleanup test category {category.id}"):
                spend_db.delete_category(category.id)

    @pytest.fixture
    def test_spend(self, spend_db, test_category, new_spending_data, fake_name):
        with allure.step(f"Create test spend for category {test_category.id}"):
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

            with allure.step(f"Cleanup test spend {spend.id}"):
                spend_db.delete_spend(spend.id)

    @allure.story("CRUD Operations")
    def test_category_crud(self, test_category, spend_db, fake_name, random_category):
        with allure.step("Verify categories list contains test category"):
            categories = spend_db.get_categories(fake_name)
            assert len(categories) >= 1
            assert any(c.id == test_category.id for c in categories)

        with allure.step("Verify category details by ID"):
            category = spend_db.get_category_by_id(test_category.id)
            assert category is not None
            assert category.name == random_category
            assert category.username == fake_name
            assert not category.archived

    @allure.story("Spend Operations")
    def test_spend_operations(self, test_spend, spend_db, test_category, new_spending_data):
        with allure.step("Verify spend details"):
            spend = spend_db.get_spend_by_id(test_spend.id)
            assert spend is not None
            assert spend.amount == float(new_spending_data["amount"])
            assert spend.category_id == test_category.id
            assert isinstance(spend.spend_date, date)

    @allure.story("CRUD Operations")
    def test_update_category(self, test_category, spend_db):
        new_name = "Updated " + test_category.name

        with allure.step(f"Update category name to '{new_name}'"):
            spend_db.update_category(test_category.id, new_name=new_name)

        with allure.step("Verify category was updated"):
            updated = spend_db.get_category_by_id(test_category.id)
            assert updated.name == new_name

    @allure.story("CRUD Operations")
    def test_delete_category_by_name(self, spend_db, fake_name, random_category):
        with allure.step("Create temporary category"):
            temp_category = Category(
                name=random_category,
                username=fake_name,
                archived=False
            )
            with Session(spend_db.engine) as session:
                session.add(temp_category)
                session.commit()

        with allure.step(f"Delete category by name '{random_category}'"):
            spend_db.delete_category_by_name(random_category)

        with allure.step("Verify category was deleted"):
            assert spend_db.get_category_by_name(random_category) is None