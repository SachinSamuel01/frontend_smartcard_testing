import streamlit as st
import requests
import json
import warnings
warnings.filterwarnings("ignore")

BASE_URL = "https://backend-smartcard.onrender.com"
# BASE_URL= "http://localhost:8000"

def main():
    st.title("PDF Collection Manager")

    # Upload PDF files and/or web links
    with st.form("upload_form", clear_on_submit=True):
        collection_name = st.text_input("Collection Name")
        uploaded_files = st.file_uploader("Upload PDFs", accept_multiple_files=True, type=["pdf",'csv'])
        web_links = st.text_area("Web Links (one per line)")
        upload_button = st.form_submit_button("Upload")

        if upload_button:
            if not collection_name:
                st.error("Collection name is required.")
            elif not uploaded_files and not web_links.strip():
                st.error("At least one PDF or web link is required.")
            else:
                files = [("files", (file.name, file, file.type)) for file in uploaded_files]
                links = "\n".join([link.strip() for link in web_links.split("\n") if link.strip()])

                
                
                data = {"name": collection_name, "links": links}
                json_data = json.dumps(data)

                response = requests.post(
                    f"{BASE_URL}/upload",
                    files=files,
                    data={"json_data": json_data}
                )
                if response.status_code == 200:
                    st.success(f"Files and links uploaded successfully to collection: {collection_name}")
                else:
                    st.error(f"Failed to upload files or links: {response.json().get('detail', 'Unknown error')}")

   

    response = requests.get(f"{BASE_URL}/collections")
    if response.status_code == 200:
        collections = response.json()
        for collection in collections:
            col_name = collection['name']
            st.write(f"**Collection Name:** {col_name}")

            col1, col2 = st.columns(2)
            with col1:
                deploy_button = st.button(f"Deploy {col_name}", key=f"deploy_{col_name}")
            with col2:
                delete_button = st.button(f"🗙 Delete {col_name}", key=f"delete_{col_name}")

            if deploy_button:
                response = requests.get(f"{BASE_URL}/collections/{col_name}/deploy")
                if response.status_code == 200:
                    st.session_state['current_collection'] = col_name
                    st.session_state['vector_db'] = response.json()['vector_db']
                    st.session_state['query_responses'] = []
                    st.session_state['page'] = 'query'
                    st.rerun()

            if delete_button:
                response = requests.delete(f"{BASE_URL}/collections/delete", json={"name": col_name})
                if response.status_code == 200:
                    st.success(response.json()["message"])
                    st.rerun()

    st.write("---")  # Separator
    st.title(f"Do not test the business card image write now")
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    
    if uploaded_image is not None:
        # files = {"image": uploaded_image.getvalue()}
        # files = [("files", (file.name, file, file.type)) for file in uploaded_files]
        file= {"image":(uploaded_image.name, uploaded_image, uploaded_image.type)}
        response = requests.post(f"{BASE_URL}/upload_image", files=file)
        if response.status_code == 200:
            st.session_state['card_details'] = st.session_state.get('card_details', []) + [response.json().get("response", "No response from backend")]  # Display the response from FastAPI
        else:
            st.error("Failed to upload image")
    for r in st.session_state.get('card_details', []):
        st.write(r)
        st.write("---")


def query_page():
    collection_name = st.session_state['current_collection']
    st.title(f"Query Collection: {collection_name}")

    st.write("### Previous Queries and Responses")
    for q, r in st.session_state['query_responses']:
        st.write(f"**Query:** {q}")
        st.write(f"**Response:** {r}")
        st.write("---")

    query = st.text_input("Enter your query", key="query_input")
    if st.button("Submit Query", key="submit_button"):
        # Send query to backend
        payload = {"query": query}
        response = requests.post(f"{BASE_URL}/query", json=payload)
        if response.status_code == 200:
            response_text = response.json().get("response", "No response from backend")
            st.session_state['query_responses'].append((query, response_text))
            st.rerun()
        else:
            st.error("Failed to get response from backend")

    if st.button("Back"):
        st.session_state['page'] = 'main'
        st.rerun()

if 'page' not in st.session_state:
    st.session_state['page'] = 'main'

if st.session_state['page'] == 'main':
    main()
else:
    query_page()