import os
import cv2
import pdf2image
import time
import re
import easyocr
from PIL import Image
from paddleocr import PaddleOCR, draw_ocr
import ddddocr

base_path = './OCR Materials'

page_column = ['Company Legal Name_eng','Company Legal Name_ch','Business Name_eng','Business Name_ch',
               'Type of Company','Company Number','Business Registration Address','Email Address','Share Capital',
               'Secretary_Name_Ch','Secretary_Name_En','Secretary_Address','Secretary_Email','Secretary_ID',
                'Secretary_Cor_Name_Ch','Secretary_Cor_Name_En','Secretary_Cor_Address','Secretary_Cor_Email',
                'Director1_Name_Ch','Director1_Name_En','Director1_Address','Director1_Email','Director1_ID',
                'Director2_Name_Ch','Director2_Name_En','Director2_Address','Director2_Email','Director3_Name_Ch',
                'Director3_Name_En','Director3_Address','Director3_Email','Director4_Name_Ch','Director4_Name_En',
                'Director4_Address','Director4_Email','Director4_ID','Director5_Name_Ch','Director5_Name_En',
                'Director5_Address','Director5_Email','Director5_ID']

file_type = ['Certificate of Change of Name.pdf','NAR1 Annual Return.pdf','NNC1 - Incorporation Form.pdf']


def get_image_from_pdf(base_path,file_type):
    """
    change the pdf into PNG image,each page is one image saved in image_dir/temp accrodding to name of company
    args:
        base_path:the company path
        file_type:the different types of file in one company
    return:
        dir_dict:{company_name:{file_type}:{page-number:'',the path of the image:'',image save dir path}}
    
    """
    dir_dict = {}
    for dir_name in os.listdir(base_path):
        dir_dict[dir_name] = {}
        for i in file_type:
                
                try:
                    file_path = os.path.join(base_path,dir_name)+'/{}'.format(i)
                    images_from_path = pdf2image.convert_from_path(file_path,dpi=300)
                    base_filename = os.path.splitext(os.path.basename(file_path))[0]
                    try:
                        os.mkdir(os.path.join(base_path,dir_name)+'/temp')
                    except:
                        print('already exist')
                    save_path = os.path.join(base_path,dir_name)+'/temp'
                    print('--- Temp file: %s ---' % base_filename)        
                    img_file_list = []
                    print('--- Total Number of pages: %d ---' % len(images_from_path))
                    for i, page in enumerate(images_from_path):
                        new_filename = os.path.join(save_path, base_filename) + '_' + str(i) + '.PNG'
                        page.save(new_filename,'PNG')
                        img_file_list.append({'page-number': i+1, 'file-name': new_filename,'save_path':save_path})
                    print(file_path)
                    dir_dict[dir_name].update({base_filename:img_file_list})
                except:
                    file_path = os.path.join(base_path,dir_name)+'/{}'.format(i)
                    base_filename = os.path.splitext(os.path.basename(file_path))[0]
                    dir_dict[dir_name].update({base_filename:[]})
        
    return  dir_dict



def read_ID (img_file,area_lis,save_path):
    img_file = cv2.imread(img_file)
    img = [img_file[int(i[1]):int(i[3]),int(i[0]):int(i[2])] for i in area_lis]
    img = cv2.hconcat(img)
    cv2.imwrite(save_path+'/temp.PNG',img)
    
    dddd = ddddocr.DdddOcr(old=True)
    
    with open(save_path+'/temp.PNG', 'rb') as f:
        image = f.read()

    ID_Number = dddd.classification(image)
    
    return ID_Number


def chose_address(column_name,address_list,content_dict):
    try:
        for i in range(len(address_list[0])):
            if address_list[0][i][0].count(' ')>address_list[1][i][0].count(' '):
                content_dict[column_name] = content_dict[column_name]+[address_list[0][i][0]]
            elif address_list[0][i][0].count(' ')<address_list[1][i][0].count(' '):
                content_dict[column_name] = content_dict[column_name]+[address_list[1][i][0]]
            else:
                if address_list[0][i][1] > address_list[1][i][1]:
                    content_dict[column_name] = content_dict[column_name]+[address_list[0][i][0]]
                else:
                    content_dict[column_name] = content_dict[column_name]+[address_list[1][i][0]]
    except:
        print('errors')
        content_dict[column_name]=[]




