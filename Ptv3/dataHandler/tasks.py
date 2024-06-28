# tasks/tasks.py  
  
from django_rq import job  
import time  
import json
import numpy as np
import threading
import open3d as o3d
from dataHandler.models import MedicalCase 
import os 
import torch
  
@job  
def long_running_task(seconds):  
    time.sleep(seconds)  
    # print('完成！')
    return f"Task completed after {seconds} seconds"  


@job
def save_tooth_model(json_data):
    print('start save')
    time.sleep(10)
    print('done')
     
    print(json_data.keys())
    print(json_data['upperPoints'].keys())
    print(json_data['upperPolys'].keys())
    id = json_data['id']
    print('id:', id)

    upperPointsData = np.array(json_data['upperPoints']['values'])
    upperPolysData = np.array(json_data['upperPolys']['values'])
    lowerPointsData = np.array(json_data['lowerPoints']['values'])
    lowerPolysData = np.array(json_data['lowerPolys']['values'])

    # 开启两个子线程分别保存上下牙
    threadUpper = threading.Thread(target=convertToPolyData(upperPointsData, upperPolysData, id, 'upper'))
    threadLower = threading.Thread(target=convertToPolyData(lowerPointsData, lowerPolysData, id, 'lower'))

    threadUpper.start()
    threadLower.start()

    threadUpper.join()
    threadLower.join()
    print('here')
    # 分割
    start_segment(id)
    return f"model saved" 

# 分割
def start_segment(id):
    
    current_dir = os.getcwd()
    print("当前工作目录：", current_dir)
    # 切换到指定目录
    new_dir = "../../Src/Pointcept/"
    os.chdir(new_dir)
    print("切换后的工作目录：", os.getcwd())
    
    patient = MedicalCase.objects.get(patient_id=id) 
    model_path = patient.model_path
    label_path = patient.label_path
    inputPath = model_path.split('Pointcept/')[1]
    outputPath = label_path.split('Pointcept/')[1]
    if not os.path.exists(outputPath):  # 检查目录是否存在  
        os.makedirs(outputPath)  # 如果目录不存在，则创建它 
    cmd = f"sh scripts/infer.sh -p python -g 1 -d tgnet -n semseg-pt-v3m1-0-tgnet-fps-good -w model_best -i 'data/request_modeldata/{id}/' -o 'data/request_result/' -k true"
    print(cmd)
    print('开始分割',id)
    # os.system('python ./inference_final.py --input_path ../../learn-django/myDjangoApp/data/segObj/00OMSZGW/ --save_path ../../learn-django/myDjangoApp/data/resultData/00OMSZGW/')
    os.system(cmd)

    os.chdir(current_dir)
    # 更新状态
    patient.status = True
    patient.save()
    print('分割结束')
    

# 保存模型数据
def convertToPolyData(pointsData, polysData, id, jaw):
        
    print(jaw,'start convert')
    points = pointsData.reshape(-1,3)
    triangles = polysData.reshape(-1,4)
    triangles = triangles[:,1:4]
    
    # 翻转模型
    if jaw == 'upper':
        points[:,0] = -points[:,0]
        points[:,2] = -points[:,2]
        
          
    # 创建Open3D的网格对象  
    mesh = o3d.geometry.TriangleMesh()  
    mesh.vertices = o3d.utility.Vector3dVector(points)  
    mesh.triangles = o3d.utility.Vector3iVector(triangles)  
    
    
    # 去除重复点  
    # mesh.remove_duplicated_vertices() 

    vertices = np.asarray(mesh.vertices)
    
    # 中心偏移和resize
    center = np.mean(vertices, axis=0)
    coord = vertices - center
    print('  ',coord.min(0))
    print('  ',coord.max(0))
    if jaw == 'upper':
        coord[:,2] += 2
        # 设置旋转角度  
        theta = - np.pi / 6  # 例如，这里设置为 45 度  
        
        # 创建绕 x 轴的旋转矩阵  
        rotation_matrix = np.array([  
            [1, 0, 0],  
            [0, np.cos(theta), -np.sin(theta)],  
            [0, np.sin(theta), np.cos(theta)]  
        ])  
        # 进行矩阵乘法来实现旋转  
        coord = np.dot(rotation_matrix, coord.T).T
    coord /= (coord.max(0)[0] - coord.min(0)[0])/2
    
    print('  ',coord.min(0))
    print('  ',coord.max(0))
    
    mesh.compute_vertex_normals()
    normal = np.asarray(mesh.vertex_normals)


    pthData = {}
    pthData['coord'] = coord
    pthData['normal'] = normal
    pthData['id'] = id
    pthData['jaw'] = jaw
  
    patient = MedicalCase.objects.get(patient_id=id)
    # print('wooo') 
    model_path = patient.model_path
    if not os.path.exists(model_path):  # 检查目录是否存在  
        os.makedirs(model_path)  # 如果目录不存在，则创建它 
    torch.save(pthData, model_path+id+'_'+jaw+'.pth')
    print(jaw,'saved!')
