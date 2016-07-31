# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Contributor(s): Campbell Barton, Witold Jaworski
# ***** End GPL LICENSE BLOCK *****

'''
Creates Python predefinition (*.pypredef) files for Blender API
The *.pypredef files are useful for syntax checking and
auto-completion of expressions in Eclipse IDE (with PyDev plugin)

This program is based on Campbell Barton's sphinx_doc_gen.py script

@author: Witold Jaworski (http://www.airplanes3d.net)
'''

# FIXES/UPDATES:
# 2012-03-01: In Blender 2.62 the description of the @roll argument in EditBone.transform()
#             method has an unexpected empty line, which break processing. Added handling
#             for that case in process_line() method
# 2013-03-01: In Blender 2.66 two methods of the bpy.types.Space obejects are reported as
#             Python - implemented methods, while tehy are not:
#             draw_handler_add() and draw_handler_remove()
#             I have added additional try.. except caluse to hande such errors in the future
#             (However, as long as the descriptions of these methods are wrong, tehy are not documented)
# 2013-03-13: Updates  by Brian Henke:
#             * add a no-op (pass) to functions; most were passing because they have comments but the parser fails when there are none.
#             * Remove the "import" class because it is a reserved keyword.
# 2013-03-14: Further updates: I have found another function (py_c_func2predef()) which was ommited in
#             the Brian update. I added the "pass" statement generation there.

HELP_MSG = '''Usage:
    Run this script from Blender root path:

    .\blender.exe -b -P pypredef_gen.py

    This will generate PyDev python predefiniton files (for Eclipse) in doc\python_api\pypredef\,
    assuming that .\blender.exe is the blender executable, and you have placed this script in Blender root path.'''

# Script settings
ENABLE_ECHO = False
PYPREDEF_EXT = ".py"

INCLUDED_MODULES = (
    "bpy",
    "bpy.app",
    "bpy.path",
    "bpy.props",
    "bpy.utils",
    "bge",
    "aud",
    "bgl",
    "blf",
    "mathutils",
    "mathutils.geometry"
)

_BPY_STRUCT_FAKE = "bpy_struct"
_IDENT = "    " # (4 spaces)

# Dictionary for correcting some type descriptions
TYPE_ABERRATIONS = {
        "boolean"   : "bool",
        "integer"   : "int",
        "enum"      : "str",
        "string"    : "str",
        "Matrix"    : "mathutils.Matrix",
        "Vector"    : "mathutils.Vector",
        "Quaternion": "mathutils.Quaternion",
        "Color"     : "mathutils.Color",
        "Euler"     : "mathutils.Euler",
        "subclass of bpy_struct" : "bpy_struct",
        "subclass of bpy.types.bpy_struct" : "bpy_struct",
        "bpy.types.FCurve or list if index is -1 with an array property." : "bpy.types.FCurve",
        "float triplet": "(float, float, float)",
        "string in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']" : "str #in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']",
        "tuple of 2 floats":"(float, float)",
        "mathutils.Vector's" : "mathutils.Vector",
        "list of mathutils.Vector's":"[mathutils.Vector]",
        "tuple, pair of floats":"(float, float)",
        "tuple of mathutils.Vector's":"(mathutils.Vector, mathutils.Vector)",
        "mathutils.Vector or None":"mathutils.Vector",
        "list of strigs":"[str]",
        "list of ints":"[int]",
        "list of strings":"[str]",
        "FCurve or list if index is -1 with an array property":"FCurve",
        "list of key, value tuples": ("[(str, types.{})]".format(_BPY_STRUCT_FAKE))
}

import os
import sys
import shutil
import inspect
import types
import bpy
import rna_info

class ExampleClass(object):
    @property
    def a_property(self):
        return None

    @classmethod
    def a_classmethod(cls):
        return None

    @staticmethod
    def a_staticmethod():
        return None

PropertyType                = type(ExampleClass.a_property)                  # Members marked as @property
ClassMethodType             = type(ExampleClass.__dict__["a_classmethod"])   # Members marked as @classmethod
StaticMethodType            = type(ExampleClass.__dict__["a_staticmethod"])  # Members marked as @staticmethod
ClassMethodDescriptorType   = type(dict.__dict__['fromkeys'])
MethodDescriptorType        = type(dict.get)
GetSetDescriptorType        = type(int.real)


def write_indented_lines(ident, print_function, text, strip=True):
    ''' Helper function. Apply same indentation to all lines in a multilines text.
    Details:
        @ident (string): the required prefix (spaces)
        @print_function (function): the print() or file.write() function
        @text (string): the lines that have to be shifted right
        @strip (boolean): True, when the lines should be stripped from leading and trailing spaces
    '''
    if text is None:
        return
    for line in text.split("\n"):
        if strip:
            print_function(ident + line.strip() + "\n")
        else:
            print_function(ident + line + "\n")

