# -*- coding: utf-8 -*-

# @Description:   用于统计bbox的准确度
# @Author: CaptainHu
# @Date: 2020-08-18 15:55:27
# @LastEditors: CaptainHu
from logging import PlaceHolder
import os
from glob import glob
import sys
from collections import defaultdict
from enum import Enum
import time

import streamlit as st
import numpy as np

import utils
from SessionState import state

current_mod_name=sys.modules[__name__].__name__

state.add_attr(current_mod_name,{'answer_dir':'', \
                            'pending_dir':'',\
                            'result':{}})

class SHOW_FLAG(Enum):
    ANNO='显示答案'
    PEND='显示待查'

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

@utils.cache(app_mod_name=current_mod_name,cache_dict_key='result')
def count_result(anno_dir:str,pend_dir:str,ans_xmls_info:tuple,pend_xmls_info:tuple,iou_thr:float,small_thr:tuple =None,ignore_small:bool=False):
    a_recs,a_npos=ans_xmls_info
    idxs=range(len(pend_xmls_info[0]))
    wrong_label=[] #框错了标签的
    unaccurate_box=[] #框的位置不准的
    surplus_box=[]#  多框的框
    ans_no_box=[] # 答案没有的框
    no_diff=[]
    for xml_id,class_id,diff,bb,idx in zip(*pend_xmls_info,idxs):
        current_iou_thr=iou_thr
        pend_xml_path=os.path.join(pend_dir,xml_id)
        anno_xml_path=os.path.join(anno_dir,xml_id)
        R=a_recs[xml_id]
        BBGT=R['bbox']
        ovmax = -np.inf
        if small_thr:
            if (bb[2]-bb[0])*(bb[3]-bb[1]) < small_thr[0]*small_thr[1]:
                if ignore_small:
                    continue
                else:
                    current_iou_thr=max(0.2,iou_thr-0.3)
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
        else:
            st.error('{} have a zero area gt'.format(xml_id))
            raise ValueError()

        # 框准了
        if ovmax >= current_iou_thr:
            if not R['det'][jmax]:
                if R['name'][jmax] == class_id:
                    R['det'][jmax]=True
                    if R['difficult'][jmax] != diff:
                        no_diff.append(((pend_xml_path,class_id,bb),(anno_xml_path,R['name'][jmax],BBGT[jmax])))
                else:
                    wrong_label.append(((pend_xml_path,class_id,bb),(anno_xml_path,R['name'][jmax],BBGT[jmax])))
            else:
                if R['name'][jmax]==class_id:
                    surplus_box.append(((pend_xml_path,class_id,bb),(anno_xml_path,R['name'][jmax],BBGT[jmax])))
                else:
                    wrong_label.append(((pend_xml_path,class_id,bb),(anno_xml_path,R['name'][jmax],BBGT[jmax])))
        elif current_iou_thr>ovmax>0:
            unaccurate_box.append(((pend_xml_path,class_id,bb),(anno_xml_path,R['name'][jmax],BBGT[jmax])))
        else:
            ans_no_box.append((pend_xml_path,class_id,bb))

    wl_rate=len(wrong_label)/len(idxs)
    ub_rate=len(unaccurate_box)/len(idxs)
    total_ans_bb_num=0
    no_det_bb_list=[]
    for ans_xml_id,ans_xml_info in a_recs.items():
        for idx,bb_result_flag in enumerate(ans_xml_info['det']):
            total_ans_bb_num +=1
            if not bb_result_flag:
                no_det_bb_list.append((ans_xml_id,ans_xml_info['bbox'][idx]))

    return wl_rate,wrong_label,ub_rate,unaccurate_box,surplus_box,no_diff,no_det_bb_list,len(no_det_bb_list)/total_ans_bb_num

def get_common_file(pend_dir,anno_dir):
    r'''获取答案目录和待测目录里相同名字的样本,即从待测样本里把参进去的答案找出来
    '''
    pend_files=set([os.path.basename(x) for x in glob(os.path.join(pend_dir,'*.xml'))])
    anno_files=set([os.path.basename(x) for x in glob(os.path.join(anno_dir,'*.xml'))])
    comm_file=pend_files&anno_files
    pc_files=[]
    af_files=[]
    for file in comm_file:
        pc_files.append(os.path.join(pend_dir,file))
        af_files.append(os.path.join(anno_dir,file))
    return pc_files,af_files

def deal_one_sub_pend_dir(sub_pend_dir,anno_dir,iou_thr:float,small_thr,ignore_small,placeholder_widget):
    sub_xml_dir=utils.get_son_dir(sub_pend_dir)
    placeholder_widget.text('{}  结果计算中'.format(sub_xml_dir))
    pc_files,af_files=get_common_file(sub_xml_dir,anno_dir)
    if not pc_files:
        placeholder_widget.markdown("**在{} 下没有找到xml，请检查目录地址**".format(sub_xml_dir))
        sys.exit()
    if not af_files:
        placeholder_widget.markdown("**在{} 下没有找到xml，请检查目录地址**".format(anno_dir))
        sys.exit()
    pend_result,ann_result=get_xml_list_info(pc_files,af_files)
    result=count_result(anno_dir,sub_xml_dir,ann_result,pend_result,iou_thr,small_thr,ignore_small)
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

def export_result(result_dict, save_dir):
    for check_person_dir_path,result in result_dict.items():
        person_name=check_person_dir_path.split(os.path.sep)[-1]
        p_save_dir=os.path.join(save_dir,person_name)
        if not os.path.exists(p_save_dir):
            os.mkdir(p_save_dir)
        _,wrong_label,_,unaccurate_box,_,_,_,_=result
        with open(os.path.join(p_save_dir,'wrong_label.txt'),'w') as fw:
            fw.writelines([x[0][0].replace('.xml','.jpg')+'\n' for x in wrong_label])
        with open(os.path.join(p_save_dir,'unaccurate_box'),'w') as fw:
            fw.writelines([x[0][0].replace('.xml','.jpg')+'\n' for x in unaccurate_box])

