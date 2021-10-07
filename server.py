import requests as rq
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
import pytesseract
import time
import re
from PIL import Image
from flask import Flask,jsonify
from flask import request
import json
import random
import os
app = Flask(__name__)


def clean_name(text):
    text=re.sub('[^a-zA-Z0-9]','',text)
    return text
@app.route("/",methods=['POST'])
def service():    
    input_request = request.json
    drt_s=input_request['DRT']
    party_s=input_request['party_s']
    name = str(random.random())+".jpg"
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    driver = webdriver.Chrome('./chrome_selenium/chromedriver.exe')
    # Loadwebsite
    driver.get("https://drt.gov.in/front/page1_advocate.php")
    time.sleep(5)
    DRT = driver.find_element_by_id("schemaname")
    party_name = driver.find_element_by_id("name")
    captcha_input = driver.find_element_by_name("answer")
    captcha = driver.find_elements_by_class_name("imgcaptcha")[0].screenshot_as_png
    submit = driver.find_element_by_name("submit11")
    soup = BeautifulSoup(DRT.get_attribute('innerHTML'),'html.parser')
    option = [i['value'] for i in soup.findAll('option') if i.text.lower().strip() == drt_s.lower().strip() and hasattr(i,'value')]
    if(option):
        Select(DRT).select_by_value(option[0])
        party_name.send_keys(party_s)
        with open("./Captcha/"+name,"wb") as cap:
            cap.write(captcha)
        im = Image.open("./Captcha/"+name)
        text = pytesseract.image_to_string(im)
        text = "".join([i for i in text if i.isnumeric()])
        captcha_input.send_keys(text)
        submit.submit()
        time.sleep(5)
        table_data = driver.find_elements_by_class_name("scroll-table1")[1].get_attribute('innerHTML')
        table_soup = BeautifulSoup(table_data,'html.parser')
        columns = [clean_name(i.text) for i in table_soup.findAll('thead')[0].findAll('th')]
        final_dict = {}
        for i in range(len(columns)):
            final_dict[columns[i]]=[]
        for row in table_soup.find('tbody').findAll('tr'):
            if len(row.findAll('td'))==len(columns):
                for i in range(len(columns)):
                    if (row.findAll('td')[i].text.strip()=="MORE DETAIL"):
                        final_dict[columns[i]].append(re.sub("'\);","",re.sub(".+\('",'',row.findAll('td')[-1].find('a')['href'])))
                    else:                    
                        final_dict[columns[i]].append(re.sub('\s+',' ',row.findAll('td')[i].text))
            else:
                print(row.findAll('td'))
        more_details={}
        more_details['key']=final_dict['ViewMore']
        petion_detail={}
        resp_detail={}
        more_details['rawTables']=[]
        case_status = {}
        case_details = {}
        case_list = {}
        for i in more_details['key']:
            extra = rq.get('https://drt.gov.in/drtlive/Misdetailreport.php?no='+i)
            if extra.status_code==200:
                soup_extra = BeautifulSoup(extra.content,'html.parser')
                tables = soup_extra.findAll('table')
                more_details['rawTables'].append([str(i) for i in tables])
                flag = -1
                flag2=-1
                case_status[i] = {}
                case_details[i] = {}
                petion_detail[i]={}
                resp_detail[i]={}
                case_list[i]={}
                for dupe in tables[0].findAll('table'):
                    dupe.extract()
                for tr in tables[0].findAll('tr'):
                    if tr.find('th'):
                        if "CASE STATUS" in tr.find('th').text.strip():
                            flag = 1
                        if "CASE LISTING" in tr.find('th').text.strip():
                            flag = 2
                    if flag == 1:
                        if len(tr.findAll('td'))>1:
                            case_status[i][clean_name(tr.findAll('td')[0].text)]=tr.findAll('td')[1].text.strip()
                    elif flag==2:
                        if len(tr.findAll('td'))>1 and hasattr(tr.findAll('td')[0],"width"):
                            case_details[i][clean_name(tr.findAll('td')[0].text)]=tr.findAll('td')[1].text.strip()
                for tr in tables[1].findAll('tr'):
                    if tr.find('th'):
                        if "APPLICANT DETAIL" in tr.find('th').text.strip():
                            flag2 = 1
                        if "DEFENDENT DETAILS" in tr.find('th').text.strip():
                            flag2 = 2
                    if flag2 == 1:
                        if len(tr.findAll('br'))>0:
                            for line in tr.strings:
                                if len(clean_name(line))>1:
                                    if ':' in line:
                                        petion_detail[i][clean_name(line.split(':')[0])]=line.split(':')[1] if len(line.split(':'))>1 else ""
                                    else:
                                        petion_detail[i][clean_name(line.split('-')[0])]=line.split('-')[1] if len(line.split('-'))>1 else ""

                    elif flag2==2:
                        if len(tr.findAll('br'))>0:
                            for line in tr.strings:
                                if len(clean_name(line))>1:
                                    if ':' in line:
                                        resp_detail[i][clean_name(line.split(':')[0])]=line.split(':')[1] if len(line.split(':'))>1 else ""
                                    else:
                                        resp_detail[i][clean_name(line.split('-')[0])]=line.split('-')[1] if len(line.split('-'))>1 else ""
                case_list[i][clean_name(tables[2].findAll('tr')[1].findAll('td')[0].text)]=[]
                case_list[i][clean_name(tables[2].findAll('tr')[1].findAll('td')[1].text)]=[]
                case_list[i][clean_name(tables[2].findAll('tr')[1].findAll('td')[2].text)]=[]
                temp = tables[2].findAll('tr')[2].findAll('td')
                while(temp):
                    case_list[i][clean_name(tables[2].findAll('tr')[1].findAll('td')[2].text)].append(temp[-1].text)
                    temp.pop(-1)
                    case_list[i][clean_name(tables[2].findAll('tr')[1].findAll('td')[1].text)].append(temp[-1].text)
                    temp.pop(-1)
                    case_list[i][clean_name(tables[2].findAll('tr')[1].findAll('td')[0].text)].append(temp[-1].text)
                    temp.pop(-1)
                    
        driver.close()
        try:
            os.mkdir("drt_"+drt_s+"_party_"+party_s)
        except:
            pass
        with open("drt_"+drt_s+"_party_"+party_s+"/"+"first.json",'w') as file:
            json.dump(final_dict,file)
        with open("drt_"+drt_s+"_party_"+party_s+"/"+"More.json",'w') as file:
            json.dump(more_details,file)
        with open("drt_"+drt_s+"_party_"+party_s+"/"+"case_stat.json",'w') as file:
            json.dump(case_status,file)
        with open("drt_"+drt_s+"_party_"+party_s+"/"+"case_detail.json",'w') as file:
            json.dump(case_details,file)
        with open("drt_"+drt_s+"_party_"+party_s+"/"+"petitioner.json",'w') as file:
            json.dump(petion_detail,file)
        with open("drt_"+drt_s+"_party_"+party_s+"/"+"respondent.json",'w') as file:
            json.dump(resp_detail,file)
        with open("drt_"+drt_s+"_party_"+party_s+"/"+"case_list.json",'w') as file:
            json.dump(case_list,file)
        return jsonify({"Status":"Passed"}),200
    else:
        driver.close()
        return jsonify({"error": "Option not found"}), 400
if __name__ == '__main__':
    app.run(host="localhost", port=8000, threaded=True)

#TODO: Add headless option to Chrome
#TODO: Save data to a DB 