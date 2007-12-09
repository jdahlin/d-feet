def convert_complex_type(subsig):
    result = None

    c = subsig[0]

    #if c == 'a':
    #    result = ['Array of ', sig_to_type_list(subsig[1:])]

    return result

def convert_simple_type(c):
    result = None

    if c == 'i':
        result = 'Int32'
    elif c == 'u':
        result = 'UInt32'
    elif c == 's':
        result = 'String'
    elif c == 'b':
        result = 'Byte'
    elif c == 'o':
        result = 'Object Path'
    elif c == 'd':
        result = 'Double'
    elif c == 'v':
        result = 'Variant'

    return result

def sig_to_type_list(sig):
    i = 0
    result = []
    for c in sig:
        type = convert_simple_type(c)
        if not type:
            type = convert_complex_type(sig[i:])
            if not type:
                type = 'Error(' + c + ')'

        result.append(type)
        i+=1
        
    return result

def type_list_to_string(type_list):
    result = ''

    result = ', '.join(type_list)

    return result

def sig_to_markup(sig, span_attr_str):
    list = sig_to_type_list(sig)
    markedup_list = []
    for dbus_type in list:
        m = '<span ' + span_attr_str + '>'
        m += dbus_type + '</span>'
        markedup_list.append(m)

    return type_list_to_string(markedup_list)

def sig_to_string(sig):
    return type_list_to_string(sig_to_type_list(sig))
