```bash
    ,---,                                 ,-.                       
  .'  .' `\                           ,--/ /|                       
,---.'     \     ,---.              ,--. :/ |               __  ,-. 
|   |  .`\  |   '   ,'\             :  : ' /              ,' ,'/ /| 
:   : |  '  |  /   /   |    ,---.   |  '  /       ,---.   '  | |' | 
|   ' '  ;  : .   ; ,. :   /     \  '  |  :      /     \  |  |   ,' 
'   | ;  .  | '   | |: :  /    / '  |  |   \    /    /  | '  :  /   
|   | :  |  ' '   | .; : .    ' /   '  : |. \  .    ' / | |  | '    
'   : | /  ;  |   :    | '   ; :__  |  | ' \ \ '   ;   /| ;  : |    
|   | '` ,/    \   \  /  '   | '.'| '  : |--'  '   |  / | |  , ;    
;   :  .'       `----'   |   :    : ;  |,'     |   :    |  ---'     
|   ,.'                   \   \  /  '--'        \   \  /            
'---'                      `----'                `----'                                                                         

         _____         _                                 
        |  __ \       | |                                
        | |  \/  __ _ | |_   ___ __      __  __ _  _   _ 
        | | __  / _` || __| / _ \\ \ /\ / / / _` || | | |
        | |_\ \| (_| || |_ |  __/ \ V  V / | (_| || |_| |
micrOS   \____/ \__,_| \__| \___|  \_/\_/   \__,_| \__, |
	                                            __/ |
    	                                           |___/ 
```

## Create docker `micros-gateway` image

```
docker build --no-cache -t micros-gateway:1.0 .
```

## Start `micros-gateway` container

```
docker run --name micros-gateway -p 5000:5000 -e GATEWAYIP="10.0.1.1" -d micros-gateway:1.0
```

### List docker image
    docker images

### Get container IP
    docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' micros-gateway

### List all containers
    docker ps -a

### Start/Stop docker container
    docker stop <container_id>
    docker start <container_id>

### Interactive "log-in" to container (container id)
    docker exec -it micros-gateway /bin/bash

### Remove docker image
    docker image rm <image_id>

### List docker network info
    docker network ls
    docker network inspect bridge

```
______                                _    _                       
| ___ \                              | |  | |                      
| |_/ / _ __   ___   _ __ ___    ___ | |_ | |__    ___  _   _  ___ 
|  __/ | '__| / _ \ | '_ ` _ \  / _ \| __|| '_ \  / _ \| | | |/ __|
| |    | |   | (_) || | | | | ||  __/| |_ | | | ||  __/| |_| |\__ \
\_|    |_|    \___/ |_| |_| |_| \___| \__||_| |_| \___| \__,_||___/
```
                                                            
# Prometheus:

### Gateway in a container:

```
docker run --name prometheus -d -p 9090:9090 -v ./prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
```

### Gateway on localhost (hybrid setup):

```
docker run --name prometheus -d -p 9090:9090 -p 5000:5000 -v ./prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
```

```
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' prometheus
```

Graphana

```
docker run -d --name grafana -p 3000:3000   -e "GF_SERVER_ROOT_URL=http://localhost:3000"   --network micros_micros_nw --link prometheus:prometheus grafana/grafana
```


```                                                                                
  ,----..                        ____                                                 
 /   /   \                     ,'  , `. ,-.----.                                      
|   :     :    ,---.        ,-+-,.' _ | \    /  \     ,---.                           
.   |  ;. /   '   ,'\    ,-+-. ;   , || |   :    |   '   ,'\    .--.--.               
.   ; /--`   /   /   |  ,--.'|'   |  || |   | .\ :  /   /   |  /  /    '      ,---.   
;   | ;     .   ; ,. : |   |  ,', |  |, .   : |: | .   ; ,. : |  :  /`./     /     \  
|   : |     '   | |: : |   | /  | |--'  |   |  \ : '   | |: : |  :  ;_      /    /  | 
.   | '___  '   | .; : |   : |  | ,     |   : .  | '   | .; :  \  \    `.  .    ' / | 
'   ; : .'| |   :    | |   : |  |/      :     |`-' |   :    |   `----.   \ '   ;   /| 
'   | '/  :  \   \  /  |   | |`-'       :   : :     \   \  /   /  /`--'  / '   |  / | 
|   :    /    `----'   |   ;/           |   | :      `----'   '--'.     /  |   :    | 
 \   \ .'              '---'            `---'.|                 `--'---'    \   \  /  
  `---`                                   `---`                              `----'   
```
                                                                                      

# Docker compose

### In the background

```bash
docker-compose -p micros up -d

docker-compose up --force-recreate -p micros -d
```

```bash
docker-compose -p micros up
```

```
docker-compose restart prometheus
```

```
 _   _ ______  _          
| | | || ___ \| |         
| | | || |_/ /| |     ___ 
| | | ||    / | |    / __|
| |_| || |\ \ | |____\__ \
 \___/ \_| \_|\_____/|___/ hints
```
                          
# Docker external service access:
Prometheus: http://10.0.1.61:9090
micrOS gateway for Prometheus: http://10.0.1.61:5000/metrics/TinyDevBoard/esp32+temp
