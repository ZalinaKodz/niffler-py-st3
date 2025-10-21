from typing import Callable

import grpc
from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message


class LoggingInterceptor(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        method_name = client_call_details.method.split('/')[-1]
        print(f"\n/guru.qa.grpc.niffler.NifflerCurrencyService/{method_name}")

        # Логируем запрос
        try:
            if hasattr(request, 'DESCRIPTOR'):
                request_json = MessageToJson(request, preserving_proto_field_name=True)
                print(request_json)
            else:
                print(str(request))
        except Exception as e:
            print(f"Error logging request: {e}")

        # Продолжаем выполнение и получаем ответ
        response_future = continuation(client_call_details, request)

        # Обрабатываем ответ, когда он будет доступен
        def log_response_callback(response_future):
            try:
                response = response_future.result()
                if hasattr(response, 'DESCRIPTOR'):
                    response_json = MessageToJson(response, preserving_proto_field_name=True)
                    print(response_json)
                else:
                    print(str(response))
            except Exception as e:
                print(f"Error in response: {e}")

        # Добавляем callback для логирования ответа
        response_future.add_done_callback(lambda f: log_response_callback(f))

        return response_future