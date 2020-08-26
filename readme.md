# Install
```bash
conda env create -f environment.yaml
```

# Run
## 使用统计功能
```bash
conda activate check_img
streamlit run main_app.py
```

## 使用故意改错功能
直接修改`creat_wrong_label.py`的参数然后执行

## 使用提取答案的功能
extract_ansser.py脚本，具体用法参见脚本`main`函数的注释

## Todo：
- 后期若是拓展的话，需要优化缓存机制
- creat_wrong_label.py需要优化一下，没有改diffcult功能