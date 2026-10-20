import ast
import math
import os
import re

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex


Window.clearcolor = get_color_from_hex("#0A0A0A")
Window.set_title("SADAF Calculator")

RED = get_color_from_hex("#E50914")
DARK = get_color_from_hex("#1A1A1A")
DARK_LIGHT = get_color_from_hex("#2A2A2A")
WHITE = get_color_from_hex("#FFFFFF")
GRAY = get_color_from_hex("#8D8D8D")
BLACK = get_color_from_hex("#000000")

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sadaf_font.ttf")
BRAND_FONT = FONT_PATH if os.path.exists(FONT_PATH) else "Roboto"
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.svg")
if os.path.exists(ICON_PATH):
    try:
        Window.set_icon(ICON_PATH)
    except Exception:
        pass

FUNCTIONS = ("sin", "cos", "tan", "log", "ln", "√")
OPERATORS = ("+", "-", "×", "÷", "^")


class Heart(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw, size=self.draw)
        self.draw()

    def draw(self, *args):
        self.canvas.clear()
        side = min(self.width, self.height)
        x = self.x + (self.width - side) / 2
        y = self.y + (self.height - side) / 2

        with self.canvas:
            Color(*RED)
            Ellipse(pos=(x, y + side * 0.4), size=(side * 0.5, side * 0.5))
            Ellipse(pos=(x + side * 0.5, y + side * 0.4), size=(side * 0.5, side * 0.5))
            Line(points=[x + side * 0.12, y + side * 0.5, x + side * 0.5, y + side * 0.08, x + side * 0.88, y + side * 0.5], width=2)


class CalculatorEngine:
    def __init__(self):
        self.is_rad = True

    @staticmethod
    def format_number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "Error"
        if isinstance(value, int):
            return str(value)
        if not math.isfinite(value):
            return "Error"
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
        exp = re.sub(r"(?<=\))(?=\d)", "*", exp)
        exp = re.sub(r"(?<=\d)(?=pi\b)", "*", exp)
        exp = re.sub(r"(?<=\d)(?=e\b)", "*", exp)
        exp = re.sub(r"(?<=\d)(?=sin\b|cos\b|tan\b|log\b|ln\b|sqrt\b)", "*", exp)

        exp = re.sub(r"\b(pi|e)\(", r"\1*(", exp)
        return exp

    def calculate(self, expression):
        text = str(expression).strip() if expression is not None else ""
        if not text or text == "Error":
            return "0" if not text else "Error"

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
            value = self._evaluate(node.operand, functions)
            if isinstance(node.op, ast.UAdd):
                return value
            if isinstance(node.op, ast.USub):
                return -value
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
                if abs(right) > 1000:
                    raise ValueError("Exponent too large")
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


class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.color = WHITE
        self.padding = (dp(10), dp(10))


