import streamlit as st
import pandas as pd
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)


# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="AI Access Governance Agent",
    page_icon="🔐",
    layout="wide"
)

# =========================================================
# VISUAL DESIGN
# =========================================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0b1020 0%, #111827 48%, #0b132b 100%);
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 2rem 2.2rem;
        border: 1px solid rgba(96, 165, 250, 0.28);
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.96), rgba(15, 23, 42, 0.90));
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        font-size: 2.65rem;
        margin: 0;
        color: #f8fafc;
        letter-spacing: -1px;
    }

    .hero p {
        color: #cbd5e1;
        font-size: 1.05rem;
        margin-top: 0.8rem;
        line-height: 1.6;
    }

    .badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: rgba(34, 197, 94, 0.13);
        border: 1px solid rgba(34, 197, 94, 0.35);
        color: #86efac;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    .section-card {
        padding: 1.25rem;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.20);
        background: rgba(15, 23, 42, 0.72);
        min-height: 150px;
    }

    .section-card h3 {
        color: #e2e8f0;
        margin-top: 0;
    }

    .section-card p {
        color: #94a3b8;
        font-size: 0.92rem;
    }

    .footer-note {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 2.5rem;
    }

    div[data-testid="stFileUploader"] {
        border: 1px dashed rgba(96, 165, 250, 0.55);
        border-radius: 14px;
        padding: 0.55rem;
        background: rgba(30, 41, 59, 0.45);
    }

    div.stButton > button {
        border-radius: 12px;
        font-weight: 700;
        padding: 0.7rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="badge">● IAM RISK INTELLIGENCE PLATFORM</div>
    <h1>🔐 GRC Sentinel AI</h1>
    <p>
        AI-powered access governance and risk analysis for IAM and IT audit reviews.
        Upload an access report and your internal policy to identify risks,
        assess alignment, and generate practical corrective actions.
    </p>
</div>
""", unsafe_allow_html=True)

st.info(
    "Use this tool as an audit-support assistant. All findings must be validated "
    "by the responsible business, IAM, and security teams before action is taken."
)


# =========================================================
# OPENAI CLIENT
# =========================================================
import os
from openai import OpenAI

# Prefer Streamlit Secrets in deployment; fall back to environment variables locally.
api_key = st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY is not configured. Add it in Streamlit Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# =========================================================
# READ POLICY FILE
# =========================================================

def read_policy_file(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):

        return uploaded_file.getvalue().decode(
            "utf-8",
            errors="ignore"
        )

    elif file_name.endswith(".docx"):

        document = Document(uploaded_file)

        paragraphs = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                paragraphs.append(paragraph.text)

        return "\n".join(paragraphs)

    elif file_name.endswith(".pdf"):

        reader = PdfReader(uploaded_file)

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n".join(pages)

    return ""


# =========================================================
# READ ACCESS REPORT
# =========================================================

def read_access_report(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):

        return pd.read_csv(uploaded_file)

    elif file_name.endswith(".xlsx"):

        return pd.read_excel(uploaded_file)

    elif file_name.endswith(".xls"):

        return pd.read_excel(uploaded_file)

    return None


# =========================================================
# CREATE PDF REPORT
# =========================================================

def create_pdf_report(summary_text, report_date):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        spaceAfter=6
    )

    story = []

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "AI ACCESS GOVERNANCE",
            title_style
        )
    )

    story.append(
        Paragraph(
            "IAM Risk & Corrective Action Report",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            f"Report Date: {report_date}",
            subtitle_style
        )
    )

    story.append(Spacer(1, 10))

    # -----------------------------------------------------
    # PROCESS AI SUMMARY
    # -----------------------------------------------------

    lines = summary_text.split("\n")

    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            story.append(Spacer(1, 5))
            continue

        # Remove markdown symbols
        clean_line = clean_line.replace("**", "")
        clean_line = clean_line.replace("###", "")
        clean_line = clean_line.replace("##", "")
        clean_line = clean_line.replace("#", "")

        # Section headings
        if (
            clean_line.upper().startswith("EXECUTIVE SUMMARY")
            or clean_line.upper().startswith("KEY FINDINGS")
            or clean_line.upper().startswith("HIGH")
            or clean_line.upper().startswith("CRITICAL")
            or clean_line.upper().startswith("CORRECTIVE ACTION")
            or clean_line.upper().startswith("MANAGEMENT SUMMARY")
            or clean_line.upper().startswith("BUSINESS IMPACT")
            or clean_line.upper().startswith("RISK")
        ):

            story.append(
                Paragraph(
                    clean_line,
                    heading_style
                )
            )

        else:

            # Convert basic markdown bullets
            if clean_line.startswith("- "):

                clean_line = "• " + clean_line[2:]

            story.append(
                Paragraph(
                    clean_line.replace("&", "&amp;"),
                    body_style
                )
            )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# FILE UPLOAD
# =========================================================

st.markdown("## 📥 Evidence Workspace")
st.caption("Provide the two evidence sources required for the access governance review.")

upload_col1, upload_col2 = st.columns(2, gap="large")

with upload_col1:
    st.markdown("""
    <div class="section-card">
        <h3>📊 User Access Report</h3>
        <p>Upload an Excel or CSV file containing user, role, application, and access information.</p>
    </div>
    """, unsafe_allow_html=True)
    access_file = st.file_uploader(
        "Choose access report",
        type=["xlsx", "xls", "csv"],
        key="access_report_uploader"
    )

with upload_col2:
    st.markdown("""
    <div class="section-card">
        <h3>📄 Internal IAM Policy</h3>
        <p>Upload the internal access policy that will be used as the control baseline.</p>
    </div>
    """, unsafe_allow_html=True)
    policy_file = st.file_uploader(
        "Choose IAM policy",
        type=["pdf", "docx", "txt"],
        key="iam_policy_uploader"
    )


# =========================================================
# ANALYSIS
# =========================================================

if access_file and policy_file:

    st.success("Evidence package received. Both files are ready for validation.")

    try:

        # -------------------------------------------------
        # READ ACCESS REPORT
        # -------------------------------------------------

        access_df = read_access_report(access_file)

        # -------------------------------------------------
        # READ POLICY
        # -------------------------------------------------

        policy_text = read_policy_file(policy_file)

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if access_df is None:

            st.error(
                "Unable to read the User Access Report."
            )

            st.stop()

        if not policy_text.strip():

            st.error(
                "Unable to extract text from the Internal IAM Policy."
            )

            st.stop()

        # -------------------------------------------------
        # DISPLAY ACCESS REPORT
        # -------------------------------------------------

        st.markdown("## 🔎 Evidence Preview")

        st.dataframe(
            access_df,
            width="stretch"
        )

        # Convert access report into text
        access_data = access_df.to_string(
            index=False
        )

        # -------------------------------------------------
        # ANALYZE BUTTON
        # -------------------------------------------------

        if st.button(
            "🔍 Analyze Access Governance",
            type="primary"
        ):

            with st.spinner(
                "AI is analyzing user access and identifying IAM risks..."
            ):

                prompt = f"""

You are an experienced IT Auditor and IAM / Access Governance
specialist.

Analyze the company's User Access Report against its Internal
IAM / Access Policy.

The objective is to identify access governance risks and provide
practical corrective actions.

==================================================
USER ACCESS REPORT
==================================================

{access_data}

==================================================
INTERNAL IAM / ACCESS POLICY
==================================================

{policy_text}

==================================================
IMPORTANT RULES
==================================================

1. Use ONLY the information provided.

2. Do not invent users, roles, applications, permissions,
   policy requirements or access.

3. If information is missing, clearly state:

Information Not Available

4. Do not assume that a finding represents a confirmed
   security incident.

5. Clearly distinguish between confirmed findings and
   potential risks.

6. Use simple language that can be understood by technical
   teams and business stakeholders.

7. Give immediate corrective actions for HIGH and CRITICAL
   risks.

==================================================
REQUIRED ANALYSIS
==================================================

# 1. ACCESS SUMMARY

Provide:

- Total number of users
- Applications identified
- Privileged users
- Administrator accounts
- Sensitive applications
- Users with multiple privileged roles
- Dormant accounts, if available
- Orphan accounts, if available
- Shared accounts, if available

# 2. IAM RISK FINDINGS

Identify:

- Excessive privileges
- Administrator access
- Privileged access
- Access inconsistent with job role
- Excessive application access
- Multiple privileged roles
- Dormant accounts
- Orphan accounts
- Shared accounts
- Segregation of Duties conflicts
- Sensitive application access
- Potential privilege escalation exposure
- Unusual access patterns

For EVERY finding provide:

Finding:
User / Account:
Job Role:
Application:
Assigned Access:
Expected Access:
Reason for Concern:
Evidence:
Risk Severity:

Use:

CRITICAL
HIGH
MEDIUM
LOW

# 3. INTERNAL POLICY ASSESSMENT

Compare user access against the uploaded Internal IAM Policy.

For each relevant requirement provide:

Policy Requirement:
Affected User / Account:
Observed Access:
Policy Expectation:
Assessment:
Evidence:
Recommended Action:

Use:

ALIGNED
NOT ALIGNED
PARTIALLY ALIGNED
REQUIRES VALIDATION
INFORMATION NOT AVAILABLE

Do not invent policy requirements.

# 4. PRIVILEGED ACCESS REVIEW

Specifically analyze:

- Administrator accounts
- Admin roles
- Privileged users
- Multiple privileged roles
- Users with more privileges than their apparent job requirement
- Users with access to sensitive systems

Explain the risk in simple language.

# 5. SEGREGATION OF DUTIES REVIEW

Look for combinations such as:

Request + Approve

Create Vendor + Approve Vendor

Create Payment + Approve Payment

Developer + Production Administrator

User Creation + User Approval

If information is unavailable, state:

Information Not Available

# 6. BUSINESS IMPACT

For HIGH and CRITICAL findings explain:

- What could go wrong?
- Who or what could be affected?
- Why does the issue matter to the business?

Possible impacts:

- Unauthorized access
- Data exposure
- Fraud
- Privilege escalation
- Unauthorized transactions
- Operational disruption
- Financial loss
- Reputational damage

Only mention impacts relevant to the actual finding.

# 7. IMMEDIATE CORRECTIVE ACTION

For every HIGH and CRITICAL finding provide:

Issue:
Immediate Action:
Responsible Team:
Priority:
Suggested Timeline:

# 8. MANAGEMENT SUMMARY

Provide a short management-friendly summary covering:

- Overall access governance observations
- Major IAM risks
- Privileged access concerns
- Policy gaps
- HIGH and CRITICAL findings
- Immediate actions required

==================================================
IMPORTANT FOR PDF SUMMARY
==================================================

After the detailed analysis, create a separate section called:

PDF EXECUTIVE SUMMARY

This section MUST be concise and suitable for a management report.

Include ONLY:

1. Overall Risk Summary

2. Key Findings

For each important finding:

Finding:
Severity:
Affected Account:
Risk:
Business Impact:

3. Corrective Actions

For each HIGH and CRITICAL issue:

Issue:
Corrective Action:
Priority:
Suggested Timeline:

4. Management Summary

Keep this PDF EXECUTIVE SUMMARY concise.

"""


                try:

                    # -------------------------------------------------
                    # AI CALL
                    # -------------------------------------------------

                    response = client.responses.create(
                        model="gpt-5.6-luna",
                        input=prompt
                    )

                    result = response.output_text

                    # -------------------------------------------------
                    # SHOW FULL ANALYSIS
                    # -------------------------------------------------

                    st.success(
                        "Access governance analysis completed."
                    )

                    st.markdown("## 📊 Access Governance Findings")

                    st.markdown(result)

                    # -------------------------------------------------
                    # FIND PDF EXECUTIVE SUMMARY
                    # -------------------------------------------------

                    pdf_marker = "PDF EXECUTIVE SUMMARY"

                    if pdf_marker in result:

                        pdf_summary = result.split(
                            pdf_marker,
                            1
                        )[1]

                    else:

                        # Fallback:
                        # use the full result if marker is missing
                        pdf_summary = result

                    # -------------------------------------------------
                    # CREATE PDF
                    # -------------------------------------------------

                    report_date = datetime.now().strftime(
                        "%d %B %Y"
                    )

                    pdf_bytes = create_pdf_report(
                        pdf_summary,
                        report_date
                    )

                    # -------------------------------------------------
                    # DOWNLOAD SECTION
                    # -------------------------------------------------

                    st.markdown("## 📄 Management Report")

                    st.write(
                        "A summarized PDF containing the key findings "
                        "and corrective actions is ready for download."
                    )

                    st.download_button(
                        label="📥 Download IAM Risk Report (PDF)",
                        data=pdf_bytes,
                        file_name="AI_Access_Governance_Risk_Report.pdf",
                        mime="application/pdf",
                        type="primary",
                        width="stretch"
                    )

                except Exception as e:

                    st.error(
                        f"AI analysis failed: {str(e)}"
                    )

    except Exception as e:

        st.error(
            f"File processing failed: {str(e)}"
        )


else:

    st.warning(
        "Please upload both the User Access Report "
        "and the Internal IAM Policy."
    )


st.markdown("""
<div class="footer-note">
    GRC Sentinel AI • IAM & Access Governance • Validate findings before taking action
</div>
""", unsafe_allow_html=True)
