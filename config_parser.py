import re
import xml.etree.ElementTree as ET
import sys

class ConfigParser:
    def __init__(self):
        # Словарь для хранения глобальных переменных и их значений
        self.constants = {}
        # Корневой элемент для XML-документа
        self.xml_root = ET.Element("config")

    def parse_file(self, file_path):
        """
        Читает файл построчно и передает строки на обработку.
        """
        with open(file_path, 'r') as file:
            lines = file.readlines()
        for line in lines:
            self.parse_line(line.strip())  # Удаляем лишние пробелы

    def parse_line(self, line):
        """
        Определяет тип строки и вызывает соответствующие методы для её обработки.
        """
        # Игнорируем пустые строки и комментарии
        if not line or line.startswith("#"):
            return
        # Если строка объявляет глобальную переменную
        if line.startswith("global "):
            self.parse_global(line)
        # Если строка содержит выражение
        elif line.startswith("^"):
            self.evaluate_expression(line[1:])
        # Если строка не подходит под известные форматы
        else:
            raise SyntaxError(f"Unknown syntax: {line}")

    def parse_global(self, line):
        """
        Обрабатывает строки, объявляющие глобальные переменные.
        Пример строки: global x = 10;
        """
        # Регулярное выражение для извлечения имени переменной и значения
        match = re.match(r"global\s+([_a-zA-Z][_a-zA-Z0-9]*)\s*=\s*(.+);", line)
        if not match:
            raise SyntaxError(f"Invalid global declaration: {line}")
        # Извлекаем имя и значение переменной
        name, value = match.groups()
        # Преобразуем значение в Python-объект
        value = self.parse_value(value)
        # Сохраняем переменную в словарь
        self.constants[name] = value
        # Добавляем переменную в XML-документ
        self.add_to_xml(name, value)

    def parse_value(self, value):
        """
        Преобразует значение переменной из строки в Python-объект.
        """
        # Если значение похоже на массив
        if value.startswith("array(") and value.endswith(")"):
            return self.parse_array(value)
        # Если значение является числом
        elif value.isdigit():
            return int(value)
        # Если значение — это имя другой переменной
        elif value in self.constants:
            return self.constants[value]
        # Если значение не подходит под известные форматы
        else:
            raise SyntaxError(f"Invalid value: {value}")

    def parse_array(self, array_str):
        """
        Обрабатывает массивы, записанные в формате array(...).
        """
        # Удаляем ключевое слово "array()" и разделяем элементы
        array_str = array_str[len("array("):-1]
        # Преобразуем каждый элемент массива в Python-объект
        return [self.parse_value(val.strip()) for val in array_str.split(",")]

    def evaluate_expression(self, expression):
        """
        Вычисляет выражения, записанные после символа ^.
        Поддерживает операции +, -, *, /, mod, max.
        """
        # Разделяем выражение на токены
        tokens = expression.split()
        stack = []  # Стек для вычислений
        for token in tokens:
            if token.isdigit():
                stack.append(int(token))  # Числа добавляются в стек
            elif token in self.constants:
                stack.append(self.constants[token])  # Подставляем значение переменной
            elif token == "+":
                b, a = stack.pop(), stack.pop()
                stack.append(a + b)
            elif token == "-":
                b, a = stack.pop(), stack.pop()
                stack.append(a - b)
            elif token == "*":
                b, a = stack.pop(), stack.pop()
                stack.append(a * b)
            elif token == "/":
                b, a = stack.pop(), stack.pop()
                stack.append(a // b)  # Целочисленное деление
            elif token == "mod":
                b, a = stack.pop(), stack.pop()
                stack.append(a % b)  # Остаток от деления
            elif token == "max":
                b, a = stack.pop(), stack.pop()
                stack.append(max(a, b))  # Максимум из двух чисел
            else:
                raise SyntaxError(f"Unknown token in expression: {token}")
        # После вычисления в стеке должен остаться один элемент
        if len(stack) != 1:
            raise SyntaxError(f"Invalid expression: {expression}")
        result = stack.pop()
        print(f"Result of expression: {result}")
        return result

    def add_to_xml(self, name, value):
        """
        Добавляет глобальную переменную в XML-документ.
        """
        # Создаём элемент XML для переменной
        element = ET.SubElement(self.xml_root, "constant", name=name)
        if isinstance(value, list):  # Если значение — массив
            for val in value:
                ET.SubElement(element, "value").text = str(val)
        else:  # Если значение — одиночное число
            element.text = str(value)

    def to_xml(self):
        """
        Преобразует XML-дерево в строку.
        """
        return ET.tostring(self.xml_root, encoding='unicode')

if __name__ == "__main__":
    # Проверяем, передан ли путь к файлу в аргументах
    if len(sys.argv) != 2:
        print("Usage: python config_parser.py <file_path>")
        sys.exit(1)

    # Получаем путь к файлу из аргументов командной строки
    file_path = sys.argv[1]
    parser = ConfigParser()
    try:
        # Парсим файл и выводим результат в виде XML
        parser.parse_file(file_path)
        print(parser.to_xml())
    except SyntaxError as e:
        # Обрабатываем синтаксические ошибки
        print(f"Syntax error: {e}")
        sys.exit(1)
