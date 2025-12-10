from models.enums import Sex, DietPurpose, ActivityLevel

class UserInfo:
    """
    Args:
        height(float): cm
        weight(float): kg
        age(int): 세는 나이
        sex(Sex Enum): 남자는 0, 여자는 1
        bmi(float): kg / m^2
        purpose(DietPurpose Enum): 일반 0 | 다이어트 1 | 벌크업 2
        preference(list[FoodCategory Enum]): [1순위, 2순위, 3순위]
        activity_factor(ActivityLevel Enum): (활동 지수(float), label(str))
        
        calories_required(float): kcal
        carbon_required(float): g
        protein_required(float): g
        fat_required(float): g
        
    """
    def __init__(self, height=0.0, weight=0.0, age=0, sex=None, purpose=None, preference=None, activity_factor=None):
        self.height = height
        self.weight = weight
        self.age = age
        self.sex = Sex(sex) if isinstance(sex, int) else sex
        self.bmi = 0.0
        self.purpose = DietPurpose(purpose) if isinstance(purpose, int) else purpose
        self.preference = preference or []

        self.activity_factor = ActivityLevel(activity_factor) if isinstance(activity_factor, int) else activity_factor
        
        self.calories_required = 0.0
        self.carbon_required = 0.0
        self.protein_required = 0.0
        self.fat_required = 0.0
        
    def calculate_bmi(self):
        if self.height <= 0:
            raise ValueError("키는 양수가 되어야 합니다.")
        self.bmi = self.weight / (self.height / 100)**2
        
    