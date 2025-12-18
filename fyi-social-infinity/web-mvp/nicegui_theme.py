"""
FYI Social ∞ - NiceGUI Theme Implementation
2035 Cyber-Futuristic Design System for Web MVP
"""

# Custom CSS for NiceGUI to match the exact 2035 aesthetic
CYBER_THEME_CSS = """
<style>
    /* Import Satoshi Font */
    @import url('../assets/fonts/Satoshi/satoshi.css');
    
    /* 2035 Cyber Color System */
    :root {
        --cyber-bg: #000000;
        --cyber-void: #0a0a1f;
        --cyber-primary: #00f2ff;
        --cyber-purple: #8b00ff;
        --cyber-green: #00ff9d;
        --cyber-glass: rgba(10, 10, 31, 0.09);
        --cyber-border: rgba(0, 242, 255, 0.4);
    }
    
    /* Global Background */
    body {
        font-family: 'Satoshi', system-ui, sans-serif !important;
        background: linear-gradient(180deg, var(--cyber-void) 0%, var(--cyber-bg) 100%) !important;
        color: #ffffff !important;
    }
    
    /* NiceGUI Card Overrides - Glassmorphism */
    .q-card {
        background: var(--cyber-glass) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid var(--cyber-border) !important;
        border-radius: 16px !important;
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.4) !important;
        animation: float 6s ease-in-out infinite;
    }
    
    /* Buttons - Glowing Border Style */
    .q-btn {
        font-family: 'Satoshi', sans-serif !important;
        font-weight: 500 !important;
        border: 2px solid var(--cyber-primary) !important;
        background: transparent !important;
        color: var(--cyber-primary) !important;
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .q-btn:hover {
        background: var(--cyber-primary) !important;
        color: #000000 !important;
        box-shadow: 0 0 40px rgba(0, 242, 255, 0.8) !important;
        transform: scale(1.02);
    }
    
    /* Input Fields - Cyber Style */
    .q-field__control {
        background: var(--cyber-glass) !important;
        border: 1px solid var(--cyber-border) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    
    .q-field__control:hover {
        border-color: var(--cyber-primary) !important;
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.3) !important;
    }
    
    /* Typography - Satoshi Font */
    .text-h1, .text-h2, .text-h3, .text-h4, .text-h5, .text-h6 {
        font-family: 'Satoshi', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Gradient Text */
    .cyber-text-gradient {
        background: linear-gradient(90deg, var(--cyber-primary) 0%, var(--cyber-purple) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Float Animation */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* Glow Animation */
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 242, 255, 0.4); }
        50% { box-shadow: 0 0 40px rgba(0, 242, 255, 0.8); }
    }
    
    .animate-glow {
        animation: glow 2s ease-in-out infinite;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--cyber-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--cyber-primary);
        border-radius: 4px;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.5);
    }
    
    /* Upload Zone Styling */
    .upload-zone {
        border: 4px dashed var(--cyber-primary);
        border-radius: 50%;
        padding: 60px;
        text-align: center;
        animation: glow 3s ease-in-out infinite;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        transform: scale(1.05);
        border-color: var(--cyber-green);
    }
    
    /* Virality Meter - Arc Reactor Style */
    .virality-meter {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        border: 6px solid var(--cyber-primary);
        box-shadow: 
            0 0 40px rgba(0, 242, 255, 0.8),
            inset 0 0 20px rgba(0, 242, 255, 0.3);
        animation: rotate 10s linear infinite;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* AI Status Orb */
    .ai-orb {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: radial-gradient(circle, var(--cyber-purple), #5a0099);
        box-shadow: 0 0 30px rgba(139, 0, 255, 0.8);
        animation: breathe 3s ease-in-out infinite;
    }
    
    @keyframes breathe {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    /* Sidebar Styling */
    .q-drawer {
        background: rgba(10, 10, 31, 0.5) !important;
        backdrop-filter: blur(16px) !important;
        border-right: 1px solid var(--cyber-border) !important;
    }
    
    /* Selection Styling */
    ::selection {
        background: var(--cyber-primary);
        color: var(--cyber-bg);
    }
</style>
"""

def apply_cyber_theme(app):
    """Apply the 2035 cyber theme to a NiceGUI app"""
    from nicegui import ui
    
    # Inject custom CSS
    ui.add_head_html(CYBER_THEME_CSS)
    
    # Set dark mode
    ui.colors(
        primary='#00f2ff',
        secondary='#8b00ff',
        accent='#00ff9d',
        dark='#000000',
        positive='#00ff9d',
        negative='#ff006e',
        info='#00f2ff',
        warning='#ffb800'
    )
