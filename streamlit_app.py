import streamlit as st
import pandas as pd
from lxml import etree
from streamlit_gsheets import GSheetsConnection

st.title("Coretax Error Wizard")
xml_file = st.file_uploader("Upload your XML file", type="xml")
error_file = st.file_uploader("Upload your Excel error file", type=["xls","xlsx"])
master_type = st.segmented_control(
    "Master NITKU",
    options=['Excel','Google Sheet'],
    selection_mode="single",
)
if master_type:
    match master_type:
        case 'Excel':
            master_file = st.file_uploader('Excel File', type=['xlsx'])
        case 'Google Sheet':
            master_file = st.text_input('Google Sheet Link')


# Only process data if form is submitted and inputs are non-empty
if st.button('Run') and xml_file and error_file and master_file:
    # Read XML File
    xml_bytes = xml_file.read()
    xml_text = xml_bytes.decode('utf-8')
    xml_lines = xml_text.splitlines()
    
    root = etree.fromstring(xml_bytes)
    npwp = root.find("TIN").text
    # Read Error File
    xls = pd.ExcelFile(error_file)
    sheet_names = xls.sheet_names
    df_error = pd.read_excel(error_file,sheet_name=sheet_names[0])
    df_error.columns = ['line_no','remark','error_field']
    
    # Get all error lines
    error_lines = []
    for index,row in df_error.iterrows():
        if row['error_field'] == 'CounterpartTin':
            x = df_error['line_no'][index] - 1
            error_type = 'nik'
        elif row['error_field'] == 'IDPlaceOfBusinessActivityOfIncomeRecipient':
            x = df_error['line_no'][index] - 2
            error_type = 'nitku'
        res_line = xml_lines[x]
        error_string = res_line[22:38]
        error_lines.append({'nik': error_string,'type':error_type})
    # Sort by type and Delete duplicates of nitku and nik error
    df_error = pd.DataFrame(error_lines)
    df_error = df_error.sort_values(by='type', ascending=True)
    df_error = df_error.drop_duplicates(subset='nik', keep='first')
    
    # Split error data by type
    df_nik = df_error[df_error['type'] == 'nik'].reset_index(drop=True)
    df_nitku = df_error[df_error['type'] == 'nitku'].reset_index(drop=True)
    
    # For NIK error : Get Status & Gross from XML and remove from original XML
    manual_list = []
    tin_list = df_nik.iloc[:, 0].astype(str).str.strip().str.zfill(16)
    for tin in tin_list:
        for parent in root.xpath(".//*"):
            for bp21 in parent.findall("Bp21"):
                exist = bp21.findtext("CounterpartTin")
                if exist and exist.strip().zfill(16) == tin:
                    # Extract before removing
                    status = bp21.findtext("StatusTaxExemption")
                    gross = bp21.findtext("Gross")
                    manual_list.append({
                        "CounterpartTIN": tin,
                        "StatusTaxExemption": status,
                        "Gross": int(gross) if gross and gross.isdigit() else gross
                    })
                    # Remove the matching <Bp21> node from parent
                    parent = bp21.getparent()
                    parent.remove(bp21)
                    break  # Found and removed, stop inner loop
            else:
                continue
            break 
    if manual_list:
        st.divider()
        st.write("Manual Input:")
        st.success("Data extracted successfully!")
        dl_excel = pd.DataFrame(manual_list)
        dl_excel.to_excel('bp21_bulk.xlsx', index=False)
        with open("bp21_bulk.xlsx", "rb") as f:
                st.download_button("📊 Download XLSX", f, "bp21_bulk.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        # st.dataframe(manual_list)
    else:
        st.warning("No matching CounterpartTINs found.")
     
     
    # For NITKU error : Compare NITKU with master and replace with Master NITKU
    match master_type:
            case 'Excel':
                xls = pd.ExcelFile(master_file)
                df_master = pd.read_excel(master_file, sheet_name=xls.sheet_names[0])
            case 'Google Sheet':
                conn = st.connection("gsheets", type=GSheetsConnection)
                df_master = conn.read(spreadsheet=master_file,ttl=0)
                
    tin_list = df_nitku.iloc[:, 0].astype(str).str.strip().str.zfill(16)
    cols = list(df_master.columns)
    if len(cols) >= 2:
        cols[0] = 'nik'
        cols[1] = 'nitku'
    df_master.columns = cols
    df_master['nik'] = df_master['nik'].astype(str).str.strip().str.zfill(16)
    updated = 0
    for tin in tin_list:
        for bp21 in root.xpath(".//Bp21"):
            exist = bp21.findtext("CounterpartTin")
            if exist and exist.strip().zfill(16) == tin:
                # Replace existing NITKU with NITKU Master
                elem = bp21.find("IDPlaceOfBusinessActivityOfIncomeRecipient")
                found = df_master[df_master['nik'] == tin].reset_index(drop=True)
                # if elem and found:
                if not found.empty and elem is not None:
                    elem.text = found.loc[0, 'nitku']
                    updated += 1
                break  # Found and removed, stop inner loop
    if updated > 0:
        st.divider()
        st.write("Replace NITKU:")
        st.success(f'Updated {updated} records')
        NSMAP = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    
        # Root element with namespace and schema
        new_root = etree.Element(
            'Bp21Bulk',
            nsmap=NSMAP,
            attrib={
                '{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation': 'schema.xsd'
            }
        )
        
        # Add TIN
        tin_el = etree.SubElement(new_root, 'TIN')
        tin_el.text = npwp

        # List of Bp21
        list_of_bp21 = etree.SubElement(new_root, 'ListOfBp21')

        for bp21 in root.xpath(".//Bp21"):
            list_of_bp21.append(bp21)

        # Convert to XML string
        tree = etree.ElementTree(new_root)
        tree.write('bp21_no_nik_nitku_error.xml', pretty_print=True, xml_declaration=True, encoding='UTF-8')
        with open("bp21_no_nik_nitku_error.xml", "rb") as f:
            st.download_button("📄 Download XML", f, "bp21_no_nik_nitku_error.xml", mime="application/xml")
    else:
        st.warning("No NITKU records replaced.")   