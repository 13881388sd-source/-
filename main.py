import math
import os
import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

Window.clearcolor = get_color_from_hex("#0A0A0A")
GOLD = get_color_from_hex("#D4AF37")
DARK = get_color_from_hex("#1A1A1A")
DARK_LIGHT = get_color_from_hex("#2A2A2A")

_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sadaf_font.ttf")
BRAND_FONT = _FONT_PATH if os.path.exists(_FONT_PATH) else "Roboto"

FUNCS = ['sin', 'cos', 'tan', 'log', 'ln', '√']


class CalculatorEngine:
    def __init__(self):
        self.is_rad = True

    def calculate(self, expression):
        try:
            exp = expression.replace('×', '*').replace('÷', '/').replace('^', '**')
            exp = exp.replace('π', str(math.pi)).replace('%', '/100')
            exp = exp.replace('√', 'sqrt')
            exp = re.sub(r'(\d)\(', r'\1*(', exp)
            allowed_names = {k: getattr(math, k) for k in
                             ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sqrt', 'exp',
                              'factorial', 'radians', 'degrees', 'pi', 'e']}
            allowed_names['ln'] = math.log
            allowed_names['log'] = math.log10

            if not self.is_rad:
                exp = exp.replace('sin', 'sin_r').replace('cos', 'cos_r').replace('tan', 'tan_r')
                allowed_names['sin_r'] = lambda x: math.sin(math.radians(x))
                allowed_names['cos_r'] = lambda x: math.cos(math.radians(x))
                allowed_names['tan_r'] = lambda x: math.tan(math.radians(x))

            result = eval(exp, {"__builtins__": {}}, allowed_names)
            if isinstance(result, float) and result.is_integer():
                return str(int(result))
            return str(round(result, 10)).rstrip('0').rstrip('.')
        except Exception:
            return "Error"


class SadafCalculatorApp(App):
    title = "SADAF Calculator"

    def build(self):
        self.engine = CalculatorEngine()
        self.expression = ""

        root = BoxLayout(orientation='vertical', padding=10, spacing=8)

        header = Label(text="SADAF", font_name=BRAND_FONT, font_size='52sp',
                       color=GOLD, size_hint_y=0.15)
        root.add_widget(header)
        sub_header = Label(text="LUXURY EDITION  •  SCIENTIFIC", font_name=BRAND_FONT,
                           font_size='10sp', color=get_color_from_hex("#888888"),
                           size_hint_y=0.04)
        root.add_widget(sub_header)

        self.history_label = Label(text="", font_size='16sp',
                                   color=get_color_from_hex("#888888"), size_hint_y=0.06,
                                   halign='right', text_size=(Window.width - 20, None))
        self.result_label = Label(text="0", font_size='42sp',
                                  color=get_color_from_hex("#FFFFFF"), size_hint_y=0.16,
                                  halign='right', text_size=(Window.width - 20, None),
                                  bold=True)
        root.add_widget(self.history_label)
        root.add_widget(self.result_label)

        buttons = [
            ['RAD', '(', ')', 'C', '⌫'],
            ['sin', 'cos', 'tan', '√', '^'],
            ['7', '8', '9', '÷', 'log'],
            ['4', '5', '6', '×', 'ln'],
            ['1', '2', '3', '-', 'π'],
            ['0', '.', '%', '+', '='],
        ]

        grid = GridLayout(cols=5, spacing=8, size_hint_y=0.59)
        for row in buttons:
            for text in row:
                btn = Button(text=text, font_size='16sp', background_normal='',
                             background_color=DARK, color=get_color_from_hex("#FFFFFF"))
                if text in ['=', '+', '-', '×', '÷', '^']:
                    btn.background_color = GOLD
                    btn.color = get_color_from_hex("#000000")
                elif text in ['C', '⌫', 'RAD']:
                    btn.background_color = DARK_LIGHT

                btn.bind(on_press=self.on_button_press)
                grid.add_widget(btn)

        root.add_widget(grid)
        return root

    def on_button_press(self, instance):
        text = instance.text
        if self.expression == "Error":
            self.expression = ""

        if text == 'C':
            self.expression = ""
            self.history_label.text = ""
        elif text == '⌫':
            self.expression = self.expression[:-1]
        elif text == '=':
            self.history_label.text = self.expression
            self.expression = self.engine.calculate(self.expression)
        elif text in ('RAD', 'DEG'):
            self.engine.is_rad = not self.engine.is_rad
            instance.text = "RAD" if self.engine.is_rad else "DEG"
            return
        elif text in FUNCS:
            self.expression += text + "("
        else:
            self.expression += text

        self.result_label.text = self.expression if self.expression else "0"


if __name__ == '__main__':
    SadafCalculatorApp().run()
