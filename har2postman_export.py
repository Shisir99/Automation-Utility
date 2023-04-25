import json
from datetime import datetime
import uuid
import json
import random
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

def har2postman(har,prerequest_script,dic2,import_data):

    postman_collection = {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": f"collection_complex {hour_min}",
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
    import_position = 0

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
            if login_count==1:
                import_position = i
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
    
    postman_collection['item'][0]['item'].insert(import_position+1,import_data)

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
                    if type(value)==str and key != "sourceValue":
                        modified_dict[key]="{{" + f"{dict2[value]}" + "}}"
                    elif key != "sourceValue":
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


def visit_all_items(data,global_dict):

    for gsi in data['gsiDetails']:
        lst = []
        lst.append(gsi['name'])
        lst.append(gsi['id'])
        lst.append(gsi['masterId'])
        global_dict['gsi'].append(lst)
        global_dict[gsi['name']]=[]
        for cu in gsi['solutionLogic']:
            lst = []
            lst.append(cu['DATA']['name'])
            lst.append(cu['DATA']['masterId'])
            global_dict[gsi['name']].append(lst)

    for role in data['roles']:
        lst = []
        lst.append(role['name'])
        lst.append(role['id'])
        global_dict['roles'].append(lst)
    
    for entity in data['entities']:
        lst = []
        lst.append(entity['name'])
        lst.append(entity['id'])
        lst.append(entity['masterId'])
        global_dict['entities'].append(lst)
        global_dict[entity['name']]=[]
        for attribute in entity['nslAttributes']:
            lst = []
            lst.append(attribute['name'])
            lst.append(attribute['id'])
            global_dict[entity['name']].append(lst)

    for cu in data['basicCus']:
        lst =[]
        lst.append(cu['name'])
        lst.append(cu['id'])
        lst.append(cu['masterId'])
        global_dict['basicCus'].append(lst)
        global_dict[cu['name']]=[]
        for layer in cu['layers']:
            for participatingItems in layer['participatingItems']:
                lst=[]
                lst.append(participatingItems['item']['DATA']['name'])
                lst.append(participatingItems['item']['DATA']['id'])
                lst.append(participatingItems['item']['DATA']['masterId'])
                global_dict[cu['name']].append(lst)
    return global_dict


def add_role_conflict(roles_list):
    conflict_lst = []
    for role in roles_list:
       role_conflict = {
        "itemType": "ROLE",
        "sourceValue": role[0],
        "targetValue": f"{role[0]}",
        "conflictAction": "RENAME",
        "isConflictResolved": True,
        "conflicting": True,
        "fixConflictInternally": False,
        "reservedBetConflict": False,
        "id": role[1],
        "selectedNamerole": False,
        "selectedrole": False,
        "isResolvedcon": True,
        "message": f"Renamed from {role[0]}"
        }
       
       conflict_lst.append(role_conflict)
    return conflict_lst

def add_GE_conflict(GE_list):
    conflict_lst = []
    for entity in GE_list:
       GE_conflicts =  {
        "itemType": "GENERALENTITY",
        "sourceValue": entity[0],
        "targetValue": f"{entity[0]}",
        "conflictAction": "RENAME",
        "isConflictResolved": True,
        "conflicting": True,
        "betConflictCase": "MASTER_ID_MISMATCH",
        "fixConflictInternally": False,
        "reservedBetConflict": False,
        "id": entity[1],
        "existingMasterId":entity[1],
        "status": "PUBLISHED",
        "version": "1.0",
        "masterId": entity[2]
        }
       
       conflict_lst.append(GE_conflicts)
    return conflict_lst

def add_attribute_conflict(attr_list):
    conflict_lst =[]

    for attribute in attr_list:
        attribute_conflicts = {
            "itemType": "ATTRIBUTE",
            "sourceValue": attribute[0],
            "targetValue": f"{attribute[0]}",
            "conflictAction": "RENAME",
            "isConflictResolved": True,
            "conflicting": True,
            "fixConflictInternally": False,
            "reservedBetConflict": False,
            "id": attribute[1]
            } 
        conflict_lst.append(attribute_conflicts)
    
    return conflict_lst

def add_CU_conflict(CU_list):
    conflict_lst = []

    for cu in CU_list:
        cu_conflicts =  {
        "itemType": "CHANGEUNIT",
        "sourceValue": cu[0],
        "targetValue": f"{cu[0]}",
        "conflictAction": "RENAME",
        "isConflictResolved": True,
        "betConflictCase": "MASTER_ID_MISMATCH",
        "conflicting": True,
        "fixConflictInternally": False,
        "reservedBetConflict": False,
        "id": cu[1],
        "existingMasterId":cu[1],
        "status": "PUBLISHED",
        "version": "1.0",
        "masterId": cu[2]
        }

        conflict_lst.append(cu_conflicts)
    
    return conflict_lst

def add_GSI_conflict(GSI_list):
    conflict_list = []

    for gsi in GSI_list:
        gsi_conflicts = {
        "itemType": "GSI",
        "sourceValue": gsi[0],
        "targetValue": f"{gsi[0]}",
        "conflictAction": "RENAME",
        "isConflictResolved": True,
        "conflicting": True,
        "betConflictCase": "MASTER_ID_MISMATCH",
        "fixConflictInternally": False,
        "reservedBetConflict": False,
        "id": gsi[1],
        "existingMasterId":gsi[1],
        "status": "PUBLISHED",
        "version": "1.0",
        "masterId": gsi[2]
        }

        conflict_list.append(gsi_conflicts)
    return conflict_list

def add_conflicts(global_dict):
    #print(global_dict)
    conflicts = {
    "hasConflict": True,
    "roleCount": len(global_dict['roles']),
    "roleConflictCount": len(global_dict['roles']),
    "entityCount": len(global_dict['entities']),
    "entityConflictCount": len(global_dict['entities']),
    "changeUnitCount": len(global_dict['basicCus']),
    "changeUnitConflictCount": len(global_dict['basicCus']),
    "gsiCount": len(global_dict['gsi']),
    "gsiConflictCount": len(global_dict['gsi']),
    "bookCount": 0,
    "bookConflictCount": 0,
    "dashBoardConflictCount": 0,
    "dataSetConflictCount": 0,
    "dashBoardCount": 0,
    "dataSetCount": 0,
    "connectionCount": 0,
    "connectionConflictCount": 0,
    "roleConflicts": add_role_conflict(global_dict['roles']),
    "geConflicts": add_GE_conflict(global_dict['entities']),
    "cuConflicts": add_CU_conflict(global_dict['basicCus']),
    "gsiConflicts": add_GSI_conflict(global_dict['gsi']),
    "bookConflicts": [],
    "dashBoardConflicts": [],
    "dataSetConflicts": [],
    "connectionConflicts": []
}

    return conflicts


def generate_sol_details(data):
    gsi_dict = {}
    final_list = []
    for gsi in data['gsi']:
        cu_dict = {}
        gsi_dict[gsi[0]] = cu_dict
        
        for cu in data[gsi[0]]:
            entity_dict = {}
            cu_dict[cu[0]] = entity_dict
            
            for entity in data[cu[0]]:
                attr_list = []
                entity_dict[entity[0]] = attr_list
                
                for attr in data[entity[0]]:
                    attr_list.append(attr[0])
        final_list.append({gsi[0]:gsi_dict[gsi[0]]})

    

    return final_list

def add_import_request(data):
    url = "https://qa3.nslhub.com/dsd-orch/importexport/Import/GSI"
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
        "name": "Importing the solution",
        "event":[{"listen": "prerequest","script":{"exec":[],"type":"text/javascript"}},{"listen": "test","script":{"exec":[
                                        "pm.test(\"Check status code\", function(){",
                    "  pm.expect(pm.response.code).to.eq(200);",
                    "});"]}}],
        "request": {
            "method": "POST",
            "header": [],
            "body": {},
            "url": url_obj,
        },
        "response": []
    }
    headers = [
      {
        "key": "Accept-Language",
        "value": "EN"
      },
      {
        "key": "User-Agent",
        "value": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
      },
      {
        "key": "Content-Type",
        "value": "application/json"
      },
      {
        "key": "Accept",
        "value": "application/json, text/plain, */*"
      },
      {
		"key": "Authorization",
		"value": "{{BearerToken}}"
	    }
    ]
    for header in headers:
        if header['key']=='authorization' or header['key']=='Authorization':
            item['request']['header'].append({
                "key": header['key'],
                "value": '{{BearerToken}}'
            })
        else:
            item['request']['header'].append({
                "key": header['key'],
                "value": header['value']
            })
            
    item['request']['body'] = {
        "mode": "raw",
        "raw": json.dumps(data)
                }
    
    return item

