"""
Vector Database Operations Page - v2 Redesign
3 Tabs: Manage Documents, Dashboard, Log History
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import re

from core.vector_operations import vector_db_operations
from utils.logger import get_logger
from ui.styles.vectordb_page import apply_vector_operations_styling
from config.departments_services import DEPARTMENTS_SERVICES, DOCUMENT_TYPES

from core.db_manager import (
    add_document,
    delete_document,
    get_documents_by_department_service,
    get_all_documents,
    get_all_services,
    get_services_by_department,
    get_document_count_for_service,
    add_service,
    upsert_service,
    update_service_status,
    log_action,
    get_all_logs,
    get_logs_by_department_service
)

logger = get_logger(__name__)


def _safe_key(name: str) -> str:
    """Create Streamlit-safe key from arbitrary name."""
    if not isinstance(name, str):
        name = str(name)
    return re.sub(r"[^0-9a-zA-Z_]", "_", name)


# ============================================================
# TAB 1: MANAGE DOCUMENTS
# ============================================================

def _show_manage_documents_tab():
    """Manage documents: 
    1. Select/Add Department
    2. Select/Add Service
    3. List & manage documents with upload option
    """
    st.subheader("📄 Manage Documents")
    
    # Show success message from previous upload if exists
    if st.session_state.get("upload_success_message"):
        st.balloons()
        st.success(st.session_state.upload_success_message)
        st.session_state.upload_success_message = None
    
    # Get all services
    all_services = get_all_services()
    departments = sorted(list(set([s["department"] for s in all_services])))
    
    if not departments:
        st.error("No departments found. Please initialize the system.")
        return
    
    # STEP 1: Department Selection
    st.markdown("### 🏢 Step 1: Select or Add Department")
    col_dept_sel, col_dept_add = st.columns([3, 1])
    
    with col_dept_sel:
        selected_dept = st.selectbox("Select Department", options=departments, key="manage_dept_select")
    
    with col_dept_add:
        if st.button("➕ Add New", key="btn_add_dept_new"):
            st.session_state.show_add_dept_form = True
    
    # Add department form
    if st.session_state.get("show_add_dept_form"):
        new_dept = st.text_input("Enter Department Name", key="new_dept_input")
        col_create, col_cancel = st.columns(2)
        with col_create:
            if st.button("✅ Create Department", key="btn_create_dept_confirm"):
                if new_dept.strip():
                    st.success(f"Department '{new_dept}' registered (add a service to activate)")
                    st.session_state.show_add_dept_form = False
                    st.session_state.new_custom_dept = new_dept
                else:
                    st.error("Department name cannot be empty")
        with col_cancel:
            if st.button("❌ Cancel", key="btn_cancel_dept"):
                st.session_state.show_add_dept_form = False
    
    # Use custom dept if just created
    if st.session_state.get("new_custom_dept"):
        selected_dept = st.session_state.new_custom_dept
    
    st.markdown("---")
    
    # STEP 2: Service Selection
    st.markdown("### 📌 Step 2: Select or Add Service")
    
    dept_services = get_services_by_department(selected_dept)
    service_names = sorted([s["service"] for s in dept_services])
    
    col_svc_sel, col_svc_add = st.columns([3, 1])
    
    with col_svc_sel:
        # Simple service selector (like department selection)
        if service_names:
            selected_service = st.selectbox(
                "Select Service",
                options=service_names,
                key="manage_service_select"
            )
        else:
            selected_service = None
            st.warning("No services available for this department. Please add one.")
    
    with col_svc_add:
        if st.button("➕ Add New", key="btn_add_svc_new"):
            st.session_state.show_add_svc_form = True
    
    # Add service form
    if st.session_state.get("show_add_svc_form"):
        new_service = st.text_input(f"Enter Service Name (for {selected_dept})", key="new_svc_input")
        col_create_svc, col_cancel_svc = st.columns(2)
        with col_create_svc:
            if st.button("✅ Create Service", key="btn_create_svc_confirm"):
                if new_service.strip():
                    try:
                        add_service(selected_dept, new_service)
                        st.success(f"Service '{new_service}' created (Inactive)")
                        st.session_state.show_add_svc_form = False
                        st.session_state.new_custom_service = new_service
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Service name cannot be empty")
        with col_cancel_svc:
            if st.button("❌ Cancel", key="btn_cancel_svc"):
                st.session_state.show_add_svc_form = False
    
    # Use custom service if just created
    if st.session_state.get("new_custom_service"):
        selected_service = st.session_state.new_custom_service
    
    st.markdown("---")
    
    # STEP 3: List Documents & Upload (only after dept AND service are selected)
    if selected_service:
        st.markdown(f"### 📚 Listing Documents in {selected_dept} → {selected_service}")
        
        docs = get_documents_by_department_service(selected_dept, selected_service)
        
        # List documents
        if docs:
            st.markdown(f"**Found {len(docs)} document(s)**")
            for i, doc in enumerate(docs, 1):
                col_doc, col_type, col_action = st.columns([3, 2, 1])
                with col_doc:
                    st.markdown(f"**{i}. {doc.get('filename', 'Unknown')}**")
                with col_type:
                    st.caption(f"Type: {doc.get('document_type', 'N/A')}")
                with col_action:
                    if st.button("🗑️", key=f"del_{_safe_key(doc.get('filename', ''))}_{i}"):
                        st.session_state[f"confirm_del_{_safe_key(doc.get('filename', ''))}_{i}"] = True
                
                # Confirm delete
                if st.session_state.get(f"confirm_del_{_safe_key(doc.get('filename', ''))}_{i}"):
                    st.warning(f"Delete {doc.get('filename', '')}?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Yes", key=f"yes_{_safe_key(doc.get('filename', ''))}_{i}"):
                            # Delete from Chroma
                            result = vector_db_operations.delete_document_by_filename(doc.get('filename'))
                            if result["success"]:
                                # Delete from Mongo
                                delete_document(doc.get('filename'))
                                # Log action
                                log_action(selected_dept, selected_service, doc.get('filename'), doc.get('document_type', 'Unknown'), "delete")
                                # Update service status if no docs remain
                                remaining = get_documents_by_department_service(selected_dept, selected_service)
                                if not remaining:
                                    update_service_status(selected_dept, selected_service, "Inactive")
                                st.success("Document deleted")
                                st.session_state.pop(f"confirm_del_{_safe_key(doc.get('filename', ''))}_{i}", None)
                                st.rerun()
                            else:
                                st.error(result.get("message", "Delete failed"))
                    with col_no:
                        if st.button("❌ No", key=f"no_{_safe_key(doc.get('filename', ''))}_{i}"):
                            st.session_state.pop(f"confirm_del_{_safe_key(doc.get('filename', ''))}_{i}", None)
                            st.rerun()
                
                st.divider()
        else:
            st.info("No documents in this service yet.")
        
        
        
        # Upload new documents (multiple files supported)
        st.markdown("##### ➕ Upload New Documents in service")
        uploaded_files = st.file_uploader(
            "Select one or more PDF files", 
            type=["pdf"], 
            accept_multiple_files=True,
            key=f"upload_pdf_{st.session_state.get('upload_counter', 0)}"
        )
        
        if uploaded_files:
            st.info(f"📂 {len(uploaded_files)} file(s) selected for upload")
            
            # Document type selection - individual for each file
            st.markdown("**📋 Select Document Type for Each File:**")
            
            doc_types_map = {}  # filename -> doc_type
            
            # Individual type selection for each file (always)
            for idx, file in enumerate(uploaded_files):
                st.markdown(f"**File {idx + 1}: {file.name}**")
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    type_choice = st.radio(
                        f"Type source for {file.name}", 
                        options=["Predefined", "Custom"], 
                        horizontal=True, 
                        key=f"individual_choice_{idx}_{st.session_state.get('upload_counter', 0)}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    if type_choice == "Predefined":
                        doc_types_map[file.name] = st.selectbox(
                            f"Select type", 
                            options=DOCUMENT_TYPES, 
                            key=f"individual_type_select_{idx}_{st.session_state.get('upload_counter', 0)}",
                            label_visibility="collapsed"
                        )
                    else:
                        doc_types_map[file.name] = st.text_input(
                            f"Enter custom type", 
                            placeholder="e.g., Standard Operating Procedure",
                            key=f"individual_type_custom_{idx}_{st.session_state.get('upload_counter', 0)}",
                            label_visibility="collapsed"
                        )
                
                st.divider()
            
            if st.button("🚀 Upload All Documents", type="primary", use_container_width=True, key=f"btn_upload_all_{st.session_state.get('upload_counter', 0)}"):
                # Validate all types are provided
                if not all(doc_types_map.values()):
                    st.error("❌ Please select or enter a document type for all files")
                else:
                    # Track upload results
                    upload_results = []
                    total_chunks = 0
                    progress_bar = st.progress(0)
                    status_container = st.container()
                    
                    for file_idx, uploaded_file in enumerate(uploaded_files):
                        doc_type = doc_types_map[uploaded_file.name]
                        
                        with status_container:
                            st.write(f"\n📄 **Uploading: {uploaded_file.name}** ({file_idx + 1}/{len(uploaded_files)})")
                        
                        try:
                            with st.spinner(f"Processing {uploaded_file.name}..."):
                                # STEP 1: Add to Chroma Vector DB (embedded, local)
                                st.write("  📍 Step 1/4: Uploading to Chroma Database...")
                                result = vector_db_operations.add_pdf_to_vectorstore(
                                    uploaded_file,
                                    uploaded_file.name,
                                    selected_dept,
                                    selected_service,
                                    doc_type
                                )
                                
                                if not result.get("success"):
                                    st.error(f"  ❌ Chroma upload failed: {result.get('message', 'Unknown error')}")
                                    logger.error(f"Chroma upload failed for {uploaded_file.name}: {result}")
                                    upload_results.append({
                                        "filename": uploaded_file.name,
                                        "success": False,
                                        "error": result.get('message', 'Unknown error')
                                    })
                                    continue
                                
                                chunks_added = result.get('chunks_added', 0)
                                total_chunks += chunks_added
                                logger.info(f"✅ Successfully added to Chroma: {uploaded_file.name} ({chunks_added} chunks)")
                                
                                # STEP 2: Add document metadata to MongoDB
                                st.write("  📍 Step 2/4: Saving document metadata...")
                                add_document(uploaded_file.name, selected_dept, selected_service, doc_type)
                                logger.info(f"✅ Document metadata saved to MongoDB: {uploaded_file.name}")
                                
                                # STEP 3: Update service status to Active (only once, but safe to repeat)
                                st.write("  📍 Step 3/4: Updating service status...")
                                upsert_service(selected_dept, selected_service, "Active")
                                logger.info(f"✅ Service status updated to Active: {selected_dept} → {selected_service}")
                                
                                # STEP 4: Log the action
                                st.write("  📍 Step 4/4: Recording audit log...")
                                log_action(selected_dept, selected_service, uploaded_file.name, doc_type, "upload")
                                logger.info(f"✅ Upload action logged: {uploaded_file.name}")
                                
                                st.success(f"  ✅ {uploaded_file.name} uploaded with {chunks_added} chunks")
                                
                                upload_results.append({
                                    "filename": uploaded_file.name,
                                    "success": True,
                                    "chunks": chunks_added,
                                    "type": doc_type
                                })
                                
                        except Exception as e:
                            logger.error(f"Error uploading {uploaded_file.name}: {e}", exc_info=True)
                            st.error(f"  ❌ Upload failed for {uploaded_file.name}: {str(e)}")
                            upload_results.append({
                                "filename": uploaded_file.name,
                                "success": False,
                                "error": str(e)
                            })
                        
                        # Update progress bar
                        progress_bar.progress((file_idx + 1) / len(uploaded_files))
                    
                    # Show summary
                    st.markdown("---")
                    successful = sum(1 for r in upload_results if r["success"])
                    failed = len(upload_results) - successful
                    
                    if successful > 0:
                        st.balloons()
                        st.success(
                            f"🎉 **Batch Upload Complete!**\n\n"
                            f"✅ Successfully Uploaded: **{successful}** files\n"
                            f"❌ Failed: **{failed}** files\n"
                            f"📊 Total Chunks Added: **{total_chunks}**\n\n"
                            f"🏢 Department: **{selected_dept}**\n"
                            f"📌 Service: **{selected_service}**\n\n"
                            f"📚 All documents are now ready for RAG queries!"
                        )
                    
                    if failed > 0:
                        st.warning(f"⚠️ {failed} file(s) failed to upload. Check details above.")
                    
                    # Increment counter to clear file uploader
                    if "upload_counter" not in st.session_state:
                        st.session_state.upload_counter = 0
                    st.session_state.upload_counter += 1
                    st.rerun()

    else:
        st.info("👆 Please select a department and service first to view and manage documents")



# ============================================================
# TAB 2: DASHBOARD
# ============================================================

def _show_dashboard_tab():
    """Dashboard with filters: department, service, status."""
    st.subheader("📊 Dashboard")
    
    all_services = get_all_services()
    
    if not all_services:
        st.error("No services found.")
        return
    
    # Filters
    col_dept, col_svc, col_status = st.columns(3)
    
    with col_dept:
        all_depts = sorted(list(set([s["department"] for s in all_services])))
        dept_filter = st.selectbox("🏢 Department", options=["All"] + all_depts, key="dash_dept_filter")
    
    with col_svc:
        if dept_filter == "All":
            all_svc_names = sorted(list(set([s["service"] for s in all_services])))
        else:
            all_svc_names = sorted([s["service"] for s in all_services if s["department"] == dept_filter])
        
        svc_search = st.text_input("🔍 Search Service", key="dash_svc_search", placeholder="Type to filter...")
        filtered_svc_names = [s for s in all_svc_names if svc_search.lower() in s.lower()] if svc_search else all_svc_names
    
    with col_status:
        status_filter = st.selectbox("📊 Status", options=["All", "Active", "Inactive"], key="dash_status_filter")
    
    st.markdown("---")
    
    # Build dashboard data
    rows = []
    for svc in all_services:
        dept = svc.get("department")
        service = svc.get("service")
        status = svc.get("status", "Inactive")
        last_updated = svc.get("last_updated")
        
        # Apply filters
        if dept_filter != "All" and dept != dept_filter:
            continue
        if svc_search and service not in filtered_svc_names:
            continue
        if status_filter != "All" and status != status_filter:
            continue
        
        # Get document count
        doc_count = get_document_count_for_service(dept, service)
        
        # Format last_updated
        if isinstance(last_updated, datetime):
            last_updated_str = last_updated.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_updated_str = str(last_updated) if last_updated else "—"
        
        rows.append({
            "Department": dept,
            "Service": service,
            "Document Count": doc_count,
            "Status": status,
            "Last Updated": last_updated_str
        })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No services match your filters.")

    
    st.markdown("---")
    
    # Build dashboard data
    rows = []
    for svc in all_services:
        dept = svc.get("department")
        service = svc.get("service")
        status = svc.get("status", "Inactive")
        last_updated = svc.get("last_updated")
        
        # Apply filters
        if dept_filter != "All" and dept != dept_filter:
            continue
        if svc_search and service not in filtered_svc_names:
            continue
        
        # Get document count
        doc_count = get_document_count_for_service(dept, service)
        
        # Format last_updated
        if isinstance(last_updated, datetime):
            last_updated_str = last_updated.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_updated_str = str(last_updated) if last_updated else "—"
        
        rows.append({
            "Department": dept,
            "Service": service,
            "Document Count": doc_count,
            "Status": status,
            "Last Updated": last_updated_str
        })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No services match your filters.")


# ============================================================
# TAB 3: LOG HISTORY
# ============================================================

def _show_log_history_tab():
    """Log history with dept/service filters."""
    st.subheader("📝 Log History")
    
    all_logs = get_all_logs()
    
    if not all_logs:
        st.info("No activity logs yet.")
        return
    
    # Filters
    col_dept, col_svc, col_action = st.columns(3)
    
    all_depts = sorted(list(set([l["department"] for l in all_logs])))
    with col_dept:
        dept_filter = st.selectbox("Department", options=["All"] + all_depts, key="log_dept_filter")
    
    if dept_filter == "All":
        all_svc_names = sorted(list(set([l["service"] for l in all_logs])))
    else:
        all_svc_names = sorted(list(set([l["service"] for l in all_logs if l["department"] == dept_filter])))
    
    with col_svc:
        svc_search = st.text_input("Search Service", key="log_svc_search")
        filtered_svc_names = [s for s in all_svc_names if svc_search.lower() in s.lower()] if svc_search else all_svc_names
    
    all_actions = sorted(list(set([l["action"] for l in all_logs])))
    with col_action:
        action_filter = st.selectbox("Action", options=["All"] + all_actions, key="log_action_filter")
    
    st.markdown("---")
    
    # Filter logs
    filtered_logs = []
    for log in all_logs:
        if dept_filter != "All" and log["department"] != dept_filter:
            continue
        if svc_search and log["service"] not in filtered_svc_names:
            continue
        if action_filter != "All" and log["action"] != action_filter:
            continue
        filtered_logs.append(log)
    
    if filtered_logs:
        df = pd.DataFrame(filtered_logs)
        
        # Format timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        st.dataframe(
            df[["timestamp", "department", "service", "document_name", "document_type", "action"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No logs match your filters.")


# ============================================================
# MAIN PAGE
# ============================================================

def show_vector_operations_page():
    """Main vector operations page."""
    apply_vector_operations_styling()
    
    if st.button("← Back to Chat", type="secondary"):
        st.session_state.current_page = "chat"
        st.rerun()
    
    st.title("🗄️ Vector Database Operations")
    st.markdown("---")
    
    # Stats
    stats = vector_db_operations.get_document_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 Total Files in Vector DB", stats.get("unique_files", 0))
    with col2:
        if stats.get("available"):
            st.success("✅ Vector store operational")
        else:
            st.error("❌ Vector store unavailable")
    
    st.markdown("---")
    
    # 3 Tabs
    tab1, tab2, tab3 = st.tabs(["📄 Manage Documents", "📊 Dashboard", "📝 Log History"])
    
    with tab1:
        _show_manage_documents_tab()
    
    with tab2:
        _show_dashboard_tab()
    
    with tab3:
        _show_log_history_tab()
