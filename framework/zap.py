from zapv2 import ZAPv2


class ZAP_API(object):

    def __init__(self, core):
            self.Core = core
            zap_proxy_address = "http://" + self.Core.Config.FrameworkConfigGet("ZAP_PROXY_ADDR") + ":" + self.Core.Config.FrameworkConfigGet("ZAP_PROXY_PORT")
            self.zap = ZAPv2(proxies={'http': zap_proxy_address, 'https': zap_proxy_address}) #the values are hard-coded just for the test purpose, will be taken from config later

    def ForwardRequest(self, target_id, transaction_id):
        request = self.Core.DB.Transaction.GetByIDAsDict(int(transaction_id), target_id=int(target_id))['raw_request']
        self.zap.core.send_request(request)