# Helper functions, that transforms the RST doctext like this:
#   .. method:: from_pydata(vertices, edges, faces)
#
#     Make a mesh from a list of verts/edges/faces
#     Until we have a nicer way to make geometry, use this.
#
#     :arg vertices: float triplets each representing (X, Y, Z) eg: [(0.0, 1.0, 0.5), ...].
#     :type vertices: iterable object
#     :arg edges: int pairs, each pair contains two indices to the *vertices* argument. eg: [(1, 2), ...]
#     :type edges: iterable object
#     :arg faces: iterator of faces, each faces contains three or four indices to the *vertices* argument. eg: [(5, 6, 8, 9), (1, 2, 3), ...]
#     :type faces: iterable object
#
# into pypredef header definition list, which contains following text:
#
#   def from_pydata(vertices, edges, faces):
#       ''' Make a mesh from a list of verts/edges/faces
#           Until we have a nicer way to make geometry, use this.
#           Arguments:
#           @vertices (iterable object): float triplets each representing (X, Y, Z) eg: [(0.0, 1.0, 0.5), ...].
#           @edges (iterable object): int pairs, each pair contains two indices to the *vertices* argument. eg: [(1, 2), ...]
#           @faces (iterable object): iterator of faces, each faces contains three or four indices to the *vertices* argument. eg: [(5, 6, 8, 9), (1, 2, 3), ...]
#       '''

# Some blender built-in functions have nothing, but such formatted docstring (in bpy.props, for example)
def rst2list(doc):
    '''Method tries convert given doctext into list of definition elements
        Arguments:
        @doc (string) - the documentation text of the member (preferably in sphinx RST syntax)
        Returns: dictionary with identified elements of the definition (keys: "@def","@description","@returns", and zero or more function arguments)
                 each dictionary item is a small dictionary, which content depends on the keyword:
                 "@def":
                         "prototype" : function declaration - "<name>([<arg1[,..]])"
                         "description": (optional) general description of the function
                         "type": (optional) type of the returned value - usually for the properties
                 then the list of arguments follows (if it exists)
                 [argument name:]
                         "name": argument's name (just to make the printing easier)
                         "type": argument's type (may be a class name)
                         "description": argument's description
                         "ord": nr kolejny
                 ["@returns":]
                         optional: what function/property returns:
                         "description": description of the content
                         "type":        the name of returned type
                         "ord": nr kolejny
                 ["@note":]
                         optional: note, added to description (below argument list)
                         "description": description of the content
                         "ord": nr kolejny
                 ["@seealso":]
                         optional: reference, added to description (below argument list)
                         "description": description of the content
                         "ord": nr kolejny
    '''
    def process_line(line, definition, last_entry):
        '''Helper function, that analyzes the line and tries to place the
           information it contains into "working definition"
           Arguments:
           @line (string): single line of the description
           @definition (dictionary of dictionaries): working definition of the member
           @last_entry (string): the key in definition, which was used lately (before this call)

           Returns: updated last_entry (string)
        '''
        def type_name(line):
            ''' Helper function, that tries to extract the name of Python type
                Arguments:
                @line (string): text (single line) to analyze (the expression that begins with :type: or :rtype:)
                returns the identified type or None, when it cannot identify it!
            '''
            expr = line.split(" ", 1) # split ":type: float" into (':type:', 'float')
            if len(expr) < 2: return None # we cannot identify it!
            result = expr[1].strip()
            if result in TYPE_ABERRATIONS:
                return TYPE_ABERRATIONS[result]
            else:
                return result

        line = line.lstrip(" ")
        line = line.replace(":class:", "").replace("`","") # replace occurences of ":class:`<TypeName>`" with "<TypeName>"
        line = line.replace(":exc:","").replace("`","")    # replace occurences of ":exc:`<TypeName>`" with "<TypeName>"
        if line.startswith(".. method::") or line.startswith(".. function::") or line.startswith(".. classmethod::"):
            prototype = (line.split("::", 1)[1]).lstrip(" ")
            last_entry = "@def"
            definition["@def"].setdefault("prototype", prototype)
        elif line.startswith(":arg"):
            expr = line.split(" ", 2)
            name = expr[1].rstrip(":")
            if len(expr) == 3:
                definition.setdefault(name,{"name":name, "description":expr[2], "ord":len(definition)})
            else:
                definition.setdefault(name,{"name":name, "description":"", "ord":len(definition)})
            last_entry = name
        elif line.startswith(":type:"): # property type
            expr = type_name(line)
            if expr: definition["@def"].setdefault("type",expr)
            last_entry = "@def"
        elif line.startswith(":return:"): # return description
            expr = line.split(" ",1)
            name = "@returns"
            definition.setdefault(name,{"name": "returns", "description":expr[1], "ord":len(definition)})
            last_entry = name
        elif line.startswith(":rtype:"): # type, returned by the function
            expr = type_name(line)
            if last_entry != "@returns": last_entry = "@def"
            if expr: definition[last_entry].setdefault("type",expr)
        elif line.startswith(":type"): # argument's type
            expr = line.split(" ",2)
            name = expr[1].rstrip(":")
            try:
                definition[name].setdefault("type", expr[2])
                last_entry = name
            except:
                print("Missing argument declaration for '{}'".format(name))
        elif line.startswith(".. note:: "): # note to member description
            line = line.replace(".. note:: ", "")
            name = "@note"
            definition.setdefault(name, {"description":line, "ord":len(definition)})
            last_entry = name
        elif line.startswith(".. seealso::"): # reference to external resource
            line = line.replace(".. seealso:: ","")
            name = "@seealso"
            definition.setdefault(name,{"description":line, "ord":len(definition)})
            last_entry = name
        elif line.startswith(".. literalinclude::"):
            pass # skip this line
        else: # this is just second line of description for the last entry
            #  (whole member, or just an single argument)
            if last_entry in definition and line != "" and not line.startswith("Undocumented"):
                item = definition[last_entry]
                if "description" not in item:
                    item.setdefault("description", line)
                else:
                    item["description"] = item["description"] + line + "\n"
        return last_entry
    #--------------------------------- process_line
    lines = doc.split("\n")
    last_key = "@def"
    definition = {last_key:{"description":"", "ord":0}} # at the beginning: empty description of function definition

    for line in lines:
        last_key = process_line(line,definition,last_key)
    # now let's check the result, stored in <definition> dictionary:
    return definition

