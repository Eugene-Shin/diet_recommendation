from models.user_info import UserInfo

def display_daily_requirements(user: UserInfo)-> None:
    print("=========== 사용자의 일일 영양 섭취 권장량 ===========")
    print(f'칼로리 : {user.calories_required:.2f}kcal')
    print(f'탄수화물 : {user.carbon_required:.2f}g')
    print(f'단백질 : {user.protein_required:.2f}g')
    print(f'지방 : {user.fat_required:.2f}g')
    