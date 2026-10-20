import math
import ast
import re

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex

Window.clearcolor = get_color_from_hex("#0A0A0A")

RED = get_color_from_hex("#E50914")
DARK = get_color_from_hex("#1A1A1A")
DARK_LIGHT = get_color_from_hex("#2A2A2A")
WHITE = get_color_from_hex("#FFFFFF")
GRAY = get_color_from_hex("#8A8A8A")

FUNCTIONS = ("sin", "cos", "tan", "log", "ln", "√")
OPERATORS = ("+", "-", "×", "÷", "^")


class CalculatorEngine:
    def __init__(self):
        self.is_rad = True

    @staticmethod
    def format_number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "Error"
        if not math.isfinite(value):
            return "Error"
        if isinstance(value, int):
            return str(value)
        if value.is_integer():
            return str(int(value))
        return format(value, ".12g")

    @staticmethod
    def normalize_expression(text):
        exp = str(text).strip()
        if not exp:
            return ""
        exp = exp.replace("×", "*").replace("÷", "/")
        exp = exp.replace("^", "**").replace("π", "pi")
        exp = exp.replace("√", "sqrt").replace("%", "/100")
        exp = re.sub(r"(?<=\d)(?=\()", "*", exp)
        exp = re.sub(r"(?<=\))(?=\()", "*", exp)
        exp = re.sub(r"(?<=\d)(?=pi\b)", "*", exp)
        exp = re.sub(r"(?<=\d)(?=e\b)", "*", exp)
        exp = re.sub(r"(?<=\d)(?=sin\b|cos\b|tan\b|log\b|ln\b|sqrt\b)", "*", exp)
        exp = re.sub(r"\b(pi|e)\(", r"\1*(", exp)
        return exp

    def calculate(self, expression):
        text = str(expression).strip() if expression is not None else ""
        if not text:
            return "0"
        if text == "Error":
            return "Error"

        exp = self.normalize_expression(text)
        if not exp:
            return "0"
        if exp.endswith(("+", "-", "*", "/", "**")):
            return "Error"

        try:
            functions = {
                "sin": lambda x: math.sin(x) if self.is_rad else math.sin(math.radians(x)),
                "cos": lambda x: math.cos(x) if self.is_rad else math.cos(math.radians(x)),
                "tan": lambda x: math.tan(x) if self.is_rad else math.tan(math.radians(x)),
                "log": math.log10,
                "ln": math.log,
                "sqrt": math.sqrt,
            }
            tree = ast.parse(exp, mode="eval")
            result = self._evaluate(tree.body, functions)
            return self.format_number(result)
        except Exception:
            return "Error"

    def _evaluate(self, node, functions):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise ValueError("Invalid value")

        if isinstance(node, ast.Name):
            if node.id == "pi":
                return math.pi
            if node.id == "e":
                return math.e
            raise ValueError("Unknown name")

        if isinstance(node, ast.UnaryOp):
            val = self._evaluate(node.operand, functions)
            if isinstance(node.op, ast.UAdd):
                return val
            if isinstance(node.op, ast.USub):
                return -val
            raise ValueError("Invalid unary operation")

        if isinstance(node, ast.BinOp):
            left = self._evaluate(node.left, functions)
            right = self._evaluate(node.right, functions)

            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            raise ValueError("Invalid operation")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Invalid function")
            name = node.func.id
            if name not in functions or len(node.args) != 1 or node.keywords:
                raise ValueError("Invalid function")
            value = self._evaluate(node.args[0], functions)
            if name in ("log", "ln") and value <= 0:
                raise ValueError("Log input must be positive")
            if name == "sqrt" and value < 0:
                raise ValueError("Square root input must be non-negative")
            return functions[name](value)

        raise ValueError("Invalid expression")


