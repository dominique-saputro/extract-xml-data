import streamlit as st
import pandas as pd

with st.form('my_form'):
    st.write('Extract Errors')
    xml_file = st.file_uploader('XML File')
    err_string = st.text_area('ERROR LINES')
    submitted = st.form_submit_button('Run')

# Only process data if form is submitted and inputs are non-empty
if submitted and xml_file and err_string:
    # Read the XML file
    xml_bytes = xml_file.read()
    xml_text = xml_bytes.decode('utf-8')
    xml_lines = xml_text.splitlines()
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
    st.write("Please upload an XML file and enter error lines to extract NIKs.")
