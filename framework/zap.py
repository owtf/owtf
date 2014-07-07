from zapv2 import ZAPv2


class ZAP_API(object):

    def __init__(self, core):
            self.Core = core
            self.zap = ZAPv2(proxies={'http': 'http://127.0.0.1:8090', 'https': 'http://127.0.0.1:8090'}) #the values are hard-coded just for the test purpose, will be taken from config later

    def ForwardRequest(self, target_id, transaction_id):
        request = self.Core.DB.Transaction.GetByIDAsDict(int(transaction_id), target_id=int(target_id))['raw_request']
        self.zap.core.send_request(request)

