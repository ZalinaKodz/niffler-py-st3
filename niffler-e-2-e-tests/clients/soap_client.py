from typing import Dict, Any, Tuple, List

import requests
from xml.etree import ElementTree as ET
from models.soap import PageInfo, SoapUser


class SoapClient:
    def __init__(self, base_url: str = "http://localhost:8089/ws"):
        self.base_url = base_url
        self.wsdl_url = f"{base_url}/userdata.wsdl"
        self.headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }

    def _create_soap_envelope(self, body_content: str) -> str:
        """Создание SOAP конверта"""
        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="niffler-userdata">
    <soap:Body>
        {body_content}
    </soap:Body>
</soap:Envelope>"""

    def _make_soap_call(self, operation: str, xml_body: str) -> Tuple[Any, int]:
        """Базовый метод для SOAP вызовов"""
        envelope = self._create_soap_envelope(xml_body)

        try:
            response = requests.post(
                self.base_url,
                data=envelope,
                headers=self.headers,
                timeout=30
            )

            print(f"SOAP Request: {operation}")
            print(f"Request XML: {envelope}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Text: {response.text}")

            return self._parse_soap_response(response.text), response.status_code

        except requests.exceptions.RequestException as e:
            print(f"SOAP Request failed: {str(e)}")
            return f"Request failed: {str(e)}", 500

    def _parse_soap_response(self, xml_response: str) -> Dict[str, Any]:
        """Парсинг SOAP ответа с правильной обработкой namespace"""
        try:
            # Регистрируем namespace для корректного парсинга
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ns2': 'niffler-userdata',
                'tns': 'niffler-userdata'
            }

            root = ET.fromstring(xml_response)

            # Ищем Body с учетом namespace
            body = root.find('.//soap:Body', namespaces)
            if body is None:
                # Пробуем без namespace
                body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')

            if body is not None and len(body) > 0:
                response_element = body[0]
                return self._parse_element_with_namespace(response_element)

            return {"error": "No valid response body found"}

        except ET.ParseError as e:
            print(f"XML parsing error: {str(e)}")
            return {"error": f"XML parsing failed: {str(e)}"}

    def _parse_element_with_namespace(self, element: ET.Element) -> Dict[str, Any]:
        """Рекурсивный парсинг XML элемента с удалением namespace из тегов"""
        result = {}

        for child in element:
            # Удаляем namespace из тега
            tag = self._remove_namespace(child.tag)

            if len(child) == 0:
                # Текстовый элемент
                result[tag] = child.text
            else:
                # Вложенный элемент
                child_data = self._parse_element_with_namespace(child)

                if tag in result:
                    if isinstance(result[tag], list):
                        result[tag].append(child_data)
                    else:
                        result[tag] = [result[tag], child_data]
                else:
                    result[tag] = child_data

        return result

    def _remove_namespace(self, tag: str) -> str:
        """Удаляет namespace из XML тега"""
        if '}' in tag:
            return tag.split('}', 1)[1]
        return tag

    def _extract_user_from_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение пользователя из ответа"""
        print(f"Extracting user from: {response_data}")

        # Если ответ уже содержит данные пользователя на верхнем уровне
        user_keys = ['id', 'username', 'currency', 'friendshipStatus']
        if any(key in response_data for key in user_keys):
            return response_data

        # Ищем вложенного пользователя
        if 'user' in response_data:
            user_data = response_data['user']
            if isinstance(user_data, dict):
                return user_data
            elif isinstance(user_data, list) and user_data:
                return user_data[0]

        # Если структура другая, ищем любые данные пользователя
        for key, value in response_data.items():
            if isinstance(value, dict) and any(k in value for k in user_keys):
                return value

        return response_data

    # Основные методы API

    def get_current_user(self, username: str) -> Tuple[Dict[str, Any], int]:
        """Получение текущего пользователя"""
        xml_body = f"""
        <tns:currentUserRequest>
            <tns:username>{username}</tns:username>
        </tns:currentUserRequest>"""

        response, status_code = self._make_soap_call("currentUser", xml_body)
        user_data = self._extract_user_from_response(response)
        print(f"Extracted user data: {user_data}")
        return user_data, status_code

    def update_user(self, user: SoapUser) -> Tuple[Dict[str, Any], int]:
        """Обновление пользователя"""
        user_xml_parts = [
            f"<tns:id>{user.id}</tns:id>" if user.id else "<tns:id></tns:id>",
            f"<tns:username>{user.username}</tns:username>",
            f"<tns:currency>{user.currency.value}</tns:currency>"
        ]

        if user.firstname:
            user_xml_parts.append(f"<tns:firstname>{user.firstname}</tns:firstname>")
        if user.surname:
            user_xml_parts.append(f"<tns:surname>{user.surname}</tns:surname>")
        if user.fullname:
            user_xml_parts.append(f"<tns:fullname>{user.fullname}</tns:fullname>")

        user_xml = "\n".join(user_xml_parts)

        xml_body = f"""
        <tns:updateUserRequest>
            <tns:user>
                {user_xml}
            </tns:user>
        </tns:updateUserRequest>"""

        response, status_code = self._make_soap_call("updateUser", xml_body)
        return self._extract_user_from_response(response), status_code

    def get_all_users(self, username: str, search_query: str = None) -> Tuple[List[Dict[str, Any]], int]:
        """Получение всех пользователей"""
        search_xml = f"<tns:searchQuery>{search_query}</tns:searchQuery>" if search_query else ""
        xml_body = f"""
        <tns:allUsersRequest>
            <tns:username>{username}</tns:username>
            {search_xml}
        </tns:allUsersRequest>"""

        response, status_code = self._make_soap_call("allUsers", xml_body)

        users = []
        if 'user' in response:
            user_data = response['user']
            if isinstance(user_data, list):
                users = user_data
            elif isinstance(user_data, dict):
                users = [user_data]

        return users, status_code

    def get_all_users_page(self, username: str, page_info: PageInfo, search_query: str = None) -> Tuple[
        Dict[str, Any], int]:
        """Получение пользователей с пагинацией"""
        search_xml = f"<tns:searchQuery>{search_query}</tns:searchQuery>" if search_query else ""

        sort_xml = ""
        for sort_item in page_info.sort:
            sort_xml += f"""
            <tns:sort>
                <tns:property>{sort_item.property}</tns:property>
                <tns:direction>{sort_item.direction.value}</tns:direction>
            </tns:sort>"""

        page_info_xml = f"""
        <tns:pageInfo>
            <tns:page>{page_info.page}</tns:page>
            <tns:size>{page_info.size}</tns:size>
            {sort_xml}
        </tns:pageInfo>"""

        xml_body = f"""
        <tns:allUsersPageRequest>
            <tns:username>{username}</tns:username>
            {page_info_xml}
            {search_xml}
        </tns:allUsersPageRequest>"""

        return self._make_soap_call("allUsersPage", xml_body)

    def get_friends(self, username: str, search_query: str = None) -> Tuple[List[Dict[str, Any]], int]:
        """Получение списка друзей"""
        search_xml = f"<tns:searchQuery>{search_query}</tns:searchQuery>" if search_query else ""
        xml_body = f"""
        <tns:friendsRequest>
            <tns:username>{username}</tns:username>
            {search_xml}
        </tns:friendsRequest>"""

        response, status_code = self._make_soap_call("friends", xml_body)

        users = []
        if 'user' in response:
            user_data = response['user']
            if isinstance(user_data, list):
                users = user_data
            elif isinstance(user_data, dict):
                users = [user_data]

        return users, status_code

    def get_friends_page(self, username: str, page_info: PageInfo, search_query: str = None) -> Tuple[
        Dict[str, Any], int]:
        """Получение друзей с пагинацией"""
        search_xml = f"<tns:searchQuery>{search_query}</tns:searchQuery>" if search_query else ""

        sort_xml = ""
        for sort_item in page_info.sort:
            sort_xml += f"""
            <tns:sort>
                <tns:property>{sort_item.property}</tns:property>
                <tns:direction>{sort_item.direction.value}</tns:direction>
            </tns:sort>"""

        page_info_xml = f"""
        <tns:pageInfo>
            <tns:page>{page_info.page}</tns:page>
            <tns:size>{page_info.size}</tns:size>
            {sort_xml}
        </tns:pageInfo>"""

        xml_body = f"""
        <tns:friendsPageRequest>
            <tns:username>{username}</tns:username>
            {page_info_xml}
            {search_xml}
        </tns:friendsPageRequest>"""

        return self._make_soap_call("friendsPage", xml_body)