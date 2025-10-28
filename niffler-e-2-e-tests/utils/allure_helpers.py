import json
import logging
import time
from json import JSONDecodeError
from typing import Dict, List

import allure
import curlify
from allure_commons.types import AttachmentType
from requests import Response


def allure_logger(config):
    listener = config.pluginmanager.get_plugin("allure_listener")
    return listener.allure_logger

def allure_attach_request(function):
    """Декоратор логироваания запроса, хедеров запроса, хедеров ответа в allure шаг и аллюр аттачмент и в консоль."""
    def wrapper(*args, **kwargs):
        method, url = args[1], args[2]
        with allure.step(f"{method} {url}"):

            response: Response = function(*args, **kwargs)

            curl = curlify.to_curl(response.request)
            logging.debug(curl)
            logging.debug(response.text)

            allure.attach(
                body=curl.encode("utf8"),
                name=f"Request {response.status_code}",
                attachment_type=AttachmentType.TEXT,
                extension=".txt"
            )
            try:
                allure.attach(
                    body=json.dumps(response.json(), indent=4).encode("utf8"),
                    name=f"Response json {response.status_code}",
                    attachment_type=AttachmentType.JSON,
                    extension=".json"
                )
            except JSONDecodeError:
                allure.attach(
                    body=response.text.encode("utf8"),
                    name=f"Response text {response.status_code}",
                    attachment_type=AttachmentType.TEXT,
                    extension=".txt")
            allure.attach(
                body=json.dumps(dict(response.headers), indent=4).encode("utf8"),
                name=f"Response headers {response.status_code}",
                attachment_type=AttachmentType.JSON,
                extension=".json"
            )
        return response

    return wrapper


def attach_sql(conn, cursor, statement, parameters, context, executemany):
    try:
        if parameters:
            if isinstance(parameters, dict):
                param_str = str(parameters)
            else:
                param_str = ", ".join(map(str, parameters))
            sql_full = f"{statement} -- params: {param_str}"
        else:
            sql_full = statement
    except Exception as e:
        sql_full = f"Ошибка формирования SQL: {e}"

    try:
        db_name = context.connection.engine.url.database
    except Exception:
        db_name = "unknown"

    name = f"{statement.split()[0]} {db_name}"
    allure.attach(sql_full, name=name, attachment_type=AttachmentType.TEXT)


class Epic:
    app_name = "Niffler"
    api = "REST API"
    soap = "SOAP API"
    grpc = "gRPC Services"
    kafka = "Kafka Integration"
    ui = "UI Tests"
    database = "Database Operations"


class Feature:
    userdata = "User Data Management"
    friends = "Friends Management"
    auth = "Authentication"
    spending = "Spending Management"
    category = "Category Management"
    currency = "Currency Operations"
    registration = "User Registration"


class Story:
    user_management = "User Management"
    friends_management = "Friends Management"
    api_crud = "CRUD Operations"
    boundary_tests = "Boundary Value Tests"
    kafka_messaging = "Kafka Message Flow"
    soap_operations = "SOAP API Operations"
    grpc_calls = "gRPC Service Calls"


