import json
from datetime import datetime
import uuid
import collections
from urllib.parse import urlsplit
from haralyzer import HarParser

now = datetime.now()
hour_min = now.strftime("%H_%M")


def filter_har(har_parser):
  data = har_parser.har_data
  har_entries = har_parser.har_data["entries"]

  dict_list = []
  total = 0
  count = 0
 
  for entry in har_entries:
    total = total +1
    #print(entry)
    if entry["_resourceType"]=="xhr" and entry['response']['status']==200:
      url = entry["request"]["url"]
      if (url.endswith("/getAds") or url.endswith(".json") or url.endswith("EN") or url.endswith(".jpg") or url.endswith(".json") or url.endswith("/Global/EN") or url.endswith(".jpg") or "/api/client/getIdentityProviders?tenantName=" in url or ("/design/tenant/v2/login/name/" in url) or ("/design/tenant/v2/public/design/" in url) or url.endswith("/login/otp/getCountryCodes") or ("/cdm/api/cdm/envConfigInfo?clientId=" in url) or url.endswith("/design/tenant/v2/site/metadata/user") or url.endswith("/design/tenant/v2/config/templates") or url.endswith("/notifications/api/notification/get-unread-count") or ("/dsd-orch/design/ui-elem" in url) or url.endswith("/dsd-orch/design/user/profile") or url.endswith("/dsd-orch/core/attributeTypesWithDetails") or url.endswith("/dsd-orch/core/attributeTypesWithDetails") or ("/dsd-bets-store/collection/getAllCollectionSpace" in url) or url.endswith("/dsd-orch/nslgrammar/cu_validate") or url.endswith("/nsl2text/batch_fat2flat")) is False:
        count = count+1 

        headers = entry["request"]["headers"]
        new_headers = []
        for header in headers:
            if header["name"].lower().startswith("sec-")==False and header["name"].startswith(":")==False and header["name"].lower()!="accept-encoding" and header["name"].lower()!="accept" and header["name"].lower()!="cookie" and header["name"].lower()!="origin" and header["name"].lower()!="referer" and header["name"].lower()!="user-agent" and header["name"].lower()!="content-length":
                new_headers.append(header)
        
        entry["request"]["headers"] = new_headers
        dict_list.append(entry)
        


  new_data = har_parser.har_data
  new_data["entries"] = dict_list
  print(f"Total entries before--->{total}")
  print(f"Total entries after--->{count}")
  final_data = json.dumps({"log":new_data})

  return final_data

