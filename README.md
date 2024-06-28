## conda 环境
**选择ptv3**

## run service
```sh
# 开启redis
redis-server 
redis-cli
```


```sh
# 开启django
python3 manage.py runserver 0.0.0.0:8000
```


```sh
# 开启rq任务队列
python manage.py rqworker  
```
## 如何配置端口映射
1. 在k8s上配置一个services，用于映射该pod的端口

2. 这里将pod的8000端口即django默认端口映射到30838

3. 在django的setting里配置ALLOWED_HOSTS,加入该pod上游服务器172.16.200.96

4. 在内网下访问http://172.16.200.96:30838/来访问django服务