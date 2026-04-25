from core.file import FileCrypto
from core.config import cfg
import json
class KeyStore:
    key_file= "data/key.lic"
    def __init__(self):
        self.store = FileCrypto(cfg.get("safe.lic_key","store.csol.store.werss"))
    def save(self,text):
        items=[]
        if type(text) != str:
            for  item in text:
                if item["domain"] ==".qq.com" :
                    continue
                items.append(item)
        text=json.dumps(items)
        self.store.encrypt_to_file(self.key_file, text.encode("utf-8"))
    def load(self):
        try:
            text=self.store.decrypt_from_file(self.key_file).decode("utf-8")
            items= json.loads(text)
            new_items=[]
            for  item in items:
                if "domain" in item:
                    del item["domain"]
                if item['name'] =="_clck":
                    continue
                if item['name'] =="token":
                    continue
                new_items.append(item)
            return new_items
        except:
            return ""
        
Store=KeyStore()