def har2postman(har,prerequest_script,dic2):

    postman_collection = {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": f"collection{hour_min}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "_exporter_id": "15974284"
        },
        "item": []
    }

    dic = {"name":f"Automation {hour_min}","item":[]}
    postman_collection['item'].append(dic)

    entry = har['log']['entries']

    curr_user=""
    login_count=0
    gsi_count=0
    entity_count = 0
    cu_count=0
    dynamic_dic={}
    dynamic_count=0
    global_dict= collections.defaultdict(list)
    global_set= set()
    global_dict_reverse = {} 
    flag = False

    for j in range(len(entry)):
        if 'content' in entry[j]['response']:
            if 'text' in entry[j]['response']['content']:
                try:
                    res = json.loads(entry[j]['response']['content']['text'])
                    dic = select_dynamic(res,dynamic_dic,j,[])
                    dynamic_dic.update(dic)
                except ValueError:
                    pass
        
    #print(f"1 ---------------->{dynamic_dic}")

    
    for i in range(len(entry)):
        url = entry[i]['request']['url']
        url_components = urlsplit(url)

        url_obj = {
            'raw': url,
            'protocol': url_components.scheme,
            'host': [url_components.hostname]
        }

        if url_components.port:
            url_obj['host'][0]['value'] += ':' + str(url_components.port)

        if url_components.query:
            url_obj['query'] = [{'key': param.split('=')[0], 'value': param.split('=')[1]} for param in url_components.query.split('&')]

        if url_components.path:
            url_obj['path'] = [part for part in url_components.path.split('/')]
            path_parts = [part for part in url_components.path.split('/')]
            updated_path_parts = []
            for part in path_parts:
                if part in dic2:
                    updated_path_parts.append("{{" + dic2[part]+ "}}")
                else:
                    updated_path_parts.append(part)
            url_obj['path'] = updated_path_parts

        item = {
            "name": url_components.path if url_components.path else '/',
            "event":[{"listen": "prerequest","script":{"exec":[],"type":"text/javascript"}},{"listen": "test","script":{"exec":[
                                            "pm.test(\"Check status code\", function(){",
                        "  pm.expect(pm.response.code).to.eq(200);",
                        "});"]}}],
            "request": {
                "method": entry[i]['request']['method'],
                "header": [],
                "body": {},
                "url": url_obj,
            },
            "response": []
        }
        
        for header in entry[i]['request']['headers']:
            if header['name']=='authorization' or header['name']=='Authorization':
                item['request']['header'].append({
                    "key": header['name'],
                    "value": '{{BearerToken}}'
                })
            else:
                item['request']['header'].append({
                    "key": header['name'],
                    "value": header['value']
                })
                
        if 'postData' in entry[i]['request'] and  entry[i]['request']['method']!= "GET":
            if 'text' in entry[i]['request']['postData']:
                try:
                    body_data = json.loads(entry[i]['request']['postData']['text'])
                    body_data = iterate_nested_dict(body_data,dic2)
                    dic,dynamic_count,global_dict = check_dynamic(dynamic_dic,global_dict,dic2,dynamic_count,body_data,i)
                    # print(f"2 ---------------->{dynamic_dic}")
                    for key in global_dict:
                        for j in global_dict[key]:
                            global_dict_reverse["{{"+j+"}}"] = key

                    item['request']['body'] = {
                        "mode": "raw",
                        "raw": json.dumps(dic)
                    }


                except ValueError:
                    pass
        # print(f"type of dic is --> {type(dic)}")
        # if "agents" in dic:
            # print(f"type of agents in dic is --> {type(dic['agents']['agentType'])}")
        if url.endswith("login-action"):
            # print(global_dict_reverse)
            login_count=login_count+1
            body = json.loads(item['request']['body']['raw'])
            # body = dic
            if body['userName'].startswith("{{"):
                curr_user = global_dict_reverse[body['userName']]
            else:
                curr_user = body['userName']
            item['name'] = f"Login as {curr_user}"
            item['event'][1]['script']['exec'].append("pm.environment.set('BearerToken',\"Bearer \"+pm.response.json().result.access_token);\r")
            item['event'][1]['script']['exec'].append("pm.environment.set('RefreshToken',pm.response.json().result.refresh_token);")
            if login_count ==1:
                item['event'][0]['script']['exec']=prerequest_script

        if url.endswith("/tenant/gsi"):
            gsi_count=gsi_count+1
            if gsi_count%4==0:
                cu_count = 0
            res = json.loads(entry[i]['response']['content']['text'])
            
            item['name'] = f"Create GSI_{gsi_count}"
            dic2[res['result']['id']]=f"SolutionId{gsi_count}"  
            dic2[res['result']['dsdId']]=f"SolutionDsdId{gsi_count}"
            dic2[res['result']['masterId']]=f"SolutionMasterId{gsi_count}"

            item['event'][1]['script']['exec'].append("\r")
            item['event'][1]['script']['exec'].append(f"pm.variables.set('SolutionId{gsi_count}',pm.response.json().result.id);\r")
            item['event'][1]['script']['exec'].append(f"pm.variables.set('SolutionDsdId{gsi_count}',pm.response.json().result.dsdId);\r")
            item['event'][1]['script']['exec'].append(f"pm.variables.set('SolutionMasterId{gsi_count}',pm.response.json().result.masterId);")

        if url.endswith("/tenant/entity"):
            entity_count=entity_count+1
            attr_count = 1 
            # if gsi_count%4==0:
            #     cu_count = 0
            res = json.loads(entry[i]['response']['content']['text'])
            
            item['name'] = f"Create Entity_{entity_count}"
            dic2[res['result']['id']]=f"EntityId{entity_count}"  
            dic2[res['result']['dsdId']]=f"EntityDsdId{entity_count}"

            for i,attr in enumerate(res['result']['nslAttributes']):
                dic2[res['result']['nslAttributes'][i]['id']]=f"AttributeId{entity_count}{attr_count}"
                dic2[res['result']['nslAttributes'][i]['dsdId']]=f"AttributeDsdId{entity_count}{attr_count}"

                item['event'][1]['script']['exec'].append(f"pm.variables.set('AttributeId{entity_count}{attr_count}',pm.response.json().result.nslAttributes[{i}].id);\r")
                item['event'][1]['script']['exec'].append(f"pm.variables.set('AttributeDsdId{entity_count}{attr_count}',pm.response.json().result.nslAttributes[{i}].dsdId);\r")
                attr_count = attr_count+1
            # dic2[res['result']['masterId']]=f"SolutionMasterId{gsi_count}"

            item['event'][1]['script']['exec'].append("\r")
            item['event'][1]['script']['exec'].append(f"pm.variables.set('EntityId{entity_count}',pm.response.json().result.id);\r")
            item['event'][1]['script']['exec'].append(f"pm.variables.set('EntityDsdId{entity_count}',pm.response.json().result.dsdId);\r")
            # item['event'][1]['script']['exec'].append(f"pm.variables.set('SolutionMasterId{gsi_count}',pm.response.json().result.masterId);")

        if url.endswith("/tenant/change-unit"):
            cu_count=cu_count+1
            res = json.loads(entry[i]['response']['content']['text'])
            
            item['name'] = f"Create CU_{cu_count}"
            dic2[res['result']['id']]=f"CuId{cu_count}"  
            dic2[res['result']['dsdId']]=f"CuDsdId{cu_count}"

            item['event'][1]['script']['exec'].append("\r")
            item['event'][1]['script']['exec'].append(f"pm.variables.set('CuId{cu_count}',pm.response.json().result.id);\r")
            item['event'][1]['script']['exec'].append(f"pm.variables.set('CuDsdId{cu_count}',pm.response.json().result.dsdId);\r")

        elif url.endswith("logout-action"):
            item['name'] = f"Logout - {curr_user}"
        
        
        item['request']['url']['host']="{{TenantName}}.{{BaseURL}}"
        postman_collection['item'][0]['item'].append(item)

    for k in range(len(entry)):
        for key in global_dict.keys():
            for i in global_dict[key]:
                dynamic_attribute = i
                if dynamic_attribute not  in global_set:
                    global_set.add(dynamic_attribute)
                    position = dynamic_dic[key][1]
                    path = dynamic_dic[key][2]
                    str_path=construct_string(path)

                postman_collection['item'][0]['item'][position]['event'][1]['script']['exec'].append(f"pm.variables.set('{dynamic_attribute}',pm.response.json().{str_path});\r")
    print(f"dynamic_dict is----> {dynamic_dic}")
    return postman_collection