def extract_from_page1(ocr_en,ocr_tra,img_file_list,page_column):
    
 
    save_path = img_file_list[0]['save_path']
    rectangle_dict = {}
    content_dict = dict.fromkeys(page_column,[])
    c_number_flag = False
    print('extract data from page 1')
    start_time = time.time()
    image = cv2.imread(img_file_list[0]['file-name'],cv2.IMREAD_GRAYSCALE)
    result_eng = ocr_en.ocr(image)
    result_ch = ocr_tra.ocr(image)  
    
    rectangle_dict['Company Name'] = [x[0] for x in result_ch if '公司名稱' in x[1][0]]
    rectangle_dict['Company Number'] = [x[0] for x in result_ch if '公司編號' in x[1][0]]
    rectangle_dict['Business Name'] = [x[0] for x in result_ch if '商業名稱' in x[1][0]]
    rectangle_dict['Type of Company'] = [x[0] for x in result_ch if '公司類別' in x[1][0]]
    rectangle_dict['Business Registration Address'] = [x[0] for x in result_ch if '辦事處地址' in x[1][0]]    
    rectangle_dict['page1_end'] = [x[0] for x in result_ch if '資料' in x[1][0]]
    
    lis1_compare = []
    
    for content in result_eng:
                  
        if content[0][0][0]>rectangle_dict['Company Number'][0][0][0] and content[0][0][1]>rectangle_dict['Company Number'][0][2][1]\
            and content[0][0][1] < rectangle_dict['Company Name'][0][0][1]:
                content_dict['Company Number'] = [content[1][0]]
        
        if content[0][0][1]-rectangle_dict['Company Name'][0][0][1]>20 and \
            rectangle_dict['Business Name'][0][0][1]-content[0][0][1]>20 and content[1][1]>0.7:
                print(content[1][0])
                content_dict['Company Legal Name_eng'] = content_dict['Company Legal Name_eng']+[content[1][0]]

        elif content[0][0][1]-rectangle_dict['Business Name'][0][0][1]>20 and \
            rectangle_dict['Type of Company'][0][0][1]-content[0][0][1]>20 and content[1][1]>0.7:
                content_dict['Business Name_eng'] = content_dict['Business Name_eng']+[content[1][0]]
        
        elif content[0][0][1]-rectangle_dict['Business Registration Address'][0][0][1]>20 and \
            rectangle_dict['page1_end'][0][0][1]-content[0][0][1]>20:
                content_dict['Business Registration Address'] = content_dict['Business Registration Address'] + [content[1][0]]
                content_dict['Business Registration Address'] = [' '.join(content_dict['Business Registration Address'])]
     
    lis1_compare.append(content_dict['Business Registration Address'].copy())
    content_dict['Business Registration Address'] = []
    
                
                
    
    for content in result_ch:
        
        if content[0][0][1]-rectangle_dict['Company Name'][0][0][1]>20 and \
            rectangle_dict['Business Name'][0][0][1]-content[0][0][1]>20 and re.findall(r'[\u4e00-\u9fa5]+',content[1][0]):
                content_dict['Company Legal Name_ch'] = content_dict['Company Legal Name_ch']+[content[1][0]]
        
        elif content[0][0][1]-rectangle_dict['Business Name'][0][0][1]>20 and \
            rectangle_dict['Type of Company'][0][0][1]-content[0][0][1]>20 and re.findall(r'[\u4e00-\u9fa5]+',content[1][0]):
                content_dict['Business Name_ch'] = content_dict['Business Name_ch']+[content[1][0]]

                
        elif content[0][0][1]-rectangle_dict['Business Registration Address'][0][0][1]>20 and \
            rectangle_dict['page1_end'][0][0][1]-content[0][0][1]>20:
                content_dict['Business Registration Address'] = content_dict['Business Registration Address'] + [content[1][0]]
    lis1_compare.append(content_dict['Business Registration Address'].copy())
    content_dict['Business Registration Address'] = []
    
    chose_address('Business Registration Address',lis1_compare,content_dict)
    
    
    
    type_lis = ['Private company','Public company','Company limited by guarantee']
    type_position1 = [x[0] for x in result_eng if 'Pri' in x[1][0] and 'compa' in x[1][0]][0]
    type_position2 = [x[0] for x in result_eng if 'Pub' in x[1][0] and 'compa' in x[1][0]][0]
    type_position3 = [x[0] for x in result_eng if 'guaran' in x[1][0] and 'Compa' in x[1][0]][0]
    
    lis1 = [type_position1,type_position2,type_position3]
    
    lis2 = []
    
    for i in lis1:
        left = int(i[0][0] - 130)
        right = int(i[0][0] - 10)
        up = int(i[0][1] - 50)
        bottom = int(i[0][1] - 15)
        
        image_cut = image[up:bottom,left:right]
        lis2.append(image_cut)
    
    for i,j in enumerate(lis2):
        cv2.imwrite('type_{}.jpg'.format(i),j)
    
    sum_pix = [x.sum() for x in lis2]   
    content_dict['Type of Company'] = [type_lis[i] for i,j in enumerate(sum_pix) if j == min(sum_pix)]

    return content_dict





