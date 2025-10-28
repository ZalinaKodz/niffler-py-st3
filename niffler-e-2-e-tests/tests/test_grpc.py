import allure
import grpc
import pytest
from google.protobuf import empty_pb2

from fixtures.grpc_fixtures import TestNifflerCurrencyServiceBase
from internal.pb.niffler_currency_pb2 import CalculateRequest, CurrencyValues, CurrencyResponse


@allure.epic("gRPC Services")
@allure.feature("Currency Service")
@allure.tag("grpc", "currency", "integration")
@pytest.mark.grpc
class TestNifflerCurrencyServiceIntegration(TestNifflerCurrencyServiceBase):
    """Integration tests with actual server behavior."""

    @allure.title("Get all currencies - successful retrieval")
    @allure.story("Currency Management")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description("""
    Test successful retrieval of all available currencies from gRPC service.
    Verifies that all expected currencies are present with valid exchange rates.
    """)
    @pytest.mark.integration
    def test_get_all_currencies_success(self, client):
        with allure.step("Execute GetAllCurrencies gRPC call"):
            response = client.get_all_currencies(empty_pb2.Empty())

        with allure.step("Verify response structure and content"):
            assert isinstance(response, CurrencyResponse)
            assert len(response.allCurrencies) == 4

            currencies_dict = {
                currency.currency: currency.currencyRate
                for currency in response.allCurrencies
            }

            allure.attach(
                str(currencies_dict),
                name="Retrieved Currencies",
                attachment_type=allure.attachment_type.JSON
            )

        with allure.step("Verify all expected currencies are present"):
            expected_currencies = [
                CurrencyValues.RUB, CurrencyValues.USD,
                CurrencyValues.EUR, CurrencyValues.KZT
            ]

            for currency in expected_currencies:
                with allure.step(f"Check currency {currency}"):
                    assert currency in currencies_dict
                    assert currencies_dict[currency] > 0
                    allure.attach(
                        f"Currency: {currency}, Rate: {currencies_dict[currency]}",
                        name=f"Currency_{currency}",
                        attachment_type=allure.attachment_type.TEXT
                    )

    @allure.title("Calculate rate - exact conversions: {spend_currency} -> {desired_currency}")
    @allure.story("Currency Conversion")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description("""
    Test exact currency conversions based on known exchange rates.
    Validates precision of currency conversion calculations.
    """)
    @pytest.mark.integration
    @pytest.mark.parametrize(
        "spend_currency,desired_currency,amount,expected_amount",
        [
            (CurrencyValues.EUR, CurrencyValues.RUB, 100.0, 7200.0),
            (CurrencyValues.USD, CurrencyValues.EUR, 100.0, 92.592),
            (CurrencyValues.RUB, CurrencyValues.USD, 1000.0, 15.0),
            (CurrencyValues.KZT, CurrencyValues.EUR, 10000.0, 19.444),
        ],
        ids=lambda x: f"{x}" if not isinstance(x, float) else f"{x:.1f}"
    )
    def test_calculate_rate_exact_conversions(self, client, spend_currency,
                                              desired_currency, amount, expected_amount):
        with allure.step(f"Prepare conversion request: {amount} {spend_currency} -> {desired_currency}"):
            request = CalculateRequest(
                spendCurrency=spend_currency,
                desiredCurrency=desired_currency,
                amount=amount
            )

        with allure.step("Execute CalculateRate gRPC call"):
            response = client.calculate_rate(request)

        with allure.step("Verify conversion result with tolerance"):
            tolerance = 0.1
            actual_amount = response.calculatedAmount
            difference = abs(actual_amount - expected_amount)

            allure.attach(
                f"Expected: {expected_amount}\nActual: {actual_amount}\nDifference: {difference}\nTolerance: {tolerance}",
                name="Conversion Details",
                attachment_type=allure.attachment_type.TEXT
            )

            assert difference <= tolerance, (
                f"Expected {expected_amount}, got {actual_amount}, difference {difference} > tolerance {tolerance}"
            )


