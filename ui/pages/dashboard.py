"""
Dashboard page for managing PDF documents
"""
import streamlit as st
from datetime import datetime
from core.vector_operations import vector_db_operations
from core.vector_store import vector_store_manager
from utils.logger import get_logger
import pandas as pd

logger = get_logger(__name__)

# Department list (40 departments)
DEPARTMENTS = [
    "",
    "Agricultural Marketing Department",
    "Agriculture Department",
    "Animal Resources Development Department",
    "Backward Classes Welfare Department",
    "CMO Department",
    "Consumer Affairs Department",
    "Co-operation Department",
    "Finance Department",
    "Fire & Emergency Services Department",
    "Fisheries Department",
    "Food Processing Ind. and Horticulture Department",
    "Food & Supplies Department",
    "Health & Family Welfare Department",
    "Higher Education Department",
    "Home & Hill Affairs Department",
    "Housing Department",
    "Information & Cultural Affairs Department",
    "Irrigation & Waterways Department",
    "Labour Department",
    "Land & Land Reforms and Refugee Relief & Rehabilitation",
    "Law Department",
    "Mass Education Extn. & Library Services",
    "Micro, Small & Medium Enterprises and Textiles Department",
    "Minority Affairs & Madrasah Education Department",
    "Panchayats & Rural Development Department",
    "Personnel & Administrative Reforms Department",
    "Power Department",
    "Public Health Engineering Department",
    "School Education Department",
    "Self-Help Group & Self- Employment Department",
    "Technical Education, Training & Skill Development Department",
    "Tourism Department",
    "Transport Department",
    "Tribal Development",
    "Urban Development and Municipal Affairs Department",
    "Urban Dev & ΜΑ",
    "Water Resources Investigation & Development Department",
    "West Bengal Forest Department",
    "Women & Child Development and Social Welfare Department",
    "Youth Services and Sports Department"
]

# Document types
DOC_TYPES = ["", "Manual", "Guidelines", "Required documents"]

# Service options (dummy strings)
SERVICES = [
    "",
    "Service 1",
    "Service 2",
    "Service 3",
    "Service 4",
    "Service 5",
    "Service 6",
    "Service 7",
    "Service 8",
    "Service 9",
    "Service 10"
]

def show_dashboard_page():
    """Main dashboard page."""
    # Initialize log in session state
    if "file_log" not in st.session_state:
        st.session_state.file_log = []
    
    # Header with back button and log section
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        if st.button("← Back to Chat", type="secondary"):
            st.session_state.current_page = "chat"
            st.rerun()
        st.title("📊 PDF Dashboard")
    
    with col_header2:
        _render_file_log()
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh", use_container_width=False):
        st.rerun()
    
    # Load PDFs from Chroma vector store
    with st.spinner("Loading PDFs from Chroma database..."):
        pdfs_data = get_all_pdfs_with_metadata()
    
    if not pdfs_data:
        st.info("📭 No PDFs found in the database.")
        st.markdown("💡 **Tip:** Upload PDFs from the Vector Database page to see them here.")
        return
    
    # Display the dashboard table
    display_dashboard_table(pdfs_data)

def _render_file_log():
    """Render file insertion/deletion log in top right corner."""
    st.subheader("📋 File Log")
    
    # Get recent logs (last 10)
    recent_logs = st.session_state.file_log[-10:] if st.session_state.file_log else []
    
    if not recent_logs:
        st.info("No file operations yet")
    else:
        # Display in reverse order (newest first)
        for log_entry in reversed(recent_logs):
            timestamp = log_entry.get("timestamp", "")
            action = log_entry.get("action", "")
            filename = log_entry.get("filename", "")
            
            if action == "inserted":
                st.success(f"✅ {timestamp}\n📄 {filename}")
            elif action == "deleted":
                st.error(f"❌ {timestamp}\n📄 {filename}")
            elif action == "modified":
                st.info(f"🔄 {timestamp}\n📄 {filename}")
    
    # Clear log button
    if st.button("Clear Log", use_container_width=True, key="clear_log"):
        st.session_state.file_log = []
        st.rerun()