####------------------------------------------------------------------------------------------




with open("export/vendorSolution.json", "r") as file:
    import_data = json.load(file)
global_dict= {
        "roles": [],
        "entities": [],
        "basicCus": [],
        "gsi":[]
    }

global_dict = visit_all_items(import_data,global_dict)
print(global_dict)
random_number = random.randint(1000, 9999)
conflicts = add_conflicts(global_dict)



# output_file = "parsed_export.json"
# with open(f'./parsed_export/{output_file}', 'w') as f:
#     json.dump(data, f)


sol_details = generate_sol_details(global_dict)
#sol_details = [{"HAR GSI 1804": {"Testing HAR CU1 1804": {"Testing HAR Entity1":["name","place"]},"Testing HAR CU2 1804": {"Testing HAR Entity1":["name","place"]} }}]




dic2, script = generate_prerequest_script(sol_details)
#print(f"dic2 is ---->{dic2}")
global_dict = {}

print(iterate_nested_dict(conflicts,dic2))

import_data['conflictsAndResolutions'] = iterate_nested_dict(conflicts,dic2)

with open('./har/export_solution_execution.har', 'r') as f:
    har_parser = HarParser(json.loads(f.read()))

import_data = add_import_request(import_data)

har = json.loads(filter_har(har_parser))
collection_data = har2postman(har,script,dic2,import_data)

output_file = "collection_"+hour_min+".json"
with open(f'./collection/{output_file}', 'w') as f:
    json.dump(collection_data, f)