def rna2list(info):
    ''' Prepares list of definition elements
        Arguments:
        @info (one of rna_info.Info*RNA types) - the descriptor of Struct, Operator, Function or Property
        Returns: dictionary of the same structure, like the one returned by rst2list()
                 "@def":
                         "prototype" : used in structs and functions
                                       for struct: declaration "class AClass(ABaseClass):"
                                       for function or operator: declaration - "<name>([<arg1[,..]])"
                                       for property: declaration - "<name> = <TypeReturned> [# (read only)]"
                         "decorator": (optional) "@classmethod" or "@staticmethod"
                         "description": (optional) general description of the element
                         "hint"       : (optional) formatting hint for the doc2definition() function: "property" for RNA properties, "class" for RNA structs
                 then the list of function's arguments follows (if they exist)
                 [argument name:]
                         "name": argument's name (just to make the printing easier)
                         "type": argument's type (may be a class name)
                         "description": argument's description
                         "ord": ordinal number
                 ["@returns":]
                         optional: what function/property returns:
                         "description": description of the content
                         "type":        the name of returned type
                         "ord": ordinal number (for functions)
                 ["@note":]
                         optional: note, added to description (below argument list)
                         "description": description of the content
                         "ord": ordinal number
                 ["@seealso":]
                         optional: reference, added to description (below argument list)
                         "description": description of the content
                         "ord": oridinal number

    '''
    def type_name(name, include_namespace=False):
        ''' Helper function, that corrects some wrong type names
            Arguments:
            @name (string): "raw" name, received from RNA
            @include_namespace: True, when append the bpy.types. prefix
            returns the corrected type name (string)
        '''
        if name in TYPE_ABERRATIONS:
            name = TYPE_ABERRATIONS[name]
        if include_namespace:
            name = "types." + name
        return name

    def get_argitem(arg, prev_ord, is_return=False):
        '''Helper function, that creates an argument definition subdictionary
           Arguments:
           @arg (rna_info.InfoPropertyRNA): descriptor of the argument
           @prev_ord (int): previous order index (to set the value for the "ord" key)

           Returns: an definistion subdictionary (keys: "name", "type", "description", "ord")
        '''
        if arg.fixed_type:
            arg_type = arg.fixed_type.identifier
        else:
            arg_type = arg.type
        if is_return:
            description = arg.get_type_description(as_ret = True) #without default value!
        else:
            description = arg.get_type_description(as_arg = True) #without default value!

        if arg.collection_type == None:
            description = description.replace(arg_type, "", 1) #remove the first occurence of type name - it repeats the declaration!

        if description.startswith(","): #it may happen, when the arg_type was at the begining of the string:
            description = (description[1:]) #skip the leading colon
        if description.startswith(" "):
            description = (description[1:]) #skip first space

        #add some human comments (if it exists):
        if arg.description:
            description = arg.description + "\n" + _IDENT + description

        if is_return:
            return {"name":"returns", "description":description, "type":type_name(arg_type, arg.fixed_type != None), "ord":(prev_ord + 1)}
        else:
            return {"name":arg.identifier, "description":description, "type":type_name(arg_type), "ord":(prev_ord + 1)}

    def get_return(returns, prev_ord):
        '''Helper function, that creates the return definition subdictionary ("@returns")
           Arguments:
           @returns (list of rna_info.InfoPropertyRNA): descriptor of the return values
           @prev_ord (int): previous order index (to set the value for the "ord" key)

           Returns: an definistion subdictionary (keys: type", "description", "ord")
        '''
        if len(returns) == 1:
            return get_argitem(returns[0],prev_ord,is_return = True)
        else: #many different values:
            description = "\n("
            for ret in returns:
                item = get_argitem(ret, prev_ord, is_return = True)
                description = description + "\n{0}{1}({2}):{3}".format(_IDENT, ret.identifier, item.pop("type"), item.pop("description"))
            #give just the description, not the type!
            description = description + "\n)"
            return {"name":"returns", "description":description, "ord":(prev_ord + 1)}

    definition = {"@def":{"description":"", "ord":0}} #at the beginning: empty description of function definition

    if type(info) == rna_info.InfoStructRNA:
        #base class of this struct:
        base_id = getattr(info.base, "identifier", _BPY_STRUCT_FAKE)
        prototype = "class {0}(types.{1}):".format(info.identifier, base_id)
        definition["@def"].setdefault("prototype", prototype)
        definition["@def"]["description"] = info.description
        definition["@def"].setdefault("hint", "class")

    elif type(info) == rna_info.InfoPropertyRNA:
        if info.collection_type:
            prop_type = info.collection_type.identifier
        elif info.fixed_type:
            prop_type = info.fixed_type.identifier
        else:
            prop_type = info.type
        prototype = "{0} = {1}()".format(info.identifier, type_name(prop_type, info.fixed_type != None))
        if info.is_readonly:
            prototype = prototype + " # (read only)"

        prototype = prototype + " # debug102"

        definition["@def"].setdefault("prototype", prototype)
        definition["@def"].setdefault("hint","property")

        if info.description:
            definition["@def"]["description"] = info.description

        definition.setdefault("@returns",{"name" : "returns", "description" : info.get_type_description(as_ret = True), "ord" : 1})

    elif type(info) == rna_info.InfoFunctionRNA:
        args_str = ", ".join(prop.get_arg_default(force=False) for prop in info.args)
        prototype = "{0}({1})".format(info.identifier, args_str)
        definition["@def"].setdefault("prototype",prototype)
        if info.is_classmethod: definition["@def"].setdefault("decorator","@classmethod\n")
        definition["@def"]["description"] = info.description
        #append arguments:
        for arg in info.args:
            definition.setdefault(arg.identifier, get_argitem(arg,len(definition)))
        #append returns (operators have none):
        if info.return_values:
            definition.setdefault("@returns",get_return(info.return_values,len(definition)))

    elif type(info) == rna_info.InfoOperatorRNA:
        args_str = ", ".join(prop.get_arg_default(force=False) for prop in info.args)
        prototype = "{0}({1})".format(info.func_name, args_str)
        definition["@def"].setdefault("prototype",prototype)
        # definition["@def"].setdefault("decorator","@staticmethod\n")
        if info.description and info.description != "(undocumented operator)":
            definition["@def"]["description"] = info.description
        else: #just empty line
            definition["@def"]["description"] = "undocumented"
        #append arguments:
        for arg in info.args:
            definition.setdefault(arg.identifier, get_argitem(arg,len(definition)))
    else:
        raise TypeError("type was not InfoFunctionRNA, InfoStructRNA, InfoPropertyRNA or InfoOperatorRNA")

    return definition