def extract_from_page2(content_dict,ocr_en,ocr_tra,img_file_list):
    
    print('extract data from page 2')
    # print('page 1 time:{}'.format(time.time()-start_time))
    rectangle_dict = {}                   
    image = cv2.imread(img_file_list[1]['file-name'],1)
    result_eng = ocr_en.ocr(image)
    result_ch = ocr_tra.ocr(image)
    lis1 = []
    rectangle_dict['Email Address'] = [x[0] for x in result_ch if '公司編號' in x[1][0]]+[x[0] for x in result_ch if '按揭' in x[1][0]]
    rectangle_dict['Share Capital'] = [[x[0] for x in result_ch if '總款額' in x[1][0]][0]]
    right = rectangle_dict['Email Address'][0][1][0]-200
    left = rectangle_dict['Email Address'][1][1][0]
    down = rectangle_dict['Email Address'][0][0][1]
    
    for content in result_eng:  
        up_mid_line = int((content[0][0][0]+content[0][1][0])/2)
        left_mid_line = int((content[0][0][1]+content[0][3][1])/2)
        if left<up_mid_line<right and content[0][0][1]<down:
            content_dict['Email Address'] = content_dict['Email Address'] + [content[1][0]]
        
        
        if rectangle_dict['Share Capital'][0][0][0]-100<up_mid_line<rectangle_dict['Share Capital'][0][1][0]+100 and \
            content[0][1][1]>rectangle_dict['Share Capital'][0][2][1]:
               content_dict['Share Capital'] = content[1][0]
               lis1.append(content[1][0])
    content_dict['Share Capital'] = [lis1[-1]]
    return content_dict



