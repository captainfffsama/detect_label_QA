# -*- coding: utf-8 -*-

# @Description:
# @Author: CaptainHu
# @Date: 2020-08-18 15:54:13
# @LastEditors: CaptainHu

import os
from collections.abc import Sequence
import sys

import streamlit as st
import matplotlib.pyplot as plt

import utils
from SessionState import state

current_mod_name=sys.modules[__name__].__name__

state.add_attr(current_mod_name,{'answer_txt_dir':'','pending_txt_dir':''})

@st.cache(allow_output_mutation=True)
def _presistent_list():
    return []

_presis_list=_presistent_list()

@st.cache
def show_describtion():
        readme_text='''
        输入目录的组织方式为：\n
        - 对于标准答案txt： 输入目录为txt的上一层目录 \n
        - 对于待查txt: 每人检查的txt单独存放一个目录，输入目录为每人目录的上一层目录 \n
        程序将统计各个答案txt和待查txt中对的上的样本，并计算精确度，精确度计算方式如下：
        \n
        '''
        readme_text +=r'''$$
        presion=\frac{{answer}\bigcap{pending}}{answer}
        $$'''
        return readme_text

def get_one_person_result(pending_sub_dir):
    ans_txt_path=utils.glob_file_path(state.func1_app['answer_txt_dir'],filter_='*.txt')
    txt_content=get_txt_content(ans_txt_path,pending_sub_dir)
    bar_num,bar_bin_name=get_chart_data(txt_content,ans_txt_path)
    return bar_num,bar_bin_name

def get_txt_content(ans_txt_path_list:list,pending_txt_dir:str) -> list:
    txt_content=[]
    for a_txt_path in ans_txt_path_list:
        txt_name=os.path.basename(a_txt_path)
        p_txt_path=os.path.join(pending_txt_dir,txt_name)
        a_txt_content=utils.read_txt(a_txt_path)
        if os.path.exists(p_txt_path):
            p_txt_content=utils.read_txt(p_txt_path)
            txt_content.append((a_txt_content,p_txt_content))
        else:
            txt_content.append((a_txt_content,[]))
            st.warning("{}不存在，请检查".format(a_txt_path))
    return txt_content

@st.cache
def get_chart_data(txt_content,txt_path_list):
    txt_name_list=[os.path.basename(txt_path) for txt_path in txt_path_list]
    txt_content_len=[(len(a),len(p)) for a,p in txt_content]
    precision_list=[count_precision(a,p) for a,p in txt_content]
    bar_bin_name=[i+":"+str(j) for i,j in zip(txt_name_list,precision_list)]
    return txt_content_len,bar_bin_name

def count_precision(a,p):
    a_set=set(a)
    p_set=set(p)
    return len(a_set&p_set)/len(a_set)

def draw_bar(bar_num,bar_bin_name,bin_class:tuple,color:tuple):
    x =list(range(len(bar_num)))
    width = 1/(2*len(bar_num[0]))

    if isinstance(bar_num[0],Sequence) and not isinstance(bar_num[0],str):
        parallel_bin_num=len(bar_num[0])
        for i in range(parallel_bin_num):
            if parallel_bin_num//2 ==i:
                tick_label=bar_bin_name
            else:
                tick_label=None
            plt.bar(x,[j[i] for j in bar_num] , width=width, label=bin_class[i],tick_label = tick_label,fc = color[i])
            x=[j+width for j in x]
    else:
        plt.bar(x,bar_num, width=width, label=bin_class[0],tick_label = bar_bin_name,fc = color[0])

    plt.legend()

def main():
    state.re_init(current_mod_name)
    if st.checkbox("显示说明",value=True):
        st.markdown(show_describtion())
    state.func1_app['answer_txt_dir']= st.text_input("输入标准答案txt的目录",value=state.func1_app['answer_txt_dir'])
    state.func1_app['pending_txt_dir']=st.text_input("输入待查txt的目录",value=state.func1_app['pending_txt_dir'])
    if os.path.exists(state.func1_app['answer_txt_dir']) and os.path.exists(state.func1_app['pending_txt_dir']):
        sub_dir=utils.get_sub_dir(state.func1_app['pending_txt_dir'])
        if sub_dir:
            show_sub_dir_id=st.slider("",0,len(sub_dir))
            if len(sub_dir)==show_sub_dir_id:
                show_sub_dir_id=len(sub_dir)-1
            st.text("当前显示目录是{}".format(sub_dir[show_sub_dir_id]))
            draw_bar(*get_one_person_result(sub_dir[show_sub_dir_id]),('answer','pending'),('r','g'))
            st.pyplot()

        else:
            st.error('待测文件夹目录结构不对')
    else:
        st.error('txt 目录不存在，请检查')

