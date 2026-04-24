#!/bin/bash
echo "=========================================="
echo "  Vue3 + Django-Ninja CI 配置向导"
echo "=========================================="
echo ""

read -p "请输入服务器 IP: " HOST
read -p "请输入前端部署路径 (默认: /www/wwwroot/template-vue3-django-ninja): " FRONTEND_PATH
FRONTEND_PATH=${FRONTEND_PATH:-/www/wwwroot/template-vue3-django-ninja}
read -p "请输入后端部署路径 (默认: /www/template-vue3-django-ninja): " BACKEND_PATH
BACKEND_PATH=${BACKEND_PATH:-/www/template-vue3-django-ninja}
read -p "请输入虚拟环境路径 (默认: /www/template-vue3-django-ninja/venv): " VENV_PATH
VENV_PATH=${VENV_PATH:-/www/template-vue3-django-ninja/venv}

echo ""
echo "请在 GitHub 仓库页面手动配置以下 Secrets 和 Variables："
echo ""
echo "【Secrets】"
echo "  SSH_PRIVATE_KEY"
echo ""
echo "【Variables - 必填】"
echo "  DEPLOY_SERVER_HOST = $HOST"
echo "  DEPLOY_FRONTEND_PATH = $FRONTEND_PATH"
echo "  DEPLOY_BACKEND_PATH = $BACKEND_PATH"
echo "  DEPLOY_VENV_PATH = $VENV_PATH"
echo ""
echo "【Variables - 建议配置】"
echo "  DJANGO_SETTINGS_MODULE = config.settings.production"
echo "  ENABLE_MIGRATE = true"
echo "  ENABLE_COLLECTSTATIC = false"
echo "  DEPLOY_RESTART_COMMAND = sudo systemctl restart template-vue3-django-ninja"
echo "  APP_PORT = 8000"
echo ""
echo "配置完成后，执行 git push 即可触发首次部署。"
echo "=========================================="
