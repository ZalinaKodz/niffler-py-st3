import allure
import grpc
import pytest
from google.protobuf import empty_pb2

from fixtures.grpc_fixtures import TestNifflerCurrencyServiceBase
from internal.pb.niffler_currency_pb2 import CalculateRequest, CurrencyValues, CurrencyResponse


@allure.epic("gRPC Services")
@allure.feature("Currency Service")
@pytest.mark.grpc
class TestNifflerCurrencyServiceIntegration(TestNifflerCurrencyServiceBase):
    """Integration tests with actual server behavior."""

    @pytest.mark.integration
    def test_get_all_currencies_success(self, client):
        """Test successful retrieval of all currencies."""
        # Act
        response = client.get_all_currencies(empty_pb2.Empty())

        # Assert
        assert isinstance(response, CurrencyResponse)
        assert len(response.allCurrencies) == 4

        currencies_dict = {currency.currency: currency.currencyRate
                           for currency in response.allCurrencies}

        # Verify all expected currencies are present
        expected_currencies = [CurrencyValues.RUB, CurrencyValues.USD,
                               CurrencyValues.EUR, CurrencyValues.KZT]
        for currency in expected_currencies:
            assert currency in currencies_dict
            assert currencies_dict[currency] > 0

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "spend_currency,desired_currency,amount,expected_amount",
        [
            # Exact conversions based on server rates
            (CurrencyValues.EUR, CurrencyValues.RUB, 100.0, 7200.0),  # 100 * 1.08 / 0.015
            (CurrencyValues.USD, CurrencyValues.EUR, 100.0, 92.592),  # 100 * 1.0 / 1.08
            (CurrencyValues.RUB, CurrencyValues.USD, 1000.0, 15.0),  # 1000 * 0.015 / 1.0
            (CurrencyValues.KZT, CurrencyValues.EUR, 10000.0, 19.444),  # 10000 * 0.0021 / 1.08
        ]
    )
    def test_calculate_rate_exact_conversions(self, client, spend_currency,
                                              desired_currency, amount, expected_amount):
        """Test exact currency conversions based on known rates."""
        # Arrange
        request = CalculateRequest(
            spendCurrency=spend_currency,
            desiredCurrency=desired_currency,
            amount=amount
        )

        # Act
        response = client.calculate_rate(request)

        # Assert with tolerance for floating point arithmetic
        tolerance = 0.1  # Allow small rounding differences
        assert abs(response.calculatedAmount - expected_amount) <= tolerance, (
            f"Expected {expected_amount}, got {response.calculatedAmount}"
        )



