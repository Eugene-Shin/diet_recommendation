from enum import Enum

class Sex(Enum):
    MALE = 0
    FEMALE = 1
    
class DietPurpose(Enum):
    NORMAL = 0
    DIET = 1
    BULK = 2
    
class FoodCategory(Enum):
    RICE = (1, "밥")
    BREAD = (2, "빵")
    NOODLES_AND_DUMPLINGS = (3, "면 및 만두")
    PORRIDGE_AND_SOUP = (4, "죽 및 스프")
    SOUP = (5, "국 및 탕")
    STEW = (6, "찌개 및 전골")
    STEAMED = (7, "찜")
    GRILLED = (8, "구이")
    PANCAKE = (9, "전 및 부침")
    STIR_FRY = (10, "볶음")
    BRAISED = (11, "조림")
    FRIED = (12, "튀김")
    NAMUL = (13, "나물 및 숙채")
    SEASONED = (14, "생채 및 무침")
    KIMCHI = (15, "김치")
    SALTED_FISH = (16, "젓갈")
    PICKLED = (17, "장아찌 및 절임")
    SAUCE = (18, "장 및 양념류")
    GRAINS = (24, "곡류 및 서류")
    BEANS_AND_NUTS = (25, "두류·견과·종실류")
    VEGETABLES_AND_SEAWEED = (26, "채소 및 해조류")
    FISH_MEAT = (27, "수조어육류")

    @property
    def code(self):
        return self.value[0]

    @property
    def label(self):
        return self.value[1]
    
class ActivityLevel(Enum):
    VERY_LOW = (1, 1.2, "매우 낮음(거의 운동 X)")
    LIGHT = (2, 1.375, "가벼운 활동(주 1~3회)")
    MODERATE = (3, 1.55, "보통 활동(주 4~5회)")
    HIGH = (4, 1.725, "높은 활동(주 6~7회)")
    VERY_HIGH = (5, 1.9, "매우 높음(육체 노동·선수)")
    
    def __init__(self, code: int, factor: float, label: str):
        self._code = code
        self._factor = factor
        self._label = label
        
    @property
    def code(self):
        return self._code
    
    @property
    def factor(self)-> float:
        return self._factor
    
    @property
    def label(self)-> str:
        return self._label
    
