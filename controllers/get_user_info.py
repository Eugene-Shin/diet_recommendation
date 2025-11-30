from models.user_info import UserInfo
from models.enums import FoodCategory, ActivityLevel

def get_activity_factor()-> float:
    print("\n활동량을 입력하세요.")
    
    activity_levels = sorted(ActivityLevel, key=lambda c: c.factor)
    
    for level in activity_levels:
        print(f"{level.code}) {level.label}")
        
    while True:
        try:
            choice = int(input("나의 활동량 : "))
            
            match = next((l for l in activity_levels if l.code == choice), None)
            
            if match:
                break
            else:
                print("잘못된 번호입니다.")
        except ValueError:
            print("숫자를 입력하세요.")
            
    return match

def get_preference()-> list:
    print("\n선호하는 음식 카테고리 번호를 입력하세요. (1, 2, 3순위)")

    categories = sorted(FoodCategory, key=lambda c: c.value[0])
    
    for c in categories:
        print(f"{c.code}) {c.label}")
        
    preference = []
    picked = set()
    
    for rank in [1, 2, 3]:
        while True:
            try:
                choice = int(input(f"{rank}순위 : "))
                
                match = next((c for c in categories if c.value[0] == choice), None)

                if match and match not in picked:
                    preference.append(match)
                    picked.add(match)
                    break
                else:
                    print("잘못된 번호이거나 이미 선택한 항목입니다.")
            except ValueError:
                print("숫자를 입력하세요.")
                
    return preference

def get_user_info()-> UserInfo:
    print("사용자 정보를 입력하세요.")
    
    def ask_float(prompt, lo, hi):
        while True:
            try:
                v = float(input(prompt))
                
                if lo < v < hi:
                    return v
            except ValueError as e:
                print(f'입력오류: {e}')
                continue
            print("잘못된 입력값입니다.")
    
    def ask_int(prompt, lo, hi):
        while True:
            try:
                v = int(input(prompt))
                
                if lo < v < hi:
                    return v
            except ValueError as e:
                print(f'입력오류: {e}')
                continue
            print("잘못된 입력값입니다.")
            
    height = ask_float("신장(cm) : ", 0.0, 300.0)
    weight = ask_float("체중(kg) : ", 0.0, 1000.0)
    age = ask_int("나이(세) : ", 0, 150)
    
    while True:
        sex = int(input("성별(남성 0 | 여성 1) : "))
        
        if sex in (0, 1):
            break;
        else:
            print("잘못된 입력값입니다.")
    
    while True:
        purpose = int(input("목적(일반 0 | 다이어트 1 | 벌크업 2) : "))
        
        if purpose in (0, 1, 2):
            break;
        else:
            print("잘못된 입력값입니다.")
        
    activity_factor = get_activity_factor()
    
    preference = get_preference()
    
    user = UserInfo(height=height, weight=weight, age=age, sex=sex, purpose=purpose, preference=preference, activity_factor=activity_factor)
             
    user.calculate_bmi()
    
    print("사용자 정보 입력 완료!")
    
    return user