# TODO: rewrite
def doc2definition(doc, docstring_ident=_IDENT):
    '''Method converts given doctext into declaration and docstring comment
    Details:
        @doc (string or list) - the documentation text of the member (preferably in sphinx RST syntax)
                                or ready dictionary of dictionaries, like the result of rst2list() (see above)
        @docstring_ident (string) - the amount of spaces before docstring markings
        @function - function, that should be used to get the list
        Returns: dictionary with following elements:
             "declaration": function declaration (may be omitted for attributes docstrings)
             "docstring": properly idented docstring (leading and trailing comment markings included)
             "returns": type, returned by property/function (to use in eventual return statement)
    '''
    def pop(definition,key):
        '''Removes the given element form the dictionary
            Arguments:
            @definition: dictionary[key]
            @key:        the key in the definition dictionary
        '''
        if key in definition:
            return definition.pop(key)
        else:
            return None

    def format_arg(data):
        '''Returns line of text, describing an argument or return statement
            Arguments:
            data (dictionary): a "subdictionary" of <definition>, describing single item:
                                ("ord", "name", ["description"],["type"])
        '''
        if "type" in data and "description" in data:
            return "@{name} ({type}): {description}".format(**data)
        elif "type" in data:
            return "@{name} ({type}): <not documented>".format(**data)
        elif "description" in data:
            return "@{name}: {description}".format(**data)
        else:
            return "@{name}: <not documented>".format(**data)

    def get(definition, key, subkey):
        ''' Returns the given value from the definition dictionary, or None
            when it does not exists
            Arguments:
            @definition: dictionary[key] of dictionaries[subkey]
            @key:        the key in the definition dictionary
            @subkey:     the key in the definition[key] subdictionary
        '''
        if key in definition:
            if subkey in definition[key]:
                return definition[key][subkey]
            else:
                return None
        else:
            return None

    if doc is None:
        return {"docstring" : docstring_ident + "\n"}

    if type(doc) is str:
        definition = rst2list(doc)
    else:
        definition = doc # assume, that doc is the ready definition list!

    rtype = get(definition, "@def", "type")
    if rtype is None:
        rtype = get(definition,"@returns", "type") # for functions

    _returns = pop(definition, "@returns")

    _note = pop(definition,"@note")

    _seealso = pop(definition, "@seealso")

    declaration = get(definition, "@def", "prototype")
    decorator   = get(definition, "@def", "decorator")
    hint        = get(definition, "@def", "hint")
    if declaration:
        if hint in ("property", "class"):
            pass # no prefix needed
        elif decorator:
            declaration = decorator + "def " + declaration + ":"
        else:
            declaration = "def " + declaration + ":"

    _def = pop(definition, "@def") # remove the definition from the list

    ident = docstring_ident + _IDENT # all next row will have additional ident, to match the first line
    lines = [] #lines of the docstring text

    al = lines.append # trick, to re-use the write_indented_lines to add the line

    if "description" in _def:
        write_indented_lines(ident,al,_def["description"],False) #fill the <lines> list
        if lines:
            lines[0] = lines[0][len(ident):] # skip the ident in the first and the last line:
                                             # (the docstring's prefix "   '''" will be placed there)

    if definition.keys(): # Are named arguments there?
        write_indented_lines(ident, al, "Arguments:", False)

        for tuple in sorted(definition.items(),key = lambda item: item[1]["ord"]): # sort the lines in the original sequence
            # first item of the <tuple> is the key, second - the value (dictionary describing a single element)
            write_indented_lines(ident, al, format_arg(tuple[1]), False)
        al("\n")

    if _returns:
        write_indented_lines(ident, al, format_arg(_returns), False)

    if _note and "description" in _note:
        write_indented_lines(ident, al, "Note: " + _note["description"], False)

    if _seealso and "description" in _seealso:
        write_indented_lines(ident, al, "(seealso " + _seealso["description"] + ")\n", False)

    if not lines:
        lines.append("<not documented>\n")

    result = {"docstring" : docstring_ident + "'''" + "".join(lines) + docstring_ident + "'''\n"}

    if declaration:
        result.setdefault("declaration", declaration)

    if rtype:
        result.setdefault("returns", rtype)

    return result

