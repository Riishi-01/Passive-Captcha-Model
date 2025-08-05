"""
Site Routes for Frontend Deployment
Serves the UIDAI integrated HTML files with passive captcha
"""

from flask import Blueprint, send_from_directory, render_template_string, request
import os
import logging

# Create blueprint for site routes
site_bp = Blueprint('site', __name__)

# Path to the site directory
SITE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'site ')

@site_bp.route('/site')
def site_index():
    """Main site index with available pages"""
    try:
        # List available files in the site directory
        files = []
        if os.path.exists(SITE_DIR):
            for file in os.listdir(SITE_DIR):
                if file.endswith('.html'):
                    files.append(file)
        
        index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UIDAI Site Directory - Passive Captcha Protected</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 2rem;
            font-size: 2.5rem;
        }
        .security-badge {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            display: inline-block;
            margin-left: 10px;
        }
        .file-list {
            list-style: none;
            padding: 0;
        }
        .file-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin: 10px 0;
            padding: 15px;
            transition: all 0.3s ease;
        }
        .file-item:hover {
            background: #e9ecef;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,123,255,0.2);
        }
        .file-link {
            text-decoration: none;
            color: #007bff;
            font-weight: 500;
            font-size: 1.1rem;
        }
        .file-description {
            color: #6c757d;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        .protection-info {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            🏛️ UIDAI Site Directory
            <span class="security-badge">🛡️ PROTECTED</span>
        </h1>
        
        <div class="protection-info">
            <h3 style="margin-top: 0; color: #155724;">🛡️ Security Status</h3>
            <p style="margin-bottom: 0; color: #155724;">All pages are protected by advanced Passive Captcha technology, providing real-time bot detection and behavioral analysis without user interaction.</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">""" + str(len(files)) + """</div>
                <div class="stat-label">Protected Pages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">100%</div>
                <div class="stat-label">Protection Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">Real-time</div>
                <div class="stat-label">Monitoring</div>
            </div>
        </div>

        <h2>📄 Available Pages</h2>
        <ul class="file-list">""" + ''.join([f"""
            <li class="file-item">
                <a href="/site/{file}" class="file-link">📄 {file}</a>
                <div class="file-description">
                    {'UIDAI Home Page with integrated passive captcha protection' if 'Home' in file 
                     else 'UIDAI About Page with behavioral analysis' if 'About' in file
                     else 'Enhanced UIDAI page with real-time security monitoring' if 'integrated' in file
                     else 'Government page with advanced bot detection'}
                </div>
            </li>""" for file in files]) + """
        </ul>

        <div style="text-align: center; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #dee2e6;">
            <p style="color: #6c757d;">
                <strong>🔒 Security Features:</strong> 
                Mouse tracking • Keyboard analysis • Scroll monitoring • Real-time detection • ML classification
            </p>
            <a href="/prototype" style="background: linear-gradient(45deg, #007bff, #0056b3); color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;">
                📊 View Analytics Dashboard
            </a>
        </div>
    </div>
</body>
</html>
        """
        
        return index_html
        
    except Exception as e:
        logging.error(f"Error serving site index: {e}")
        return f"Error loading site index: {e}", 500

@site_bp.route('/site/<filename>')
def serve_site_file(filename):
    """Serve specific HTML files from the site directory"""
    try:
        # Security check - only allow .html files
        if not filename.endswith('.html'):
            return "Only HTML files are allowed", 403
            
        file_path = os.path.join(SITE_DIR, filename)
        
        if not os.path.exists(file_path):
            return f"File {filename} not found", 404
            
        # Read and serve the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Log the access
        logging.info(f"Served site file: {filename} from {request.remote_addr}")
        
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        logging.error(f"Error serving site file {filename}: {e}")
        return f"Error loading file: {e}", 500

@site_bp.route('/site/assets/<path:filename>')
def serve_site_assets(filename):
    """Serve asset files from the site directory"""
    try:
        assets_dir = os.path.join(SITE_DIR, 'assets')
        if os.path.exists(assets_dir):
            return send_from_directory(assets_dir, filename)
        else:
            return "Asset not found", 404
    except Exception as e:
        logging.error(f"Error serving site asset {filename}: {e}")
        return f"Error loading asset: {e}", 500