class SadafCalculatorApp(App):
    title = "SADAF Calculator"

    def build(self):
        self.engine = CalculatorEngine()
        self.expression = ""
        self.memory = 0
        self.just_calculated = False
        self.history = []

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8), background_color=BLACK)
        root.canvas.before.clear()
        with root.canvas.before:
            Color(*BLACK)
            Rectangle(pos=root.pos, size=root.size)

        header = BoxLayout(orientation="horizontal", size_hint_y=0.14, spacing=dp(8))
        header.add_widget(Widget())
        heart = Heart(size_hint=(None, None), size=(dp(42), dp(42)))
        header.add_widget(heart)

        title_label = Label(
            text="SADAF",
            font_name=BRAND_FONT,
            font_size="32sp",
            bold=True,
            color=RED,
            size_hint_x=None,
            width=dp(150),
            halign="center",
            valign="middle",
        )
        header.add_widget(title_label)
        header.add_widget(Widget())
        root.add_widget(header)

        subtitle = Label(
            text="LUXURY EDITION  •  SCIENTIFIC",
            font_name=BRAND_FONT,
            font_size="10sp",
            color=GRAY,
            size_hint_y=0.05,
            halign="center",
        )
        root.add_widget(subtitle)

        mode_box = BoxLayout(size_hint_y=0.04, spacing=dp(8))
        self.mode_label = Label(
            text="RAD",
            font_name=BRAND_FONT,
            color=RED,
            font_size="11sp",
            halign="right",
            valign="middle",
        )
        mode_box.add_widget(Widget())
        mode_box.add_widget(self.mode_label)
        root.add_widget(mode_box)

        self.history_label = Label(
            text="",
            font_size="15sp",
            color=GRAY,
            size_hint_y=0.08,
            halign="right",
            valign="middle",
        )
        self.history_label.bind(size=lambda label, size: setattr(label, "text_size", size))
        root.add_widget(self.history_label)

        self.result_label = Label(
            text="0",
            font_size="42sp",
            color=WHITE,
            bold=True,
            size_hint_y=0.18,
            halign="right",
            valign="middle",
        )
        self.result_label.bind(size=lambda label, size: setattr(label, "text_size", size))
        root.add_widget(self.result_label)

        action_bar = BoxLayout(size_hint_y=0.06, spacing=dp(5))
        history_button = RoundedButton(text="HISTORY", font_size="12sp", background_color=DARK_LIGHT)
        history_button.bind(on_press=self.show_history)
        action_bar.add_widget(history_button)
        action_bar.add_widget(Widget())
        root.add_widget(action_bar)

        rows = [
            ["MC", "MR", "M+", "M-", "COPY"],
            ["RAD", "(", ")", "C", "DEL"],
            ["sin", "cos", "tan", "√", "^"],
            ["7", "8", "9", "÷", "log"],
            ["4", "5", "6", "×", "ln"],
            ["1", "2", "3", "-", "π"],
            ["0", ".", "%", "+", "="],
        ]

        grid = GridLayout(cols=5, spacing=dp(6), size_hint_y=0.56)
        for row in rows:
            for text in row:
                button = RoundedButton(text=text, font_name=BRAND_FONT, font_size="15sp")
                button.background_color = DARK
                if text in ("=", "+", "-", "×", "÷", "^"):
                    button.background_color = RED
                elif text in ("C", "DEL", "RAD", "MC", "MR", "M+", "M-", "COPY"):
                    button.background_color = DARK_LIGHT
                button.bind(on_press=self.on_button_press)
                grid.add_widget(button)

        root.add_widget(grid)
        return root

    def update_display(self):
        self.result_label.text = self.expression if self.expression else "0"

    def reset_error_state(self):
        if self.expression == "Error":
            self.expression = ""
            self.just_calculated = False

    def update_mode_label(self):
        self.mode_label.text = "RAD" if self.engine.is_rad else "DEG"

    def add_operator(self, operator):
        self.reset_error_state()

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

    def insert_memory_value(self, value):
        if value in (None, "", "Error"):
            return
        if not self.expression or self.expression == "Error":
            self.expression = value
            return
        if self.expression[-1].isdigit() or self.expression[-1] == ")":
            self.expression += "*" + value
        else:
            self.expression += value

    def memory_action(self, action):
        self.reset_error_state()

        if action == "MC":
            self.memory = 0
            self.history_label.text = "Memory cleared"
            self.update_display()
            return

        if action == "MR":
            value = CalculatorEngine.format_number(self.memory)
            self.insert_memory_value(value)
            self.just_calculated = False
            self.history_label.text = "Memory recalled"
            self.update_display()
            return

        if action in ("M+", "M-"):
            if not self.expression:
                self.history_label.text = "No value to store"
                return
            value = self.engine.calculate(self.expression)
            if value == "Error":
                self.expression = "Error"
                self.history_label.text = "Invalid expression"
                self.update_display()
                return
            number = float(value)
            if action == "M+":
                self.memory += number
            else:
                self.memory -= number
            self.history_label.text = f"Memory {action}"
            self.update_display()

    def copy_result(self):
        value = self.expression if self.expression and self.expression != "Error" else self.result_label.text
        if value == "0" and self.expression == "":
            value = "0"
        Clipboard.copy(value)
        self.history_label.text = "Copied: " + value

    def show_history(self, *args):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        scroll = ScrollView()
        label = Label(
            text="\n".join(self.history) if self.history else "No calculations yet",
            size_hint_y=None,
            halign="right",
            valign="top",
            color=WHITE,
        )
        label.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        label.bind(texture_size=lambda widget, size: setattr(widget, "height", size[1] + dp(20)))
        scroll.add_widget(label)
        content.add_widget(scroll)

        close_btn = RoundedButton(text="CLOSE", font_size="12sp", background_color=RED)
        close_btn.bind(on_press=lambda instance: popup.dismiss())
        content.add_widget(close_btn)

        popup = Popup(title="Calculation history", content=content, size_hint=(0.9, 0.7))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def append_numeric(self, text):
        self.reset_error_state()

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
                if self.expression and self.expression[-1].isdigit() or self.expression.endswith(")"):
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

    def on_button_press(self, button):
        text = button.text

        if text == "HISTORY":
            self.show_history()
            return

        if text in ("MC", "MR", "M+", "M-"):
            self.memory_action(text)
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
            self.expression = self.expression[:-1] if self.expression and self.expression != "Error" else ""
            self.just_calculated = False
            self.history_label.text = ""
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
            self.update_mode_label()
            self.history_label.text = "Mode: " + ("RAD" if self.engine.is_rad else "DEG")
            return

        if text in OPERATORS:
            self.just_calculated = False
            self.add_operator(text)
            self.update_display()
            return

        if text in FUNCTIONS:
            self.reset_error_state()
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
