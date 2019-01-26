import os
import warnings

"""
Class to set dictionary keys as map attributes
"""
class Configuration(object):

    def __init__(self, config_map):
        for key in config_map:
            if config_map[key] == 'None':
                config_map[key] = None
            # set FSLDIR to the environment $FSLDIR if the user sets it to
            # 'FSLDIR' in the pipeline config file
            if key == 'FSLDIR':
                if config_map[key] == 'FSLDIR':
                    if os.environ.get('FSLDIR'):
                        config_map[key] = os.environ['FSLDIR']
            setattr(self, key, config_map[key])
        self.__update_attr()

    def return_config_elements(self):
        # this returns a list of tuples
        # each tuple contains the name of the element in the yaml config file
        # and its value

        # TODO ASH use __dict__ to retrieve elements
        attributes = [
            (attr, getattr(self, attr))
            for attr in dir(self)
            if not callable(attr) and not attr.startswith("__")
        ] 
        return attributes
        
    # method to find any pattern ($) in the configuration
    # and update the attributes with its pattern value
    def update_attr(self):
        from string import Template 
        
        # TODO remove function from here
        def check_pattern(orig_key):
            temp = Template(orig_key)
            if type(temp.template) is str:
                patterns = temp.pattern.findall(temp.template)
                pattern_map = {}
                for pattern in patterns:
                    for val in pattern:
                        if val:
                            if not pattern_map.get(val):
                                if getattr(self, val):
                                    pattern_map[val] = getattr(self, val)
                                else: 
                                    raise ValueError("No value found for attribute %s. "\
                                                    "Please check the configuration file" %val)
                if pattern_map:
                    return check_pattern(Template(orig_key).substitute(pattern_map))
                else:
                    return orig_key
            else:
                return orig_key
                
        def check_path(key):
            if type(key) is str and '/' in key:
                if not os.path.exists(key):
                    warnings.warn("Invalid path- %s. Please check your configuration file"%key)
            
        attributes = [(attr, getattr(self, attr)) for attr in dir(self) \
                      if not callable(attr) and not attr.startswith("__")]     
        
        for attr in attributes:
            new_key = check_pattern(attr[1])
            #check_path(new_key)
            setattr(self, attr[0], new_key)

    __update_attr = update_attr
    
    def update(self, key, val):
        setattr(self, key, val)
        
    def __copy__(self):
        newone = type(self)({})
        newone.__dict__.update(self.__dict__)
        newone.__update_attr()
        return newone
