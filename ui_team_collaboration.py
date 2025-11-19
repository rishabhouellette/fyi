"""
Team Collaboration Module for FYI Social Media Management Platform
Multi-user team management, permissions, and approval workflows
"""
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from datetime import datetime
from typing import List, Dict
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

# Role definitions with permissions
ROLES = {
    "admin": ["create_post", "approve_post", "publish_post", "manage_team", "view_analytics", "manage_content"],
    "editor": ["create_post", "view_analytics", "manage_content"],
    "publisher": ["approve_post", "publish_post", "view_analytics"],
    "viewer": ["view_analytics"],
}

class TeamCollaborationFrame(ctk.CTkFrame):
    """Team management with roles, permissions, and approval workflows"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.selected_user = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create team collaboration UI"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Team Collaboration", font=("Arial", 18, "bold")).pack(side="left")
        
        ctk.CTkButton(
            header_frame, text="➕ Add Team Member", width=150,
            command=self._add_team_member
        ).pack(side="right", padx=5)
        
        # Main tabs for Team Members and Approval Queue
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("Team Members")
        self.tabview.add("Approval Queue")
        self.tabview.add("Permissions")
        
        # ===== TEAM MEMBERS TAB =====
        team_tab = self.tabview.tab("Team Members")
        
        self.team_list = ctk.CTkScrollableFrame(team_tab, fg_color="#1a1a1a")
        self.team_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== APPROVAL QUEUE TAB =====
        approval_tab = self.tabview.tab("Approval Queue")
        
        status_frame = ctk.CTkFrame(approval_tab)
        status_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(status_frame, text="Filter:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.approval_filter = ctk.CTkComboBox(
            status_frame, values=["All", "Pending", "Approved", "Rejected"],
            state="readonly", width=120
        )
        self.approval_filter.set("Pending")
        self.approval_filter.pack(side="left", padx=5)
        self.approval_filter.configure(command=self._refresh_approval_queue)
        
        self.approval_list = ctk.CTkScrollableFrame(approval_tab, fg_color="#1a1a1a")
        self.approval_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== PERMISSIONS TAB =====
        perms_tab = self.tabview.tab("Permissions")
        
        # Role definitions display
        roles_frame = ctk.CTkScrollableFrame(perms_tab, fg_color="#1a1a1a")
        roles_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for role_name, permissions in ROLES.items():
            self._create_role_widget(roles_frame, role_name, permissions)
    
    def refresh(self):
        """Refresh team data"""
        self._refresh_team_members()
        self._refresh_approval_queue()
    
    def _refresh_team_members(self):
        """Display team members"""
        for widget in self.team_list.winfo_children():
            widget.destroy()
        
        # Mock team members - in real app, fetch from database
        team_members = [
            {"id": 1, "name": "You", "email": "admin@example.com", "role": "admin", "status": "active"},
            {"id": 2, "name": "John Doe", "email": "john@example.com", "role": "editor", "status": "active"},
            {"id": 3, "name": "Jane Smith", "email": "jane@example.com", "role": "publisher", "status": "active"},
        ]
        
        for member in team_members:
            self._create_member_widget(member)
    
    def _create_member_widget(self, member: Dict):
        """Create team member widget"""
        widget = ctk.CTkFrame(
            self.team_list, fg_color="#333333", border_width=1, border_color="#444444"
        )
        widget.pack(fill="x", padx=5, pady=5)
        
        # Member info
        info_frame = ctk.CTkFrame(widget, fg_color="#333333")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame, text=member['name'], font=("Arial", 12, "bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame, text=member['email'], font=("Arial", 10),
            text_color="#AAAAAA"
        ).pack(anchor="w")
        
        # Role and status
        role_frame = ctk.CTkFrame(widget, fg_color="#333333")
        role_frame.pack(side="right", padx=10, pady=10)
        
        role_label = ctk.CTkLabel(
            role_frame, text=member['role'].upper(), font=("Arial", 10, "bold"),
            fg_color="#2B6FFF", text_color="#FFFFFF", padx=8, pady=4,
            corner_radius=3
        )
        role_label.pack(side="left", padx=5)
        
        status_color = "#51CF66" if member['status'] == "active" else "#FF6B6B"
        status_label = ctk.CTkLabel(
            role_frame, text=member['status'].upper(), font=("Arial", 9),
            fg_color=status_color, text_color="#FFFFFF", padx=6, pady=3,
            corner_radius=3
        )
        status_label.pack(side="left", padx=5)
        
        # Actions
        if member['id'] != 1:  # Don't allow editing self
            ctk.CTkButton(
                role_frame, text="Edit", width=50,
                command=lambda: self._edit_member(member)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                role_frame, text="🗑️", width=30, fg_color="#FF6B6B",
                command=lambda: self._remove_member(member)
            ).pack(side="left", padx=2)
    
    def _add_team_member(self):
        """Add new team member"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Team Member")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # Email
        ctk.CTkLabel(dialog, text="Email:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15, 0))
        email_entry = ctk.CTkEntry(dialog, placeholder_text="member@example.com")
        email_entry.pack(fill="x", padx=15, pady=5)
        
        # Name
        ctk.CTkLabel(dialog, text="Full Name:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(10, 0))
        name_entry = ctk.CTkEntry(dialog, placeholder_text="John Doe")
        name_entry.pack(fill="x", padx=15, pady=5)
        
        # Role
        ctk.CTkLabel(dialog, text="Role:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(10, 0))
        role_combo = ctk.CTkComboBox(
            dialog, values=list(ROLES.keys()), state="readonly"
        )
        role_combo.set("editor")
        role_combo.pack(fill="x", padx=15, pady=5)
        
        def save_member():
            email = email_entry.get().strip()
            name = name_entry.get().strip()
            role = role_combo.get()
            
            if not email or not name:
                messagebox.showwarning("Warning", "Fill all fields")
                return
            
            self.db.log_activity(
                self.team_id, 1, "add_team_member",
                "team_collaboration", None,
                {"email": email, "name": name, "role": role}
            )
            
            messagebox.showinfo("Success", f"Added {name} as {role}")
            dialog.destroy()
            self._refresh_team_members()
        
        ctk.CTkButton(dialog, text="Add Member", command=save_member).pack(pady=20)
    
    def _edit_member(self, member: Dict):
        """Edit team member role"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {member['name']}")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        
        ctk.CTkLabel(dialog, text=f"New role for {member['name']}:", font=("Arial", 10)).pack(pady=10)
        
        role_combo = ctk.CTkComboBox(
            dialog, values=list(ROLES.keys()), state="readonly"
        )
        role_combo.set(member['role'])
        role_combo.pack(fill="x", padx=15, pady=5)
        
        def save_role():
            new_role = role_combo.get()
            self.db.log_activity(
                self.team_id, 1, "edit_team_member",
                "team_collaboration", member['id'],
                {"new_role": new_role}
            )
            messagebox.showinfo("Success", f"Updated role to {new_role}")
            dialog.destroy()
            self._refresh_team_members()
        
        ctk.CTkButton(dialog, text="Save", command=save_role).pack(pady=10)
    
    def _remove_member(self, member: Dict):
        """Remove team member"""
        if messagebox.askyesno("Confirm", f"Remove {member['name']} from team?"):
            self.db.log_activity(
                self.team_id, 1, "remove_team_member",
                "team_collaboration", member['id'],
                {"member_name": member['name']}
            )
            messagebox.showinfo("Success", f"Removed {member['name']}")
            self._refresh_team_members()
    
    def _refresh_approval_queue(self):
        """Refresh approval queue"""
        for widget in self.approval_list.winfo_children():
            widget.destroy()
        
        filter_status = self.approval_filter.get()
        
        # Mock pending approvals
        approvals = [
            {"id": 1, "post_title": "New Product Launch Video", "created_by": "John Doe", "status": "pending", "created": "2024-01-15"},
            {"id": 2, "post_title": "Monthly Newsletter", "created_by": "Jane Smith", "status": "pending", "created": "2024-01-15"},
            {"id": 3, "post_title": "Customer Testimonial", "created_by": "John Doe", "status": "approved", "created": "2024-01-14"},
        ]
        
        if filter_status != "All":
            approvals = [a for a in approvals if a['status'].lower() == filter_status.lower()]
        
        if not approvals:
            ctk.CTkLabel(
                self.approval_list, text="No posts in queue",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for approval in approvals:
            self._create_approval_widget(approval)
    
    def _create_approval_widget(self, approval: Dict):
        """Create approval item widget"""
        widget = ctk.CTkFrame(
            self.approval_list, fg_color="#333333", border_width=1, border_color="#444444"
        )
        widget.pack(fill="x", padx=5, pady=5)
        
        # Content
        content_frame = ctk.CTkFrame(widget, fg_color="#333333")
        content_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            content_frame, text=approval['post_title'], font=("Arial", 12, "bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            content_frame, text=f"By: {approval['created_by']} • {approval['created']}", 
            font=("Arial", 9), text_color="#AAAAAA"
        ).pack(anchor="w")
        
        # Status badge
        status_color = "#FFD43B" if approval['status'] == "pending" else "#51CF66" if approval['status'] == "approved" else "#FF6B6B"
        status_label = ctk.CTkLabel(
            content_frame, text=approval['status'].upper(), font=("Arial", 9, "bold"),
            fg_color=status_color, text_color="#000000", padx=6, pady=3,
            corner_radius=3
        )
        status_label.pack(anchor="w", pady=(5, 0))
        
        # Actions
        if approval['status'] == "pending":
            action_frame = ctk.CTkFrame(widget, fg_color="#333333")
            action_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(
                action_frame, text="✓ Approve", width=80, fg_color="#51CF66",
                command=lambda: self._approve_post(approval)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                action_frame, text="✕ Reject", width=80, fg_color="#FF6B6B",
                command=lambda: self._reject_post(approval)
            ).pack(side="left", padx=2)
    
    def _approve_post(self, approval: Dict):
        """Approve pending post"""
        self.db.log_activity(
            self.team_id, 1, "approve_post",
            "team_collaboration", approval['id'],
            {"post_title": approval['post_title']}
        )
        messagebox.showinfo("Success", f"Approved: {approval['post_title']}")
        self._refresh_approval_queue()
    
    def _reject_post(self, approval: Dict):
        """Reject post"""
        dialog = ctk.CTkInputDialog(text="Reason for rejection:", title="Reject Post")
        reason = dialog.get_input()
        
        if reason:
            self.db.log_activity(
                self.team_id, 1, "reject_post",
                "team_collaboration", approval['id'],
                {"post_title": approval['post_title'], "reason": reason}
            )
            messagebox.showinfo("Success", f"Rejected: {approval['post_title']}")
            self._refresh_approval_queue()
    
    def _create_role_widget(self, parent, role_name: str, permissions: List[str]):
        """Create role definition widget"""
        frame = ctk.CTkFrame(parent, fg_color="#333333", border_width=1, border_color="#444444")
        frame.pack(fill="x", padx=5, pady=5)
        
        # Role name
        ctk.CTkLabel(
            frame, text=role_name.upper(), font=("Arial", 12, "bold"),
            text_color="#2B6FFF"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Permissions list
        for perm in permissions:
            perm_text = perm.replace("_", " ").title()
            ctk.CTkLabel(
                frame, text=f"✓ {perm_text}", font=("Arial", 10),
                text_color="#CCCCCC"
            ).pack(anchor="w", padx=20, pady=2)
        
        # Add padding
        ctk.CTkLabel(frame, text="").pack(pady=5)
