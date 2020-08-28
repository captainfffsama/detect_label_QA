# -*- coding: utf-8 -*-

# @Description:
# @Author: CaptainHu
# @Date: 2020-08-18 16:00:13
# @LastEditors: CaptainHu

import os
import sys
import glob
import xml.etree.ElementTree as ET
from functools import wraps
from collections import defaultdict
import random

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import streamlit as st
import cv2

from SessionState import state

COLOR_DIC=mcolors.CSS4_COLORS

def get_color():
    return random.sample(COLOR_DIC.keys(),1)[0]

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

def parse_rec(filename) -> list:
    r"""
        分析xml文件
    """
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

def cache(*,app_mod_name:str,cache_dict_key:str,used:int=100):
    r'''缓存装饰器.若state没有app_mod_name这个属性,会给其添加这个属性,并初始化为一个字典.
        被装饰函数的结果会以传入参数的repr的hash作为key,存到state.app_mod_name[cache_dict_key][key]里
        每次执行被装饰函数前会检查缓存字典中是否存在这个值,存在就不再执行函数,而是直接返回值

        Args:
            app_mode_name:str
                一般是小的app的模块名称,可以由app的py中执行`sys.modules[__name__].__name__`得到.装饰器
                会尝试在缓存对象state中获取这个属性,若是没有,就创建

            cache_dict_key:str
                每次执行被装饰函数时,函数的结果应都缓存在这个键中

            used:int=100
                用于指示使用被装饰函数的前多少个参数的的repr作为hash.
    '''
    def deco(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            if not hasattr(state,app_mod_name):
                setattr(state,app_mod_name,{cache_dict_key:{}})
                print("Warning!!!state of {} does not init".format(app_mod_name))

            cache_attr=getattr(state,app_mod_name)
            if cache_dict_key not in cache_attr.keys():
                cache_attr[cache_dict_key]={}

            args_str=','.join([repr(x)[:100] for x in args[:used]])
            kwargs_value=list(kwargs.values())
            kwargs_str=','.join([repr(x)[:100] for x in kwargs_value[:used]])
            cache_key=hash(func.__name__+args_str+kwargs_str)
            if cache_key not in cache_attr[cache_dict_key]:
                cache_attr[cache_dict_key][cache_key]=func(*args,**kwargs)
            else:
                print('just use cache')
            return cache_attr[cache_dict_key][cache_key]
        return wrapper
    return deco

def draw_img(fig:'Figure',image:'np.ndarray',grid:'GridSpec',\
            title:str=None,no_ticks:bool=True,**kwargs) -> 'SubplotBase':
    if no_ticks:
        kwargs['xticks']=[]
        kwargs['yticks']=[]
    subplot=fig.add_subplot(grid,title=title,**kwargs)
    subplot.imshow(image)
    return subplot


def draw_obj(axes,obj_info,color:'Hex str') -> 'handles':
    if obj_info is None:
        return None
    rect=obj_info[-4:]
    rect=(rect[0],rect[1],rect[2]-rect[0],rect[3]-rect[1])
    patch_handle=axes.add_patch(patches.Rectangle(tuple(rect[:2]),rect[2],rect[3],fill=False,color=color))

    if 5==len(obj_info):
        label_info=obj_info[0]
        axes.text(rect[0], rect[1],label_info,c=color,
                style='italic', fontsize='xx-small',
                bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 0})
    return patch_handle

def draw_detec_pair_obj(img,ann_obj:list=None,pend_obj:list=None):
    if isinstance(img,str):
        img=cv2.imread(img,cv2.IMREAD_IGNORE_ORIENTATION|cv2.IMREAD_COLOR)
        img=img[:,:,::-1]

    fig=plt.figure()
    grid=plt.GridSpec(1,1)
    ax=draw_img(fig,img,grid[0,0])
    if ann_obj:
        color='LawnGreen'
        for obj in ann_obj:
            draw_obj(ax,obj,color)

    if pend_obj:
        color='LightCoral'
        for obj in pend_obj:
            draw_obj(ax,obj,color)

    return fig