@allure.epic("gRPC Services")
@allure.feature("Currency Service")
@allure.tag("grpc", "currency", "boundary")
@pytest.mark.grpc
class TestNifflerCurrencyServiceBoundaryValues(TestNifflerCurrencyServiceBase):
    """Boundary value tests adjusted for actual server behavior."""

    @allure.title("Amount boundaries: {description}")
    @allure.story("Boundary Values")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test currency conversion with various boundary amount values.")
    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount,expected_result,description",
        [
            (0.000001, 0.0, "Micro amount - server returns 0"),
            (0.001, 0.0, "Very small amount - server returns 0"),
            (0.01, 0.00926, "Minimum working amount USD->EUR"),
            (0.1, 0.0926, "Small amount USD->EUR"),
            (1.0, 0.926, "Unit amount USD->EUR"),
            (100.0, 92.59, "Normal amount USD->EUR"),
            (1000.0, 925.93, "Large amount USD->EUR"),
            (100000.0, 92592.59, "Very large amount USD->EUR"),
            (1000000.0, 925925.93, "Extreme amount USD->EUR"),
        ]
    )
    def test_calculate_rate_amount_boundaries(self, client, amount, expected_result,
                                              description):
        with allure.step(f"Prepare request with amount: {amount}"):
            request = CalculateRequest(
                spendCurrency=CurrencyValues.USD,
                desiredCurrency=CurrencyValues.EUR,
                amount=amount
            )

        with allure.step("Execute conversion"):
            response = client.calculate_rate(request)

        with allure.step(f"Verify result for {description}"):
            actual_amount = response.calculatedAmount

            if expected_result == 0.0:
                assert actual_amount == 0.0, (
                    f"Expected 0.0, got {actual_amount}"
                )
                allure.attach(
                    f"Amount: {amount}\nResult: {actual_amount}\nBehavior: Returns 0 for very small amounts",
                    name="Zero Result Behavior",
                    attachment_type=allure.attachment_type.TEXT
                )
            else:
                tolerance = 0.01 if amount <= 1.0 else amount * 0.01
                difference = abs(actual_amount - expected_result)

                allure.attach(
                    f"Amount: {amount}\nExpected: {expected_result}\nActual: {actual_amount}\nDifference: {difference}\nTolerance: {tolerance}",
                    name="Conversion Details",
                    attachment_type=allure.attachment_type.TEXT
                )

                assert difference <= tolerance, (
                    f"Expected ~{expected_result}, got {actual_amount}, difference {difference} > tolerance {tolerance}"
                )

    @allure.title("Currency pairs: {description}")
    @allure.story("Currency Pairs")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "spend_currency,desired_currency,amount,description",
        [
            (CurrencyValues.RUB, CurrencyValues.USD, 1000.0, "RUB->USD normal"),
            (CurrencyValues.USD, CurrencyValues.RUB, 100.0, "USD->RUB normal"),
            (CurrencyValues.EUR, CurrencyValues.KZT, 50.0, "EUR->KZT normal"),
            (CurrencyValues.KZT, CurrencyValues.EUR, 50000.0, "KZT->EUR normal"),
            (CurrencyValues.USD, CurrencyValues.KZT, 10.0, "USD->KZT normal"),
        ]
    )
    def test_calculate_rate_currency_pairs_positive(self, client, spend_currency,
                                                    desired_currency, amount, description):
        with allure.step(f"Test currency pair: {spend_currency} -> {desired_currency}"):
            request = CalculateRequest(
                spendCurrency=spend_currency,
                desiredCurrency=desired_currency,
                amount=amount
            )

            response = client.calculate_rate(request)

        with allure.step("Verify positive result"):
            assert response.calculatedAmount >= 0, (
                f"Should be non-negative, got {response.calculatedAmount}"
            )

        with allure.step(
                "Check same currency handling" if spend_currency == desired_currency else "Check conversion result"):
            if spend_currency == desired_currency:
                assert response.calculatedAmount == amount, (
                    "Same currency should return original amount"
                )
            else:
                allure.attach(
                    f"From: {spend_currency}\nTo: {desired_currency}\nAmount: {amount}\nResult: {response.calculatedAmount}",
                    name="Conversion Result",
                    attachment_type=allure.attachment_type.TEXT
                )

    @allure.title("Negative amounts: {description}")
    @allure.story("Error Handling")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount,description",
        [
            (-0.01, "Small negative amount"),
            (-1.0, "Unit negative amount"),
            (-100.0, "Medium negative amount"),
            (-1000.0, "Large negative amount"),
        ]
    )
    def test_calculate_rate_negative_amounts(self, client, amount, description):
        with allure.step(f"Test with negative amount: {amount}"):
            request = CalculateRequest(
                spendCurrency=CurrencyValues.USD,
                desiredCurrency=CurrencyValues.EUR,
                amount=amount
            )

            response = client.calculate_rate(request)

        with allure.step("Verify non-positive result for negative input"):
            assert response.calculatedAmount <= 0, (
                f"Negative input should produce non-positive output, got {response.calculatedAmount}"
            )

            allure.attach(
                f"Input: {amount}\nOutput: {response.calculatedAmount}",
                name="Negative Amount Handling",
                attachment_type=allure.attachment_type.TEXT
            )