class TestNifflerCurrencyServiceBoundaryValues(TestNifflerCurrencyServiceBase):
    """Boundary value tests adjusted for actual server behavior."""

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
        """Test amount boundaries with server's actual behavior."""
        # Arrange
        request = CalculateRequest(
            spendCurrency=CurrencyValues.USD,
            desiredCurrency=CurrencyValues.EUR,
            amount=amount
        )

        # Act
        response = client.calculate_rate(request)

        # Assert based on server behavior
        if expected_result == 0.0:
            # Server returns 0 for very small amounts
            assert response.calculatedAmount == 0.0, (
                f"{description}: Expected 0.0, got {response.calculatedAmount}"
            )
        else:
            # Allow tolerance for floating point calculations
            tolerance = 0.01 if amount <= 1.0 else amount * 0.01  # 1% tolerance
            assert abs(response.calculatedAmount - expected_result) <= tolerance, (
                f"{description}: Expected ~{expected_result}, got {response.calculatedAmount}"
            )

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "spend_currency,desired_currency,amount,description",
        [
            # Various currency pairs with reasonable amounts
            (CurrencyValues.RUB, CurrencyValues.USD, 1000.0, "RUB->USD normal"),
            (CurrencyValues.USD, CurrencyValues.RUB, 100.0, "USD->RUB normal"),
            (CurrencyValues.EUR, CurrencyValues.KZT, 50.0, "EUR->KZT normal"),
            (CurrencyValues.KZT, CurrencyValues.EUR, 50000.0, "KZT->EUR normal"),
            (CurrencyValues.USD, CurrencyValues.KZT, 10.0, "USD->KZT normal"),
        ]
    )
    def test_calculate_rate_currency_pairs_positive(self, client, spend_currency,
                                                    desired_currency, amount, description):
        """Test that currency conversions produce positive results."""
        # Arrange
        request = CalculateRequest(
            spendCurrency=spend_currency,
            desiredCurrency=desired_currency,
            amount=amount
        )

        # Act
        response = client.calculate_rate(request)

        # Assert
        assert response.calculatedAmount >= 0, (
            f"{description}: Should be non-negative, got {response.calculatedAmount}"
        )

        # Additional check for same currency
        if spend_currency == desired_currency:
            assert response.calculatedAmount == amount, (
                "Same currency should return original amount"
            )

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount,description",
        [
            # NEGATIVE AMOUNTS: Server accepts them without validation
            (-0.01, "Small negative amount"),
            (-1.0, "Unit negative amount"),
            (-100.0, "Medium negative amount"),
            (-1000.0, "Large negative amount"),
        ]
    )
    def test_calculate_rate_negative_amounts(self, client, amount, description):
        """Test server's handling of negative amounts (no validation)."""
        # Arrange
        request = CalculateRequest(
            spendCurrency=CurrencyValues.USD,
            desiredCurrency=CurrencyValues.EUR,
            amount=amount
        )

        # Act
        response = client.calculate_rate(request)

        # Assert: Server processes negative amounts without error
        # Result will be negative based on conversion logic
        assert response.calculatedAmount <= 0, (
            f"{description}: Negative input should produce non-positive output"
        )

    @pytest.mark.boundary
    def test_calculate_rate_zero_amount(self, client):
        """Test currency conversion with zero amount."""
        # Arrange
        request = CalculateRequest(
            spendCurrency=CurrencyValues.USD,
            desiredCurrency=CurrencyValues.EUR,
            amount=0.0
        )

        # Act
        response = client.calculate_rate(request)

        # Assert
        assert response.calculatedAmount == 0.0, "Zero amount should result in zero"

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount,description",
        [
            (0.01, "Minimal working amount"),
            (1.0, "Small amount"),
            (100.0, "Medium amount"),
        ]
    )
    def test_calculate_rate_precision_consistency(self, client, amount, description):
        """Test precision consistency across amount scales."""
        # Skip very small amounts that return 0
        if amount < 0.01:
            pytest.skip("Very small amounts return 0 on server")

        # Arrange - test USD->EUR and EUR->USD conversions
        request_usd_eur = CalculateRequest(
            spendCurrency=CurrencyValues.USD,
            desiredCurrency=CurrencyValues.EUR,
            amount=amount
        )

        request_eur_usd = CalculateRequest(
            spendCurrency=CurrencyValues.EUR,
            desiredCurrency=CurrencyValues.USD,
            amount=amount
        )

        # Act
        response_usd_eur = client.calculate_rate(request_usd_eur)
        response_eur_usd = client.calculate_rate(request_eur_usd)

        # Assert - both conversions should work
        assert response_usd_eur.calculatedAmount > 0, f"USD->EUR {description} failed"
        assert response_eur_usd.calculatedAmount > 0, f"EUR->USD {description} failed"

        # Verify round-trip consistency (with tolerance for conversion fees/rounding)
        original_to_eur = response_usd_eur.calculatedAmount
        eur_back_to_usd = client.calculate_rate(CalculateRequest(
            spendCurrency=CurrencyValues.EUR,
            desiredCurrency=CurrencyValues.USD,
            amount=original_to_eur
        )).calculatedAmount

        # Allow 5% tolerance for round-trip conversion differences
        round_trip_diff = abs(amount - eur_back_to_usd) / amount
        assert round_trip_diff <= 0.05, (
            f"Round-trip conversion difference too large: {round_trip_diff:.2%}"
        )


