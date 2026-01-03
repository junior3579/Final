#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependências do Backend
pip install -r requirements.txt

# Instalar pnpm (se não estiver disponível)
if ! command -v pnpm &> /dev/null
then
    npm install -g pnpm
fi

# Instalar dependências do Frontend e Buildar
pnpm install
pnpm run build

# Limpar diretório static do backend e copiar novo build
mkdir -p backend/static
rm -rf backend/static/*
cp -r dist/* backend/static/

echo "Build finalizado com sucesso!"