@allure.epic("gRPC Services")
@allure.feature("Currency Service")
@allure.tag("grpc", "currency", "error-handling")
@pytest.mark.grpc
class TestNifflerCurrencyServiceErrorScenarios(TestNifflerCurrencyServiceBase):
    """Tests for error scenarios and edge cases."""

    @allure.title("Unspecified currency handling")
    @allure.story("Error Scenarios")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description("Test that UNSPECIFIED currency returns proper gRPC error.")
    @pytest.mark.boundary
    def test_calculate_rate_unspecified_currency(self, client):
        with allure.step("Prepare request with UNSPECIFIED currency"):
            request = CalculateRequest(
                spendCurrency=CurrencyValues.UNSPECIFIED,
                desiredCurrency=CurrencyValues.USD,
                amount=100.0
            )

        with allure.step("Verify gRPC error is raised"):
            with pytest.raises(grpc.RpcError) as exc_info:
                client.calculate_rate(request)

        with allure.step("Check error code and details"):
            assert exc_info.value.code() == grpc.StatusCode.UNKNOWN

            allure.attach(
                f"Error Code: {exc_info.value.code()}\nDetails: {exc_info.value.details()}",
                name="gRPC Error Details",
                attachment_type=allure.attachment_type.TEXT
            )


@allure.epic("gRPC Services")
@allure.feature("Currency Service")
@allure.tag("grpc", "currency", "equivalence")
@pytest.mark.grpc
class TestNifflerCurrencyServiceEquivalencePartitioning(TestNifflerCurrencyServiceBase):
    """Equivalence partitioning tests adjusted for server behavior."""

    @allure.title("Amount equivalence: {description}")
    @allure.story("Equivalence Partitioning")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount,expected_behavior,description",
        [
            (0.0, "valid", "Zero amount"),
            (0.01, "valid", "Minimum working amount"),
            (100.0, "valid", "Normal amount"),
            (1000000.0, "valid", "Large amount"),
            (0.001, "valid_returns_zero", "Very small amount returns 0"),
            (0.0001, "valid_returns_zero", "Micro amount returns 0"),
            (-0.01, "valid_negative", "Small negative amount"),
            (-100.0, "valid_negative", "Medium negative amount"),
        ]
    )
    def test_amount_equivalence_partitions(self, client, amount, expected_behavior,
                                           description):
        with allure.step(f"Test amount: {amount} ({description})"):
            request = CalculateRequest(
                spendCurrency=CurrencyValues.USD,
                desiredCurrency=CurrencyValues.EUR,
                amount=amount
            )

            response = client.calculate_rate(request)

        with allure.step(f"Verify {expected_behavior} behavior"):
            actual_amount = response.calculatedAmount

            behavior_info = {
                "valid": "Positive or zero result",
                "valid_returns_zero": "Returns exactly 0",
                "valid_negative": "Negative or zero result"
            }

            allure.attach(
                f"Amount: {amount}\nExpected Behavior: {expected_behavior}\n"
                f"Actual Result: {actual_amount}\nDescription: {behavior_info[expected_behavior]}",
                name="Equivalence Partition Result",
                attachment_type=allure.attachment_type.TEXT
            )

            if expected_behavior == "valid":
                assert actual_amount >= 0
            elif expected_behavior == "valid_returns_zero":
                assert actual_amount == 0.0
            elif expected_behavior == "valid_negative":
                assert actual_amount <= 0