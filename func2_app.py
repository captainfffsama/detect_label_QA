# -*- coding: utf-8 -*-

# @Description:   用于统计bbox的准确度
# @Author: CaptainHu
# @Date: 2020-08-18 15:55:27
# @LastEditors: CaptainHu
import os
from glob import glob
import sys

import streamlit as st
import numpy as np


import utils
import SessionState as SS

state = SS.get()
state.add_attr('func2_app',{'answer_dir':'','pending_dir':'','xml_info_cache':{},'result':{}})

@st.cache
def show_describtion():
        readme_text='''
        输入目录的组织方式为：\n
        - 对于标准答案： 输入目录为xml的上一层目录 \n
        - 对于待查: 每人检查的xml单独存放一个目录，输入目录为每人目录的上一层目录 \n
        \n
        '''
        return readme_text


def get_xml_list_info(pc_file,anno_file) -> tuple:
    result_dict_pc={}
    for xml_path in pc_file:
        result_dict_pc[os.path.basename(xml_path)]=utils.parse_rec(xml_path)
    pending_result=get_pend_info(result_dict_pc)

    result_dict_an={}
    for xml_path in anno_file:
        result_dict_an[os.path.basename(xml_path)]=utils.parse_rec(xml_path)
    anno_result=get_anno_info(result_dict_an)
    return pending_result,anno_result

def get_pend_info(result_dict):
    xml_ids=[]
    class_ids=[]
    diff=[]
    bboxs=[]
    for xml_name,xml_rec in result_dict.items():
        for obj in xml_rec:
            xml_ids.append(xml_name)
            class_ids.append(obj['name'])
            diff.append(obj['difficult'])
            bboxs.append([float(x) for x in obj['bbox']])
    bboxs=np.array(bboxs).astype(float)
    return xml_ids,class_ids,diff,bboxs

def get_anno_info(result_dict):
    recs={}
    npos=0
    for xml_name,xml_rec in result_dict.items():
        bbox=np.array([x['bbox'] for x in xml_rec])
        difficult = np.array([x['difficult'] for x in xml_rec]).astype(np.bool)
        det=[False] *len(xml_rec)
        name=[x['name'] for x in xml_rec]
        npos=npos +sum(~difficult)
        recs[xml_name]={'bbox':bbox,
                        'difficult':difficult,
                        'name': name,
                        'det':det
        }
    return recs,npos

def count_result(anno_dir,pend_dir,ans_xmls_info,pend_xmls_info):
    cache_key=anno_dir+pend_dir
    if cache_key in state.func2_app['result'].keys():
        return state.func2_app['result'][cache_key]

    a_recs,a_npos=ans_xmls_info
    idxs=range(len(pend_xmls_info[0]))
    wrong_label=[] #框错了标签的
    unaccurate_box=[] #框的位置不准的
    surplus_box=[]#  多框的框
    no_diff=[]
    for xml_id,class_id,diff,bb,idx in zip(*pend_xmls_info,idxs):
        R=a_recs[xml_id]
        BBGT=R['bbox']
        ovmax = -np.inf
        if BBGT.size > 0:
            ixmin = np.maximum(BBGT[:, 0], bb[0])
            iymin = np.maximum(BBGT[:, 1], bb[1])
            ixmax = np.minimum(BBGT[:, 2], bb[2])
            iymax = np.minimum(BBGT[:, 3], bb[3])
            iw = np.maximum(ixmax - ixmin + 1., 0.)
            ih = np.maximum(iymax - iymin + 1., 0.)
            inters = iw * ih

            # union
            uni = ((bb[2] - bb[0] + 1.) * (bb[3] - bb[1] + 1.) +
                   (BBGT[:, 2] - BBGT[:, 0] + 1.) *
                   (BBGT[:, 3] - BBGT[:, 1] + 1.) - inters)

            overlaps = inters / uni
            ovmax = np.max(overlaps)
            jmax = np.argmax(overlaps)
            if R['name'][jmax] != class_id:
                wrong_label.append((xml_id,class_id,bb))
        else:
            st.error('{} have a zero area gt'.format(xml_id))
            raise ValueError()

        # 框准了
        if ovmax > 0.8:
            if not R['det'][jmax] and (R['name'] == class_id):
                R['det'][jmax]=True
                if R['difficult'][jmax] != diff:
                    no_diff.append((xml_id,class_id,bb))
            else:
                if R['name'] == class_id:
                    surplus_box.append((xml_id,class_id,bb))

        else:
            unaccurate_box.append((xml_id,class_id,bb))
    wl_rate=len(wrong_label)/len(idxs)
    ub_rate=len(unaccurate_box)/len(idxs)
    total_ans_bb_num=0
    no_det_bb_list=[]
    for ans_xml_id,ans_xml_info in a_recs.items():
        for idx,bb_result_flag in enumerate(ans_xml_info['det']):
            total_ans_bb_num +=1
            if not bb_result_flag:
                no_det_bb_list.append((ans_xml_id,ans_xml_info['bbox'][idx]))

    state.func2_app['result'][cache_key]=(wl_rate,wrong_label,ub_rate,unaccurate_box,surplus_box,no_diff,no_det_bb_list,len(no_det_bb_list)/total_ans_bb_num)
    return wl_rate,wrong_label,ub_rate,unaccurate_box,surplus_box,no_diff,no_det_bb_list,len(no_det_bb_list)/total_ans_bb_num


