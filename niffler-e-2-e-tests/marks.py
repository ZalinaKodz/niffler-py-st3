import pytest

class TestData:
    @staticmethod
    def page_info(page_infos):
        return pytest.mark.parametrize("page_info", page_infos, ids=lambda pi: f"page_{pi.page}_size_{pi.size}")