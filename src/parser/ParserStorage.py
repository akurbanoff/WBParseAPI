class ParserStorage():
    def __init__(self):
        self.good_id_list = list()
        self.price = str()
        self.good_name = str()

    def getList(self) -> list:
        return self.good_id_list

    def addNewId(self, Id: str):
        self.good_id_list.append(Id)

    def delIdFromList(self, id: int):
        good_index = self.good_id_list.index(id)
        self.good_id_list.pop(good_index)

    def clearList(self):
        self.good_id_list = list()

    def getPrice(self) -> int:
        return self.price

    def getGoodName(self) -> str:
        return self.good_name

    def setPrice(self, newPrice: str):
        self.price = newPrice

    def setGoodName(self, newName):
        self.good_name = newName