def construct_string(lst):
    result = ''
    for item in lst:
        if isinstance(item, str):
            result += f'.{item}'
        elif isinstance(item, int):
            result += f'[{item}]'
        elif isinstance(item, list):
            result += construct_string(item)
    return result.strip('.')


def generate_prerequest_script(sol_details):
    
    sol_list = []
    cu_list = []
    ent_list = []
    attr_list = []
    final_list =[]
    dict1 = {}
    script=[]
    for i in range(len(sol_details)):
        for j in sol_details[i]:
            ii = i +1
            sol_list.append(f"SolutionName{ii}")
            dict1[f"SolutionName{ii}"] = j

            for k in sol_details[i][j]:
                jj = len(cu_list)+1
                cu_list.append(f"CuName{jj}")
                dict1[f"CuName{jj}"] = k

                for l in sol_details[i][j][k]:
                    kk = len(ent_list)+1
                    ent_list.append(f"EntityName{kk}")
                    dict1[f"EntityName{kk}"] = l

                    for m in range(len(sol_details[i][j][k][l])):
                        attr_list.append(f"AttributeName{kk}{m+1}")
                        dict1[f"AttributeName{kk}{m+1}"] = sol_details[i][j][k][l][m]

    script.append("pm.variables.clear();\r")
    script.append("\r")
    script.append("pm.variables.set('RandomNumber', (new Date()).toISOString().replace(/[^0-9]/g, '').slice(0, -3) + '' + Math.floor((Math.random() * 100000) + 1));\r")
    script.append("\r")

    for key in dict1:
        if "AttributeName" not in key:
            script.append(f"pm.variables.set('{key}', '{dict1[key]}'+ pm.variables.get('RandomNumber') );\r")
        else:
           script.append(f"pm.variables.set('{key}','{dict1[key]}');\r")

    dic2 = {} 
    for key in dict1:
        dic2[dict1[key]] = key

    return dic2,script



