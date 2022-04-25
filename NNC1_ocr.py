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

page_column = ['Company Legal Name_eng','Company Legal Name_ch','Type of Company','Company Number','Business Registration Address','Email Address','Share Capital',
               'Founder1_Name_Ch','Founder1_Name_En','Founder1_Address','Founder1_capital','Founder2_Name_Ch','Founder2_Name_En','Founder2_Address','Founder2_capital',
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
    print('extract data from page 1')
    start_time = time.time()
    image = cv2.imread(img_file_list[0]['file-name'],cv2.IMREAD_GRAYSCALE)
    result_eng = ocr_en.ocr(image)
    result_ch = ocr_tra.ocr(image)  
    
    rectangle_dict['Company Legal Name_eng'] = [x[0] for x in result_ch if '英文名稱' in x[1][0]]
    rectangle_dict['Company Legal Name_ch'] = [x[0] for x in result_ch if '中文名稱' in x[1][0]]
    rectangle_dict['Company Number'] = [x[0] for x in result_ch if '編號' in x[1][0]]
    rectangle_dict['Type of Company'] = [x[0] for x in result_ch if '公司類別' in x[1][0]]
    rectangle_dict['Business Registration Address'] = [x[0] for x in result_ch if 'Regis' in x[1][0] and ' Office'in x[1][0]]    
    rectangle_dict['Email Address'] = [x[0] for x in result_ch if '電郵地址' in x[1][0]]
    
    compare_lis1 = []
    
    for content in result_eng:
        up_mid = (content[0][0][0]+content[0][1][0])/2
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Company Number'][0][0][0]<up_mid and rectangle_dict['Company Number'][0][2][1]<left_mid and \
            left_mid<rectangle_dict['Company Number'][0][2][1]+80:
                content_dict['Company Number'] = [content[1][0]]
        
        elif rectangle_dict['Company Legal Name_eng'][0][2][1]<left_mid<rectangle_dict['Company Legal Name_eng'][0][2][1]+265:
                content_dict['Company Legal Name_eng'] = content_dict['Company Legal Name_eng']+[content[1][0]]
                
        elif rectangle_dict['Business Registration Address'][0][2][1]<left_mid<rectangle_dict['Business Registration Address'][0][2][1]+325:
                content_dict['Business Registration Address'] = content_dict['Business Registration Address']+[content[1]]

        elif rectangle_dict['Email Address'][0][2][1]<left_mid<rectangle_dict['Email Address'][0][2][1]+140:
                content_dict['Email Address'] = content_dict['Email Address']+[content[1][0]]

    compare_lis1.append(content_dict['Business Registration Address'].copy())
    content_dict['Business Registration Address'] = []

    
    for content in result_ch:
        up_mid = (content[0][0][0]+content[0][1][0])/2
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Company Legal Name_ch'][0][2][1]<left_mid<rectangle_dict['Company Legal Name_ch'][0][2][1]+265:
                content_dict['Company Legal Name_ch'] = content_dict['Company Legal Name_ch']+[content[1][0]]
                    
        elif rectangle_dict['Business Registration Address'][0][2][1]<left_mid<rectangle_dict['Business Registration Address'][0][2][1]+325:
                 content_dict['Business Registration Address'] = content_dict['Business Registration Address']+[content[1]]
                 
    compare_lis1.append(content_dict['Business Registration Address'].copy())

    content_dict['Business Registration Address'] = []   

    chose_address('Business Registration Address',compare_lis1,content_dict)     
    
    type_lis = ['Private company','Public company']
    type_position1 = [x[0] for x in result_eng if 'Privat' in x[1][0]][0]
    type_position2 = [x[0] for x in result_eng if 'Publi' in x[1][0]][0]
    
    lis1 = [type_position1,type_position2]
    
    lis2 = []
    
    for i in lis1:
        left = int(i[0][0] + 5)
        right = int(i[0][0] + 65)
        up = int(i[0][1] + 5)
        bottom = int(i[0][1] + 50)
        
        image_cut = image[up:bottom,left:right]
        lis2.append(image_cut)
    
    for i,j in enumerate(lis2):
        cv2.imwrite('type_{}.jpg'.format(i),j)
    
    sum_pix = [x.sum() for x in lis2]   
    content_dict['Type of Company'] = [type_lis[i] for i,j in enumerate(sum_pix) if j == min(sum_pix)]

                
    return content_dict





def extract_from_page3(content_dict,ocr_en,ocr_tra,img_file_list):
    
    print('extract data from page 2')
    # print('page 1 time:{}'.format(time.time()-start_time))
    rectangle_dict = {}                   
    image = cv2.imread(img_file_list[2]['file-name'],1)
    result_en = ocr_en.ocr(image)
    result_ch = ocr_tra.ocr(image)
    
    lis1_compare = []
    lis2_compare = []

    # rectangle_dict['Secretary_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
    rectangle_dict['Founder1_Name_En'] = list(filter(lambda k: '英文姓名' in k[1][0], result_ch))[0][0]
    rectangle_dict['Founder1_Address'] = list(filter(lambda k: '地址' in k[1][0], result_ch))[0][0]
    rectangle_dict['Founder1_capital'] = list(filter(lambda k: '總值' in k[1][0], result_ch))[0][0]
   
    # rectangle_dict['Secretary_Cor_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[1][0]
    rectangle_dict['Founder2_Name_En'] = list(filter(lambda k: '英文姓名' in k[1][0], result_ch))[1][0]
    rectangle_dict['Founder2_Address'] = list(filter(lambda k: '地址' in k[1][0], result_ch))[1][0]
    rectangle_dict['Founder2_capital'] = list(filter(lambda k: '總值' in k[1][0], result_ch))[1][0]
    
    for content in result_ch:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if  rectangle_dict['Founder1_Name_En'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder1_Name_En'][1][1]-190<left_mid<rectangle_dict['Founder1_Name_En'][1][1]-40:
                content_dict['Founder1_Name_Ch'] =[content[1][0]]
                                          
        elif rectangle_dict['Founder2_Name_En'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder2_Name_En'][1][1]-190<left_mid<rectangle_dict['Founder2_Name_En'][1][1]-40:
                content_dict['Founder1_Name_Ch'] =[content[1][0]]
                
        elif rectangle_dict['Founder1_Address'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder1_Address'][1][1]-10<left_mid<rectangle_dict['Founder1_Address'][1][1]+255:
                content_dict['Founder1_Address'] = content_dict['Founder1_Address']+[content[1]]

        elif rectangle_dict['Founder2_Address'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder2_Address'][1][1]-10<left_mid<rectangle_dict['Founder2_Address'][1][1]+255:
                content_dict['Founder2_Address'] = content_dict['Founder2_Address']+[content[1]]
                
                
    # re.findall(r'[^\u4e00-\u9fa5]+',content[1][0])
    lis1_compare.append(content_dict['Founder1_Address'].copy())
    lis2_compare.append(content_dict['Founder2_Address'].copy())
    content_dict['Founder1_Address'] = []
    content_dict['Founder2_Address'] = []
                    

    for content in result_en:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Founder1_Name_En'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder1_Name_En'][1][1]-10<left_mid<rectangle_dict['Founder1_Name_En'][2][1]+215:
                content_dict['Founder1_Name_En'] = content_dict['Founder1_Name_En']+[content[1][0]]
              
        elif rectangle_dict['Founder1_Address'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder1_Address'][1][1]-10<left_mid<rectangle_dict['Founder1_Address'][1][1]+255:
                content_dict['Founder1_Address'] = content_dict['Founder1_Address']+[content[1]]

        elif rectangle_dict['Founder2_Name_En'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder2_Name_En'][1][1]-40<left_mid<rectangle_dict['Founder2_Name_En'][1][1]-190:
                content_dict['Founder2_Name_En'] =[content[1][0]]
                  
        elif rectangle_dict['Founder2_Address'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Founder2_Address'][1][1]-10<left_mid<rectangle_dict['Founder2_Address'][1][1]+255:
                content_dict['Founder2_Address'] = content_dict['Founder2_Address']+[content[1]]

        elif rectangle_dict['Founder1_capital'][1][0]+20<content[0][0][0]<rectangle_dict['Founder1_capital'][1][0]+400 and \
            rectangle_dict['Founder1_capital'][1][1]-20<left_mid<rectangle_dict['Founder1_capital'][1][1]+140:
                content_dict['Founder1_capital'] = content_dict['Founder1_capital']+[content[1][0]]
        
        elif rectangle_dict['Founder2_capital'][1][0]+20<content[0][0][0]<rectangle_dict['Founder2_capital'][1][0]+400 and \
            rectangle_dict['Founder2_capital'][1][1]-20<left_mid<rectangle_dict['Founder2_capital'][1][1]+140:
                content_dict['Founder2_capital'] = content_dict['Founder2_capital']+[content[1][0]]
 

    lis1_compare.append(content_dict['Founder1_Address'].copy())
    lis2_compare.append(content_dict['Founder2_Address'].copy())

    content_dict['Founder1_Address'] = []
    content_dict['Founder2_Address'] = []

    
######chose the highest conf between result_en and result_ch
    chose_address('Founder1_Address',lis1_compare,content_dict)
    chose_address('Founder2_Address',lis2_compare,content_dict)


    return content_dict


def extract_from_page4(content_dict, ocr_en, ocr_tra, img_file_list):
    print('extract data from page 4')
    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))
    result_en = ocr_en.ocr(img_file_list[3]['file-name'])
    result_ch = ocr_tra.ocr(img_file_list[3]['file-name'])

    lis1_compare = []
    lis2_compare = []

    # rectangle_dict['Secretary_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
    rectangle_dict['Secretary_Name_En'] = \
    list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[0][0]
    rectangle_dict['Secretary_Address'] = list(filter(lambda k: ('香港' in k[1][0]) and ('地址' in k[1][0]), result_ch))[0][
        0]
    rectangle_dict['Secretary_Email'] = list(filter(lambda k: ('電郵地址' in k[1][0]), result_ch))[0][0]
    rectangle_dict['Se1_right'] = list(filter(lambda k: ('姓氏' in k[1][0]), result_ch))[0][0]
    rectangle_dict['Secretary_ID'] = \
    list(filter(lambda k: ('Card' in k[1][0]) and ('Num' in k[1][0]), result_en))[0][0]

    # rectangle_dict['Secretary_Cor_Name_Ch'] = list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[1][0]
    rectangle_dict['Secretary_Cor_Name_En'] = \
    list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[1][0]
    rectangle_dict['Secretary_Cor_Address'] = \
    list(filter(lambda k: ('香港' in k[1][0]) and ('址' in k[1][0]), result_ch))[1][0]
    rectangle_dict['Secretary_Cor_Email'] = list(filter(lambda k: ('郵地址' in k[1][0]), result_ch))[1][0]

    for content in result_ch:
        left_mid = (content[0][0][1] + content[0][3][1]) / 2
        if rectangle_dict['Se1_right'][1][0] + 100 < content[0][0][0] and \
                rectangle_dict['Secretary_Name_En'][1][1] - 150 < left_mid < rectangle_dict['Secretary_Name_En'][1][
            1] - 60:
            content_dict['Secretary_Name_Ch'] = [content[1][0]]

        elif rectangle_dict['Secretary_Cor_Name_En'][1][0] + 200 < content[0][0][0] and \
                rectangle_dict['Secretary_Cor_Name_En'][1][1] - 170 < left_mid < \
                rectangle_dict['Secretary_Cor_Name_En'][1][1] - 60:
            content_dict['Secretary_Cor_Name_Ch'] = [content[1][0]]

        elif rectangle_dict['Secretary_Address'][1][0] + 50 < content[0][0][0] and \
                rectangle_dict['Secretary_Address'][1][1] < left_mid < rectangle_dict['Secretary_Email'][1][1] - 130:
            content_dict['Secretary_Address'] = content_dict['Secretary_Address'] + [content[1]]

        elif rectangle_dict['Secretary_Cor_Address'][1][0] + 50 < content[0][0][0] and \
                rectangle_dict['Secretary_Cor_Address'][1][1] - 20 < left_mid < \
                rectangle_dict['Secretary_Cor_Email'][1][1] - 130:
            content_dict['Secretary_Cor_Address'] = content_dict['Secretary_Cor_Address'] + [content[1]]
    # re.findall(r'[^\u4e00-\u9fa5]+',content[1][0])
    lis1_compare.append(content_dict['Secretary_Address'].copy())
    lis2_compare.append(content_dict['Secretary_Cor_Address'].copy())
    content_dict['Secretary_Address'] = []
    content_dict['Secretary_Cor_Address'] = []

    for content in result_en:
        left_mid = (content[0][0][1] + content[0][3][1]) / 2
        if rectangle_dict['Se1_right'][1][0] + 100 < content[0][0][0] and \
                rectangle_dict['Secretary_Name_En'][1][1] - 50 < left_mid < rectangle_dict['Secretary_Name_En'][2][
            1] + 110:
            content_dict['Secretary_Name_En'] = content_dict['Secretary_Name_En'] + [content[1][0]]

        elif rectangle_dict['Se1_right'][1][0] + 100 < content[0][0][0] and \
                rectangle_dict['Secretary_Email'][1][1] < left_mid < rectangle_dict['Secretary_Email'][2][1] + 50:
            content_dict['Secretary_Email'] = content_dict['Secretary_Email'] + [content[1][0]]

        elif rectangle_dict['Secretary_Address'][1][0] + 50 < content[0][0][0] and \
                rectangle_dict['Secretary_Address'][1][1] < left_mid < rectangle_dict['Secretary_Email'][1][1] - 130:
            content_dict['Secretary_Address'] = content_dict['Secretary_Address'] + [content[1]]

        elif rectangle_dict['Secretary_Cor_Address'][1][0] + 50 < content[0][0][0] and \
                rectangle_dict['Secretary_Cor_Address'][1][1] - 20 < left_mid < \
                rectangle_dict['Secretary_Cor_Email'][1][1] - 130:
            content_dict['Secretary_Cor_Address'] = content_dict['Secretary_Cor_Address'] + [content[1]]

        elif rectangle_dict['Secretary_Cor_Name_En'][1][0] + 200 < content[0][0][0] and \
                rectangle_dict['Secretary_Cor_Name_En'][1][1] - 50 < left_mid < \
                rectangle_dict['Secretary_Cor_Name_En'][2][1] + 25:
            content_dict['Secretary_Cor_Name_En'] = [content[1][0]]


        elif rectangle_dict['Secretary_Cor_Email'][1][0] + 200 < content[0][0][0] < \
                rectangle_dict['Secretary_Cor_Email'][1][0] + 1500 and \
                rectangle_dict['Secretary_Cor_Email'][1][1] < left_mid < rectangle_dict['Secretary_Cor_Email'][2][1] + 50:
            content_dict['Secretary_Cor_Email'] = content_dict['Secretary_Cor_Email'] + [content[1][0]]



    lis1_compare.append(content_dict['Secretary_Address'].copy())
    lis2_compare.append(content_dict['Secretary_Cor_Address'].copy())
    print(lis1_compare)
    print(lis2_compare)
    content_dict['Secretary_Address'] = []
    content_dict['Secretary_Cor_Address'] = []

    ######chose the highest conf between result_en and result_ch
    chose_address('Secretary_Address', lis1_compare, content_dict)
    chose_address('Secretary_Cor_Address', lis2_compare, content_dict)

    area_lis = []
    #####get ID if catch message from the ID area

    area_lis.append((rectangle_dict['Secretary_ID'][1][0] + 202, rectangle_dict['Secretary_ID'][0][1] - 32,
                         rectangle_dict['Secretary_ID'][1][0] + 282, rectangle_dict['Secretary_ID'][0][1] + 35))

    area_lis.append((rectangle_dict['Secretary_ID'][1][0] + 325, rectangle_dict['Secretary_ID'][0][1] - 32,
                         rectangle_dict['Secretary_ID'][1][0] + 405, rectangle_dict['Secretary_ID'][0][1] + 35))

    for i in range(7):
        area_lis.append(
            (rectangle_dict['Secretary_ID'][1][0] + 475 + i * 145, rectangle_dict['Secretary_ID'][0][1] - 32,
             rectangle_dict['Secretary_ID'][1][0] + 545 + i * 142, rectangle_dict['Secretary_ID'][0][1] + 35))

    content_dict['Secretary_ID'] = [read_ID(img_file_list[3]['file-name'], area_lis, img_file_list[3]['save_path'])]

    return content_dict




    
def extract_from_page5(content_dict, ocr_en, ocr_tra, img_file_list):
    print('extract data from page5')

    # content_dict = dict.fromkeys(page_column, [])
    # c_number_flag = False

    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))
    result_en = ocr_en.ocr(img_file_list[4]['file-name'])
    result_ch = ocr_tra.ocr(img_file_list[4]['file-name'])

    lis1_compare = []

    rectangle_dict['Director1_Name_Ch'] = \
    list(filter(lambda k: ('Name' in k[1][0]) and ('Chin' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director1_Name_En'] = \
    list(filter(lambda k: ('Name' in k[1][0]) and ('Engli' in k[1][0]), result_en))[0][0]
    rectangle_dict['Director1_Address'] = list(filter(lambda k: '住址' in k[1][0], result_ch))[0][0]
    rectangle_dict['Director1_Email'] = list(filter(lambda k: '電郵地址' in k[1][0], result_ch))[0][0]
    # rectangle_dict['Dir_right'] = list(filter(lambda k: '姓氏' in k[1][0],result_ch))[0][0]
    rectangle_dict['Director1_ID'] = \
    list(filter(lambda k: ('dentity' in k[1][0]) and ('Card' in k[1][0]), result_en))[0][0]

    for content in result_ch:
        left_mid = (content[0][0][1] + content[0][3][1]) / 2
        if rectangle_dict['Director1_Name_Ch'][1][0] + 300 < content[0][0][0] and \
                rectangle_dict['Director1_Name_Ch'][1][1] - 55 < left_mid < rectangle_dict['Director1_Name_Ch'][2][
            1] + 10:
            content_dict['Director1_Name_Ch'] = [content[1][0]]


        elif rectangle_dict['Director1_Address'][1][0] + 200 < content[0][0][0] and \
                rectangle_dict['Director1_Address'][0][1] < left_mid < rectangle_dict['Director1_Address'][0][1] + 320:
            content_dict['Director1_Address'] = content_dict['Director1_Address'] + [content[1]]

    lis1_compare.append(content_dict['Director1_Address'].copy())
    content_dict['Director1_Address'] = []

    for content in result_en:
        left_mid = (content[0][0][1] + content[0][3][1]) / 2
        if rectangle_dict['Director1_Name_En'][1][0] + 300 < content[0][0][0] and \
                rectangle_dict['Director1_Name_En'][1][1] - 50 < left_mid < rectangle_dict['Director1_Name_En'][2][
            1] + 290:
            content_dict['Director1_Name_En'] = content_dict['Director1_Name_En'] + [content[1][0]]

        elif rectangle_dict['Director1_Address'][1][0] + 200 < content[0][0][0] and \
                rectangle_dict['Director1_Address'][0][1] < left_mid < rectangle_dict['Director1_Address'][0][1] + 320:
            content_dict['Director1_Address'] = content_dict['Director1_Address'] + [content[1]]

        elif rectangle_dict['Director1_Email'][1][0] + 200 < content[0][0][0] and \
                rectangle_dict['Director1_Email'][1][1] < left_mid < rectangle_dict['Director1_Email'][2][1] + 50:
            content_dict['Director1_Email'] = content_dict['Director1_Email'] + [content[1][0]]

        elif rectangle_dict['Director1_ID'][1][0] + 200 < content[0][0][0] and \
                rectangle_dict['Director1_ID'][1][1] - 60 < left_mid < rectangle_dict['Director1_ID'][2][1]:
            content_dict['Director1_ID'] = content_dict['Director1_ID'] + [content[1][0]]

    lis1_compare.append(content_dict['Director1_Address'].copy())
    content_dict['Director1_Address'] = []
    chose_address('Director1_Address', lis1_compare, content_dict)

    area_lis = []
    area_lis.append((rectangle_dict['Director1_ID'][1][0] + 202, rectangle_dict['Director1_ID'][0][1] - 32,
                         rectangle_dict['Director1_ID'][1][0] + 282, rectangle_dict['Director1_ID'][0][1] + 35))

    area_lis.append((rectangle_dict['Director1_ID'][1][0] + 325, rectangle_dict['Director1_ID'][0][1] - 32,
                         rectangle_dict['Director1_ID'][1][0] + 405, rectangle_dict['Director1_ID'][0][1] + 35))

    for i in range(7):
        area_lis.append(
                (rectangle_dict['Director1_ID'][1][0] + 475 + i * 145, rectangle_dict['Director1_ID'][0][1] - 32,
                 rectangle_dict['Director1_ID'][1][0] + 545 + i * 142, rectangle_dict['Director1_ID'][0][1] + 35))

    content_dict['Director1_ID'] = [read_ID(img_file_list[4]['file-name'], area_lis, img_file_list[4]['save_path'])]

    return content_dict



def extract_from_page6(content_dict,ocr_en,ocr_tra,img_file_list):
    
    print('extract data from page6')
    rectangle_dict = {}
    # print('page 2 time:{}'.format(time.time()-start_time))  
    result_en = ocr_en.ocr(img_file_list[5]['file-name'])
    result_ch = ocr_tra.ocr(img_file_list[5]['file-name'])
    
    lis1_compare = []
    
    rectangle_dict['Director2_Name_En'] = [x[0] for x in result_ch if '英文名稱' in x[1][0]][0]
    rectangle_dict['Director2_Address'] = [x[0] for x in result_ch if '地址' in x[1][0]][0]
    rectangle_dict['Director2_Email'] = [x[0] for x in result_ch if '電郵地址' in x[1][0]][0]


    for content in result_ch:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director2_Name_En'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Director2_Name_En'][1][1]-280<left_mid<rectangle_dict['Director2_Name_En'][1][1]-50:
                content_dict['Director2_Name_Ch'] =[content[1][0]]
                      
        elif rectangle_dict['Director2_Address'][1][0]+50<content[0][0][0] and \
            rectangle_dict['Director2_Address'][0][1]-10<left_mid<rectangle_dict['Director2_Address'][0][1]+265:
                content_dict['Director2_Address'] = content_dict['Director2_Address']+[content[1]]
        
    lis1_compare.append(content_dict['Director2_Address'].copy())
    content_dict['Director2_Address'] = []
    
    
    for content in result_en:
        left_mid = (content[0][0][1]+content[0][3][1])/2
        if rectangle_dict['Director2_Name_En'][1][0]+150<content[0][0][0] and \
            rectangle_dict['Director2_Name_En'][1][1]<left_mid<rectangle_dict['Director2_Name_En'][1][1]+230:
                content_dict['Director2_Name_En']=content_dict['Director2_Name_En']+[content[1][0]]
        
        elif rectangle_dict['Director2_Address'][1][0]+50<content[0][0][0] and \
            rectangle_dict['Director2_Address'][0][1]-10<left_mid<rectangle_dict['Director2_Address'][0][1]+265:
                content_dict['Director2_Address'] = content_dict['Director2_Address']+[content[1]]
        
        elif rectangle_dict['Director2_Email'][1][0]+130<content[0][0][0] and \
            rectangle_dict['Director2_Email'][1][1]<left_mid<rectangle_dict['Director2_Email'][1][1]+90:
                content_dict['Director2_Email'] = content_dict['Director2_Email']+[content[1][0]]

    
    lis1_compare.append(content_dict['Director2_Address'].copy())
    content_dict['Director2_Address'] = []
    chose_address('Director2_Address',lis1_compare,content_dict) 
    
    return content_dict

    






if __name__ == "__main__":
    
    dir_dict = get_image_from_pdf(base_path,file_type)
    
    img_file_list = dir_dict['2. SEASON YACHTING LIMITED']['NNC1 - Incorporation Form']
    
    ocr_en = PaddleOCR(lang='en',det_model_dir='./ch_ppocr_server_v2.0_det_infer',det_db_box_thresh=0.01)
    ocr_tra = PaddleOCR(lang = 'chinese_cht',det_model_dir='./ch_ppocr_server_v2.0_det_infer',det_db_box_thresh=0.01)
    
    
    start = time.time()  
    x = extract_from_page1(ocr_en,ocr_tra,img_file_list,page_column)
    
    x = extract_from_page3(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page4(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page5(x,ocr_en,ocr_tra,img_file_list)
    
    x = extract_from_page6(x,ocr_en,ocr_tra,img_file_list)
    
    try:
        for key,value in x.items():
            x[key] = ' '.join(value)
    except:
        x[key] = value[0]
    
    print(time.time()-start)

    





