from typing import Callable

import allure
import grpc
from google.protobuf.json_format import MessageToJson

class AllureInterceptor(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        method_name = client_call_details.method.split('/')[-1]

        # Логируем запрос сразу
        try:
            if hasattr(request, 'DESCRIPTOR'):
                request_json = MessageToJson(request, preserving_proto_field_name=True)
                allure.attach(
                    request_json,
                    name=f"Request: {method_name}",
                    attachment_type=allure.attachment_type.JSON
                )
            else:
                allure.attach(
                    str(request),
                    name=f"Request: {method_name}",
                    attachment_type=allure.attachment_type.TEXT
                )
        except Exception as e:
            allure.attach(
                f"Error logging request: {str(e)}",
                name=f"Request Error: {method_name}",
                attachment_type=allure.attachment_type.TEXT
            )

        # Продолжаем выполнение и получаем ответ
        response_future = continuation(client_call_details, request)

        # Обрабатываем ответ, когда он будет доступен
        def log_response_callback(response_future):
            try:
                response = response_future.result()
                if hasattr(response, 'DESCRIPTOR'):
                    response_json = MessageToJson(response, preserving_proto_field_name=True)
                    allure.attach(
                        response_json,
                        name=f"Response: {method_name}",
                        attachment_type=allure.attachment_type.JSON
                    )
                else:
                    allure.attach(
                        str(response),
                        name=f"Response: {method_name}",
                        attachment_type=allure.attachment_type.TEXT
                    )
            except Exception as e:
                allure.attach(
                    f"Error: {str(e)}",
                    name=f"Response Error: {method_name}",
                    attachment_type=allure.attachment_type.TEXT
                )

        # Добавляем callback для логирования ответа
        response_future.add_done_callback(lambda f: log_response_callback(f))

        return response_future