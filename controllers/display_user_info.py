from models.user_info import UserInfo

def display_user_info(user: UserInfo)-> None:
    print("============== 사용자 정보 ==============")
    print(f'신장 : {user.height}cm')
    print(f'체중 : {user.weight}kg')
    print(f'나이 : {user.age}세')
    print(f'성별 : {user.sex.name}')
    print(f'BMI : {user.bmi:.2f}kg/m^2')
    print(f'목적 : {user.purpose.name}')
    print('선호하는 음식 :', ", ".join(p.label for p in user.preference))
    print(f'사용자의 일일 활동량 : {user.activity_factor.label}')