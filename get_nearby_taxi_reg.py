from geopy.distance import geodesic
from enum import IntFlag
import os
import sys
import json
import math


# Define stand types using IntFlag
class TaxiStandType(IntFlag):
    URBAN = 1
    CROSS_HARBOUR = 2
    NT = 4
    LANTAU = 8


# 定义距离计算
def haversine_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers



# Elastic正则化
def calculate_f_score(distance, order_count, alpha=5, beta=0.5, lambda_l1=0.1, lambda_l2=0.1):
    """Calculate the f_score using adjusted parameters for distance and order_count"""
    
    # L1 正则化项（绝对值）
    l1_regularization = lambda_l1 * (abs(distance) + abs(order_count))
    
    # L2 正则化项（平方）
    l2_regularization = lambda_l2 *  (distance**2+order_count) 
    # f_score 计算，调整 alpha 和 beta，减弱正则化项
    f_score = (alpha / distance) + (beta * order_count) - l2_regularization
    
    return f_score


# 获取附近的士站并计算 f_score
def get_nearby_taxi_stands(user_lat, user_lng, user_hour, stand_type, stand_data, lambda_l1=0.1, lambda_l2=0.5):
    candidates = []
    
    for stand in stand_data:
        if (stand_type & TaxiStandType.URBAN and stand['isUrban']) or \
           (stand_type & TaxiStandType.CROSS_HARBOUR and stand['isCrossHarbour']) or \
           (stand_type & TaxiStandType.NT and stand['isNTTaxi']) or \
           (stand_type & TaxiStandType.LANTAU and stand['isLantauTaxi']):
           
            # 计算距离
            distance = haversine_distance(user_lat, user_lng, stand['location']['latitude'], stand['location']['longitude'])
            order_count = stand['order_count'][str(user_hour).zfill(2)]

            # 计算 f_score，结合 L1 和 L2 正则化
            f_score = calculate_f_score(distance, order_count, alpha=1, beta=1, lambda_l1=lambda_l1, lambda_l2=lambda_l2)
            stand['f_score'] = f_score
            stand['distance'] = distance  # 添加距离信息
            stand['order_count'] = order_count  # 添加订单量信息  
            
            candidates.append(stand)
    
    # 根据 f_score 排序，获取前5个站点
    top_5_by_fscore = sorted(candidates, key=lambda x: x['f_score'], reverse=True)[:5]
    # 根据距离排序，获取前5个站点
    top_5_by_distance = sorted(candidates, key=lambda x: x['distance'])[:5]
    # 根据订单数量排序，获取前5个站点
    top_5_by_order_count = sorted(candidates, key=lambda x: x['order_count'], reverse=True)[:5]
    
    # 分别打印按 f_score、距离、订单数量排序的结果
    print("\nTop 5 Taxi Stands by f_score:")
    for i, stand in enumerate(top_5_by_fscore):
        print(f"Rank {i + 1}: Stand ID {stand['stand_id']}, Distance: {stand['distance']:.2f} km, Order Count: {stand['order_count']}, f_score: {stand['f_score']:.2f}")

    print("\nTop 5 Taxi Stands by Distance:")
    for i, stand in enumerate(top_5_by_distance):
        print(f"Rank {i + 1}: Stand ID {stand['stand_id']}, Distance: {stand['distance']:.2f} km, Order Count: {stand['order_count']}")

    print("\nTop 5 Taxi Stands by Order Count:")
    for i, stand in enumerate(top_5_by_order_count):
        print(f"Rank {i + 1}: Stand ID {stand['stand_id']}, Distance: {stand['distance']:.2f} km, Order Count: {stand['order_count']}")
    
    # 返回按 f_score 排序的前5个站点的ID
    top_5_stand_ids = [stand['stand_id'] for stand in top_5_by_fscore]

    
    return top_5_stand_ids


def get_resource_path(relative_path):
    """ Get the absolute path to the resource, works for both development and PyInstaller environments. """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


# 从用户输入读取信息
def get_user_inputs():
    # 获取用户的经度和纬度
    user_lat = float(input("Please enter your latitude: "))
    user_lng = float(input("Please enter your longitude: "))
    
    # 获取用户的当前时间（小时）
    user_hour = int(input("Please enter the current hour (0-23): "))
    
    # 获取用户想要的站点类型
    print("Please select the taxi stand type(s):")
    print("1: Urban")
    print("2: Cross Harbour")
    print("4: New Territories")
    print("8: Lantau")
    print("For multiple types, enter numbers separated by | (e.g., 1|2 for Urban and Cross Harbour)")
    
    selected_types = input("Enter your selection: ")
    
    # 将输入的站点类型转换为 IntFlag
    stand_type = 0
    for part in selected_types.split("|"):
        stand_type |= int(part)
    
    return user_lat, user_lng, user_hour, stand_type

#------------------------------------test_case-----------------------------------------------#
def main():
    print("Welcome to the Taxi Stand Finder!")
    # 获取用户输入
    user_lat, user_lng, user_hour, stand_type = get_user_inputs()
    # Load json:
    # with open('taxi_stands_demand_ours.json', 'r') as f:
    #     stand_data = json.load(f)
    json_file = get_resource_path("taxi_stands_data.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        stand_data = json.load(f)
    
    # 以上为推荐算法的输入参数
    
    # get_top5:
    top_5_stand_ids = get_nearby_taxi_stands(user_lat, user_lng, user_hour, stand_type, stand_data)
    print(top_5_stand_ids)

    
if __name__ == "__main__":
    main()