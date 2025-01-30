class CityBuilding:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = [f"{key}: {value}" for key, value in self.__dict__.items()]
        return "\n".join(attributes)


class household:
    def __init__(self, residents, h_area, KW_LSTM, KW_Stats):
        self.residents = residents
        self.h_area = h_area
        self.KW_LSTM = KW_LSTM
        self.KW_Stats = KW_Stats