def get_all_pdfs_with_metadata():
    """
    Retrieve all PDFs from Chroma with their metadata.
    
    Returns:
        List of dictionaries containing PDF information
    """
    try:
        if not vector_store_manager.is_available():
            logger.warning("Vector store not available.")
            st.error("Vector store is not available. Please check the connection.")
            return []
        
        # Get stats from Chroma
        stats = vector_store_manager.get_stats()
        
        if not stats.get("available") or stats.get("total_documents", 0) == 0:
            return []
        
        # Get all documents from Chroma collection
        all_docs = vector_store_manager.collection.get()
        
        # Extract unique PDFs with metadata
        pdfs_dict = {}
        
        if all_docs and all_docs.get('metadatas'):
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata and "filename" in metadata:
                    filename = metadata["filename"]
                    
                    # If we haven't seen this PDF before, create entry
                    if filename not in pdfs_dict:
                        pdfs_dict[filename] = {
                            "PDF Name": filename.replace('.pdf', '') if filename.endswith('.pdf') else filename,
                            "Department": metadata.get("department", ""),
                            "Service": metadata.get("service", ""),
                            "Type": metadata.get("document_type", ""),
                            "Description": metadata.get("description", ""),
                            "Status": metadata.get("status", "Active"),
                            "Date and Time": metadata.get("date_time", ""),
                            "filename": filename  # Keep original filename for updates
                        }
                    else:
                        # Update date_time if this chunk has a newer timestamp
                        chunk_date = metadata.get("date_time", "")
                        if chunk_date and chunk_date > pdfs_dict[filename]["Date and Time"]:
                            pdfs_dict[filename]["Date and Time"] = chunk_date
        
        # Convert to list and sort by PDF Name
        pdfs_list = list(pdfs_dict.values())
        pdfs_list.sort(key=lambda x: x["PDF Name"])
        
        return pdfs_list
        
    except Exception as e:
        logger.error(f"Error retrieving PDFs from Chroma: {e}")
        st.error(f"Failed to load PDFs: {str(e)}")
        return []

