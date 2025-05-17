import os
import smtplib
import re
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, List, Optional, Union

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)

class EmailTool(Tool[Dict[str, Any]]):
    """Tool for sending emails and managing email templates."""
    
    name = "email"
    description = "Send emails and manage email templates"
    parameters = {
        "action": {
            "type": "string",
            "description": "The email action to perform ('send_email', 'send_template_email', 'get_template', 'save_draft')",
            "enum": ["send_email", "send_template_email", "get_template", "save_draft"]
        },
        "to": {
            "type": "string",
            "description": "Recipient email address(es), comma-separated for multiple recipients"
        },
        "subject": {
            "type": "string",
            "description": "Email subject line"
        },
        "body": {
            "type": "string",
            "description": "Email body content"
        },
        "cc": {
            "type": "string",
            "description": "Carbon copy recipients (comma-separated)"
        },
        "bcc": {
            "type": "string",
            "description": "Blind carbon copy recipients (comma-separated)"
        },
        "is_html": {
            "type": "boolean",
            "description": "Whether the email body contains HTML formatting",
            "default": False
        },
        "template_name": {
            "type": "string",
            "description": "Name of the email template to use"
        },
        "template_vars": {
            "type": "object",
            "description": "Variables to substitute in the template"
        },
        "draft_id": {
            "type": "string",
            "description": "Identifier for an email draft"
        },
        "draft_data": {
            "type": "object",
            "description": "Email draft data to store"
        }
    }
    required_params = ["action"]
    
    def __init__(self, **kwargs):
        """Initialize the email tool with optional configuration.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP authentication username
            password: SMTP authentication password
            default_sender: Default sender email address
            template_dir: Directory for email templates
            rate_limit: Maximum number of emails per day
        """
        super().__init__(**kwargs)
        
        # Get credentials from environment or config
        self.smtp_server = kwargs.get("smtp_server") or os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(kwargs.get("smtp_port") or os.getenv("EMAIL_SMTP_PORT", "587"))
        self.username = kwargs.get("username") or os.getenv("EMAIL_USERNAME")
        self.password = kwargs.get("password") or os.getenv("EMAIL_PASSWORD")
        self.default_sender = kwargs.get("default_sender") or self.username
        
        # Template directory
        self.template_dir = kwargs.get("template_dir") or os.getenv("EMAIL_TEMPLATE_DIR", "./email_templates")
        
        # Rate limiting
        self.rate_limit = kwargs.get("rate_limit", 50)  # Default 50 emails per day
        self.sent_count = 0
        
        # Draft storage (in-memory for simplicity)
        self.drafts = {}
        
        # Load templates
        self.templates = {}
        self._load_templates()
        
    def _load_templates(self):
        """Load email templates from the template directory."""
        if self.template_dir and os.path.exists(self.template_dir):
            try:
                for filename in os.listdir(self.template_dir):
                    if filename.endswith('.html') or filename.endswith('.txt'):
                        name = os.path.splitext(filename)[0]
                        with open(os.path.join(self.template_dir, filename), 'r') as f:
                            self.templates[name] = f.read()
                logger.info(f"Loaded {len(self.templates)} email templates from {self.template_dir}")
            except Exception as e:
                logger.error(f"Error loading email templates: {e}")
        else:
            if self.template_dir:
                logger.warning(f"Email template directory not found: {self.template_dir}")
    
    def validate_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _parse_email_list(self, emails: str) -> List[str]:
        """Parse comma-separated email addresses into a list."""
        if not emails:
            return []
        email_list = [email.strip() for email in emails.split(',')]
        return email_list
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Run the email tool with the specified action."""
        action = kwargs.pop('action', 'send_email')
        
        if action == 'send_email':
            return self._send_email(**kwargs)
        elif action == 'send_template_email':
            return self._send_template_email(**kwargs)
        elif action == 'get_template':
            return self._get_template(**kwargs)
        elif action == 'save_draft':
            return self._save_draft(**kwargs)
        else:
            return {
                "status": "error", 
                "message": f"Unknown action: {action}"
            }
    
    def _send_email(self, 
                   to: str, 
                   subject: str = "", 
                   body: str = "", 
                   cc: str = None,
                   bcc: str = None,
                   is_html: bool = False) -> Dict[str, Any]:
        """
        Send an email to the specified recipients.
        
        Args:
            to: Comma-separated recipient email address(es)
            subject: Email subject
            body: Email body content
            cc: Comma-separated carbon copy recipient(s)
            bcc: Comma-separated blind carbon copy recipient(s)
            is_html: Whether the body content is HTML
            
        Returns:
            Dict containing status and message
        """
        # Check for required credentials
        if not self.username or not self.password:
            return {
                "status": "error",
                "message": "Email credentials not configured. Please set EMAIL_USERNAME and EMAIL_PASSWORD environment variables."
            }
        
        # Check rate limit
        if self.sent_count >= self.rate_limit:
            return {"status": "error", "message": "Daily email limit reached"}
        
        # Parse email addresses
        to_list = self._parse_email_list(to)
        cc_list = self._parse_email_list(cc) if cc else []
        bcc_list = self._parse_email_list(bcc) if bcc else []
        
        # Validate email addresses
        all_recipients = to_list + cc_list + bcc_list
        for email in all_recipients:
            if not self.validate_email(email):
                return {"status": "error", "message": f"Invalid email address: {email}"}
        
        # Prepare message
        msg = MIMEMultipart()
        msg['From'] = self.default_sender
        msg['To'] = ', '.join(to_list)
        msg['Subject'] = subject
        
        # Add CC if present
        if cc_list:
            msg['Cc'] = ', '.join(cc_list)
        
        # Attach body
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
        
        # Create combined recipient list
        recipients = to_list + cc_list + bcc_list
        
        # Validate that we have at least one recipient
        if not recipients:
            return {"status": "error", "message": "No valid recipients specified"}
            
        # Send email
        try:
            self.logger.info(f"Sending email to {len(recipients)} recipients with subject: {subject}")
            
            # For safety in development/testing, log but don't actually send
            # REMOVE THIS CONDITION FOR PRODUCTION USE
            if os.getenv("EMAIL_DRY_RUN") == "true":
                self.logger.info("DRY RUN MODE: Email would be sent to: " + ", ".join(recipients))
                return {
                    "status": "success", 
                    "message": "[DRY RUN] Email would be sent successfully",
                    "recipients": recipients,
                    "subject": subject
                }
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                self.sent_count += 1
                
                self.logger.info(f"Email sent successfully to {len(recipients)} recipients")
                return {
                    "status": "success", 
                    "message": "Email sent successfully",
                    "recipients": recipients,
                    "subject": subject
                }
                
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return {"status": "error", "message": f"Failed to send email: {str(e)}"}
    
    def _get_template(self, template_name: str) -> Dict[str, Any]:
        """Get an email template by name."""
        template = self.templates.get(template_name)
        if template:
            return {
                "status": "success",
                "template": template,
                "template_name": template_name
            }
        else:
            available_templates = list(self.templates.keys())
            return {
                "status": "error", 
                "message": f"Template '{template_name}' not found",
                "available_templates": available_templates
            }
    
    def _send_template_email(self, 
                            template_name: str,
                            to: str,
                            subject: str,
                            template_vars: Dict[str, Any] = None,
                            cc: str = None,
                            bcc: str = None,
                            is_html: bool = True) -> Dict[str, Any]:
        """
        Send an email using a template.
        
        Args:
            template_name: Name of the template to use
            to: Comma-separated recipient email address(es)
            subject: Email subject
            template_vars: Variables to substitute in the template
            cc: Comma-separated carbon copy recipient(s)
            bcc: Comma-separated blind carbon copy recipient(s)
            is_html: Whether to treat the template as HTML
            
        Returns:
            Dict containing status and message
        """
        # Get the template
        template = self.templates.get(template_name)
        if not template:
            available_templates = list(self.templates.keys())
            return {
                "status": "error", 
                "message": f"Template '{template_name}' not found",
                "available_templates": available_templates
            }
        
        # Apply template variables
        body = template
        if template_vars:
            for key, value in template_vars.items():
                placeholder = f"{{{{{key}}}}}"
                body = body.replace(placeholder, str(value))
        
        # Send the email with the processed template
        return self._send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            is_html=is_html
        )
    
    def _save_draft(self, draft_id: str, draft_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save an email draft for later use."""
        if not draft_id:
            return {"status": "error", "message": "Draft ID is required"}
        
        if not draft_data:
            return {"status": "error", "message": "No draft data provided"}
        
        try:
            self.drafts[draft_id] = draft_data
            return {
                "status": "success", 
                "message": f"Draft '{draft_id}' saved successfully",
                "draft_id": draft_id
            }
        except Exception as e:
            self.logger.error(f"Error saving draft: {str(e)}", exc_info=True)
            return {"status": "error", "message": f"Failed to save draft: {str(e)}"} 