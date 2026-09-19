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

st.title("🔐 AI Access Governance Agent")

st.write(
    "Upload a User Access Report and your Internal IAM / Access Policy. "
    "The AI agent will identify access governance risks and provide "
    "practical corrective actions."
)

st.info(
    "This tool supports IAM and IT audit reviews. "
    "Findings should be validated by the responsible business and security teams."
)


# =========================================================
# OPENAI CLIENT
# =========================================================
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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

st.header("1. Upload User Access Report")

access_file = st.file_uploader(
    "Upload Excel or CSV access report",
    type=["xlsx", "xls", "csv"]
)


st.header("2. Upload Internal IAM / Access Policy")

policy_file = st.file_uploader(
    "Upload your internal access policy",
    type=["pdf", "docx", "txt"]
)


# =========================================================
# ANALYSIS
# =========================================================

if access_file and policy_file:

    st.success("Both files uploaded successfully.")

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

        st.subheader("User Access Report")

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

                    st.header("📊 Detailed Access Governance Analysis")

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

                    st.header("📄 Management Report")

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