class TestNifflerCurrencyServiceErrorScenarios(TestNifflerCurrencyServiceBase):
    """Tests for error scenarios and edge cases."""

    @pytest.mark.boundary
    def test_calculate_rate_unspecified_currency(self, client):
        """Test UNSPECIFIED currency handling (returns StatusCode.UNKNOWN)."""
        # Arrange
        request = CalculateRequest(
            spendCurrency=CurrencyValues.UNSPECIFIED,
            desiredCurrency=CurrencyValues.USD,
            amount=100.0
        )

        # Act & Assert
        with pytest.raises(grpc.RpcError) as exc_info:
            client.calculate_rate(request)

        # Server returns UNKNOWN for UNSPECIFIED currency
        assert exc_info.value.code() == grpc.StatusCode.UNKNOWN, (
            f"Expected UNKNOWN, got {exc_info.value.code()}"
        )

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "invalid_currency",
        [
            CurrencyValues.UNSPECIFIED,
            # Add any other invalid currency values if they exist
        ]
    )
    def test_calculate_rate_invalid_currencies(self, client, invalid_currency):
        """Test handling of invalid currency values."""
        # Test spend currency invalid
        request_spend = CalculateRequest(
            spendCurrency=invalid_currency,
            desiredCurrency=CurrencyValues.USD,
            amount=100.0
        )

        with pytest.raises(grpc.RpcError) as exc_info:
            client.calculate_rate(request_spend)
        assert exc_info.value.code() == grpc.StatusCode.UNKNOWN

        # Test desired currency invalid
        request_desired = CalculateRequest(
            spendCurrency=CurrencyValues.USD,
            desiredCurrency=invalid_currency,
            amount=100.0
        )

        with pytest.raises(grpc.RpcError) as exc_info:
            client.calculate_rate(request_desired)
        assert exc_info.value.code() == grpc.StatusCode.UNKNOWN


class TestNifflerCurrencyServiceEquivalencePartitioning(TestNifflerCurrencyServiceBase):
    """Equivalence partitioning tests adjusted for server behavior."""

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "amount,expected_behavior,description",
        [
            # VALID PARTITIONS (server processes without error)
            (0.0, "valid", "Zero amount"),
            (0.01, "valid", "Minimum working amount"),
            (100.0, "valid", "Normal amount"),
            (1000000.0, "valid", "Large amount"),

            # SPECIAL CASE: Very small amounts return 0
            (0.001, "valid_returns_zero", "Very small amount returns 0"),
            (0.0001, "valid_returns_zero", "Micro amount returns 0"),

            # SPECIAL CASE: Negative amounts are accepted
            (-0.01, "valid_negative", "Small negative amount"),
            (-100.0, "valid_negative", "Medium negative amount"),
        ]
    )
    def test_amount_equivalence_partitions(self, client, amount, expected_behavior,
                                           description):
        """Test equivalence partitions for amount parameter."""
        request = CalculateRequest(
            spendCurrency=CurrencyValues.USD,
            desiredCurrency=CurrencyValues.EUR,
            amount=amount
        )

        # Act
        response = client.calculate_rate(request)

        # Assert based on expected behavior
        if expected_behavior == "valid":
            assert response.calculatedAmount >= 0
        elif expected_behavior == "valid_returns_zero":
            assert response.calculatedAmount == 0.0
        elif expected_behavior == "valid_negative":
            assert response.calculatedAmount <= 0

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "currency,expected_behavior",
        [
            # INVALID PARTITION
            (CurrencyValues.UNSPECIFIED, "invalid_unknown"),

            # VALID PARTITIONS
            (CurrencyValues.RUB, "valid"),
            (CurrencyValues.USD, "valid"),
            (CurrencyValues.EUR, "valid"),
            (CurrencyValues.KZT, "valid"),
        ]
    )
    def test_currency_equivalence_partitions(self, client, currency, expected_behavior):
        """Test equivalence partitions for currency parameters."""
        request = CalculateRequest(
            spendCurrency=currency,
            desiredCurrency=CurrencyValues.EUR,
            amount=100.0
        )

        if expected_behavior == "valid":
            response = client.calculate_rate(request)
            assert response.calculatedAmount >= 0
        else:  # invalid_unknown
            with pytest.raises(grpc.RpcError) as exc_info:
                client.calculate_rate(request)
            assert exc_info.value.code() == grpc.StatusCode.UNKNOWN