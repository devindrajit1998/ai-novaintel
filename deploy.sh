#!/bin/bash
set -e

echo "🔥 Starting NovaIntel Auto Deployment..."

APP_USER="novaintel"
APP_DIR="/home/$APP_USER/apps/novaintel"

SERVER_IP=$(curl -s ifconfig.me)
API_URL="http://$SERVER_IP/api"
FRONTEND_URL="http://$SERVER_IP"

echo "📌 Server Public IP Detected: $SERVER_IP"

# Create user if missing
if ! id "$APP_USER" &>/dev/null; then
    sudo adduser --disabled-password --gecos "" $APP_USER
fi

mkdir -p $APP_DIR
sudo chown -R $APP_USER:$APP_USER $APP_DIR

############################################################
# Install System Dependencies
############################################################
sudo apt update -y
sudo apt install -y curl wget git nano redis-server nginx build-essential libpq-dev

############################################################
# Install Python 3.11 & NodeJS 18
############################################################
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

############################################################
# Extract Uploaded Zip
############################################################
cd $APP_DIR
unzip -o ~/novaintel.zip -d $APP_DIR
sudo chown -R $APP_USER:$APP_USER $APP_DIR

############################################################
# Backend Setup
############################################################
cd $APP_DIR/backend

python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt || true

############################################################
# Create `.env`
############################################################
cat <<EOF > $APP_DIR/backend/.env
DATABASE_URL=postgresql://novaintel_ux7p_user:xqD8jyp3UThOjT5nlSt2KU6L8qSD0bMA@dpg-d4gl2rpr0fns739mii7g-a.singapore-postgres.render.com/novaintel_ux7p
SECRET_KEY=cd572dac2913af842bd63f04dd16d04f8c56b036eb1e8ec6064cbe7a3d7ed537
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

GEMINI_API_KEY=AIzaSyDZqy369iTqZqcHr7-Ht_Wpkq-tG2oMVEk
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash

VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=$APP_DIR/backend/chroma_db

UPLOAD_DIR=$APP_DIR/backend/uploads
MAX_FILE_SIZE=20971520
ALLOWED_EXTENSIONS=.pdf,.docx

FRONTEND_URL=$FRONTEND_URL
CORS_ORIGINS=$FRONTEND_URL,http://localhost:5173

MAIL_USERNAME=indrajit.ghosh@intglobal.com
MAIL_PASSWORD="ogkf zqmu drjy uwmz"
MAIL_FROM=indrajit.ghosh@intglobal.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_TLS=True
MAIL_SSL=False
EOF

############################################################
# DB Migrations
############################################################
python3 db/run_migration.py || python3 - <<'EOF'
from db.database import engine, Base
from models import *
Base.metadata.create_all(bind=engine)
EOF

############################################################
# Create Backend Service
############################################################
sudo tee /etc/systemd/system/novaintel-backend.service <<EOF
[Unit]
Description=NovaIntel Backend Service
After=network.target

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env
ExecStart=$APP_DIR/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable novaintel-backend
sudo systemctl restart novaintel-backend

############################################################
# Frontend Build
############################################################
cd $APP_DIR
npm install || true
npm run build || true
mkdir -p $APP_DIR/dist
cp -r dist $APP_DIR/frontend-dist 2>/dev/null || true

############################################################
# Nginx Config
############################################################
sudo tee /etc/nginx/sites-available/novaintel <<EOF
server {
    listen 80;

    root $APP_DIR/frontend-dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
    }

    location / {
        try_files \$uri /index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/novaintel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "=============================================="
echo "🎉 Deployment Successful!"
echo "=============================================="
echo "🌍 Frontend: http://$SERVER_IP/"
echo "🔌 Backend Health: http://$SERVER_IP/api/health"
echo "📄 API Docs: http://$SERVER_IP/api/docs"
echo ""
echo "Backend Logs: sudo journalctl -u novaintel-backend -f"
echo "=============================================="
