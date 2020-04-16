from typing import Any, Optional, Iterable
from dataclasses import dataclass
from collections import defaultdict, OrderedDict
from urllib.parse import urlparse, urlencode

class QueryException(Exception):
    """
    Base exception for query issues.
    
    A payload can be included. The string output of the Exception
    will be message and the formatted payload according to the format_payload method
    if it exists, seperated by newlines.
    """
    def __init__(self, message, payload=None):
        """
        Parameters
        ----------
        message: str
        payload: Any
        """
        self.message = message
        self.payload = payload
    
    def format_payload(self):
        """
        Format the payload for output.
        
        Returns
        -------
        str
        """
        return str(payload)
    
    def __str__(self):
        if self.payload:
            return str(self.message) + '\n' + self.format_payload()
        else:
            return str(self.message)      

class QueryValueError(QueryException, ValueError):
    """
    This value error will wrap issues from any number of invalid query arguments.
    """
    def __init__(self, message, payload=None):
        """
        Parameters
        ----------
        message: str
        payload: Iterable[str]
            The payload in this case should be a list of individual error strings.
        """
        self.message = message
        self.payload = payload
    
    def format_payload(self):
        """
        Returns
        -------
        str
        """
        full_str = ["The following arguments have errors with their values:"]
        for error_message in self.payload:
            full_str.append("    %s"%error_message)
        return '\n'.join(full_str)

class QueryRequirementError(QueryException, ValueError):
    """
    This error will handle any number of query arguments not having dependencies.
    """
    def __init__(self, message, payload=None):
        """
        Parameters
        ----------
        message: str
        payload: dict
            This payload should be a dictionary with the keys corresponding to the argument names,
            and the values corresponding to the iterable of missing requirements.
        """
        self.message = message
        self.payload = payload
        
    def format_payload(self):
        """
        Returns
        -------
        str
        """
        full_str = ["The following query arguments are missing required supporting arguments:"]
        single_fmt = '    %s is missing requirement'
        for arg_name, reqs in self.payload:
            if isinstance(reqs, str):
                reqs_str = ': '
                reqs_str += reqs
            else:
                if len(reqs) > 1:
                    reqs_str = 's: '
                    reqs_str += ', '.join(reqs[:-1]) + ' and ' + reqs[-1] + '.'
                else:
                    reqs_str = ': '
                    reqs_str += reqs[0]
            full_str.append(single_fmt%(arg_name, reqs_str))
        return '\n'.join(full_str)
    