def check_dynamic(dynamic_dic,global_dict,dic2,dynamic_count,body_data,i):
    modified_dict = body_data.copy()
    if type(body_data) is dict:
        for key, value in body_data.items():
            if isinstance(value, dict):
                modified_dict[key],dynamic_count,global_dict = check_dynamic(dynamic_dic,global_dict,dic2,dynamic_count,value,i)
            elif isinstance(value, list):
                modified_dict[key] = []
                for item in value:
                    if isinstance(item, dict):
                        new_v,dynamic_count,global_dict = check_dynamic(dynamic_dic,global_dict,dic2,dynamic_count,item,i)
                        modified_dict[key].append(new_v)
                    else:
                        modified_dict[key].append(item)
            else:
                if (value in dynamic_dic.keys() and  value not in dic2 and dynamic_dic[value][1]<i ):
                    if value not in global_dict.keys():
                        global_dict[value] = []
                        global_dict[value].append(f"{value}{len(global_dict[value])}")
                        dynamic_count = dynamic_count +1
                        modified_dict[key]= "{{"+f"{key}{len(global_dict[value])}"+"}}"
                    else:
                        modified_dict[key]="{{"+f"{key}{len(global_dict[value])}"+"}}"
                        
    return modified_dict,dynamic_count,global_dict



def iterate_nested_dict(dictionary,dict2):
    # print(dictionary)
    modified_dict = dictionary.copy()
    if type(dictionary) is dict:
        for key, value in dictionary.items():
            if isinstance(value, dict):
                modified_dict[key] = iterate_nested_dict(value,dict2)
            elif isinstance(value, list):
                # print(f"list is --> {value}")
                if key =="keywords":
                    pass
                    #print(f"------ {value} ----  {len(value)}")
                modified_dict[key] = []
                for item in value:
                    if isinstance(item, dict):
                        modified_dict[key].append(iterate_nested_dict(item,dict2))
                    else:
                        #print()
                        modified_dict[key].append(item)
                        #print(f'{modified_dict[key]}  ----@@@@@@')
            else:
                if value in dict2:
                    if type(value)==str:
                        modified_dict[key]="{{" + f"{dict2[value]}" + "}}"
                    else:
                        modified_dict[key]="{{" + f'{dict2[value]}' +"}}"
                        #print(f"modified_key is -->   {modified_dict[key]}  and type is --> {type(modified_dict[key])}")
    # print(modified_dict)
    return modified_dict

def select_dynamic(dictionary,dic,j,path):
    if type(dictionary) is dict:
        for key, value in dictionary.items():
            new_path = path+[key]
            if isinstance(value, dict):
                select_dynamic(value,dic,j,new_path)
            elif isinstance(value, list):
                for i,item in enumerate(value):
                    if isinstance(item, dict):
                        select_dynamic(item,dic,j,new_path+[i])
            else:
                dic[value] = [key,j,new_path]
    return dic


####------------------------------------------------------------------------------------------


sol_details = [{"HAR GSI 1804": {"Testing HAR CU1 1804": {"Testing HAR Entity1":["name","place"]},"Testing HAR CU2 1804": {"Testing HAR Entity1":["name","place"]} }}]

dic2, script = generate_prerequest_script(sol_details)
print(f"dic2 is ---->{dic2}")
global_dict = {}

with open('./har/solution_creation_execution_complex.har', 'r') as f:
    har_parser = HarParser(json.loads(f.read()))


har = json.loads(filter_har(har_parser))
collection_data = har2postman(har,script,dic2)

output_file = "collection"+hour_min+".json"
with open(f'./collection/{output_file}', 'w') as f:
    json.dump(collection_data, f)


