def list_join(list, conjunction_str, format_func=str, oxford_comma=True):
    '''
    Joins a list in a grammatically-correct fashion.
    :param list:
        the list to join.
    :param conjunction_str: 
        the string to use as conjunction between two items.
    :param format_func:
        a function that takes in a string and returns a formatted string (default=str, optional).
    :param oxford_comma: 
        indicates whether to use oxford comma styling (default=True, optional).
    :returns:
        a string representing the grammatically-correct joined list.
    :usage::
        >>> list_join(['apple', 'orange', 'pear'], 'and')
        apple, orange and pear'`
    '''

    if not list: return ''
    if len(list) == 1: return format_func(list[0])
    
    first_part = ', '.join([format_func(i) for i in list[:-1]])
    comma = ',' if oxford_comma and len(list) > 2 else ''

    return '{}{} {} {}'.format(first_part, comma, conjunction_str, format_func(list[-1]))

def kwargs_to_list(kwargs_dict):
    '''
    Maps a set of keyword arguments in a dictionary to
    a list of strings in the format "'key' (value='dict[key]')".
    :param kwargs_dict:
        a dictionary representing the keyword arguments to map.
    :returns:
        A list of strings in the format "'key' (value='dict[key]')".
    :usage:: 
        >>> kwargs_to_list({'name':'bob', 'id':2})
        ["'name' (value='bob')", "'id' (value='2')"]
    '''

    return ['\'{}\' (value=\'{}\')'.format(key, kwargs_dict[key]) for key in kwargs_dict if kwargs_dict[key] != None]