@dataclass
class QueryArgument:
    """
    A dataclass for handling the data associated with a single query arguement.
    
    Attributes
    ----------
    arg_name: str
        The key associated with the url query string.
    type: type
        The type that the value should be.
    required: bool, optional
        Whether or not the value is required for a query. Defaults to False.
    mutable: bool, optional
        Wheter or not the value is mutable for a query. Defaults to True.
    fmt: str, optional
        A string format for the value. Expecting either a single empty new-style '{}' 
        or empty old style '%s'. Defaults to None.
    choices: Iterable, optional
        The choices that the value can be. Defaults to None.
    requires: Iterable, optional
        The other QueryArguments that this argument is dependent on. Defaults to None
    disp_name: str, optional
        A human readable name for the arguement. Defaults to None.
    is_empty: bool
        True only if the value is None, and the argument is not required.
    value_valid: bool
        True only if the value exists if it's required to, the type is correct, and the choice matches.
    encoded: str
        The value, properly string formatted according to fmt.
    doc: str
        The docstring for any properties defined around this argument.
    error_message: str
        The message for any errors assocaited with the argument.
    
    Methods
    -------
    missing_requirements(other_arg_names)
        Get any required arguments that are missing.
    """
    arg_name : str
    type : Optional[Any]=Any
    required : bool=False
    value : Optional[Any]=None
    mutable : bool=True
    fmt : Optional[str]=None
    choices : Optional[Iterable]=None
    requires : Optional[Iterable]=None
    disp_name : Optional[str]=None
    
    @property
    def is_empty(self):
        """
        bool: True only if the value is None, and the argument is not required.
        """
        return self.value is None and not self.required
            
    @property
    def value_valid(self):
        """
        bool: True if the value is valid.
        """
        return self._has_value_if_required and self._valid_type and self._valid_choice 
    
    
    @property
    def encoded(self):
        """
        str: The value properly encoded according to any fmt string if applicable.
        """
        return self._format_value()
    
    
    @property
    def doc(self):
        """
        str: The docstring of the property associated with this argument.
        """
        name_fmt = "Query Argument%s;"
        name_str = " for '%s' (%s)"%(self.arg_name, self.disp_name) if self.disp_name else ' for %s'%self.arg_name
        name_str = name_fmt%name_str
        
        type_str = " value must be of type %s"%self.type
        choices_str = " from the following choices %s."%(self.choices, ) if self.choices else "."
        return name_str + type_str + choices_str

    
    @property
    def error_message(self):
        """
        str: The error message for the argument if one exists.
        """
        name = "'%s' (%s)"%(self.arg_name, self.disp_name) if self.disp_name else "'%s'"%self.arg_name
        
        if not self._has_value_if_required:
            return "%s : Missing value for required argument"%name
        if not self._valid_type:
            return "%s : Expected %s; got %s"%(name, self.type, type(self.value))
        if not self._valid_choice:
            return "%s : Expected an element from %s; got %s"%(name, self.choices, self.value)
        
        return None
    
    def missing_requirements(self, other_arg_names):
        """
        Get the missing requirements given the rest of the arg names.
        
        Parameters
        ----------
        other_arg_names: Iterable[str]
            The names of the other arguments (`arg_name` not `disp_name`)
        
        Returns
        -------
        Iterable[str]
            Any missing requirements if applicable.
        """
        if self.requires:
            if isinstance(self.requires, str):
                return self.requires if self.requires not in other_arg_names else None
            return [req for req in self.requires if req not in other_arg_names]
        return None
    
    
    def __setattr__(self, name, value):
        """
        Override to make sure  we use the check_value method to check the value.
        """
        if name == 'value':
            self._check_value(value)
        super(QueryArgument, self).__setattr__(name, value)
    
    def _check_value(self, val):
        """
        Check the value of the argument.
        
        Parameters
        ----------
        val: Any
            The value, should match the specified type, and choices if applicable.
        Raises
        ------
        NotImplmentedError: If trying to mutate an immutable argument value.
        ValueError: If val isn't a valid choice.
        TypeError: If val is of the wrong type.
        """
        if val is None:
            return
        
        if not self.mutable:
            raise NotImplementedError("Tried to mutate an immutable argument value.")
        if self.type != Any:
            if not isinstance(val, self.type):
                raise TypeError('Expected the value to be of type %s; got %s'%(self.type, type(val)))
        if self.choices:
            if isinstance(self.choices, str) and val != self.choices:
                raise ValueError('Expected the value to be %s; got %s'%(self.choices, val))
            if val not in self.choices:
                raise ValueError('Expected the value to be from %s; got %s'%(self.choices, val))
    
    @property
    def _has_value_if_required(self):
        """
        bool: True only if there is a value besied None if the argument is required.
        """
        return self.value is not None if self.required else True
    
    @property
    def _valid_type(self):
        """
        bool: True if the existing value matches the expected type.
        """
        if self.type == Any:
            return True
        return isinstance(self.value, self.type) or self.is_empty
    
    @property
    def _valid_choice(self):
        """
        bool: True if the existing value is one of the expected choices.
        """
        if self.choices:
            if isinstance(self.choices, str):
                self.choices = (self.choices, ) or self.is_empty
            return self.value in self.choices or self.is_empty
        return True
    
    def _format_value(self):
        """
        Returns
        -------
        str
            The value formatted to it's fmt string if applicable.
        
        Raises
        ------
        ValueError: If the value couldn't be formattted according to the fmt string.
        """
        if not self.fmt:
            return str(self.value)
        try:
            formatted = self.fmt%self.value
        except TypeError:
            formatted = self.fmt.format(self.value)

        if formatted != self.fmt:
            return formatted
        else:
            command1 = '`self.fmt%%self.value` -> %s%%%s'%(self.fmt, self.value)
            command2 = '`self.fmt.format(self.value)` -> %s.format(%s)'%(self.fmt, self.value)
            raise ValueError("String formatting error for both commands.\n"\
                             "    %s\n    %s"%(command1, command2))
        return formatted
    
def register_runtime_property(inst, name, prop):
    """
    Adds a property to an instance at run-time by creating a new class for the instance,
    and adding the property to that new class.
    
    Parameters
    ----------
    inst: Object
        The intstance to add our property to.
    name: str
        The name of the property.
    prop: property
        The property to be added.
    """
    class_name = inst.__class__.__name__ + 'Child'
    child_class = type(class_name, (inst.__class__,), {name : prop})
    inst.__class__ = child_class
            
 