def pyfunc2predef(ident, fw, identifier, py_func, is_class=True):
    ''' Creates declaration of a function or class method
        Details:
        @ident (string): the required prefix (spaces)
        @fw (function): the unified shortcut to print() or file.write() function
        @identifier (string): the name of the member
        @py_func (<py function>): the method, that is being described here
        @is_class (boolean): True, when it is a class member
    '''
    try:
        arguments = inspect.getargspec(py_func)
        if len(arguments.args) == 0 and is_class:
            fw(ident + "@staticmethod\n")
        elif len(arguments.args) == 0: # global function (is_class = false)
            pass
        elif arguments.args[0] == "cls" and is_class:
            fw(ident + "@classmethod\n")
        else: # global function
            pass

        definition = doc2definition(py_func.__doc__) # parse the eventual RST sphinx markup

        if "declaration" in definition:
            write_indented_lines(ident, fw, definition["declaration"], False)
        else:
            arg_str = inspect.formatargspec(*arguments)
            fw(ident + "def {}{}:\n".format(identifier, arg_str))

        if "docstring" in definition:
            write_indented_lines(ident, fw, definition["docstring"], False)

        if "returns" in definition:
            write_indented_lines(ident + _IDENT, fw, "return " + definition["returns"], False)
        else:
            write_indented_lines(ident + _IDENT, fw, "pass", False)

        fw(ident + "\n")
    except:
        msg = "# Unable to describe the '{}' method due to internal error\n\n".format(identifier)
        fw(ident + msg)

def py_descr2predef(ident, fw, descr, module_name, type_name, identifier):
    ''' Creates declaration of a function or class method
        Details:
        @ident (string): the required prefix (spaces)
        @fw (function): the unified shortcut to print() or file.write() function
        @descr(<type descriptor>): an object, describing the member
        @module_name (string): the name of this module
        @type_name (string): the name of the containing class
        @identifier (string): the name of the member
    '''

    if identifier.startswith("_"):
        return

    if type(descr) in (types.GetSetDescriptorType, types.MemberDescriptorType): # an attribute of the module or class
        definition = doc2definition(descr.__doc__, "") # Parse the eventual RST sphinx markup
        if "returns" in definition:
            returns = definition["returns"] + "()" + " # debug201"
        else:
            returns = "None" # we have to assign just something, to be properly parsed!

        fw(ident + identifier + " = " + returns + "\n")

        if "docstring" in definition:
            write_indented_lines(ident, fw, definition["docstring"], False)

    elif type(descr) in (MethodDescriptorType, ClassMethodDescriptorType):
        py_c_func2predef(ident, fw, module_name, type_name, identifier, descr, is_class=True)
    else:
        raise TypeError("type was not MemberDescriptiorType, GetSetDescriptorType, MethodDescriptorType or ClassMethodDescriptorType")
    fw("\n")

def py_c_func2predef(ident, fw, module_name, type_name, identifier, py_func, is_class=True):
    ''' Creates declaration of a function or class method
        Details:
        @ident (string): the required prefix (spaces)
        @fw (function): the unified shortcut to print() or file.write() function
        @type_name (string): the name of the class
        @py_func (<py function>): the method, that is being described here
        @is_class (boolean): True, when it is a class member
    '''
    definition = doc2definition(py_func.__doc__) # Parse the eventual RST sphinx markup
    if type(py_func) == ClassMethodDescriptorType:
        fw(ident + "@classmethod\n")

    if "declaration" in definition:
        write_indented_lines(ident, fw, definition["declaration"], False)
    else:
        fw(ident + "def {}(*argv):\n".format(identifier)) # Pass *argv, because we do not know about its arguments...

    if "docstring" in definition:
        write_indented_lines(ident, fw, definition["docstring"], False)

    if "returns" in definition:
        write_indented_lines(ident + _IDENT, fw, "return " + definition["returns"] + "()" + " # debug200", False)
    else:
        write_indented_lines(ident + _IDENT, fw, "pass", False)

    fw(ident + "\n")

