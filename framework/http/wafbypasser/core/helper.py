import os


def load_payload_file(payload_path, valid_size=100000, exclude_chars=[]):
    """This Function loads a list with payloads"""
    payloads = []
    try:
        with open(os.path.expanduser(payload_path), 'r') as f:
            for line in f.readlines():
                line = line.strip('\n')
                if len(line) > valid_size:
                    continue
                excluded_found = [c in line for c in exclude_chars]
                if True in excluded_found:
                    continue
                payloads.append(line)
    except Exception as e:
        Error(str(e))
    print 'Payload: %s loaded' % payload_path
    print '\t%s payload(s) found.' % str(len(payloads))
    return payloads


def Error(owtf, message):
    print "Error: " + message
    owtf.Error.FrameworkAbort(message)
