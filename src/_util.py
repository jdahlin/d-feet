# TODO: Check against other Unix's
def get_proc_from_pid(pid):
    procpath = '/proc/' + str(pid) + '/cmdline'
    fullpath = ''

    try:
        f = open(procpath, 'r')
        fullpath = f.readline().split('\0')
        f.close()
    except:
        pass

    return fullpath

