from typing import Dict

import grpc
import pytest

from internal.grpc.interceptors.allure import AllureInterceptor
from internal.grpc.interceptors.logging import LoggingInterceptor
from internal.pb.niffler_currency_pb2 import CurrencyValues
from internal.pb.niffler_currency_pb2_pbreflect import NifflerCurrencyServiceClient


INTERCEPTORS = [
    LoggingInterceptor(),
    AllureInterceptor(),
]

class TestNifflerCurrencyServiceBase:
    """Base class for Niffler Currency Service tests."""

    @pytest.fixture
    def grpc_channel(self):
        """Fixture to create gRPC channel with interceptors."""
        with grpc.insecure_channel('localhost:8092') as channel:
            # Добавляем интерцепторы к каналу
            intercepted_channel = grpc.intercept_channel(channel, *INTERCEPTORS)
            yield intercepted_channel

    @pytest.fixture
    def client(self, grpc_channel):
        """Fixture to create gRPC client with interceptors."""
        return NifflerCurrencyServiceClient(grpc_channel)