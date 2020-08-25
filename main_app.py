# -*- coding: utf-8 -*-

# @Description: 主启动器
# @Author: CaptainHu
# @Date: 2020-08-18 15:30:39
# @LastEditors: CaptainHu


import streamlit as st
import SessionState as SS

import func1_app as f1
import func2_app as f2



class WidgetsEnum(object):
    APP_FUNC1_FLAG="复核图片分类错误"
    APP_FUNC2_FLAG="复核图片标注错误"

@st.cache(allow_output_mutation=True)
def init_app_dict():
    app_func_dict_map={
        WidgetsEnum.APP_FUNC1_FLAG:f1.main,
        WidgetsEnum.APP_FUNC2_FLAG:f2.main
    }
    return app_func_dict_map

st.title("样本复核工具")
st.sidebar.title("样本复核工具")
program=st.sidebar.selectbox("请选择要使用的功能",(WidgetsEnum.APP_FUNC1_FLAG,WidgetsEnum.APP_FUNC2_FLAG))

if st.sidebar.button('清理缓存'):
    state=SS.get()
    print('main',id(state))
    state.re_init()
    st.sidebar.markdown('已尝试清理缓存')


init_app_dict()[program]()
