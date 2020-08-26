# -*- coding: utf-8 -*-

# @Description: 从答案集里提取答案用于测试检查质量
# @Author: CaptainHu
# @Date: 2020-08-25 13:18:19
# @LastEditors: CaptainHu
import os
import glob
import random
import sys
from collections import defaultdict
import shutil

from tqdm import tqdm

def get_extract_list(jpg_list:list,num:int,txt_info_dict):
    r'''从存着jpg路径的list里提取出num个path，并提取出其txt的信息

        Args：
            jpg_list:list
                元素是jpg的完整路径
            num:int
                指示了需要提取出多少个样本
            txt_info_dict:dict
                key是txt的名称，v是一个list，里面存放了属于这一类的jpg的名称

        Returns：
            list：
                被提取出的样本的路径
            dict:
                格式同`txt_info_dict`
    '''
    extract_jpg_list=[]
    extract_txt_info_dict=defaultdict(list)
    for i in tqdm(range(num)):
        jpg_path=random.choice(jpg_list)
        extract_jpg_list.append(jpg_path)
        for k,v in txt_info_dict.items():
            if os.path.basename(jpg_path) in v:
                extract_txt_info_dict[k].append(os.path.basename(jpg_path))
    return extract_jpg_list,extract_txt_info_dict

def get_txt_info(answer_dataset_dir,txt_list):
    txt_info_dict={}
    txt_dir=os.path.normpath(answer_dataset_dir+os.sep+os.pardir)
    for txt_name in txt_list:
        with open(os.path.join(txt_dir,txt_name),'r') as fr:
            content=[x.strip() for x in fr.readlines()]
        txt_info_dict[txt_name]=set(content)
    return txt_info_dict

def save_result(save_dir,img_list,img_class_info_dict):
    print('copy img')
    img_save_dir=os.path.join(save_dir,'answer')
    if not os.path.exists(img_save_dir):
        os.mkdir(img_save_dir)
    for img_path in tqdm(img_list,total=len(img_list)):
        save_img_path=os.path.join(img_save_dir,os.path.basename(img_path))
        save_xml_path=save_img_path.replace('.jpg','.xml')


        shutil.copyfile(img_path,save_img_path)
        shutil.copyfile(img_path.replace('.jpg','.xml'),save_xml_path)

    for txt_name,txt_content in img_class_info_dict.items():
        txt_path=os.path.join(save_dir,txt_name)
        with open(txt_path,'w') as fw:
            fw.writelines([x+'\n' for x in txt_content])

def main(answer_dataset_dir,txt_name_list,save_dir,extract_num):
    r'''
        Args:
            answer_dataset_dir: str
                答案样本所在的目录，读取方式用的glob，所以不支持递归
            txt_name_list: list
                元素是txt的文件名，该txt中记录了被分类成本类样本的xml的文件名，所在路径应该是在
                `answer_dataset_dir`的上一层
            save_dir: str
                提取出来之后的答案样本的保存文件夹，需要事先创建好，提取出的答案放在该文件夹下的answer文件夹中
            extract_num: int
                提取多少张样本出来，数目要小于answer_dataset中样本数量(不小于也没必要提取了啊)。

    '''
    all_ans_jpg_list=glob.glob(os.path.join(answer_dataset_dir,'*.jpg'))
    txt_info_dict=get_txt_info(answer_dataset_dir,txt_name_list)

    if extract_num >= len(all_ans_jpg_list):
        print('Error: extract_num过大,{} 只有{}个样本'.format(answer_dataset_dir,len(all_ans_jpg_list)))
        sys.exit()
    extract_img_path_list,extract_img_class_info=get_extract_list(all_ans_jpg_list,extract_num,txt_info_dict)
    save_result(save_dir,extract_img_path_list,extract_img_class_info)
    print('save done')

if __name__ =='__main__':
    answer_dataset_dir='/home/chiebotgpuhq/Share/gpu-server/data/game/toDianKeYuan/only_about_person/have_check/answer'
    txt_name_list=['2.txt','3.txt']
    extract_num=50
    save_dir='/home/chiebotgpuhq/Share/gpu-server/data/game/toDianKeYuan/only_about_person/extract_answer/2'
    main(answer_dataset_dir,txt_name_list,save_dir,extract_num)