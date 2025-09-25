#!/bin/bash
echo "🚀 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "📦 Instalando dependencias del sistema para procesamiento de documentos..."
apt-get update && apt-get install -y \
    libmagic-dev \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    python3-pip

echo "✅ Build completado exitosamente!"
