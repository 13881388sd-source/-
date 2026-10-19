import ast
import math
import os
import re

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Triangle
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

RED = get_color_from_hex("#E50914")
DARK = get_color_from_hex("#1A1A1A")
DARK_LIGHT = get_color_from_hex("#2A2A2A")
WHITE = get_color_from_hex("#FFFFFF")
GRAY = get_color_from_hex("#888888")

FONT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sadaf_font.ttf"
)
BRAND_FONT = FONT_PATH if os.path.exists(FONT_PATH) else "Roboto"

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
            Ellipse(
                pos=(x + side * 0.5, y + side * 0.4),
                size=(side * 0.5, side * 0.5)
            )
            Triangle(points=[
                x + side * 0.07, y + side * 0.47,
                x + side * 0.93, y + side * 0.47,
                x + side * 0.5, y + side * 0.05
            ])


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

    def calculate(self, expression):
        if not expression:
            return "0"

        try:
            exp = expression
            exp = exp.replace("×", "*").replace("÷", "/")
            exp = exp.replace("^", "**").replace("π", "pi")
            exp = exp.replace("√", "sqrt")
            exp = exp.replace("%", "/100")

            # ضرب ضمنی، مثل 2(3) یا 2π
            exp = re.sub(
                r"(\d|\))(?=(?:\(|pi\b|e\b|sin\b|cos\b|tan\b|log\b|ln\b|sqrt\b))",
                r"\1*",
                exp
            )
            exp = re.sub(r"\b(pi|e)\(", r"\1*(", exp)

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

        root = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(5)
        )

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=0.13,
            spacing=dp(8)
        )

        header.add_widget(Widget())

        heart = Heart(size_hint=(None, None), size=(dp(42), dp(42)))
        header.add_widget(heart)

        name = Label(
            text="SADAF",
            font_name=BRAND_FONT,
            font_size="42sp",
            color=RED,
            size_hint_x=None,
            width=dp(170)
        )
        header.add_widget(name)
        header.add_widget(Widget())
        root.add_widget(header)

        subtitle = Label(
            text="LUXURY EDITION  •  SCIENTIFIC",
            font_name=BRAND_FONT,
            font_size="10sp",
            color=GRAY,
            size_hint_y=0.04
        )
        root.add_widget(subtitle)

        self.history_label = Label(
            text="",
            font_size="15sp",
            color=GRAY,
            size_hint_y=0.07,
            halign="right",
            valign="middle"
        )
        self.history_label.bind(
            size=lambda label, size: setattr(label, "text_size", size)
        )
        root.add_widget(self.history_label)

        self.result_label = Label(
            text="0",
            font_size="40sp",
            color=WHITE,
            bold=True,
            size_hint_y=0.17,
            halign="right",
            valign="middle"
        )
        self.result_label.bind(
            size=lambda label, size: setattr(label, "text_size", size)
        )
        root.add_widget(self.result_label)

        history_button = Button(
            text="HISTORY",
            font_size="13sp",
            size_hint_y=0.05,
            background_normal="",
            background_color=DARK_LIGHT,
            color=WHITE
        )
        history_button.bind(on_press=self.show_history)
        root.add_widget(history_button)

        rows = [
            ["MC", "MR", "M+", "M-", "COPY"],
            ["RAD", "(", ")", "C", "DEL"],
            ["sin", "cos", "tan", "√", "^"],
            ["7", "8", "9", "÷", "log"],
            ["4", "5", "6", "×", "ln"],
            ["1", "2", "3", "-", "π"],
            ["0", ".", "%", "+", "="],
        ]

        grid = GridLayout(
            cols=5,
            spacing=dp(5),
            size_hint_y=0.54
        )

        for row in rows:
            for text in row:
                button = Button(
                    text=text,
                    font_size="14sp",
                    background_normal="",
                    background_color=DARK,
                    color=WHITE
                )

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

    def add_operator(self, operator):
        if not self.expression:
            if operator == "-":
                self.expression = "-"
            return

        last = self.expression[-1]

        if last in OPERATORS:
            if operator == "-":
                self.expression += "-"
            else:
                self.expression = self.expression[:-1] + operator
            return

        if last == "(" and operator != "-":
            return

        self.expression += operator

    def memory_value_text(self):
        return CalculatorEngine.format_number(self.memory)

    def memory_action(self, action):
        if action == "MC":
            self.memory = 0

        elif action == "MR":
            value = self.memory_value_text()
            if self.just_calculated or not self.expression:
                self.expression = value
            else:
                self.expression += "(" + value + ")"
            self.just_calculated = False

        elif action in ("M+", "M-"):
            value = self.engine.calculate(self.expression or "0")
            if value != "Error":
                number = float(value)
                if action == "M+":
                    self.memory += number
                else:
                    self.memory -= number

        self.update_display()

    def copy_result(self):
        if self.expression and not self.just_calculated:
            value = self.engine.calculate(self.expression)
            if value == "Error":
                value = self.result_label.text
        else:
            value = self.result_label.text

        Clipboard.copy(value)
        self.history_label.text = "Copied: " + value

    def show_history(self, *args):
        content = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        scroll = ScrollView()
        text = "\n".join(self.history) if self.history else "No calculations yet"

        label = Label(
            text=text,
            size_hint_y=None,
            halign="right",
            valign="top",
            color=WHITE
        )
        label.bind(
            width=lambda widget, width: setattr(widget, "text_size", (width, None))
        )
        label.bind(
            texture_size=lambda widget, size: setattr(widget, "height", size[1] + dp(20))
        )

        scroll.add_widget(label)
        content.add_widget(scroll)

        close_button = Button(
            text="CLOSE",
            size_hint_y=None,
            height=dp(45),
            background_normal="",
            background_color=RED
        )
        content.add_widget(close_button)

        popup = Popup(
            title="Calculation history",
            content=content,
            size_hint=(0.9, 0.7)
        )
        close_button.bind(on_press=popup.dismiss)
        popup.open()

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

        if self.expression == "Error":
            self.expression = ""
            self.just_calculated = False

        if text == "C":
            self.expression = ""
            self.history_label.text = ""
            self.just_calculated = False

        elif text == "DEL":
            self.expression = self.expression[:-1]
            self.just_calculated = False

        elif text == "=":
            if not self.expression:
                return

            old_expression = self.expression
            result = self.engine.calculate(old_expression)

            if result == "Error":
                self.expression = "Error"
            else:
                self.history.insert(0, old_expression + " = " + result)
                self.history = self.history[:30]
                self.history_label.text = old_expression
                self.expression = result

            self.just_calculated = True

        elif text in ("RAD", "DEG"):
            self.engine.is_rad = not self.engine.is_rad
            button.text = "RAD" if self.engine.is_rad else "DEG"
            return

        elif text in OPERATORS:
            self.just_calculated = False
            self.add_operator(text)

        elif text in FUNCTIONS:
            if self.just_calculated:
                self.expression = ""
            self.just_calculated = False
            self.expression += text + "("

        else:
            if self.just_calculated and (text.isdigit() or text == "."):
                self.expression = ""
            self.just_calculated = False
            self.expression += text

        self.update_display()


if __name__ == "__main__":
    SadafCalculatorApp().run()