@utils.cache(app_mod_name=current_mod_name,cache_dict_key='show_result')
def deal_show_result(result:list) -> dict:
    r'''result是类似`count_result`结果中wrong_label的结果,转换成dict
        key是pend的图片的path,value是一个list,第一位是pend的obj list,
        第二位是anno的obj_list
    '''
    result_dict=defaultdict(lambda:([],[]))
    for pair_obj in result:
        pend_obj,anno_obj=pair_obj
        jpg_path=pend_obj[0].replace('.xml','.jpg')
        result_dict[jpg_path][0].append((pend_obj[1],*pend_obj[2].tolist()))
        result_dict[jpg_path][1].append((anno_obj[1],*anno_obj[2].tolist()))

    return result_dict

def show_pair_result(result_dict):
    if not result_dict:
        return None
    img_list=tuple(result_dict.keys())
    current_img_idx=st.slider(label='',min_value=0,max_value=len(img_list)-1,value=0,step=1,key=hash(repr(result_dict)))
    current_img_path=img_list[current_img_idx]
    current_show_flag=st.multiselect(label='',options=[SHOW_FLAG.ANNO.value,SHOW_FLAG.PEND.value],key=hash(repr(result_dict)))
    pend_obj,anno_obj=result_dict[current_img_path]
    if SHOW_FLAG.ANNO.value not in current_show_flag:
        anno_obj=None
    if SHOW_FLAG.PEND.value not in current_show_flag:
        pend_obj=None
    place_holder=st.empty()
    place_holder.info('正在拼命努力疯狂竭尽全力的绘制图片img......')
    fig=utils.draw_detec_pair_obj(current_img_path,ann_obj=anno_obj,pend_obj=pend_obj)
    place_holder.pyplot(fig)
    st.write('当前显示的图片:{}'.format(current_img_path),key=current_img_path)

def main():
    state.re_init(current_mod_name)
    if st.checkbox("显示说明",value=True):
        st.markdown(show_describtion())
    state.func2_app['answer_dir'] = st.text_input("输入标准答案样本的目录",state.func2_app['answer_dir'])
    state.func2_app['pending_dir'] =st.text_input("输入待查答案样本的目录",state.func2_app['pending_dir'])
    show_widget_1 = st.empty()
    if not (os.path.exists(state.func2_app['answer_dir']) and os.path.exists(state.func2_app['pending_dir'])):
        show_widget_1.warning('xml 目录不存在')
    else:
        small_thr=None
        ignore_small=False
        if st.checkbox('启用宽容小目标模式'):
            if st.checkbox('启用忽略小目标'):
                ignore_small=True
            st.markdown('''
            宽容小目标模式下,对于尺寸小于预设值的目标,在计算iou指标的时候会降低, \n
            具体计算方式是在当前阈值下-0.3 和0.2取最大值 \n
            若启用忽略小目标,那么小于尺寸的目标将不再考虑
            ''')
            w_small_thr=st.number_input('最小宽度',min_value=1,max_value=100,value=32,step=1)
            h_small_thr=st.number_input('最小高度',min_value=1,max_value=100,value=32,step=1)
            small_thr=(h_small_thr,w_small_thr)
        iou_thr=show_widget_1.slider('请选择IOU阈值:',min_value=0.0,max_value=1.0,value=0.5,step=0.1)

        show_widget_2=st.text('计算结果中！')
        print('current count dir is {}'.format(state.func2_app['pending_dir']))
        sub_pend_dirs=utils.get_sub_dir(state.func2_app['pending_dir'])
        print('sub_dir get done!',sub_pend_dirs)
        if not sub_pend_dirs:
            show_widget_2.text(' 待查目录子目录为空，请组织成正确的目录结构')
            st.stop()
        show_widget_2.text('获取子目录')
        result_dict={}

        ans_xml_dir=utils.get_son_dir(state.func2_app['answer_dir'])

        for sub_dir in sub_pend_dirs:
            print('count!!!!')
            show_widget_2.text('{}结果计算中'.format(sub_dir))
            result=deal_one_sub_pend_dir(sub_dir,ans_xml_dir,iou_thr,small_thr,ignore_small,placeholder_widget=show_widget_2)
            result_dict[sub_dir]=result
        result_str=show_result(result_dict)
        show_widget_2.markdown(result_str)
        # 显示图片
        if st.checkbox(' 是否绘制图片有问题的结果',value=False):
            persons={x.split(os.path.sep)[-1]:x for x in result_dict.keys()}
            current_preson=st.radio("当前显示结果的文件夹",tuple(persons.keys()))
            current_preson=persons[current_preson]
            _,wrong_labe_result,_,unaccurate_result,_,_,_,_=result_dict[current_preson]
            wl_show_dict=deal_show_result(wrong_labe_result)
            ua_show_dict=deal_show_result(unaccurate_result)
            st.header('显示错误标签的图片')
            show_pair_result(wl_show_dict)
            if repr(wl_show_dict) ==repr(ua_show_dict):
                st.text('错误标签和没框准的图片一样,这里不再显示没框准的图片')
            else:
                st.header('显示没框准的图片')
                show_pair_result(ua_show_dict)


        if st.checkbox('是否导出结果',value=True):
            save_dir=st.text_input(' 结果保存的目录')
            if os.path.exists(save_dir):
                export_result(result_dict,save_dir)
                st.write('导出完毕')




