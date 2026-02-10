from osdagbridge.core.utils.common import *

class FrontendData:
    """Backend for Highway Bridge Design"""
    
    def __init__(self):
        self.module = KEY_DISP_FINPLATE
        self.design_status = False
        self.design_button_status = False
    
    def input_values(self):
        """Return list of input fields for the UI"""
        options_list = []

        t1 = (KEY_MODULE, KEY_DISP_FINPLATE, TYPE_MODULE, None, True, 'No Validator')
        options_list.append(t1)

        # Type of Structure section
        t2 = (None, DISP_TITLE_STRUCTURE, TYPE_TITLE, None, True, 'No Validator')
        options_list.append(t2)

        t3 = (KEY_STRUCTURE_TYPE, KEY_DISP_STRUCTURE_TYPE, TYPE_COMBOBOX, VALUES_STRUCTURE_TYPE, True, 'No Validator')
        options_list.append(t3)

        # Project Location section
        t4 = (None, DISP_TITLE_PROJECT, TYPE_TITLE, None, True, 'No Validator')
        options_list.append(t4)

        t5 = (KEY_PROJECT_LOCATION, KEY_DISP_PROJECT_LOCATION, TYPE_COMBOBOX, VALUES_PROJECT_LOCATION, True, 'No Validator')
        options_list.append(t5)

        # Geometric Details section
        t6 = (None, DISP_TITLE_GEOMETRIC, TYPE_TITLE, None, True, 'No Validator')
        options_list.append(t6)

        t7 = (KEY_SPAN, KEY_DISP_SPAN, TYPE_TEXTBOX, None, True, 'Double Validator')
        options_list.append(t7)

        t8 = (KEY_CARRIAGEWAY_WIDTH, KEY_DISP_CARRIAGEWAY_WIDTH, TYPE_TEXTBOX, None, True, 'Double Validator')
        options_list.append(t8)

        t9 = (KEY_FOOTPATH, KEY_DISP_FOOTPATH, TYPE_COMBOBOX, VALUES_FOOTPATH, True, 'No Validator')
        options_list.append(t9)

        t10 = (KEY_SKEW_ANGLE, KEY_DISP_SKEW_ANGLE, TYPE_TEXTBOX, None, True, 'Double Validator')
        options_list.append(t10)

        # Material Inputs section
        t11 = (None, DISP_TITLE_MATERIAL, TYPE_TITLE, None, True, 'No Validator')
        options_list.append(t11)

        t12 = (KEY_GIRDER, KEY_DISP_GIRDER, TYPE_COMBOBOX, connectdb("Material"), True, 'No Validator')
        options_list.append(t12)

        t13 = (KEY_CROSS_BRACING, KEY_DISP_CROSS_BRACING, TYPE_COMBOBOX, connectdb("Material"), True, 'No Validator')
        options_list.append(t13)

        t14 = (KEY_DECK, KEY_DISP_DECK, TYPE_COMBOBOX, connectdb("Material"), True, 'No Validator')
        options_list.append(t14)

        return options_list
    
    def set_osdaglogger(self, key):
        """Logger setup"""
        print("Logger set up (mock)")
    
    def output_values(self, flag):
        """output values List"""
        return []
    
    def func_for_validation(self, design_inputs):
        """Validation Function"""
        return None

