#!/usr/bin/env python3
"""
最简单的Streamlit测试
"""

import streamlit as st

st.title("🚀 DeepSeek A股交易系统测试")
st.write("如果你能看到这个页面，说明Streamlit工作正常！")

st.success("✅ 系统运行正常")

st.markdown("""
### 系统状态
- **股票数量**: 442只
- **覆盖率**: 98%
- **AI引擎**: DeepSeek
- **状态**: 就绪
""")

if st.button("测试按钮"):
    st.balloons()
    st.write("🎉 按钮点击成功！")