def display_dashboard_table(pdfs_data):
    """Display PDFs in a dashboard table with inline editing capabilities."""
    
    # Create DataFrame for display
    df = pd.DataFrame(pdfs_data)
    
    # Reorder columns for better display
    display_columns = ["PDF Name", "Department", "Service", "Type", "Description", 
                      "Status", "Date and Time"]
    df_display = df[display_columns].copy()
    
    st.subheader("📋 PDF Documents")
    st.markdown(f"**Total PDFs:** {len(df_display)}")
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search PDFs", placeholder="Search by PDF name, department, or service...")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
    
    # Apply filters
    if search_term:
        mask = (
            df_display["PDF Name"].str.contains(search_term, case=False, na=False) |
            df_display["Department"].str.contains(search_term, case=False, na=False) |
            df_display["Service"].str.contains(search_term, case=False, na=False)
        )
        df_display = df_display[mask]
    
    if status_filter != "All":
        df_display = df_display[df_display["Status"] == status_filter]
    
    st.markdown("---")
    
    # Display table with editing
    if len(df_display) == 0:
        st.info("No PDFs match your search criteria.")
        return
    
    # Create editable table using columns for each row
    # We'll display in a table format with editable fields
    
    # Table header with styling
    st.markdown("""
    <style>
    .dashboard-table {
        border-collapse: collapse;
        width: 100%;
    }
    .dashboard-header {
        background-color: #f0f0f0;
        font-weight: bold;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Table header
    header_cols = st.columns([2.5, 2.5, 2, 1.5, 2.5, 1, 1.8, 0.8])
    with header_cols[0]:
        st.markdown("**PDF Name**")
    with header_cols[1]:
        st.markdown("**Department**")
    with header_cols[2]:
        st.markdown("**Service**")
    with header_cols[3]:
        st.markdown("**Type**")
    with header_cols[4]:
        st.markdown("**Description**")
    with header_cols[5]:
        st.markdown("**Status**")
    with header_cols[6]:
        st.markdown("**Date and Time**")
    with header_cols[7]:
        st.markdown("**Action**")
    
    st.markdown("---")
    
    # Display each row with editable fields
    for idx, row in df_display.iterrows():
        # Find the original PDF data by matching filename
        filename = None
        original_pdf = None
        for pdf in pdfs_data:
            pdf_name = pdf["PDF Name"]
            if pdf_name == row['PDF Name']:
                filename = pdf["filename"]
                original_pdf = pdf
                break
        
        if not filename or not original_pdf:
            continue
        
        # Create columns for this row
        row_cols = st.columns([2.5, 2.5, 2, 1.5, 2.5, 1, 1.8, 0.8])
        
        with row_cols[0]:
            st.text(row['PDF Name'])
        
        with row_cols[1]:
            # Department dropdown
            dept_index = 0
            if row['Department']:
                try:
                    dept_index = DEPARTMENTS.index(row['Department'])
                except ValueError:
                    dept_index = 0
            department = st.selectbox(
                "",
                options=DEPARTMENTS,
                index=dept_index,
                key=f"dept_{filename}",
                label_visibility="collapsed"
            )
        
        with row_cols[2]:
            # Service dropdown
            service_index = 0
            if row['Service']:
                try:
                    service_index = SERVICES.index(row['Service'])
                except ValueError:
                    service_index = 0
            service = st.selectbox(
                "",
                options=SERVICES,
                index=service_index,
                key=f"service_{filename}",
                label_visibility="collapsed"
            )
        
        with row_cols[3]:
            # Type dropdown
            type_index = 0
            if row['Type']:
                try:
                    type_index = DOC_TYPES.index(row['Type'])
                except ValueError:
                    type_index = 0
            doc_type = st.selectbox(
                "",
                options=DOC_TYPES,
                index=type_index,
                key=f"type_{filename}",
                label_visibility="collapsed"
            )
        
        with row_cols[4]:
            # Description text input
            description = st.text_input(
                "",
                value=row['Description'],
                key=f"desc_{filename}",
                label_visibility="collapsed"
            )
        
        with row_cols[5]:
            # Status dropdown
            status_index = 0 if row['Status'] == "Active" else 1
            status = st.selectbox(
                "",
                options=["Active", "Inactive"],
                index=status_index,
                key=f"status_{filename}",
                label_visibility="collapsed"
            )
        
        with row_cols[6]:
            # Date and Time
            current_datetime = row['Date and Time'] if row['Date and Time'] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_time = st.text_input(
                "",
                value=current_datetime,
                key=f"datetime_{filename}",
                label_visibility="collapsed"
            )
        
        with row_cols[7]:
            # Save button
            if st.button("💾", key=f"save_{filename}", help="Save changes"):
                # Check if anything changed
                changed = (
                    department != original_pdf.get("Department", "") or
                    service != original_pdf.get("Service", "") or
                    doc_type != original_pdf.get("Type", "") or
                    description != original_pdf.get("Description", "") or
                    status != original_pdf.get("Status", "Active") or
                    date_time != original_pdf.get("Date and Time", "")
                )
                
                if changed:
                    # Update date_time to current time if changed
                    if date_time != original_pdf.get("Date and Time", ""):
                        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if update_pdf_metadata(filename, department, service, doc_type, description, status, date_time):
                        st.success("✅ Saved")
                        # Add to log
                        _add_to_log("modified", filename)
                        st.rerun()
                    else:
                        st.error("❌ Failed")
                else:
                    st.info("No changes")
        
        st.markdown("---")

def update_pdf_metadata(filename, department, service, doc_type, description, status, date_time):
    """
    Update metadata for all chunks of a PDF in Chroma.

    Args:
        filename: Original filename of the PDF
        department: Department name
        service: Service name
        doc_type: Document type
        description: Description
        status: Active/Inactive
        date_time: Date and time string
    """
    try:
        if not vector_store_manager.is_available():
            st.error("Vector store is not available.")
            return False

        collection = vector_store_manager.collection

        # Fetch all chunks matching filename
        try:
            results = collection.get(where={"filename": filename}, include=["ids", "metadatas", "documents"])
        except Exception as e:
            logger.error(f"Error querying Chroma collection: {e}")
            st.error("Failed to query Chroma for document chunks.")
            return False

        chunk_ids = results.get("ids", []) or []
        if not chunk_ids:
            st.warning(f"No chunks found for {filename}")
            return False

        # Prepare updated metadata (preserve existing values)
        metadatas = results.get("metadatas", []) or []
        updated_metadatas = []
        for meta in metadatas:
            existing = meta or {}
            merged = existing.copy()
            merged.update({
                "department": department,
                "service": service,
                "document_type": doc_type,
                "description": description,
                "status": status,
                "add_modify": "Modify",
                "date_time": date_time
            })
            updated_metadatas.append(merged)

        # Try metadata-only update first
        try:
            collection.update(ids=chunk_ids, metadatas=updated_metadatas)
            logger.info(f"Updated metadata for {len(chunk_ids)} chunks of {filename}")
            return True
        except Exception as update_err:
            logger.warning(f"Metadata-only update failed, trying upsert: {update_err}")

        # Fallback: upsert with documents if available
        documents = results.get("documents", []) or []
        if documents and len(documents) == len(chunk_ids):
            collection.upsert(ids=chunk_ids, documents=documents, metadatas=updated_metadatas)
            logger.info(f"Upserted metadata for {len(chunk_ids)} chunks of {filename}")
            return True

        st.error("Failed to update document metadata.")
        return False

    except Exception as e:
        logger.error(f"Error updating metadata for {filename}: {e}")
        st.error(f"Failed to update metadata: {str(e)}")
        return False


def _add_to_log(action, filename):
    """Add an entry to the file log."""
    if "file_log" not in st.session_state:
        st.session_state.file_log = []
    
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "filename": filename
    }
    st.session_state.file_log.append(log_entry)
    
    # Keep only last 50 entries
    if len(st.session_state.file_log) > 50:
        st.session_state.file_log = st.session_state.file_log[-50:]
