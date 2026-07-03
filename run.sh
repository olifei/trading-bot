#!/bin/bash

chmod +x trading_bot_server.py

echo "正在启动交易助手服务器..."
python trading_bot_server.py &
SERVER_PID=$!
echo "服务器PID: $SERVER_PID"

sleep 3
echo "正在启动Streamlit前端 on port $PORT..."
streamlit run streamlit_frontend.py --server.port ${PORT:-8080} --server.headless true

echo "正在关闭交易助手服务器..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null
echo "服务器已关闭"