def pyprop2predef(ident, write_func, identifier, py_prop):
    ''' Creates declaration of a property
        Details:
        @ident (string): the required prefix (spaces)
        @write_func (function): the unified shortcut to print() or file.write() function
        @identifier (string): the name of the property
        @py_prop (<py property>): the property, that is being described here
    '''
    definition = doc2definition(py_prop.__doc__, "") # Parse the eventual RST sphinx markup
    if "returns" in definition:
        declaration = identifier + " = " + definition["returns"] + " # debug100"
    else:
        declaration = identifier + " = None"    # we have to assign just something, to be properly parsed!

    # readonly properties use "data" directive, variables use "attribute" directive
    if py_prop.fset is None: declaration = declaration + " # (readonly)" + " # debug101"

    write_func(ident + declaration + "\n")

    if "docstring" in definition:
        write_indented_lines(ident, write_func, definition["docstring"], False)

    write_func(ident + "\n")

def pyclass2predef(write_func, module_name, type_name, value):
    ''' Creates declaration of a class
        Details:
        @write_func (function): the unified shortcut to print() or file.write() function
        @module_name (string): the name of the module, that contains this class
        @type_name (string): the name of the class
        @value (<class type>): the descriptor of this type
    '''
    write_func("class {}:\n".format(type_name))
    definition = doc2definition(value.__doc__) # Parse the eventual RST sphinx markup
    if "docstring" in definition:
        write_indented_lines("", write_func, definition["docstring"], False)

    descr_items = [(key, descr) for key, descr in sorted(value.__dict__.items()) if not key.startswith("__")]

    for key, descr in descr_items:
        if type(descr) == ClassMethodDescriptorType:
            py_descr2predef(_IDENT, write_func, descr, module_name, type_name, key)

    for key, descr in descr_items:
        if type(descr) == MethodDescriptorType:
            py_descr2predef(_IDENT, write_func, descr, module_name, type_name, key)

    for key, descr in descr_items:
        if type(descr) in {types.FunctionType, types.MethodType}:
            pyfunc2predef(_IDENT, write_func, key, descr)

    for key, descr in descr_items:
        if type(descr) == types.GetSetDescriptorType:
            py_descr2predef(_IDENT, write_func, descr, module_name, type_name, key)

    for key, descr in descr_items:
        if type(descr) == PropertyType:
            pyprop2predef(_IDENT, write_func, key, descr)

    write_func("\n\n")

def pymodule2predef(BASEPATH, module_name, module, title):
    attribute_set = set()
    filepath = os.path.join(BASEPATH, module_name + PYPREDEF_EXT)

    file = open(filepath, "w")
    write_func = file.write

    #The description of this module:
    if module.__doc__:
        title = title + "\n" + module.__doc__
    definition = doc2definition(title, "") # skip the leading spaces at the first line...
    write_func(definition["docstring"])
    write_func("\n\n")

    # write members of the module
    # only tested with PyStructs which are not exactly modules
    # List the properties, first:
    for key, descr in sorted(type(module).__dict__.items()):
        if key.startswith("__"):
            continue
        # naughty, we also add getset's into PyStructs, this is not typical py but also not incorrect.
        if type(descr) == types.GetSetDescriptorType :  # 'bpy_app_type' name is only used for examples and messages
            py_descr2predef("", write_func, descr, module_name, "bpy_app_type", key)
            attribute_set.add(key)

    # Then list the attributes:
    for key, descr in sorted(type(module).__dict__.items()):
        if key.startswith("__"):
            continue
        # naughty, we also add getset's into PyStructs, this is not typical py but also not incorrect.
        if type(descr) == types.MemberDescriptorType:  # 'bpy_app_type' name is only used for examples and messages
            py_descr2predef("", write_func, descr, module_name, "", key)
            attribute_set.add(key)

    del key, descr

    # list classes:
    classes = []

    for attribute in sorted(dir(module)):
        if not attribute.startswith("_"):

            if attribute in attribute_set: # skip the processed items:
                continue

            if attribute.startswith("n_"):  # annoying exception, needed for bpy.app
                continue

            value = getattr(module, attribute)

            value_type = type(value)

            if value_type == types.FunctionType:
                pyfunc2predef("", write_func, attribute, value, is_class=False)

            elif value_type in (types.BuiltinMethodType, types.BuiltinFunctionType):  # both the same at the moment but to be future proof
                # note: can't get args from these, so dump the string as is
                # this means any module used like this must have fully formatted docstrings.
                py_c_func2predef("", write_func, module_name, module, attribute, value, is_class=False)

            elif value_type == type:
                classes.append((attribute, value))

            elif value_type in (bool, int, float, str, tuple):
                # constant, not much fun we can do here except to list it.
                # TODO, figure out some way to document these!
                write_func("{} = {} # constant value\n\n".format(attribute, repr(value)))

            else:
                if ENABLE_ECHO: print("\t" + "not documenting {}.{}".format(module_name, attribute))
                continue

            attribute_set.add(attribute)
            # TODO, more types...

    # write collected classes now
    for (type_name, value) in classes:
        pyclass2predef(write_func, module_name, type_name, value)

    file.close()

