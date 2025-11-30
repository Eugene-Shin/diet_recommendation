from models.user_info import UserInfo
from models.enums import DietPurpose, Sex

class NutritionRequirementService:
    def calculate_requirements(self, user: UserInfo)-> None:
        # 기초대사량 계산
        if user.sex == Sex.MALE:
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
        else:
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age - 161
        
        # 활동대사량 계산  
        tdee = bmr * user.activity_factor.factor
        
        if user.purpose == DietPurpose.NORMAL:
            user.calories_required = tdee - 400
            user.protein_required = 1.6 * user.weight
        elif user.purpose == DietPurpose.DIET:
            user.calories_required = tdee
            user.protein_required = 1.9 * user.weight
        else:   #BULK
            user.calories_required = tdee + 400
            user.protein_required = 1.8 * user.weight
            
        user.fat_required = (user.calories_required * 0.25) / 9
        user.carbon_required = (user.calories_required - (user.protein_required * 4 + user.fat_required * 9)) / 4