def extract_from_page3(content_dict,ocr_en,ocr_tra,img_file_list):
    print('extract data from page 3')
    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))  
    result_en = ocr_en.ocr(img_file_list[2]['file-name'])
    result_ch = ocr_tra.ocr(img_file_list[2]['file-name'])
    
    lis1_compare = []
    lis2_compare = []

    # rectangle_dict['Secretary_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
    rectangle_dict['Secretary_Name_En'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[0][0]
    rectangle_dict['Secretary_Address'] = list(filter(lambda k: ('香港' in k[1][0]) and ('地址' in k[1][0]), result_ch))[0][0]
    rectangle_dict['Secretary_Email'] = list(filter(lambda k: ('電郵地址' in k[1][0]), result_ch))[0][0]
    rectangle_dict['Se1_right'] = list(filter(lambda k: ('姓氏' in k[1][0]),result_ch))[0][0]
    rectangle_dict['Secretary_ID'] = list(filter(lambda k: ('dentity' in k[1][0]) and ('Card' in k[1][0]), result_en))[0][0]

    # rectangle_dict['Secretary_Cor_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[1][0]
    rectangle_dict['Secretary_Cor_Name_En'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[1][0]
    rectangle_dict['Secretary_Cor_Address'] = list(filter(lambda k: ('香港' in k[1][0]) and ('址' in k[1][0]), result_ch))[1][0]
    rectangle_dict['Secretary_Cor_Email'] = list(filter(lambda k: ('電郵地址' in k[1][0]), result_ch))[1][0]
    
    for content in result_ch:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if  rectangle_dict['Se1_right'][1][0]+100<content[0][0][0] and \
            rectangle_dict['Secretary_Name_En'][1][1]-150<left_mid<rectangle_dict['Secretary_Name_En'][1][1]-60:
                content_dict['Secretary_Name_Ch'] =[content[1][0]]
                                          
        elif rectangle_dict['Secretary_Cor_Name_En'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Secretary_Cor_Name_En'][1][1]-170<left_mid<rectangle_dict['Secretary_Cor_Name_En'][1][1]-60:
                content_dict['Secretary_Cor_Name_Ch'] =[content[1][0]]
                
        elif rectangle_dict['Secretary_Address'][1][0]+50<content[0][0][0] and \
            rectangle_dict['Secretary_Address'][1][1]<left_mid<rectangle_dict['Secretary_Email'][1][1]-110:
                content_dict['Secretary_Address'] = content_dict['Secretary_Address']+[content[1]]

        elif rectangle_dict['Secretary_Cor_Address'][1][0]+50<content[0][0][0] and \
            rectangle_dict['Secretary_Cor_Address'][1][1]-20<left_mid<rectangle_dict['Secretary_Cor_Email'][1][1]-110:
                content_dict['Secretary_Cor_Address'] = content_dict['Secretary_Cor_Address']+[content[1]]
    # re.findall(r'[^\u4e00-\u9fa5]+',content[1][0])
    lis1_compare.append(content_dict['Secretary_Address'].copy())
    lis2_compare.append(content_dict['Secretary_Cor_Address'].copy())
    content_dict['Secretary_Address'] = []
    content_dict['Secretary_Cor_Address'] = []
                    

    for content in result_en:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Se1_right'][1][0]+100<content[0][0][0] and \
            rectangle_dict['Secretary_Name_En'][1][1]-50<left_mid<rectangle_dict['Secretary_Name_En'][2][1]+110:
                content_dict['Secretary_Name_En'] = content_dict['Secretary_Name_En']+[content[1][0]]
                
        elif rectangle_dict['Se1_right'][1][0]+100<content[0][0][0] and \
            rectangle_dict['Secretary_Email'][1][1]<left_mid<rectangle_dict['Secretary_Email'][2][1]+50:
                content_dict['Secretary_Email'] = content_dict['Secretary_Email']+[content[1][0]]
                
        elif rectangle_dict['Secretary_Address'][1][0]+50<content[0][0][0] and \
            rectangle_dict['Secretary_Address'][1][1]<left_mid<rectangle_dict['Secretary_Email'][1][1]-110:
                content_dict['Secretary_Address'] = content_dict['Secretary_Address']+[content[1]]

        elif rectangle_dict['Secretary_Cor_Address'][1][0]+50<content[0][0][0] and \
            rectangle_dict['Secretary_Cor_Address'][1][1]-20<left_mid<rectangle_dict['Secretary_Cor_Email'][1][1]-110:
                content_dict['Secretary_Cor_Address'] = content_dict['Secretary_Cor_Address']+[content[1]]
            
        elif rectangle_dict['Secretary_Cor_Name_En'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Secretary_Cor_Name_En'][1][1]-50<left_mid<rectangle_dict['Secretary_Cor_Name_En'][2][1]+25:
                content_dict['Secretary_Cor_Name_En'] = [content[1][0]]
        

        elif rectangle_dict['Secretary_Cor_Email'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Secretary_Cor_Email'][1][1]<left_mid<rectangle_dict['Secretary_Cor_Email'][2][1]+50:
                content_dict['Secretary_Cor_Email'] = content_dict['Secretary_Cor_Email']+[content[1][0]]
        
    lis1_compare.append(content_dict['Secretary_Address'].copy())
    lis2_compare.append(content_dict['Secretary_Cor_Address'].copy())

    content_dict['Secretary_Address'] = []
    content_dict['Secretary_Cor_Address'] = []

    
######chose the highest conf between result_en and result_ch
    chose_address('Secretary_Address',lis1_compare,content_dict)
    chose_address('Secretary_Cor_Address',lis2_compare,content_dict)

    area_lis = []
#####get ID if catch message from the ID area
 
    area_lis.append((rectangle_dict['Secretary_ID'][1][0]+215,rectangle_dict['Secretary_ID'][0][1]-32,
        rectangle_dict['Secretary_ID'][1][0]+290,rectangle_dict['Secretary_ID'][0][1]+35))
       
    area_lis.append((rectangle_dict['Secretary_ID'][1][0]+340,rectangle_dict['Secretary_ID'][0][1]-32,
        rectangle_dict['Secretary_ID'][1][0]+427,rectangle_dict['Secretary_ID'][0][1]+35))
        
    area_lis.append((rectangle_dict['Secretary_ID'][1][0]+470,rectangle_dict['Secretary_ID'][0][1]-32,
        rectangle_dict['Secretary_ID'][1][0]+550,rectangle_dict['Secretary_ID'][0][1]+35))
               
    for i in range(7):
        area_lis.append((rectangle_dict['Secretary_ID'][1][0]+620+i*125,rectangle_dict['Secretary_ID'][0][1]-32,
                rectangle_dict['Secretary_ID'][1][0]+710+i*123,rectangle_dict['Secretary_ID'][0][1]+35))
                    
    content_dict['Secretary_ID'] = [read_ID(img_file_list[2]['file-name'],area_lis,img_file_list[2]['save_path'])]
    
    return content_dict





def extract_from_page4(content_dict,ocr_en,ocr_tra,img_file_list):
    print('extract data from page4')
    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))  
    result_en = ocr_en.ocr(img_file_list[3]['file-name'])
    result_ch = ocr_tra.ocr(img_file_list[3]['file-name'])
    
    lis1_compare = []
    
    rectangle_dict['Director1_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director1_Name_En'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director1_Address'] = list(filter(lambda k: '住址' in k[1][0], result_ch))[0][0]
    rectangle_dict['Director1_Email'] = list(filter(lambda k: '電郵地址' in k[1][0], result_ch))[0][0]
    # rectangle_dict['Dir_right'] = list(filter(lambda k: '姓氏' in k[1][0],result_ch))[0][0]
    rectangle_dict['Director1_ID'] = list(filter(lambda k: ('dentity' in k[1][0]) and ('Card' in k[1][0]), result_en))[0][0]

    for content in result_ch:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director1_Name_Ch'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director1_Name_Ch'][1][1]-55<left_mid<rectangle_dict['Director1_Name_Ch'][2][1]+10:
                content_dict['Director1_Name_Ch'] =[content[1][0]]
                
        
        elif rectangle_dict['Director1_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director1_Address'][0][1]<left_mid<rectangle_dict['Director1_Address'][0][1]+320:
                content_dict['Director1_Address'] = content_dict['Director1_Address']+[content[1]]
        
    lis1_compare.append(content_dict['Director1_Address'].copy())
    content_dict['Director1_Address'] = []
    
    
    for content in result_en:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director1_Name_En'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director1_Name_En'][1][1]-50<left_mid<rectangle_dict['Director1_Name_En'][2][1]+125:
                content_dict['Director1_Name_En'] =content_dict['Director1_Name_En']+[content[1][0]]
        
        elif rectangle_dict['Director1_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director1_Address'][0][1]<left_mid<rectangle_dict['Director1_Address'][0][1]+320:
                content_dict['Director1_Address'] = content_dict['Director1_Address']+[content[1]]
        
        elif rectangle_dict['Director1_Email'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director1_Email'][1][1]<left_mid<rectangle_dict['Director1_Email'][2][1]+50:
                content_dict['Director1_Email'] = content_dict['Director1_Email']+[content[1][0]]
                
    lis1_compare.append(content_dict['Director1_Address'].copy())
    content_dict['Director1_Address'] = []
    chose_address('Director1_Address',lis1_compare,content_dict) 
    
    area_lis = []
  
    area_lis.append((rectangle_dict['Director1_ID'][1][0]+215,rectangle_dict['Director1_ID'][0][1]-32,
            rectangle_dict['Director1_ID'][1][0]+290,rectangle_dict['Director1_ID'][0][1]+35))
        
    area_lis.append((rectangle_dict['Director1_ID'][1][0]+347,rectangle_dict['Director1_ID'][0][1]-32,
            rectangle_dict['Director1_ID'][1][0]+427,rectangle_dict['Director1_ID'][0][1]+35))
        
    area_lis.append((rectangle_dict['Director1_ID'][1][0]+470,rectangle_dict['Director1_ID'][0][1]-32,
            rectangle_dict['Director1_ID'][1][0]+550,rectangle_dict['Director1_ID'][0][1]+35))
               
    for i in range(7):
        area_lis.append((rectangle_dict['Director1_ID'][1][0]+630+i*125,rectangle_dict['Director1_ID'][0][1]-32,
                rectangle_dict['Director1_ID'][1][0]+710+i*123,rectangle_dict['Director1_ID'][0][1]+35))
                    
    content_dict['Director1_ID'] = [read_ID(img_file_list[3]['file-name'],area_lis,img_file_list[3]['save_path'])]
    
    return content_dict

    
def extract_from_page5(content_dict,ocr_en,ocr_tra,img_file_list):
    
    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))  
    result_en = ocr_en.ocr(img_file_list[4]['file-name'])
    result_ch = ocr_tra.ocr(img_file_list[4]['file-name'])
    
    lis1_compare = []
    lis2_compare = []
    
    rectangle_dict['Director2_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director2_Name_En'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director2_Email'] = list(filter(lambda k: '電郵地址' in k[1][0], result_ch))[0][0]
    rectangle_dict['Director2_Address'] = list(filter(lambda k: '地址' in k[1][0], result_ch))[0][0]
    
    
    rectangle_dict['Director3_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[1][0]
    rectangle_dict['Director3_Name_En'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[1][0]
    rectangle_dict['Director3_Email'] = list(filter(lambda k: '電郵地址' in k[1][0], result_ch))[1][0]
    rectangle_dict['Director3_Address'] = list(filter(lambda k: '地址' in k[1][0], result_ch))[2][0]
    
    for content in result_ch:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director2_Name_Ch'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director2_Name_Ch'][1][1]-50<left_mid<rectangle_dict['Director2_Name_Ch'][1][1]+100:
                content_dict['Director2_Name_Ch'] =[content[1][0]]
                
        elif rectangle_dict['Director2_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director2_Address'][0][1]<left_mid<rectangle_dict['Director2_Address'][0][1]+300:
                content_dict['Director2_Address'] = content_dict['Director2_Address']+[content[1]]
        
        elif rectangle_dict['Director3_Name_Ch'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director3_Name_Ch'][1][1]-50<left_mid<rectangle_dict['Director3_Name_Ch'][1][1]+100:
                content_dict['Director3_Name_Ch'] =[content[1][0]]
        
        elif rectangle_dict['Director3_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director3_Address'][0][1]<left_mid<rectangle_dict['Director3_Address'][0][1]+300:
                content_dict['Director3_Address'] = content_dict['Director3_Address']+[content[1]]
    
         
    lis1_compare.append(content_dict['Director2_Address'].copy())
    lis2_compare.append(content_dict['Director3_Address'].copy())
    content_dict['Director2_Address'] = [] 
    content_dict['Director3_Address'] = []
    
    for content in result_en:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director2_Name_En'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director2_Name_En'][1][1]-50<left_mid<rectangle_dict['Director2_Name_En'][2][1]+100:
                content_dict['Director2_Name_En'] =content_dict['Director2_Name_En']+[content[1][0]]
        
        elif rectangle_dict['Director2_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director2_Address'][0][1]<left_mid<rectangle_dict['Director2_Address'][0][1]+300:
                content_dict['Director2_Address'] = content_dict['Director2_Address']+[content[1]]
        
        elif rectangle_dict['Director2_Email'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director2_Email'][1][1]<left_mid<rectangle_dict['Director2_Email'][1][1]+90:
                content_dict['Director2_Email'] = content_dict['Director2_Email']+[content[1][0]]
       
        elif rectangle_dict['Director3_Name_En'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director3_Name_En'][1][1]-50<left_mid<rectangle_dict['Director3_Name_En'][2][1]+100:
                content_dict['Director3_Name_En'] =content_dict['Director2_Name_En']+[content[1][0]]
        
        elif rectangle_dict['Director3_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director3_Address'][0][1]<left_mid<rectangle_dict['Director3_Address'][0][1]+300:
                content_dict['Director3_Address'] = content_dict['Director3_Address']+[content[1]]
        
        elif rectangle_dict['Director3_Email'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director3_Email'][1][1]<left_mid<rectangle_dict['Director3_Email'][1][1]+90:
                content_dict['Director3_Email'] = content_dict['Director3_Email']+[content[1][0]]
        
    lis1_compare.append(content_dict['Director2_Address'].copy())
    lis2_compare.append(content_dict['Director3_Address'].copy())    
    content_dict['Director2_Address']=[]
    content_dict['Director3_Address']=[]

    chose_address('Director2_Address',lis1_compare,content_dict) 
    chose_address('Director3_Address',lis2_compare,content_dict)
    
    return content_dict


def extract_from_page6(content_dict,ocr_en,ocr_tra,img_file_list):
    print('extract data from page6')
    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))  
    result_en = ocr_en.ocr(img_file_list[5]['file-name'])
    result_ch = ocr_tra.ocr(img_file_list[5]['file-name'])
    
    lis1_compare = []
    
    rectangle_dict['Director4_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director4_Name_En'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director4_Address'] = list(filter(lambda k: 'Residential' in k[1][0], result_ch))[0][0]
    rectangle_dict['Director4_Email'] = list(filter(lambda k: '電郵地址' in k[1][0], result_ch))[0][0]
    # rectangle_dict['Dir_right'] = list(filter(lambda k: '姓氏' in k[1][0],result_ch))[0][0]
    rectangle_dict['Director4_ID'] = list(filter(lambda k: ('dentity' in k[1][0]) and ('Card' in k[1][0]), result_en))[0][0]

    for content in result_ch:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director4_Name_Ch'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director4_Name_Ch'][1][1]-50<left_mid<rectangle_dict['Director4_Name_Ch'][2][1]+10:
                content_dict['Director4_Name_Ch'] =[content[1][0]]
                     
        elif rectangle_dict['Director4_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director4_Address'][0][1]-60<left_mid<rectangle_dict['Director4_Address'][0][1]+270:
                content_dict['Director4_Address'] = content_dict['Director4_Address']+[content[1]]
        
    lis1_compare.append(content_dict['Director4_Address'].copy())
    content_dict['Director4_Address'] = []
    
    
    for content in result_en:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director4_Name_En'][1][0]+300<content[0][0][0] and \
            rectangle_dict['Director4_Name_En'][1][1]-50<left_mid<rectangle_dict['Director4_Name_En'][2][1]+160:
                content_dict['Director4_Name_En'] =content_dict['Director4_Name_En']+[content[1][0]]
        
        elif rectangle_dict['Director4_Address'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director4_Address'][0][1]<left_mid<rectangle_dict['Director4_Address'][0][1]+320:
                content_dict['Director4_Address'] = content_dict['Director4_Address']+[content[1]]
        
        elif rectangle_dict['Director4_Email'][1][0]+200<content[0][0][0] and \
            rectangle_dict['Director4_Email'][1][1]<left_mid<rectangle_dict['Director4_Email'][2][1]+50:
                content_dict['Director4_Email'] = content_dict['Director4_Email']+[content[1][0]]
        
    
    lis1_compare.append(content_dict['Director4_Address'].copy())
    content_dict['Director4_Address'] = []
    chose_address('Director4_Address',lis1_compare,content_dict) 
    
    area_lis = []

    area_lis.append((rectangle_dict['Director4_ID'][1][0]+250,rectangle_dict['Director4_ID'][0][1]-32,
            rectangle_dict['Director4_ID'][1][0]+320,rectangle_dict['Director4_ID'][0][1]+35))
              
    area_lis.append((rectangle_dict['Director4_ID'][1][0]+360,rectangle_dict['Director4_ID'][0][1]-32,
            rectangle_dict['Director4_ID'][1][0]+440,rectangle_dict['Director4_ID'][0][1]+35))
        
    area_lis.append((rectangle_dict['Director4_ID'][1][0]+500,rectangle_dict['Director4_ID'][0][1]-32,
            rectangle_dict['Director4_ID'][1][0]+580,rectangle_dict['Director4_ID'][0][1]+35))
               
    for i in range(7):
        area_lis.append((rectangle_dict['Director4_ID'][1][0]+640+i*124,rectangle_dict['Director4_ID'][0][1]-32,
            rectangle_dict['Director4_ID'][1][0]+720+i*124,rectangle_dict['Director4_ID'][0][1]+35))
                    
    content_dict['Director4_ID'] = [read_ID(img_file_list[5]['file-name'],area_lis,img_file_list[5]['save_path'])]
    
    return content_dict

def extract_from_page8(content_dict,ocr_tra,img_file_list):
    
    reader_en = easyocr.Reader(['en'])
    image = cv2.imread(img_file_list[7]['file-name'],cv2.IMREAD_GRAYSCALE)

    
    #先通过paddle ocr(速度快)给表格定位从而裁剪出图片以给easy ocr处理,
    result_cut = ocr_tra.ocr(image)
    up =  int([x[0] for x in result_cut if '姓名' in x[1][0]][0][0][1]+170)
    bottom = int([x[0] for x in result_cut if '如公司的股份' in x[1][0]][0][0][1]-100)
    
    name_left = int([x[0] for x in result_cut if '姓名' in x[1][0]][0][0][0]-90)
    name_right = int([x[0] for x in result_cut if '姓名' in x[1][0]][0][1][0]+75)
    
    add_left = int([x[0] for x in result_cut if '姓名' in x[1][0]][0][1][0]+75)
    add_right = int([x[0] for x in result_cut if '現時持有' in x[1][0]][0][0][0]-20)
    
    holding_left = int([x[0] for x in result_cut if '現時持有' in x[1][0]][0][0][0]-20)
    holding_right = int([x[0] for x in result_cut if '現時持有' in x[1][0]][0][1][0]+20)
    
    image_name = image[up:bottom,name_left:name_right]
    image_address = image[up:bottom,add_left:add_right]
    image_holding = image[up:bottom,holding_left:holding_right]
    
    image_name = cv2.resize(image_name,None,fx=0.80,fy=0.80)
    image_address = cv2.resize(image_address,None,fx=0.75,fy=0.75)
    image_holding = cv2.resize(image_holding,None,fx=0.75,fy=0.75)
    
    
    en_name_lis = []
    left_lis = []
    result_name_eng = reader_en.readtext(image_name,slope_ths=0.4) 
        
    for i in result_name_eng:
        if i[2]>0.55 and not re.findall(r'[^a-zA-Z ]+',i[1]):
            if not en_name_lis:
                en_name_lis.append([i[1]])
                left_lis.append(i[0])
                continue
            elif abs(i[0][0][1]-left_lis[-1][2][1])<20:
                en_name_lis[-1] = en_name_lis[-1] + [i[1]]
                left_lis.append(i[0])
            else:
                en_name_lis.append([i[1]])
                left_lis.append(i[0])

 
    en_name_lis = [' '.join(x) for x in en_name_lis]
    
    address_lis = []
    result_add = reader_en.readtext(image_address,paragraph=True)
    for i in result_add:
        address_lis.append(i[1])
    
    holding_lis = []
    result_holding = reader_en.readtext(image_holding)
    for i in result_holding:
        holding_lis.append(i[1])
    print(holding_lis)
    
    tra_name_lis = []
    result_name_tra = ocr_tra.ocr(image_name)
    for i in result_name_tra:
        if re.findall(r'[\u4e00-\u9fa5]+',i[1][0]):
            tra_name_lis.append(i[1][0])
            
    if holding_lis:
        holding_lis = [int(''.join(re.findall(r'\d+',x))) for x in holding_lis]
    else:
        holding_lis = [1,1]

    
    sum_holding = sum(holding_lis)
    percent_list = [x/sum_holding for x in holding_lis]
    print(percent_list) 
    
    
    for i,name in enumerate(en_name_lis):
        content_dict['Shareholder{}_name_en'.format(i+1)] = [name]
        try:
          content_dict['Shareholder{}_name_ch'.format(i+1)] = [tra_name_lis[i]]
        except:
          print('No Chinese Name')
        content_dict['Shareholder{}_Address'.format(i+1)] = [address_lis[i]]
        content_dict['Shareholder{}_%'.format(i+1)] = [percent_list[i]]
        

    return content_dict   
    
def extract_from_page9(content_dict,ocr_en,ocr_tra,img_file_list):
    print('extract data from page9')
    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))
    try:
        result_en = ocr_en.ocr(img_file_list[8]['file-name'])
        result_ch = ocr_tra.ocr(img_file_list[8]['file-name'])
            
        lis1_compare = []
            
        rectangle_dict['Director5_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
        rectangle_dict['Director5_Name_En'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[0][0]
        rectangle_dict['Director5_Address'] = list(filter(lambda k: 'Residential' in k[1][0], result_ch))[0][0]
        rectangle_dict['Director5_Email'] = list(filter(lambda k: '電郵地址' in k[1][0], result_ch))[0][0]
        # rectangle_dict['Dir_right'] = list(filter(lambda k: '姓氏' in k[1][0],result_ch))[0][0]
        rectangle_dict['Director5_ID'] = list(filter(lambda k: ('dentity' in k[1][0]) and ('Card' in k[1][0]), result_en))[0][0]
        
        for content in result_ch:
            left_mid = (content[0][0][1]+content[0][3][1])/2
            if rectangle_dict['Director5_Name_Ch'][1][0]+300<content[0][0][0] and \
                rectangle_dict['Director5_Name_Ch'][1][1]-50<left_mid<rectangle_dict['Director5_Name_Ch'][2][1]+10:
                    content_dict['Director5_Name_Ch'] =[content[1][0]]
                             
            elif rectangle_dict['Director5_Address'][1][0]+200<content[0][0][0] and \
                rectangle_dict['Director5_Address'][0][1]-60<left_mid<rectangle_dict['Director5_Address'][0][1]+270:
                    content_dict['Director5_Address'] = content_dict['Director5_Address']+[content[1]]
                
        lis1_compare.append(content_dict['Director5_Address'].copy())
        content_dict['Director5_Address'] = []
            
            
        for content in result_en:
            left_mid = (content[0][0][1]+content[0][3][1])/2
            if rectangle_dict['Director5_Name_En'][1][0]+300<content[0][0][0] and \
                rectangle_dict['Director5_Name_En'][1][1]-50<left_mid<rectangle_dict['Director5_Name_En'][2][1]+160:
                    content_dict['Director5_Name_En'] =content_dict['Director5_Name_En']+[content[1][0]]
                
            elif rectangle_dict['Director5_Address'][1][0]+200<content[0][0][0] and \
                rectangle_dict['Director5_Address'][0][1]-60<left_mid<rectangle_dict['Director5_Address'][0][1]+270:
                    content_dict['Director5_Address'] = content_dict['Director5_Address']+[content[1]]
                
            elif rectangle_dict['Director5_Email'][1][0]+200<content[0][0][0] and \
                rectangle_dict['Director5_Email'][1][1]<left_mid<rectangle_dict['Director5_Email'][2][1]+50:
                    content_dict['Director5_Email'] = content_dict['Director5_Email']+[content[1][0]]
                
        lis1_compare.append(content_dict['Director5_Address'].copy())
        content_dict['Director5_Address'] = []
        chose_address('Director5_Address',lis1_compare,content_dict) 
    
            
        area_lis = []
        area_lis.append((1207,rectangle_dict['Director5_ID'][0][1]-32,1270,rectangle_dict['Director5_ID'][0][1]+35))
        area_lis.append((1330,rectangle_dict['Director5_ID'][0][1]-32,1400,rectangle_dict['Director5_ID'][0][1]+35))
                       
        for i in range(7):
            area_lis.append((1470+i*120,rectangle_dict['Director5_ID'][0][1]-32,1540+i*120,rectangle_dict['Director5_ID'][0][1]+35))
            
        print(area_lis)
        content_dict['Director5_ID'] = [read_ID(img_file_list[8]['file-name'],area_lis,img_file_list[8]['save_path'])]
        
    except:
        print('no this page')
        
    return content_dict    




if __name__ == "__main__":
    
    dir_dict = get_image_from_pdf(base_path,file_type)
    
    img_file_list = dir_dict['3. Lee Yuen Engineering & Supplies Co., Limited']['NAR1 Annual Return']
    img_file_list = dir_dict['1. JW INDUSTRIAL DEVELOPMENT LIMITED']['NAR1 Annual Return']
    img_file_list = dir_dict['4. EVER SUNNY LIMITED']['NAR1 Annual Return']
    img_file_list = dir_dict['6. UNION GROUP INTERNATIONAL COMPANY LIMITED']['NAR1 Annual Return']
    img_file_list = dir_dict['7. BEST PROFIT GROUP LIMITED']['NAR1 Annual Return']
    img_file_list = dir_dict['2. SEASON YACHTING LIMITED']['NNC1 - Incorporation Form']
    
    ocr_en = PaddleOCR(lang='en',det_model_dir='./ch_ppocr_server_v2.0_det_infer',det_db_box_thresh=0.01)
    ocr_tra = PaddleOCR(lang = 'chinese_cht',det_model_dir='./ch_ppocr_server_v2.0_det_infer',det_db_box_thresh=0.01)
    
    
    start = time.time()  
    x = extract_from_page1(ocr_en,ocr_tra,img_file_list,page_column)
    
    x = extract_from_page2(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page3(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page4(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page5(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page6(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page8(x,ocr_tra,img_file_list)
    
    x = extract_from_page9(x,ocr_en,ocr_tra,img_file_list)
    try:
        for key,value in x.items():
            x[key] = ' '.join(value)
    except:
        x[key] = value[0]
    
    print(time.time()-start)




   


# test = img_file_list[0]['save_path']+'/temp_img1.jpg'
# with open(test, 'rb') as f:
#     image = f.read()
# dddd = ddddocr.DdddOcr(old=True)
# ID_Number = dddd.classification(image)

# result1 = ocr_tra.ocr(img_file_list[0]['file-name'])    
# for line in result1:
#     print(line)
    
# result1 = ocr_en.ocr(img_file_list[0]['file-name'])
# for line in result1:
#     print(line)
    
# dddd = ddddocr.DdddOcr(old=True)
# with open('333.png', 'rb') as f:
#     image = f.read()

# for i in result1:
#     print(i)

# image = cv2.imread(img_file_list[0]['file-name'])
# amount_boxes = len(result1)
# for i in range(amount_boxes):
#         image = cv2.rectangle(image, (int(result1[i][0][0][0]), int(result1[i][0][0][1])), (int(result1[i][0][2][0]), int(result1[i][0][2][1])), (0,0,255), 2)
# cv2.imwrite('./box.jpg',image)