class SadafCalculatorApp(App):
    title = "SADAF Calculator"

    def build(self):
        self.engine = CalculatorEngine()
        self.expression = ""
        self.memory = 0
        self.just_calculated = False
        self.history = []

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        title = Label(
            text="SADAF",
            color=RED,
            bold=True,
            font_size="28sp",
            size_hint_y=0.12,
            halign="center",
        )
        root.add_widget(title)

        self.result_label = Label(
            text="0",
            color=WHITE,
            bold=True,
            font_size="38sp",
            halign="right",
            valign="middle",
            size_hint_y=0.18,
        )
        root.add_widget(self.result_label)

        self.history_label = Label(
            text="",
            color=GRAY,
            font_size="12sp",
            halign="right",
            size_hint_y=0.08,
        )
        root.add_widget(self.history_label)

        rows = [
            ["MC", "MR", "M+", "M-", "COPY"],
            ["RAD", "(", ")", "C", "DEL"],
            ["sin", "cos", "tan", "√", "^"],
            ["7", "8", "9", "÷", "log"],
            ["4", "5", "6", "×", "ln"],
            ["1", "2", "3", "-", "π"],
            ["0", ".", "%", "+", "="],
        ]

        grid = GridLayout(cols=5, spacing=dp(6), size_hint_y=0.62)
        for row in rows:
            for text in row:
                btn = Button(
                    text=text,
                    color=WHITE,
                    font_size="15sp",
                    background_normal="",
                    background_color=DARK,
                )
                if text in ("=", "+", "-", "×", "÷", "^"):
                    btn.background_color = RED
                elif text in ("C", "DEL", "RAD", "MC", "MR", "M+", "M-", "COPY"):
                    btn.background_color = DARK_LIGHT
                btn.bind(on_press=self.on_button_press)
                grid.add_widget(btn)

        root.add_widget(grid)
        return root

    def update_display(self):
        self.result_label.text = self.expression if self.expression else "0"

    def add_operator(self, operator):
        if not self.expression:
            if operator == "-":
                self.expression = "-"
            return

        last = self.expression[-1]
        if last in OPERATORS:
            if operator == "-" and last != "-":
                self.expression += "-"
            elif operator != "-":
                self.expression = self.expression[:-1] + operator
            return

        if last == "(":
            if operator == "-":
                self.expression += "-"
            return

        if last == ".":
            return

        self.expression += operator

    def memory_action(self, action):
        if action == "MC":
            self.memory = 0
            self.history_label.text = "Memory cleared"
            self.update_display()
            return

        if action == "MR":
            value = str(self.memory)
            if self.just_calculated or not self.expression:
                self.expression = value
            else:
                self.expression += value
            self.just_calculated = False
            self.update_display()
            return

        if action in ("M+", "M-"):
            if not self.expression:
                return
            result = self.engine.calculate(self.expression)
            if result == "Error":
                self.expression = "Error"
                self.update_display()
                return
            number = float(result)
            if action == "M+":
                self.memory += number
            else:
                self.memory -= number
            self.history_label.text = f"Memory {action}"

    def copy_result(self):
        value = self.expression if self.expression and self.expression != "Error" else self.result_label.text
        Clipboard.copy(value)
        self.history_label.text = "Copied: " + value

    def append_numeric(self, text):
        if self.expression == "Error":
            self.expression = ""

        if text == ".":
            if not self.expression:
                self.expression = "0."
                return
            if self.expression[-1] in OPERATORS or self.expression[-1] == "(":
                self.expression += "0."
                return
            last_token = re.split(r"[+\-×÷^]", self.expression)[-1]
            if "." in last_token:
                return
            self.expression += "."
            return

        if text in ("(", ")"):
            if text == "(":
                if self.expression and (self.expression[-1].isdigit() or self.expression.endswith(")")):
                    self.expression += "*("
                else:
                    self.expression += "("
            else:
                if not self.expression:
                    return
                if self.expression[-1] in OPERATORS or self.expression[-1] == "(":
                    return
                if self.expression.count("(") <= self.expression.count(")"):
                    return
                self.expression += ")"
            return

        if self.just_calculated and text.isdigit():
            self.expression = ""
        self.just_calculated = False

        if self.expression and self.expression[-1] == ")" and text.isdigit():
            self.expression += "*"
        self.expression += text

    def on_button_press(self, instance):
        text = instance.text

        if text in ("MC", "MR", "M+", "M-"):
            self.memory_action(text)
            self.update_display()
            return

        if text == "COPY":
            self.copy_result()
            return

        if text == "C":
            self.expression = ""
            self.history_label.text = ""
            self.just_calculated = False
            self.update_display()
            return

        if text == "DEL":
            if self.expression and self.expression != "Error":
                self.expression = self.expression[:-1]
            else:
                self.expression = ""
            self.just_calculated = False
            self.update_display()
            return

        if text == "=":
            if not self.expression:
                return
            old_expression = self.expression
            result = self.engine.calculate(old_expression)
            if result == "Error":
                self.expression = "Error"
                self.history_label.text = "Invalid expression"
            else:
                self.history.insert(0, old_expression + " = " + result)
                self.history = self.history[:30]
                self.history_label.text = old_expression
                self.expression = result
            self.just_calculated = True
            self.update_display()
            return

        if text in ("RAD", "DEG"):
            self.engine.is_rad = not self.engine.is_rad
            self.history_label.text = "Mode: " + ("RAD" if self.engine.is_rad else "DEG")
            return

        if text in OPERATORS:
            self.just_calculated = False
            self.add_operator(text)
            self.update_display()
            return

        if text in FUNCTIONS:
            if self.just_calculated:
                self.expression = ""
            self.just_calculated = False
            if self.expression and (self.expression[-1].isdigit() or self.expression[-1] == ")"):
                self.expression += "*"
            self.expression += text + "("
            self.update_display()
            return

        self.append_numeric(text)
        self.update_display()


if __name__ == "__main__":
    SadafCalculatorApp().run()
