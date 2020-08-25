# -*- coding: utf-8 -*-

# @Description:   用于将xml故意改错
# @Author: LiuRui
# @Date: 2020-08-25 11:17:33
# @LastEditors: CaptainHu

import os
import xml.etree.ElementTree as ET
import random


def find_file(_filedir, pic_format='.jpg'):
    """
    获得所有图片的绝对路径
    :param _filedir: 待处理数据集的目录
    :param pic_format: 数据集中图片的格式
    :return:
    """
    dirlists = []
    filelist = os.listdir(_filedir)
    for file in filelist:
        if os.path.splitext(file)[1] == pic_format:
            dirname = _filedir + '/' + file
            dirlists.append(dirname)
    return dirlists


def whether_creat_wrong(probability):
    """
    根据概率判断是否进行改标签操作
    :param probability: 某种操作发生的概率值
    :return: bool值
    """
    dandom_num = random.random()
    if dandom_num < probability:
        return True
    else:
        return False


if __name__ == '__main__':
    DIRECTORY = 'D:/ProjectCode/creat_wrong_label/test-xiugai'  # 待处理数据的目录
    specified_number = 30        # 需要处理的图片数目
    delete_bbox_P = 0.5         # 删除label的概率
    change_bbox_name_P = 0.2    # 修改label名字的概率
    change_bbox_size_P = 1    # 改变bbox尺寸的概率
    dirlists = find_file(DIRECTORY)
    random.shuffle(dirlists)
    dirlists_to_process = dirlists[:specified_number]
    for img_dir in dirlists_to_process:
        xml_dir = os.path.splitext(img_dir)[0] + '.xml'
        tree = ET.parse(xml_dir)
        root = tree.getroot()
        object_ele = root.findall('object')
        img_width = int(root[3][0].text)
        img_higth = int(root[3][1].text)
        delete_list = []
        # 遍历每个object
        for i in range(len(object_ele)):
            # 删除label操作
            if whether_creat_wrong(delete_bbox_P):
                delete_list.append(i+4)
                # 防止所有的label都被删除
                if len(delete_list) == len(object_ele):
                    delete_list.pop(0)
            # 修改label名字操作
            elif whether_creat_wrong(change_bbox_name_P):
                label_name_lists = ['aqmzc', 'arm', 'gzzc', 'leg', 'wcaqm',
                                    'wcgz', 'wcgz', 'xy', 'yw_gkxfw']
                label_name = object_ele[i][0].text
                if label_name in label_name_lists:
                    label_name_lists.remove(label_name)
                    random.shuffle(label_name_lists)
                    new_label_name = label_name_lists[0]
                else:
                    new_label_name = 'new_label_name'
                object_ele[i][0].text = new_label_name  # 新的label_name
            # 改变bbox尺寸操作
            elif whether_creat_wrong(change_bbox_size_P):
                # 随机生成bbox尺寸改变的比例数
                change_radio = random.choice([random.uniform(0.4, 0.7),
                                              random.uniform(1.3, 2)])
                # change_radio = 1.5
                # 更新object的中bbox参数
                xmin = int(object_ele[i][4][0].text)
                ymin = int(object_ele[i][4][1].text)
                xmax = int(object_ele[i][4][2].text)
                ymax = int(object_ele[i][4][3].text)
                centre_point_x = (xmin + xmax) // 2
                centre_point_y = (ymin + ymax) // 2
                bbox_w = xmax - xmin
                bbox_h = ymax - ymin

                xmin_new = int(centre_point_x - bbox_w * change_radio * 0.5)
                ymin_new = int(centre_point_y - bbox_h * change_radio * 0.5)
                xmax_new = int(centre_point_x + bbox_w * change_radio * 0.5)
                ymax_new = int(centre_point_y + bbox_h * change_radio * 0.5)
                # 防止label的尺寸超过图片尺寸
                if xmax_new > img_width:
                    xmax_new = img_width
                if ymax_new > img_higth:
                    ymax_new = img_higth

                object_ele[i][4][0].text = str(xmin_new)
                object_ele[i][4][1].text = str(ymin_new)
                object_ele[i][4][2].text = str(xmax_new)
                object_ele[i][4][3].text = str(ymax_new)
        # 由于每次删除一个bbox，root中的object数目便会减一，因此下标也要更新
        obj_del = 0
        for index in delete_list:
            del root[index - obj_del]
            obj_del += 1

        tree.write(xml_dir, encoding="utf-8")
