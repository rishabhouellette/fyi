-- Enhanced Database Schema for FYI Social Media Management Platform
-- Supports all 15 features: scheduling, analytics, team, inbox, library, listening, etc.

-- Users and Teams
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'viewer',  -- admin, editor, viewer
    two_factor_enabled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT DEFAULT 'viewer',  -- admin, editor, viewer
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(team_id, user_id)
);

-- Accounts (Social Media Accounts)
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    platform TEXT NOT NULL,  -- facebook, instagram, twitter, linkedin, youtube, tiktok, pinterest, etc.
    account_name TEXT NOT NULL,
    account_id TEXT NOT NULL,
    page_id TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    UNIQUE(team_id, platform, account_id)
);

-- Posts and Scheduling
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    media_paths TEXT,  -- JSON array of file paths
    scheduled_time TIMESTAMP,
    published_time TIMESTAMP,
    status TEXT DEFAULT 'draft',  -- draft, scheduled, published, failed, archived
    platform_post_id TEXT,
    approval_status TEXT DEFAULT 'pending',  -- pending, approved, rejected
    approval_by_user_id INTEGER,
    approval_at TIMESTAMP,
    internal_notes TEXT,
    created_by_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (approval_by_user_id) REFERENCES users(id)
);

-- Analytics and Performance Metrics
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    post_id INTEGER,
    platform TEXT NOT NULL,
    metric_date DATE NOT NULL,
    reach INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    engagement INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    followers INTEGER DEFAULT 0,
    follower_growth INTEGER DEFAULT 0,
    fetch_from_platform TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    UNIQUE(team_id, account_id, post_id, metric_date)
);

-- Content Library and Assets
CREATE TABLE content_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- image, video, template, hashtag, caption
    content TEXT,  -- File path or actual content
    tags TEXT,  -- JSON array of tags
    platform_compatible TEXT,  -- JSON array of platforms
    created_by_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- Social Listening and Monitoring
CREATE TABLE monitoring_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    type TEXT DEFAULT 'keyword',  -- keyword, hashtag, mention
    platforms TEXT,  -- JSON array
    alert_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE monitoring_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    source_user TEXT,
    content TEXT,
    url TEXT,
    sentiment TEXT,  -- positive, negative, neutral
    alert_sent BOOLEAN DEFAULT 0,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (keyword_id) REFERENCES monitoring_keywords(id)
);

-- Social Inbox (Messages, Comments, DMs)
CREATE TABLE social_inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    message_id TEXT NOT NULL,
    from_user_id TEXT,
    from_user_name TEXT,
    from_user_avatar TEXT,
    message_content TEXT NOT NULL,
    message_type TEXT,  -- dm, comment, mention, reply
    post_id INTEGER,
    parent_message_id TEXT,
    is_read BOOLEAN DEFAULT 0,
    is_replied BOOLEAN DEFAULT 0,
    replied_by_user_id INTEGER,
    replied_at TIMESTAMP,
    reply_content TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (replied_by_user_id) REFERENCES users(id),
    UNIQUE(team_id, platform, message_id)
);

-- First Comments and Hashtags
CREATE TABLE first_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    delay_seconds INTEGER DEFAULT 0,
    posted BOOLEAN DEFAULT 0,
    posted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE TABLE hashtag_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    popularity INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Link Shortening and UTM Tracking
CREATE TABLE shortened_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    original_url TEXT NOT NULL,
    short_code TEXT UNIQUE NOT NULL,
    short_url TEXT UNIQUE NOT NULL,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    clicks INTEGER DEFAULT 0,
    last_clicked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE link_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id INTEGER NOT NULL,
    referer TEXT,
    user_agent TEXT,
    ip_address TEXT,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (link_id) REFERENCES shortened_links(id)
);

-- API Integrations and Webhooks
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    permissions TEXT,  -- JSON array
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

CREATE TABLE webhooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    event_type TEXT,  -- post_published, post_scheduled, comment_received, etc.
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Activity Logging and Audit
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- create_post, publish_post, approve_post, reply_message, etc.
    resource_type TEXT,
    resource_id INTEGER,
    details TEXT,  -- JSON object with details
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Settings and Configuration
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    UNIQUE(team_id, key)
);

-- Indexes for Performance
CREATE INDEX idx_posts_team_account ON posts(team_id, account_id);
CREATE INDEX idx_posts_scheduled_time ON posts(scheduled_time);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_analytics_team_date ON analytics(team_id, metric_date);
CREATE INDEX idx_social_inbox_team_account ON social_inbox(team_id, account_id);
CREATE INDEX idx_social_inbox_is_read ON social_inbox(is_read);
CREATE INDEX idx_activity_log_team_user ON activity_log(team_id, user_id);
CREATE INDEX idx_monitoring_alerts_team ON monitoring_alerts(team_id);