class Query(object):
    """
    An object for interacting with a web query.
    
    Attributes
    ----------
    base_url : str
        The base url of the query
    params: str
        The parameters encoding into a url query
    url: str
        The encoded request url
        
    Methods
    -------
    make_property(name, docstring=None, mutable=True)
        Get the associated property
    register_args(**kwargs)
        Register the query arguments to the object via properties. The keys
        of the kwargs will determine the name associated with the properties
        on the query object.
    arg_value(name)
        Get the value of a given argument by name.
    """
    def __init__(self, base_url : str, **kwargs : QueryArgument):
        """
        Parameters
        ----------
        base_url: str
            The base url for the query.
        kwargs:
            Any query arguments for the query. These will be associated on
            the query object by the kwarg name.
        """
        self._args = OrderedDict()
        
        self.base_url = base_url
        self.register_args(**kwargs)
    
    @classmethod
    def make_property(cls, name, docstring=None, mutable=True):
        """
        Parameters
        ----------
        name: str
            The name of the property
        docstring: str, optional
            The docstring to be associated with the property. Defaults to None
        mutable: bool, optional
            Whether or not the value should be mutable. Defaults to True
        
        Returns
        -------
        property
        """
        def getter(self):
            return self.arg_value(name)
    
        def setter(self, val):
            self._args[name].value = val
        
        def deletter(self):
            del self._args[name]
        
        if not mutable:
            setter = None
            deletter = None
        
        return property(getter, setter, deletter, doc=docstring)
    
    def register_args(self, **kwargs : QueryArgument):
        """
        Register the properties of any query arguments.
        
        Parameters
        ----------
        kwargs:
            Any query arguments for the query. These will be associated on
            the query object by the kwarg name.
        """
        for name, arg in kwargs.items():
            self._args[name] = arg
            mutable = getattr(arg, 'mutable', True)
            arg_prop = Query.make_property(name, arg.doc, mutable)
            register_runtime_property(self, name, arg_prop)
    
    def arg_value(self, name : str):
        """
        Get the value of an argument by name.
        
        Returns
        -------
        Any
        
        Raises
        ------
        ValueError: If the name does not match a valid arg.
        """
        try:
            return self._args[name].value
        except KeyError:
            raise ValueError("No arg named '%s' defined on the query"%name)
    
    def check_parameters(self):
        """
        Runs any checks before parameters are encoded and accessed.
        """
        self._check_valid()
        self._check_requirements()
    
    @property
    def params(self):
        """
        str: The parameters encoding into a url query string.
        """
        self.check_parameters()
        params = self._merged_params()
        return urlencode(params)
    
    @property
    def url(self):
        """
        str: The full request url.
        """
        return self.base_url + ('&' if urlparse(self.base_url).query else '?') + self.params
    
    
    def __repr__(self):
        try:
            return "Query for: " + self.url
        except:
            return "Unset query object."
    
    def _invalid_values(self):
        """
        Get any error messages from invalid values.
        
        Returns
        -------
        list[str]
        """
        return [arg.error_message for arg in self._args.values() if not arg.value_valid]
    
    def _missing_requirements(self):
        """
        Get any missing reuqired arguments.
        
        Returns
        -------
        dict
        """
        arg_names = [arg.arg_name for arg in self._args.values()]
        missing = {arg.arg_name : arg.missing_requirements(arg_names) for arg in self._args.values() if arg.missing_requirements(arg_names)}
        return missing
    
    def _check_valid(self):
        """
        Check if all of the arguments are valid.
        
        Returns
        -------
        bool
            True if all arguments are valid.
        
        Raises
        ------
        QueryValueError: If any values are invalid.
        """
        invalid = self._invalid_values()
        if invalid:
            raise QueryValueError("Invalvid Query Values.", invalid)
        return True
    
    def _check_requirements(self):
        """
        Check if all of the required argments are defined.
        
        Returns
        -------
        bool
            True if all requirements are met
        
        Raises
        ------
        QueryRequirementError: If any requirements aren't met.
        """
        missing = self._missing_requirements()
        if missing:
            raise QueryRequirementError("Missing required querty arguements.", missing)
        return True
    
    def _merged_params(self):
        """
        This will merge any parameters by a '+' that share a same arg_name.
        
        Returns
        -------
        dict
        """
        merged = defaultdict(list)
        for arg in self._args.values():
            if not arg.is_empty:
                merged[arg.arg_name].append(arg.encoded)
        return {arg_name : '+'.join(vals) for arg_name, vals in merged.items()}
