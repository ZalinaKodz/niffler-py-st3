from typing import Any



class Verify:
    @staticmethod
    def category_structure(category: Any) -> None:
        """Проверка базовой структуры объекта категории"""
        assert hasattr(category, "id"), "Category missing id"
        assert hasattr(category, "name"), "Category missing name"
        assert hasattr(category, "archived"), "Category missing archived"
        assert isinstance(category.name, str), "Name should be string"
        assert isinstance(category.archived, bool), "Archived should be boolean"