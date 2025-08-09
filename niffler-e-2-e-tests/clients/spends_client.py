from typing import  Union

import allure
import pydantic

from models.spend import  SpendModel, SpendModelAdd, SpendModelEdit, ErrorResponseModel
from utils.sessions import BaseSession


class SpendClient:
    session: BaseSession

    def __init__(self, session: BaseSession):
        self.session = session

    @allure.step('[API] Get all spends: filter_currency={filter_currency}, filter_period={filter_period}')
    def get_all_spends(self, filter_currency: str = None, filter_period: str = None) -> list[SpendModel]:
        response = self.session.get(
            "/api/spends/all",
            params={"filterCurrency": filter_currency, "filterPeriod": filter_period}
        )
        return [SpendModel.model_validate(item) for item in response.json()]

    @allure.step('[API] Get spend by id: ')
    def get_spend_by_id(self, spend_id: str) -> SpendModel:
        response = self.session.get(f"/api/spends/{spend_id}")
        return SpendModel.model_validate(response.json())

    @allure.step('[API] Add spend: spend={spend}')
    def add_spend(self, spend: SpendModelAdd) -> Union[SpendModel, ErrorResponseModel]:
        response = self.session.post(
            "/api/spends/add",
            json=spend.model_dump()
        )

        try:
            # Сначала пробуем распарсить как успешный ответ
            return SpendModel.model_validate(response.json())
        except pydantic.ValidationError:
            # Если не получается, парсим как ошибку
            return ErrorResponseModel.model_validate(response.json())

    @allure.step('[API] Edit spend: spend={spend}')
    def edit_spend(self, spend: SpendModelEdit) -> SpendModel:
        response = self.session.patch(
            "/api/spends/edit",
            json=spend.model_dump()
        )
        return SpendModel.model_validate(response.json())

    @allure.step('[API] Delete spend: ids={ids}')
    def delete_spend(self, ids: list[str]) -> None:
        self.session.delete(
            "/api/spends/remove",
            params={"ids": ",".join(ids)}
        )

    @allure.step('[API] Add spend with invalid params: spend={spend}')
    def add_spend_error(self, spend: dict) -> ErrorResponseModel:
        response = self.session.post(
            "/api/spends/add",
            json=spend,
            check_status=False
        )
        return ErrorResponseModel.model_validate(response.json())