# Новые хелперы для разных типов тестов
class AllureKafkaHelper:
    """Хелпер для Kafka тестов"""

    @staticmethod
    @allure.step("📨 Отправить сообщение в Kafka: {topic}")
    def attach_kafka_message(topic: str, message: Dict, key: str = None, action: str = "send"):
        metadata = {
            "action": action,
            "topic": topic,
            "key": key,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message_size": len(str(message))
        }

        # Методанные сообщения
        allure.attach(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            name=f"Kafka {action.title()} Metadata",
            attachment_type=AttachmentType.JSON
        )

        # Тело сообщения
        if message:
            allure.attach(
                json.dumps(message, indent=2, ensure_ascii=False),
                name=f"Kafka Message {action.title()}",
                attachment_type=AttachmentType.JSON
            )

    @staticmethod
    def attach_kafka_consumer_info(consumer_group: str, topics: List[str]):
        """Прикрепляет информацию о Kafka consumer"""
        consumer_info = {
            "consumer_group": consumer_group,
            "topics": topics,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        allure.attach(
            json.dumps(consumer_info, indent=2, ensure_ascii=False),
            name="Kafka Consumer Configuration",
            attachment_type=AttachmentType.JSON
        )


class AllureAPIHelper:
    """Хелпер для API тестов"""

    @staticmethod
    @allure.step("🌐 {method} {endpoint}")
    def attach_api_call(method: str, endpoint: str, request_data: Dict = None,
                        response_data: Dict = None, status_code: int = None,
                        response_time: float = None):

        # Информация о запросе
        request_info = {
            "method": method.upper(),
            "endpoint": endpoint,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        allure.attach(
            json.dumps(request_info, indent=2, ensure_ascii=False),
            name="API Request Info",
            attachment_type=AttachmentType.JSON
        )

        # Тело запроса
        if request_data:
            allure.attach(
                json.dumps(request_data, indent=2, ensure_ascii=False),
                name="Request Body",
                attachment_type=AttachmentType.JSON
            )

        # Информация о ответе
        if status_code is not None:
            response_info = {
                "status_code": status_code,
                "response_time_ms": round(response_time * 1000, 2) if response_time else None
            }

            allure.attach(
                json.dumps(response_info, indent=2, ensure_ascii=False),
                name="API Response Info",
                attachment_type=AttachmentType.JSON
            )

        # Тело ответа
        if response_data:
            allure.attach(
                json.dumps(response_data, indent=2, ensure_ascii=False),
                name="Response Body",
                attachment_type=AttachmentType.JSON
            )


class AllureSOAPHelper:
    """Хелпер для SOAP тестов"""

    @staticmethod
    @allure.step("🔄 SOAP: {operation}")
    def attach_soap_call(operation: str, request_xml: str, response_xml: str = None,
                         status_code: int = None, username: str = None):
        # Методанные запроса
        request_meta = {
            "operation": operation,
            "username": username,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        allure.attach(
            json.dumps(request_meta, indent=2, ensure_ascii=False),
            name="SOAP Request Metadata",
            attachment_type=AttachmentType.JSON
        )

        # SOAP запрос
        allure.attach(
            request_xml,
            name=f"SOAP Request: {operation}",
            attachment_type=AttachmentType.XML
        )

        # SOAP ответ
        if response_xml:
            response_meta = {
                "status_code": status_code,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            allure.attach(
                json.dumps(response_meta, indent=2, ensure_ascii=False),
                name="SOAP Response Metadata",
                attachment_type=AttachmentType.JSON
            )

            allure.attach(
                response_xml,
                name=f"SOAP Response: {operation}",
                attachment_type=AttachmentType.XML
            )


class AllureGRPCHelper:
    """Хелпер для gRPC тестов"""

    @staticmethod
    @allure.step("🔧 gRPC: {method}")
    def attach_grpc_call(method: str, request: Dict, response: Dict = None,
                         response_time: float = None):
        # Запрос
        allure.attach(
            json.dumps(request, indent=2, ensure_ascii=False),
            name=f"gRPC Request: {method}",
            attachment_type=AttachmentType.JSON
        )

        # Ответ
        if response:
            response_info = {
                "method": method,
                "response_time_ms": round(response_time * 1000, 2) if response_time else None,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            allure.attach(
                json.dumps(response_info, indent=2, ensure_ascii=False),
                name="gRPC Response Info",
                attachment_type=AttachmentType.JSON
            )

            allure.attach(
                json.dumps(response, indent=2, ensure_ascii=False),
                name=f"gRPC Response: {method}",
                attachment_type=AttachmentType.JSON
            )



kafka_helper = AllureKafkaHelper()
api_helper = AllureAPIHelper()
soap_helper = AllureSOAPHelper()
grpc_helper = AllureGRPCHelper()