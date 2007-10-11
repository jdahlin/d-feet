
# TODO: Check against other Unix's
def get_proc_from_pid(pid):
    procpath = '/proc/' + str(pid) + '/cmdline'

    f = open(procpath, 'r')
    fullpath = f.readline() 

    print fullpath
    f.close()