def rna_property2predef(ident, write_func, descr):
    ''' Creates declaration of a property
        Details:
        @ident (string): the required prefix (spaces)
        @write_func (function): the unified shortcut to print() or file.write() function
        @descr (rna_info.InfoPropertyRNA): descriptor of the property
    '''
    definition = doc2definition(rna2list(descr),docstring_ident="")
    write_indented_lines(ident, write_func, definition["declaration"], False)

    if "docstring" in definition:
        write_indented_lines(ident, write_func, definition["docstring"], False)

def rna_function2predef(ident, write_func, descr):
    ''' Creates declaration of a function or operator
        Details:
        @ident (string): the required prefix (spaces)
        @write_func (function): the unified shortcut to print() or file.write() function
        @descr (rna_info.InfoFunctionRNA or rna_info.InfoOperatorRNA): method's descriptor
    '''
    definition = doc2definition(rna2list(descr))
    write_indented_lines(ident, write_func, definition["declaration"], False) # may contain two lines: decorator and declaration

    if "docstring" in definition:
        write_indented_lines(ident, write_func, definition["docstring"], False)

    if "returns" in definition:
        write_indented_lines(ident + _IDENT, write_func, "return " + definition["returns"], False)
    else:
        write_indented_lines(ident + _IDENT, write_func, "pass", False)

    write_func("\n")

def rna_struct2predef(ident, write_func, descr):
    ''' Creates declaration of a bpy structure
        Details:
        @ident (string): the required prefix (spaces)
        @write_func (function): the unified shortcut to print() or file.write() function
        @descr (rna_info.InfoStructRNA): the descriptor of a Blender Python class
    '''
    if ENABLE_ECHO: print("class {}:\n".format(descr.identifier))
    definition = doc2definition(rna2list(descr))
    write_indented_lines(ident, write_func, definition["declaration"], False)

    if "docstring" in definition:
        write_indented_lines(ident, write_func, definition["docstring"], False)

    # native properties
    ident = ident + _IDENT
    properties = descr.properties
    properties.sort(key=lambda prop: prop.identifier)
    for prop in properties:
        rna_property2predef(ident, write_func, prop)

    # Python properties
    properties = descr.get_py_properties()
    for identifier, prop in properties:
        pyprop2predef(ident, write_func, identifier, prop)

    # Blender native functions
    functions = descr.functions
    for function in functions:
        rna_function2predef(ident, write_func, function)

    functions = descr.get_py_functions()
    for identifier, function in functions:
        pyfunc2predef(ident, write_func, identifier, function, is_class=True)

def ops_struct2predef(ident, write_func, module, operators):
    ''' Creates "pseudo structure" for a given module of operators
        Details:
        @ident (string): the required prefix (spaces)
        @write_func (function): the unified shortcut to print() or file.write() function
        @module (string): one of bpy.ops names ("actions", for example)
        @operators (list of rna_info.InfoOperatorRNA): operators, grouped in this module
    '''
    write_func(ident + "class {0}(object):\n".format(module)) # "action" -> "class action:\n"
    ident = ident + _IDENT
    write_func(ident + "'''Special class, created just to reflect content of bpy.ops.{0}'''\n\n".format(module))

    ops = list(operators)
    ops.sort(key=lambda op: op.func_name)

    for op in ops:
        rna_function2predef(ident, write_func, op)

def bpy_base2predef(ident, write_func):
    ''' Creates a structure for the Blender base class
        Details:
        @ident (string): the required prefix (spaces)
        @write_func (function): the unified shortcut to print() or file.write() function
    '''
    fmt = ident + "class {}(object):\n"
    write_func(fmt.format(_BPY_STRUCT_FAKE))
    ident = ident + _IDENT
    write_func(ident + "'''built-in base class for all classes in bpy.types.\n\n")
    fmt = ident + _IDENT + "Note that bpy.types.{} is not actually available from within blender, it only exists for the purpose of documentation.\n" + ident + "'''\n\n"
    write_func(fmt.format(_BPY_STRUCT_FAKE))

    descr_items = [(key, descr) for key, descr in sorted(bpy.types.Struct.__bases__[0].__dict__.items()) if not key.startswith("__")]

    for key, descr in descr_items:
        if type(descr) == MethodDescriptorType:  # GetSetDescriptorType, GetSetDescriptorType's are not documented yet
            py_descr2predef(ident, write_func, descr, "bpy.types", _BPY_STRUCT_FAKE, key)

    for key, descr in descr_items:
        if type(descr) == types.GetSetDescriptorType:
            py_descr2predef(ident, write_func, descr, "bpy.types", _BPY_STRUCT_FAKE, key)
    write_func("\n\n")

