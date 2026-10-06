"""
Email Notification Service for Plan Uploads and Estimating Leads
Sends instant email alerts directly to seanray836@gmail.com
via FormSubmit (zero setup needed) and optional SMTP.
"""

import os
import smtplib
import json
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, List, Optional

DEFAULT_NOTIFICATION_EMAIL = "seanray836@gmail.com"


class EmailNotifier:
    """Manages outgoing email notifications for drawing uploads and new leads."""

    def __init__(self):
        self.notification_recipient = os.environ.get("NOTIFICATION_EMAIL", DEFAULT_NOTIFICATION_EMAIL)
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")

    def is_smtp_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_pass)

    def notify_plan_upload(
        self,
        files_info: List[Dict[str, Any]],
        state_dict: Dict[str, Any]
    ) -> bool:
        """Sends an email alert when a client uploads project drawings/plans."""
        if not files_info:
            return False

        filenames = [f.get("filename", "plan") for f in files_info]
        filenames_str = ", ".join(filenames)
        first_file = filenames[0]
        subject = f"🔔 NEW PLAN UPLOAD: {first_file} ({len(files_info)} file{'s' if len(files_info) > 1 else ''})"

        contractor_name = state_dict.get("name") or "Not provided yet"
        company = state_dict.get("company") or "Not provided yet"
        email = state_dict.get("email") or "Not provided yet"
        phone = state_dict.get("phone") or "Not provided yet"
        proj_type = state_dict.get("project_type") or "General Scope"
        trades = ", ".join(state_dict.get("trades", [])) or "To be reviewed"
        size = state_dict.get("square_footage") or "Unspecified"
        location = state_dict.get("project_location") or "Unspecified"
        bid_date = state_dict.get("bid_due_date") or "Standard (2–3 Days)"

        # Build file list HTML
        file_rows = ""
        file_text = ""
        for f in files_info:
            fn = f.get("filename", "")
            sz = f.get("size_kb", 0)
            sz_str = f"{round(sz / 1024, 2)} MB" if sz > 1024 else f"{sz} KB"
            dl_url = f.get("download_url", f"/api/download/{fn}")
            file_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #0284c7;">{fn}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{sz_str}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><a href="{dl_url}" style="background-color: #0284c7; color: #fff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">Download</a></td>
            </tr>
            """
            file_text += f"- {fn} ({sz_str})\n"

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #0f172a; color: #ffffff; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #38bdf8;">Estimation Service Chat Bot</h2>
                <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 14px;">Instant Plan Upload Notification</p>
            </div>
            
            <div style="padding: 24px; background-color: #f8fafc; color: #1e293b;">
                <div style="background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px;">
                    <strong style="color: #065f46;">A contractor has just uploaded drawings/plans to your chat bot!</strong>
                </div>

                <h3 style="border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 0;">Uploaded Drawing Files</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background-color: #f1f5f9; text-align: left;">
                            <th style="padding: 8px;">File Name</th>
                            <th style="padding: 8px;">Size</th>
                            <th style="padding: 8px;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {file_rows}
                    </tbody>
                </table>

                <h3 style="border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">Contractor & Project Scope</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold; width: 140px;">Contractor Name:</td>
                        <td style="padding: 6px 0;">{contractor_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Company:</td>
                        <td style="padding: 6px 0;">{company}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Email:</td>
                        <td style="padding: 6px 0;"><a href="mailto:{email}">{email}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Phone:</td>
                        <td style="padding: 6px 0;"><a href="tel:{phone}">{phone}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Project Type:</td>
                        <td style="padding: 6px 0;">{proj_type}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Identified Trades:</td>
                        <td style="padding: 6px 0; color: #0284c7; font-weight: bold;">{trades}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Location:</td>
                        <td style="padding: 6px 0;">{location}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Project Size:</td>
                        <td style="padding: 6px 0;">{size}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-weight: bold;">Bid Due Date:</td>
                        <td style="padding: 6px 0;">{bid_date}</td>
                    </tr>
                </table>

                <div style="margin-top: 25px; padding: 15px; background-color: #f1f5f9; border-radius: 6px; font-size: 13px; color: #64748b;">
                    <strong>Next Steps:</strong> Review the project scope and drawings to prepare a proposal. Standard turnaround time is 2–3 business days.
                </div>
            </div>
            
            <div style="background-color: #0f172a; color: #94a3b8; padding: 12px; text-align: center; font-size: 12px;">
                Estimation Service Chat Bot &bull; Direct Alert to {self.notification_recipient}
            </div>
        </div>
        """

        text_body = (
            f"NEW PLAN UPLOAD ALERT\n"
            f"=========================================\n"
            f"Files:\n{file_text}\n"
            f"Contractor: {contractor_name}\n"
            f"Company: {company}\n"
            f"Email: {email}\n"
            f"Phone: {phone}\n"
            f"Project Type: {proj_type}\n"
            f"Trades: {trades}\n"
            f"Location: {location}\n"
            f"Size: {size}\n"
            f"Bid Due Date: {bid_date}\n"
            f"=========================================\n"
        )

        first_file_path = files_info[0].get("path")
        return self._dispatch_notification(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            form_payload={
                "_subject": subject,
                "Contractor": contractor_name,
                "Company": company,
                "Email": email,
                "Phone": phone,
                "Uploaded_Plans": filenames_str,
                "Project_Type": proj_type,
                "Trades": trades,
                "Location": location,
                "Square_Footage": size,
                "Bid_Due_Date": bid_date
            },
            attachment_path=first_file_path,
            attachment_name=first_file
        )

    def notify_lead_submission(self, lead_record: Dict[str, Any]) -> bool:
        """Sends an email alert when a client submits their contact info / proposal form."""
        subject = f"📋 NEW ESTIMATING PROPOSAL LEAD: {lead_record.get('name', 'Contractor')}"
        summary_text = lead_record.get("summary_text", "")

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #0f172a; color: #ffffff; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: #38bdf8;">Estimation Service Chat Bot</h2>
                <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 14px;">New Estimating Proposal Lead</p>
            </div>
            
            <div style="padding: 24px; background-color: #f8fafc; color: #1e293b;">
                <pre style="background-color: #0f172a; color: #38bdf8; padding: 16px; border-radius: 6px; font-family: monospace; font-size: 13px; white-space: pre-wrap;">
{summary_text}
                </pre>
            </div>
        </div>
        """

        return self._dispatch_notification(
            subject=subject,
            html_body=html_body,
            text_body=summary_text,
            form_payload={
                "_subject": subject,
                "Lead_ID": lead_record.get("lead_id"),
                "Name": lead_record.get("name"),
                "Company": lead_record.get("company"),
                "Email": lead_record.get("email"),
                "Phone": lead_record.get("phone"),
                "Project_Type": lead_record.get("project_type"),
                "Trades": ", ".join(lead_record.get("trades", [])),
                "Location": lead_record.get("project_location"),
                "Square_Footage": lead_record.get("square_footage"),
                "Bid_Due_Date": lead_record.get("bid_due_date")
            }
        )

    def _dispatch_notification(
        self,
        subject: str,
        html_body: str,
        text_body: str,
        form_payload: Optional[Dict[str, Any]] = None,
        attachment_path: Optional[str] = None,
        attachment_name: Optional[str] = None
    ) -> bool:
        """Dispatches email via FormSubmit HTTP (zero-config direct email) and SMTP."""
        success = False

        # 1. Direct Webhook / FormSubmit Delivery (delivers to seanray836@gmail.com without needing password)
        try:
            payload = form_payload or {"_subject": subject, "message": text_body}
            payload["_captcha"] = "false"
            payload["_template"] = "table"
            encoded_data = urllib.parse.urlencode(payload).encode("utf-8")

            req = urllib.request.Request(
                f"https://formsubmit.co/ajax/{self.notification_recipient}",
                data=encoded_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Referer": "https://estimation-service-chatbot.vercel.app"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                resp_text = response.read().decode("utf-8")
                print(f"[EmailNotifier] Webhook response: {resp_text}")
                success = True
        except Exception as e:
            print(f"[EmailNotifier] Webhook delivery notice: {e}")

        # 2. Native SMTP Delivery if configured
        if self.is_smtp_configured():
            try:
                msg = MIMEMultipart("mixed")
                msg["Subject"] = subject
                msg["From"] = self.smtp_user
                msg["To"] = self.notification_recipient

                alt_part = MIMEMultipart("alternative")
                alt_part.attach(MIMEText(text_body, "plain", "utf-8"))
                alt_part.attach(MIMEText(html_body, "html", "utf-8"))
                msg.attach(alt_part)

                if attachment_path and os.path.exists(attachment_path):
                    if os.path.getsize(attachment_path) <= 15 * 1024 * 1024:
                        with open(attachment_path, "rb") as f:
                            part = MIMEApplication(f.read(), Name=attachment_name or os.path.basename(attachment_path))
                        part["Content-Disposition"] = f'attachment; filename="{attachment_name or os.path.basename(attachment_path)}"'
                        msg.attach(part)

                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.smtp_user, [self.notification_recipient], msg.as_string())

                print(f"[EmailNotifier] SMTP sent to {self.notification_recipient}: {subject}")
                success = True
            except Exception as e:
                print(f"[EmailNotifier] SMTP notice: {e}")

        return success


# Singleton instance
email_notifier = EmailNotifier()
