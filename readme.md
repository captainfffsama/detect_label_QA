# Install
```bash
conda env create -f environment.yaml
```

# Run
## 使用统计功能的话
```bash
conda activate check_img
streamlit run main_app.py
```

## 使用故意改错功能的话
直接修改`creat_wrong_label.py`的参数然后执行

## Todo：
- func2_app里的缓存清理存在没清干净的bug
- 后期若是拓展的话，需要优化缓存机制