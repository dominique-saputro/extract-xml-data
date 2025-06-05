import streamlit as st
import pandas as pd

with st.form('my_form'):
    st.write('Extract Errors')
    xml_string = st.text_area('XML STRING')
    err_string = st.text_area('ERROR LINES')
    submitted = st.form_submit_button('Run')

# Only process data if form is submitted and inputs are non-empty
if submitted and xml_string and err_string:
    xml_lines = xml_string.splitlines()
    err_lines = err_string.splitlines()
    nik = []

    try:
        for i in err_lines:
            x = int(i) - 2
            if 0 <= x < len(xml_lines):
                res_line = xml_lines[x]
                nik_string = res_line[22:38]
                nik.append(nik_string)
            else:
                nik.append("Line out of range")
    except Exception as e:
        st.error(f"An error occurred: {e}")

    df = pd.DataFrame(nik, columns=["Extracted NIK"])
    st.table(df)
else:
    st.write("Please submit the form to process data.")