def get_common_file(pend_dir,anno_dir):
    pend_files=set([os.path.basename(x) for x in glob(os.path.join(pend_dir,'*.xml'))])
    anno_files=set([os.path.basename(x) for x in glob(os.path.join(anno_dir,'*.xml'))])
    comm_file=pend_files&anno_files
    pc_files=[]
    af_files=[]
    for file in comm_file:
        pc_files.append(os.path.join(pend_dir,file))
        af_files.append(os.path.join(anno_dir,file))
    return pc_files,af_files

def deal_one_sub_pend_dir(sub_pend_dir,anno_dir,placeholder_widget):
    cache_key=sub_pend_dir+anno_dir
    if cache_key in state.func2_app['result'].keys():
        return state.func2_app['result'][cache_key]
    sub_xml_dir=utils.get_son_dir(sub_pend_dir)
    pc_files,af_files=get_common_file(sub_xml_dir,anno_dir)
    if not pc_files:
        placeholder_widget.markdown("**在{} 下没有找到xml，请检查目录地址**".format(sub_xml_dir))
        sys.exit()
    if not af_files:
        placeholder_widget.markdown("**在{} 下没有找到xml，请检查目录地址**".format(anno_dir))
        sys.exit()

    pend_result,ann_result=get_xml_list_info(pc_files,af_files)
    result=count_result(anno_dir,sub_xml_dir,ann_result,pend_result)
    state.func2_app['result'][cache_key]=result
    return result

def show_result(result_dict) -> str:
    result_str=''
    for sub_dir,result in result_dict.items():
        result_str += ('------------------------\n'+ \
                       '{} 结果: \n  '.format(sub_dir)+ \
                       '- 错误标签比例：{} \n  '.format(result[0])+ \
                       '- 错误标签数量：{} \n  '.format(len(result[1]))+ \
                       '- 框的不准比例：{} \n  '.format(result[2])+ \
                       '- 框的不准数量：{} \n  '.format(len(result[3]))+ \
                       '- 可能多框的数量：{}\n  '.format(len(result[4]))+ \
                       '- 缺difficult的数量：{}\n  '.format(len(result[5])))
                    #    '- 缺框的数量：{} \n  '.format(len(result[6]))+ \
                    #    '- 缺框的比例：{} \n  '.format(result[7]))
    return result_str


def main():
    if st.checkbox("显示说明",value=True):
        st.markdown(show_describtion())
    state.func2_app['answer_dir'] = st.text_input("输入标准答案样本的目录",state.func2_app['answer_dir'])
    state.func2_app['pending_dir'] =st.text_input("输入待查答案样本的目录",state.func2_app['pending_dir'])
    show_widget = st.empty()
    if not (os.path.exists(state.func2_app['answer_dir']) and os.path.exists(state.func2_app['pending_dir'])):
        show_widget.warning('xml dir is not exist')
    else:
        show_widget.text('计算结果中！')
        print('current count dir is {}'.format(state.func2_app['pending_dir']))
        sub_pend_dirs=utils.get_sub_dir(state.func2_app['pending_dir'])
        print('sub_dir get done!',sub_pend_dirs)
        if not sub_pend_dirs:
            show_widget.text(' 待查目录子目录为空，请组织成正确的目录结构')
            st.stop()
        show_widget.text('获取子目录')
        result_dict={}

        ans_xml_dir=utils.get_son_dir(state.func2_app['answer_dir'])

        for sub_dir in sub_pend_dirs:
            print('count!!!!')
            show_widget.text('{}结果计算中'.format(sub_dir))
            result=deal_one_sub_pend_dir(sub_dir,ans_xml_dir,placeholder_widget=show_widget)
            result_dict[sub_dir]=result
        result_str=show_result(result_dict)
        show_widget.markdown(result_str)




