from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.http import JsonResponse 
import json
import numpy as np 
import threading 
import os
# from .tasks.tasks import long_running_task 
# from dataHandler.tasks import long_running_task
from .tasks import long_running_task
from .tasks import save_tooth_model
from django_rq import get_queue

from dataHandler.models import MedicalCase
from django.views.decorators.csrf import csrf_exempt

def hello(request):
    return HttpResponse("Hello world ! ")

def start_long_task(request):  
    job = long_running_task.delay(10)  # 异步执行任务 
    result = job.get(timeout=None)
    return JsonResponse({'job_id': job.id,'result':result}) 


def check_task_status(request):  
    queue = get_queue('default')  
    queued_jobs = queue.jobs  # 获取队列中的所有任务 
    # job = queued_jobs[-1]
    # job = queue.fetch_job(job_id) 
    whole_response_data = [] 
    print(queued_jobs)
    for job in queued_jobs:
        if job is not None:  
            response_data = {  
                'id': job.id,
                'status': job.get_status(),  
                'result': job.result,  
            }  
        else:  
            response_data = {'error': 'Job not found'} 
        whole_response_data.append(response_data)
        print('response_data')
    return JsonResponse(json.dumps(whole_response_data),safe=False) 

# todo 查询数据库，若未分割则分割，若已分割则返回
# 接收分割请求，先保存模型
@csrf_exempt
def segmentBothTooth(request):  
    if request.method == 'POST':
          
        json_data = json.loads(request.body) 
        patient_id_to_check = json_data['id']# 要检查的病人ID
        
        # instance_to_delete = MedicalCase.objects.get(patient_id=patient_id_to_check)  # 假设这里是根据 ID 获取实例  
        # # 调用delete方法来删除这个实例  
        # instance_to_delete.delete() 
        
        # 检查病人ID是否存在  
        if MedicalCase.objects.filter(patient_id=patient_id_to_check).exists():  
            print("病人ID存在",patient_id_to_check) 
            patient = MedicalCase.objects.get(patient_id=patient_id_to_check)  
            if patient.status:  
                print("病人ID存在且状态为True") 
                upperLabelData, lowerLabelData = return_tooth_label(patient.patient_id)
                return JsonResponse({'message': 'both tooth saved successfully', 'upper': upperLabelData, 'lower': lowerLabelData}) 
            else:  
                print("病人ID存在但状态为False") 
                return JsonResponse({'message': 'model data is waiting for saving and seging', 'id': patient_id_to_check})
        else:    
            print("病人ID不存在",patient_id_to_check) 
            patient_id = patient_id_to_check
            model_path = '../../Src/Pointcept/data/request_modeldata/' + patient_id + '/test/' 
            label_path = '../../Src/Pointcept/data/request_result/result_infer_knn/'
            new_patient = MedicalCase(patient_id=patient_id, status=False, model_path=model_path, label_path=label_path) 
            new_patient.save()
            job = save_tooth_model.delay(json_data=json_data) 
        return JsonResponse({'message': 'model data starts saving and seging', 'id': patient_id_to_check})  
    else:  
        return JsonResponse({'error': 'Invalid request method'}, status=405)  
    
# 返回标签
def return_tooth_label(patient_id):
    patient = MedicalCase.objects.get(patient_id=patient_id) 
    label_path = patient.label_path
    openPath = label_path + patient_id
    with open(openPath+'_upper.json', 'r') as file:  
        upperLabelData = json.load(file)  
    with open(openPath+'_lower.json', 'r') as file:  
        lowerLabelData = json.load(file)  
    return upperLabelData, lowerLabelData



# 保存收到的labeljson到本地 by id
@csrf_exempt
def saveLabelById(request):
    if request.method == 'POST':  
        json_data = json.loads(request.body)  # 从请求中获取 JSON 数据  
        # 在这里可以将 JSON 数据保存在本地文件中，或者进行其他处理  
        id = json_data['id'] 
        type = json_data['type']
        label = json_data['label']
        
        json_data_new = {}
        json_data_new['id_patient'] = id
        json_data_new['jaw'] = type
        json_data_new['labels'] = label['labels']
        savePath = '../../Src/Pointcept/data/request_result/result_infer_knn/'
        fileName = id+'_'+type+'.json'
        if not os.path.exists(savePath):  # 检查目录是否存在 
            try: 
                os.makedirs(savePath)  # 如果目录不存在，则创建它 
            except OSError:
                print('文件已存在')
        with open(savePath + fileName, 'w') as f:  
            json.dump(json_data_new, f)  
        print('labelData saved!')
        return JsonResponse({'message': 'JSON data saved successfully'})  
    else:  
        return JsonResponse({'error': 'Invalid request method'}, status=405)  