def bpy2predef(BASEPATH, title):
    ''' Creates the bpy.predef file. It contains the bpy.dta, bpy.ops, bpy.types
        Arguments:
        BASEPATH (string): path for the output file
        title(string): descriptive title (the comment for the whole module)
    '''
    def property2predef(ident, write_func, module, name):
        ''' writes definition of a named property
            Details:
            @ident (string): the required prefix (spaces)
            @write_func (function): the unified shortcut to print() or file.write() function
            @module (string): one of bpy.ops names ("actions", for example)
            @name (string): name of the property
        '''
        value = getattr(module, name, None)
        if value:
            value_type = getattr(value, "rna_type", None)
            if value_type:
                write_func("{} = types.{}\n".format(name, value_type.identifier))
            else:
                pyclass2predef(write_func, modulr, name, value)
        write_func("\n\n")

    # read all data:
    structs, funcs, ops, props = rna_info.BuildRNAInfo()
    # open the file:
    filepath = os.path.join(BASEPATH, "bpy" + PYPREDEF_EXT)
    file = open(filepath, "w")
    write_func = file.write
    # start the file:
    definition = doc2definition(title, "") # skip the leading spaces at the first line
    write_func(definition["docstring"])
    write_func("\n\n")

    # Add data members
    property2predef("", write_func, bpy, "context")
    property2predef("", write_func, bpy, "data")

    # Group operators by modules: (dictionary of list of the operators)
    op_modules = {}
    for op in ops.values():
        op_modules.setdefault(op.module_name, []).append(op)

    # Special declaration of non-existing structure just for the ops member:
    write_func("class ops(object):\n")
    write_func(_IDENT + "'''Special class, created just to reflect content of bpy.ops'''\n\n")
    for op_module_name, ops_mod in sorted(op_modules.items(),key = lambda m : m[0]):
        if op_module_name == "import":
            continue
        ops_struct2predef(_IDENT, write_func, op_module_name, ops_mod)

    # Classes (Blender structures)
    write_func("class types(object):\n")
    write_func(_IDENT + "'''A container for all Blender types'''\n" + _IDENT + "\n")

    # Base structure
    bpy_base2predef(_IDENT, write_func)

    # Sort the type names:
    classes = list(structs.values())
    classes.sort(key=lambda cls: cls.identifier)

    for cls in classes:
        # Skip operators
        if "_OT_" not in cls.identifier:
            rna_struct2predef(_IDENT, write_func, cls)

    file.close()

def rna2predef(BASEPATH):

    shutil.rmtree(BASEPATH, True)
    os.mkdir(BASEPATH)

    if "bpy" in INCLUDED_MODULES:
        bpy2predef(BASEPATH, "Blender API main module")
    
    # internal modules
    api_module = None

    # python modules
    if "bpy.utils" in INCLUDED_MODULES:
        from bpy import utils as api_module
        pymodule2predef(BASEPATH, "bpy.utils", api_module, "Utilities (bpy.utils)")

    if "bpy.path" in INCLUDED_MODULES:
        from bpy import path as api_module
        pymodule2predef(BASEPATH, "bpy.path", api_module, "Path Utilities (bpy.path)")

    # C modules
    if "bpy.app" in INCLUDED_MODULES:
        from bpy import app as api_module
        pymodule2predef(BASEPATH, "bpy.app", api_module, "Application Data (bpy.app)")

    if "bpy.props" in INCLUDED_MODULES:
        from bpy import props as api_module
        pymodule2predef(BASEPATH, "bpy.props", api_module, "Property Definitions (bpy.props)")

    if "mathutils" in INCLUDED_MODULES:
        import mathutils as api_module
        pymodule2predef(BASEPATH, "mathutils", api_module, "Math Types & Utilities (mathutils)")

    if "mathutils.geometry" in INCLUDED_MODULES:
        import mathutils.geometry as api_module
        pymodule2predef(BASEPATH, "mathutils.geometry", api_module, "Geometry Utilities (mathutils.geometry)")

    if "blf" in INCLUDED_MODULES:
        import blf as api_module
        pymodule2predef(BASEPATH, "blf", api_module, "Font Drawing (blf)")

    if "bgl" in INCLUDED_MODULES:
        import bgl as api_module
        pymodule2predef(BASEPATH, "bgl", api_module, "Open GL functions (bgl)")

    if "aud" in INCLUDED_MODULES:
        import aud as api_module
        pymodule2predef(BASEPATH, "aud", api_module, "Audio System (aud)")

    del api_module

def main():
    import bpy
    if 'bpy' not in dir():
        print("\n" + "Error, this script must run from inside Blender")
        print(HELP_MSG)
    else:
        import shutil
        import imp
        # reload(rna_info) to avoid repeated arguments in function
        # definitions on second and the next runs (bug in rna_info.py)
        imp.reload(rna_info)

        # program run from text window has non-existing path ("/" - the root)
        if os.path.exists(__file__):
            script_dir = os.path.dirname(__file__)
        else:
            # current directory (where the blender.exe resides)
            script_dir = os.path.join(os.path.curdir)

        print("script_dir = " + script_dir)

        path_in = os.path.join(script_dir, "pypredef")

        rna2predef(path_in)

main()

if __name__ == '__main__':
    sys.exit()