import streamlit as st
import pandas as pd

with st.form('my_form'):
   st.write('Extract Errors')
   xml_string = st.text_area('XML STRING')
   err_string = st.text_area('ERROR LINES')
   st.form_submit_button('Run')

xml_lines = xml_string.splitlines()
err_lines = err_string.splitlines()
nik = []
for i in err_lines:
   x = int(i)-2
   res_line = xml_lines[x]
   nik_string = res_line[22:38]
   nik.append(nik_string)

df = pd.DataFrame(
    nik, columns=("col %d" % i for i in range(1))
)

st.table(df)