# -*- coding: utf-8 -*-

# @Description:
# @Author: CaptainHu
# @Date: 2020-08-18 16:00:13
# @LastEditors: CaptainHu

import os
import glob
import xml.etree.ElementTree as ET

import streamlit as st


def read_txt(txt_path:str) -> list:
    with open(txt_path,'r') as fr:
        content=fr.readlines()
    return [i.strip() for i in content]

def glob_file_path(file_dir:str,filter_='*.jpg') -> list:
    #遍历文件夹下所有的file
    if -1==filter_.find("*"):
        filter_="*"+filter_
    return glob.glob(os.path.join(file_dir,filter_))

def get_sub_dir(folder:str):
    if os.path.exists(folder):
        return [os.path.join(folder,x) for x in os.listdir(folder) if os.path.isdir(os.path.join(folder,x))]
    else:
        return []

def get_son_dir(folder:str):
    if os.path.exists(folder):
        return [os.path.join(folder,x) for x in os.listdir(folder) if os.path.isdir(os.path.join(folder,x))][0]
    else:
        return None,None

def parse_rec(filename):
    """Parse a PASCAL VOC xml file."""
    tree = ET.parse(filename)
    objects = []
    for obj in tree.findall('object'):
        obj_struct = {}
        obj_struct['name'] = obj.find('name').text
        obj_struct['pose'] = obj.find('pose').text
        obj_struct['truncated'] = int(obj.find('truncated').text)
        obj_struct['difficult'] = int(obj.find('difficult').text)
        bbox = obj.find('bndbox')
        obj_struct['bbox'] = [int(bbox.find('xmin').text),
                              int(bbox.find('ymin').text),
                              int(bbox.find('xmax').text),
                              int(bbox.find('ymax').text)]
        objects.append(obj_struct)

    return objects
